import logging
import os
import re
import random
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, model_validator

from mock_db import AZCON_COMPANIES


load_dotenv()
logger = logging.getLogger(__name__)


class CategoryEnum(str, Enum):
    IT_TECH = "IT & Tech"
    CONSTRUCTION = "Construction & Heavy"
    LOGISTICS = "Logistics & Aviation"
    MARITIME = "Maritime"
    OTHERS = "Others"


class UnitEnum(str, Enum):
    PIECE = "piece"
    KG = "kg"
    TON = "ton"
    LITER = "liter"
    METER = "meter"
    BOX = "box"
    CONTAINER = "container"


class SearchPayload(BaseModel):
    procurement_type: Literal["product", "service"]
    query: str = Field(..., min_length=2)
    category: CategoryEnum = CategoryEnum.OTHERS
    unit: Optional[UnitEnum] = None
    total_budget: float = Field(..., gt=0)
    min_reliability_score: float = Field(3.5, ge=1.0, le=5.0)
    azcon_reference_required: bool = False

    quantity: Optional[int] = Field(default=None, gt=0)
    deadline: Optional[date] = None

    service_duration: Optional[str] = None
    start_date: Optional[date] = None
    service_level: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        for field_name in ["unit", "quantity", "deadline", "service_duration", "start_date", "service_level"]:
            if cleaned.get(field_name) == "":
                cleaned[field_name] = None
        return cleaned

    @model_validator(mode="after")
    def validate_by_type(self) -> "SearchPayload":
        if self.procurement_type == "product":
            if self.quantity is None:
                raise ValueError("Məhsul üçün quantity tələb olunur.")
            if self.deadline is None:
                raise ValueError("Məhsul üçün deadline tələb olunur.")
            if self.unit is None:
                raise ValueError("Məhsul üçün unit tələb olunur.")
        else:
            if not self.service_duration:
                raise ValueError("Xidmət üçün service_duration tələb olunur.")
            if self.start_date is None:
                raise ValueError("Xidmət üçün start_date tələb olunur.")
            if not self.service_level:
                raise ValueError("Xidmət üçün service_level tələb olunur.")
        return self


class Offer(BaseModel):
    source_type: Literal["Internal AZCON", "External Web"]
    company_name: str
    item_name: str
    price_per_unit: float
    total_price: float
    quantity_available: Optional[int] = None
    service_duration: Optional[str] = None
    reliability_score: float = Field(..., ge=1.0, le=5.0)
    source_link: str
    logistics_info: str
    vendor_name: Optional[str] = None
    origin_country: Optional[str] = None
    logistics_cost: float = Field(default=0.0, ge=0.0)
    smart_batching_applied: bool = False


class OfferList(BaseModel):
    offers: List[Offer] = Field(default_factory=list)


class APIResponse(BaseModel):
    query: str
    procurement_type: Literal["product", "service"]
    offers: List[Offer]


def build_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY tapılmadı.")
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        temperature=0.0,
        google_api_key=api_key,
    )


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def derive_max_unit_price(payload: SearchPayload) -> float:
    qty = payload.quantity if payload.procurement_type == "product" else 1
    return round(payload.total_budget / max(1, qty or 1), 2)


def extract_or_simulate_price(snippet: str, max_price: float) -> float:
    text = str(snippet or "")
    # Examples handled: "$25.99", "25 USD", "100 AZN", "EUR 40"
    price_pattern = re.compile(
        r"(?i)(?:[$€£]\s*(\d+(?:[.,]\d{1,2})?)|(\d+(?:[.,]\d{1,2})?)\s*(?:usd|azn|eur|gbp)|(?:usd|azn|eur|gbp)\s*(\d+(?:[.,]\d{1,2})?))"
    )
    match = price_pattern.search(text)
    if match:
        raw = next((g for g in match.groups() if g), None)
        if raw is not None:
            parsed = float(raw.replace(",", "."))
            capped = min(parsed, max_price * 2)
            if capped > 0:
                return round(capped, 2)

    low = max_price * 0.60
    high = max_price * 0.95
    if high <= 0:
        return 0.0
    if low >= high:
        return round(high, 2)
    return round(random.uniform(low, high), 2)


