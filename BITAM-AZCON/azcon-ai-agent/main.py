import os
from datetime import date
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field, model_validator

from mock_db import AZCON_COMPANIES


load_dotenv()


class SearchPayload(BaseModel):
    procurement_type: Literal["product", "service"]
    query: str = Field(..., min_length=2)
    budget: float = Field(..., gt=0)
    min_reliability_score: float = Field(3.5, ge=1.0, le=5.0)
    azcon_reference_required: bool = False

    # Product fields
    quantity: Optional[int] = Field(default=None, gt=0)
    deadline: Optional[date] = None

    # Service fields
    service_duration: Optional[str] = None
    start_date: Optional[date] = None
    service_level: Optional[str] = None

    @model_validator(mode="after")
    def validate_by_type(self) -> "SearchPayload":
        if self.procurement_type == "product":
            if self.quantity is None:
                raise ValueError("Məhsul üçün quantity tələb olunur.")
            if self.deadline is None:
                raise ValueError("Məhsul üçün deadline tələb olunur.")
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


class OfferList(BaseModel):
    offers: List[Offer] = Field(..., min_length=1)


class APIResponse(BaseModel):
    query: str
    procurement_type: Literal["product", "service"]
    offers: List[Offer]


def build_llm() -> ChatGoogleGenerativeAI:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY tapılmadı.")
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        temperature=0.1,
        google_api_key=api_key,
    )


def build_tavily_tool() -> TavilySearch:
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY tapılmadı.")
    os.environ["TAVILY_API_KEY"] = tavily_api_key
    return TavilySearch(max_results=8, search_depth="advanced", include_answer=True)


def build_internal_candidates(payload: SearchPayload) -> List[Dict[str, Any]]:
    query_l = payload.query.lower().strip()
    candidates: List[Dict[str, Any]] = []

    for company, company_data in AZCON_COMPANIES.items():
        if payload.procurement_type == "product":
            for item in company_data.get("surplus_inventory", []):
                item_l = str(item.get("item_name", "")).lower()
                if query_l not in item_l and not any(token in item_l for token in query_l.split()):
                    continue

                reliability = float(item.get("reliability_score", 0))
                if reliability < payload.min_reliability_score:
                    continue

                qty = payload.quantity or 1
                unit_price = float(item.get("price_per_unit", 0))
                total_price = round(unit_price * qty, 2)
                if total_price > payload.budget:
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
                        "logistics_info": item.get("logistics_info", "Daxili AZCON logistikasi"),
                    }
                )
        else:
            for service in company_data.get("services", []):
                service_name = str(service.get("name", ""))
                service_l = service_name.lower()
                if query_l not in service_l and not any(token in service_l for token in query_l.split()):
                    continue

                candidates.append(
                    {
                        "source_type": "Internal AZCON",
                        "company_name": company,
                        "item_name": service_name,
                        "price_per_unit": round(payload.budget / 10, 2),
                        "total_price": round(payload.budget / 10, 2),
                        "quantity_available": None,
                        "service_duration": payload.service_duration,
                        "reliability_score": 4.5,
                        "source_link": "Internal",
                        "logistics_info": "Xidmet komandasi AZCON daxilinde onsite/remote destek verir",
                    }
                )

    candidates.sort(key=lambda x: (0 if x["source_type"] == "Internal AZCON" else 1, -x["reliability_score"], x["total_price"]))
    return candidates[:10]


def run_web_search(payload: SearchPayload, tavily_tool: TavilySearch) -> Any:
    if payload.procurement_type == "product":
        web_query = (
            f"B2B product suppliers for '{payload.query}', quantity {payload.quantity}, "
            f"budget {payload.budget} AZN, delivery by {payload.deadline}, minimum reliability {payload.min_reliability_score}/5"
        )
    else:
        web_query = (
            f"B2B service providers for '{payload.query}', duration {payload.service_duration}, "
            f"start date {payload.start_date}, service level {payload.service_level}, "
            f"budget {payload.budget} AZN, minimum reliability {payload.min_reliability_score}/5"
        )
    return tavily_tool.invoke({"query": web_query})


def synthesize_offers(
    llm: ChatGoogleGenerativeAI,
    payload: SearchPayload,
    internal_candidates: List[Dict[str, Any]],
    web_results: Any,
) -> OfferList:
    structured_llm = llm.with_structured_output(OfferList)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Sən AZCON procurement agentisən. "
                    "Əgər procurement_type=service olarsa yalnız service provayderlərinə fokuslan. "
                    "Əgər procurement_type=product olarsa yalnız fiziki məhsul təchizatçılarına fokuslan. "
                    "Internal candidates listesi prioritetdir. "
                    "Nəticə OfferList strukturuna tam uyğun olmalıdır. "
                    "source_type yalnız 'Internal AZCON' və ya 'External Web'. "
                    "External üçün source_link real URL olmalıdır, internal üçün 'Internal'. "
                    "Mümkünsə 5-8 arası təklif qaytar."
                ),
            ),
            (
                "human",
                "Filters: {filters}\nInternal: {internal_candidates}\nWeb: {web_results}",
            ),
        ]
    )

    chain = prompt | structured_llm
    return chain.invoke(
        {
            "filters": payload.model_dump_json(),
            "internal_candidates": internal_candidates,
            "web_results": web_results,
        }
    )


def normalize_offers(payload: SearchPayload, offers: List[Offer]) -> List[Offer]:
    normalized: List[Offer] = []
    for offer in offers:
        if offer.reliability_score < payload.min_reliability_score:
            continue
        if offer.total_price > payload.budget and offer.total_price > 0:
            continue
        if payload.azcon_reference_required and offer.source_type != "Internal AZCON":
            continue
        if payload.procurement_type == "product":
            if offer.quantity_available is None:
                offer.quantity_available = 0
            offer.service_duration = None
        else:
            if not offer.service_duration:
                offer.service_duration = payload.service_duration
            offer.quantity_available = None
        normalized.append(offer)

    normalized.sort(key=lambda x: (0 if x.source_type == "Internal AZCON" else 1, -x.reliability_score, x.total_price))
    return normalized[:8]


def fill_from_internal(payload: SearchPayload, offers: List[Offer], internal_candidates: List[Dict[str, Any]]) -> List[Offer]:
    if len(offers) >= 5:
        return offers

    seen = {(o.company_name, o.item_name, o.source_type) for o in offers}
    for candidate in internal_candidates:
        key = (candidate["company_name"], candidate["item_name"], candidate["source_type"])
        if key in seen:
            continue
        try:
            offer = Offer.model_validate(candidate)
        except Exception:
            continue
        if offer.reliability_score < payload.min_reliability_score:
            continue
        if offer.total_price > payload.budget and offer.total_price > 0:
            continue
        offers.append(offer)
        seen.add(key)
        if len(offers) >= 5:
            break
    return offers[:8]


app = FastAPI(title="AZCON Agilli Satinalma Sistemi", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        llm = build_llm()
        internal_candidates = build_internal_candidates(payload)

        web_results: Any = []
        if not payload.azcon_reference_required:
            tavily_tool = build_tavily_tool()
            web_results = run_web_search(payload, tavily_tool)

        try:
            structured = synthesize_offers(llm, payload, internal_candidates, web_results)
            normalized = normalize_offers(payload, structured.offers)
        except Exception:
            normalized = []

        final_offers = fill_from_internal(payload, normalized, internal_candidates)

        if not final_offers:
            raise HTTPException(status_code=404, detail="Nəticə tapılmadı")

        return APIResponse(
            query=payload.query,
            procurement_type=payload.procurement_type,
            offers=final_offers,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sistem xətası: {exc}") from exc