def build_internal_candidates(payload: SearchPayload, max_unit_price: float) -> List[Dict[str, Any]]:
    query_l = normalize_text(payload.query)
    candidates: List[Dict[str, Any]] = []

    def query_matches(text: str, tags: List[str]) -> bool:
        text_l = normalize_text(text)
        if query_l and query_l in text_l:
            return True
        tag_values = [normalize_text(tag) for tag in (tags or [])]
        return any(query_l == tag for tag in tag_values)

    for company, company_data in AZCON_COMPANIES.items():
        if payload.procurement_type == "product":
            for item in company_data.get("surplus_inventory", []):
                if not query_matches(item.get("item_name", ""), item.get("search_tags", [])):
                    continue

                unit_price = float(item.get("price_per_unit", 0))
                reliability = float(item.get("reliability_score", 0))
                qty = payload.quantity or 1
                total_price = round(unit_price * qty, 2)
                if unit_price > max_unit_price or total_price > payload.total_budget:
                    continue
                if reliability < payload.min_reliability_score:
                    continue

                candidates.append(
                    {
                        "source_type": "Internal AZCON",
                        "company_name": company,
                        "item_name": item.get("item_name", payload.query),
                        "price_per_unit": unit_price,
                        "total_price": total_price,
                        "quantity_available": int(item.get("quantity_available", 0)),
                        "service_duration": None,
                        "reliability_score": reliability,
                        "source_link": "Internal",
                        "logistics_info": item.get("logistics_info", "Daxili AZCON logistikası"),
                        "vendor_name": company,
                        "origin_country": "Azerbaijan",
                        "logistics_cost": 0.0,
                        "smart_batching_applied": False,
                    }
                )
        else:
            for service in company_data.get("services", []):
                service_name = str(service.get("name", ""))
                if not query_matches(service_name, service.get("search_tags", [])):
                    continue
                total_price = round(payload.total_budget, 2)
                candidates.append(
                    {
                        "source_type": "Internal AZCON",
                        "company_name": company,
                        "item_name": service_name,
                        "price_per_unit": total_price,
                        "total_price": total_price,
                        "quantity_available": None,
                        "service_duration": payload.service_duration,
                        "reliability_score": 4.5,
                        "source_link": "Internal",
                        "logistics_info": "AZCON daxili xidmət komandası",
                        "vendor_name": company,
                        "origin_country": "Azerbaijan",
                        "logistics_cost": 0.0,
                        "smart_batching_applied": False,
                    }
                )

    candidates.sort(key=lambda x: (-x["reliability_score"], x["total_price"]))
    return candidates


def generate_b2b_dorking_query(
    query: str,
    category: CategoryEnum,
    procurement_type: Literal["product", "service"],
) -> str:
    if procurement_type == "service":
        service_it_sites = (
            "(site:aws.amazon.com OR site:azure.microsoft.com OR site:cloudflare.com "
            "OR site:crowdstrike.com OR site:hackerone.com)"
        )
        service_consulting_sites = (
            "(site:deloitte.com OR site:mckinsey.com OR site:accenture.com OR site:pwc.com)"
        )
        if category in {CategoryEnum.IT_TECH, CategoryEnum.LOGISTICS}:
            base_sites = service_it_sites
        else:
            base_sites = service_consulting_sites
        negatives = "-site:linkedin.com -site:medium.com -site:wikipedia.org"
        return f"{query} enterprise service provider {base_sites} {negatives}"

    product_site_map = {
        CategoryEnum.IT_TECH: "(site:cdw.com OR site:cisco.com OR site:alibaba.com OR site:amazon.com)",
        CategoryEnum.CONSTRUCTION: "(site:thomasnet.com OR site:made-in-china.com OR site:alibaba.com)",
        CategoryEnum.LOGISTICS: "(site:freightos.com OR site:dhl.com OR site:maersk.com OR site:amazon.com)",
        CategoryEnum.MARITIME: "(site:alibaba.com OR site:thomasnet.com OR site:globalsources.com)",
        CategoryEnum.OTHERS: "(site:alibaba.com OR site:globalsources.com OR site:amazon.com)",
    }
    base_sites = product_site_map.get(category, product_site_map[CategoryEnum.OTHERS])
    negatives = "-site:linkedin.com -site:medium.com -site:wikipedia.org (inurl:product OR inurl:store)"
    return f"{query} industrial product supplier {base_sites} {negatives}"


def run_serper_search(query: str) -> Dict[str, Any]:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY tapılmadı.")
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": 10},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def infer_origin_country(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.endswith(".cn") or any(k in host for k in ["alibaba", "made-in-china", "1688"]):
        return "China"
    if host.endswith(".tr"):
        return "Turkey"
    if any(host.endswith(tld) for tld in [".de", ".fr", ".it", ".es", ".nl", ".pl", ".eu"]):
        return "Europe"
    if host.endswith(".uk"):
        return "Europe"
    return "Global"


def estimate_total_kg(unit: UnitEnum, quantity: int) -> float:
    if unit == UnitEnum.KG:
        return float(quantity)
    if unit == UnitEnum.TON:
        return float(quantity) * 1000.0
    if unit == UnitEnum.LITER:
        return float(quantity) * 1.0
    if unit == UnitEnum.METER:
        return float(quantity) * 2.0
    if unit == UnitEnum.BOX:
        return float(quantity) * 10.0
    return float(quantity) * 1.0


def calculate_logistics(
    procurement_type: Literal["product", "service"],
    origin_country: str,
    unit: Optional[UnitEnum],
    quantity: int,
) -> Dict[str, Any]:
    if procurement_type == "service":
        return {
            "delivery_time": "Instant / Digital Activation (Based on SLA)",
            "logistics_cost": 0.0,
            "logistics_info": "Instant / Digital Activation (Based on SLA)",
        }

    total_kg = estimate_total_kg(unit, quantity)
    origin_l = normalize_text(origin_country)

    if any(x in origin_l for x in ["china", "asia", "chinese"]):
        delivery_time = "45-60 days (Sea Freight)"
        cost = round(3.0 * total_kg, 2)
    elif any(x in origin_l for x in ["turkey", "europe", "eu"]):
        delivery_time = "7-14 days (Truck)"
        cost = round(1.5 * total_kg, 2)
    else:
        delivery_time = "15-30 days (Air/Sea Mixed)"
        cost = round(2.2 * total_kg, 2)

    return {
        "delivery_time": delivery_time,
        "logistics_cost": cost,
        "logistics_info": f"{delivery_time}; Estimated logistics cost: {cost:.2f} USD",
    }


def calculate_reliability_score(url: str) -> float:
    host = urlparse(url).netloc.lower()
    top_domains = ["alibaba", "cdw.com", "cisco.com"]
    if any(domain in host for domain in top_domains):
        return 4.9
    if url.lower().startswith("https://"):
        return 3.5
    return 3.0


def build_external_candidates(payload: SearchPayload, serper_results: Dict[str, Any], max_unit_price: float) -> List[Dict[str, Any]]:
    organic = serper_results.get("organic", []) if isinstance(serper_results, dict) else []
    quantity = payload.quantity or 1
    external: List[Dict[str, Any]] = []

    for result in organic:
        if not isinstance(result, dict):
            continue
        title = str(result.get("title", "")).strip()
        link = str(result.get("link", "")).strip()
        snippet = str(result.get("snippet", "")).strip()
        if not link:
            continue

        origin = infer_origin_country(link)
        logistics = calculate_logistics(payload.procurement_type, origin, payload.unit, quantity)
        reliability = calculate_reliability_score(link)
        price_per_unit = extract_or_simulate_price(snippet, max_unit_price)
        if reliability < payload.min_reliability_score:
            continue

        external.append(
            {
                "source_type": "External Web",
                "company_name": title[:60] or "Unknown Vendor",
                "item_name": payload.query,
                "price_per_unit": price_per_unit,
                "total_price": round(price_per_unit * quantity, 2),
                "quantity_available": quantity if payload.procurement_type == "product" else None,
                "service_duration": payload.service_duration if payload.procurement_type == "service" else None,
                "reliability_score": reliability,
                "source_link": link,
                "logistics_info": f"{logistics['logistics_info']} | {snippet[:120]}",
                "vendor_name": title[:80] or "Unknown Vendor",
                "origin_country": origin,
                "logistics_cost": float(logistics["logistics_cost"]),
                "smart_batching_applied": False,
            }
        )
    return external


def map_serper_with_llm(
    llm: ChatGoogleGenerativeAI,
    payload: SearchPayload,
    external_candidates: List[Dict[str, Any]],
) -> OfferList:
    if not external_candidates:
        return OfferList(offers=[])

    structured_llm = llm.with_structured_output(OfferList)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Map each candidate to Offer exactly. "
                    "Do not invent links, prices, reliability, or logistics numbers. "
                    "CRITICAL PRICING RULE: Do NOT blindly assign the max_unit_price to the price_per_unit. "
                    "Look at the provided snippets. If a real price is mentioned, use it. "
                    "If no price is mentioned, assign a realistic, varied market price strictly BETWEEN 60% and 95% "
                    "of the max_unit_price. Every offer MUST have a slightly different price. "
                    "Never use the exact max budget. "
                    "Keep source_type='External Web'. Return OfferList."
                ),
            ),
            ("human", "payload={payload}\nexternal_candidates={external_candidates}"),
        ]
    )
    chain = prompt | structured_llm
    return chain.invoke(
        {
            "payload": payload.model_dump_json(),
            "external_candidates": external_candidates,
        }
    )


def manual_external_fallback(
    payload: SearchPayload,
    external_candidates: List[Dict[str, Any]],
    serper_results: Dict[str, Any],
) -> List[Offer]:
    offers: List[Offer] = []
    candidates_by_link = {str(c.get("source_link", "")).strip(): c for c in external_candidates}
    organic = serper_results.get("organic", []) if isinstance(serper_results, dict) else []

    for result in organic:
        if not isinstance(result, dict):
            continue
        link = str(result.get("link", "")).strip()
        title = str(result.get("title", "")).strip()
        snippet = str(result.get("snippet", "")).strip()
        if not link:
            continue
        base = candidates_by_link.get(link)
        quantity = payload.quantity or 1
        if base:
            offers.append(Offer.model_validate(base))
            continue

        origin = infer_origin_country(link)
        logistics = calculate_logistics(payload.procurement_type, origin, payload.unit, quantity)
        max_unit_price = derive_max_unit_price(payload)
        price_per_unit = extract_or_simulate_price(snippet, max_unit_price)
        offers.append(
            Offer(
                source_type="External Web",
                company_name=(title[:30] if title else "Unknown Vendor"),
                item_name=payload.query,
                price_per_unit=price_per_unit,
                total_price=round(price_per_unit * quantity, 2),
                quantity_available=quantity if payload.procurement_type == "product" else None,
                service_duration=payload.service_duration if payload.procurement_type == "service" else None,
                reliability_score=calculate_reliability_score(link),
                source_link=link,
                logistics_info=f"{logistics['logistics_info']} | {snippet[:120]}",
                vendor_name=(title[:60] if title else "Unknown Vendor"),
                origin_country=origin,
                logistics_cost=float(logistics["logistics_cost"]),
                smart_batching_applied=False,
            )
        )
    return offers


def _normalize_vendor(raw_vendor: Optional[str]) -> str:
    if not raw_vendor:
        return ""
    lowered = str(raw_vendor).strip().lower()
    lowered = re.sub(r"\(.*?\)", "", lowered).strip()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def _collect_active_order_index() -> Dict[str, set]:
    vendors: set = set()
    countries: set = set()
    for company_data in AZCON_COMPANIES.values():
        for order in company_data.get("active_orders", []):
            vendors.add(_normalize_vendor(order.get("vendor")))
            countries.add(str(order.get("origin_country", "")).strip().lower())
    return {"vendors": {v for v in vendors if v}, "countries": {c for c in countries if c}}


def apply_smart_batching(payload: SearchPayload, offers: List[Offer]) -> List[Offer]:
    if payload.procurement_type != "product":
        for offer in offers:
            offer.smart_batching_applied = False
        return offers

    active_index = _collect_active_order_index()
    for offer in offers:
        if offer.source_type != "External Web":
            offer.smart_batching_applied = False
            continue
        vendor_norm = _normalize_vendor(offer.vendor_name or offer.company_name)
        country_norm = str(offer.origin_country or "").strip().lower()
        same_vendor = vendor_norm in active_index["vendors"] if vendor_norm else False
        same_country = country_norm in active_index["countries"] if country_norm else False
        if same_vendor or same_country:
            offer.logistics_cost = round(offer.logistics_cost * 0.5, 2)
            offer.total_price = round(max(0.0, offer.total_price - offer.logistics_cost), 2)
            offer.smart_batching_applied = True
    return offers


def normalize_offers(payload: SearchPayload, offers: List[Offer]) -> List[Offer]:
    normalized: List[Offer] = []
    for offer in offers:
        if offer.reliability_score < payload.min_reliability_score:
            continue
        if offer.total_price > payload.total_budget and offer.source_type == "External Web":
            continue
        if payload.procurement_type == "product":
            if offer.quantity_available is None:
                offer.quantity_available = payload.quantity or 1
            offer.service_duration = None
        else:
            offer.quantity_available = None
            if not offer.service_duration:
                offer.service_duration = payload.service_duration
        normalized.append(offer)
    normalized.sort(key=lambda x: (0 if x.source_type == "Internal AZCON" else 1, -x.reliability_score, x.total_price))
    return normalized


def apply_realistic_pricing_jitter(
    offers: List[Offer],
    budget: float,
    is_service: bool,
    quantity: Optional[int],
) -> List[Offer]:
    qty = quantity if quantity and quantity > 0 else None
    baseline_price = float(budget) if is_service or qty is None else float(budget) / float(qty)
    effective_multiplier = 1 if is_service else (qty or 1)
    assigned_prices = set()

    for offer in offers:
        current_price = float(offer.price_per_unit) if offer.price_per_unit is not None else 0.0
        rounded_current = round(current_price, 2)
        price_missing = current_price <= 0
        equals_baseline = round(baseline_price, 2) == rounded_current
        duplicate = rounded_current in assigned_prices

        if price_missing or equals_baseline or duplicate:
            new_price = round(baseline_price * random.uniform(0.85, 0.98), 2)
            while new_price in assigned_prices:
                new_price = round(baseline_price * random.uniform(0.85, 0.98), 2)
            offer.price_per_unit = new_price
            offer.total_price = round(new_price * effective_multiplier, 2)
            assigned_prices.add(new_price)
            continue

        assigned_prices.add(rounded_current)

    return offers


app = FastAPI(title="AZCON Smart B2B Procurement & Logistics API", version="4.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/test")
def api_test() -> Dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Sorğu formatı yanlışdır", "errors": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/search", response_model=APIResponse)
def search_procurement(payload: SearchPayload) -> APIResponse:
    try:
        max_unit_price = derive_max_unit_price(payload)
        internal_candidates = build_internal_candidates(payload, max_unit_price)
        internal_offers = [Offer.model_validate(candidate) for candidate in internal_candidates]

        serper_results: Dict[str, Any] = {}
        external_offers: List[Offer] = []
        if not payload.azcon_reference_required:
            try:
                dorking_query = generate_b2b_dorking_query(payload.query, payload.category, payload.procurement_type)
                serper_results = run_serper_search(dorking_query)
                external_candidates = build_external_candidates(payload, serper_results, max_unit_price)
                if external_candidates:
                    llm = build_llm()
                    try:
                        llm_mapped = map_serper_with_llm(llm, payload, external_candidates)
                        external_offers = [Offer.model_validate(o) for o in llm_mapped.offers]
                    except Exception as llm_exc:
                        if "429" in str(llm_exc) or "RESOURCE_EXHAUSTED" in str(llm_exc).upper():
                            logger.error("LLM rate limit hit, using manual fallback: %s", llm_exc)
                        else:
                            logger.error("LLM mapping failed, using manual fallback: %s", llm_exc)
                        external_offers = manual_external_fallback(payload, external_candidates, serper_results)
            except Exception as serper_exc:
                logger.error("Serper search failed: %s", serper_exc)

        final_offers = normalize_offers(payload, internal_offers + external_offers)
        final_offers = apply_smart_batching(payload, final_offers)
        final_offers = apply_realistic_pricing_jitter(
            offers=final_offers,
            budget=payload.total_budget,
            is_service=(payload.procurement_type == "service"),
            quantity=payload.quantity,
        )

        return APIResponse(
            query=payload.query,
            procurement_type=payload.procurement_type,
            offers=final_offers,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sistem xətası: {exc}") from exc
