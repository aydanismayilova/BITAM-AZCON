import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import PurchaseRequest, ResearchCache, Vendor, VendorOffer


def _normalize_query(req: PurchaseRequest) -> str:
    return f"{req.title.strip().lower()}::{req.description.strip().lower()}"

def _tokens(text: str) -> list[str]:
    cleaned = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in (text or "").lower())
    return [t for t in cleaned.split() if len(t) >= 3]


def _score_offer(offer: VendorOffer, vendor: Vendor):
    financial = max(0.0, 100.0 - min(100.0, offer.price / 10.0))
    time_score = max(0.0, 100.0 - min(100.0, offer.lead_time_days * 4.0))
    quality = min(100.0, (offer.quality_score + vendor.quality_score) / 2.0)
    trusted_bonus = 10.0 if vendor.is_trusted else 0.0
    reliability = vendor.reliability_score
    total = 0.35 * financial + 0.25 * time_score + 0.30 * quality + 0.10 * reliability + trusted_bonus
    return {
        "financial": round(financial, 2),
        "time": round(time_score, 2),
        "quality": round(quality, 2),
        "reliability": round(reliability, 2),
        "total": round(total, 2),
    }


def run_recommendation_pipeline(db: Session, purchase_request: PurchaseRequest, top_n: int = 3):
    query = _normalize_query(purchase_request)
    now = datetime.utcnow()

    cache = db.query(ResearchCache).filter(ResearchCache.normalized_query == query).order_by(ResearchCache.id.desc()).first()
    if cache:
        expiry = datetime.fromisoformat(cache.expires_at)
        if expiry > now:
            return {"source": "cache", "query": query, "results": json.loads(cache.payload_json)}

    # Offer matching: use token overlap instead of strict substring on title.
    title_tokens = set(_tokens(purchase_request.title or ""))
    desc_tokens = set(_tokens(purchase_request.description or ""))
    req_tokens = title_tokens | desc_tokens

    raw_offers = (
        db.query(VendorOffer, Vendor)
        .join(Vendor, VendorOffer.vendor_id == Vendor.id)
        .filter(VendorOffer.is_active.is_(True))
        .all()
    )

    ranked = []
    for offer, vendor in raw_offers:
        hay = f"{offer.category or ''} {offer.title or ''}".lower()
        if req_tokens:
            match_count = sum(1 for t in req_tokens if t in hay)
            if match_count <= 0:
                continue
        score = _score_offer(offer, vendor)
        ranked.append(
            {
                "vendor_id": vendor.id,
                "vendor_name": vendor.company_name,
                "trusted": vendor.is_trusted,
                "offer_title": offer.title,
                "price": offer.price,
                "currency": offer.currency,
                "lead_time_days": offer.lead_time_days,
                "scores": score,
                "reasoning": "Trusted vendors prioritized, then weighted by finance/time/quality/reliability.",
            }
        )

        open_shipments = (
            db.query(PurchaseRequest.vendor_id)
            .filter(
                PurchaseRequest.vendor_id.is_not(None),
                PurchaseRequest.delivery_date.is_not(None),
                PurchaseRequest.company_id != purchase_request.company_id,
            )
            .all()
        )

        open_vendor_ids = {row[0] for row in open_shipments if row[0]}
        for row in ranked:
            if row["vendor_id"] in open_vendor_ids:
                row["scores"]["total"] = round(row["scores"]["total"] + 12, 2)
                row["reasoning"] = (
                    "Bu şirkət seçildi, çünki hazırda digər AZCON şirkəti də bu vendordan yük gözləyir. "
                    "Karqo birləşdirilsə xərc yarıya enəcək."
                )

    ranked.sort(key=lambda r: (not r["trusted"], -r["scores"]["total"], r["lead_time_days"], r["price"]))
    result_payload = ranked[: min(max(top_n, 1), 10)]

    expires = now + timedelta(days=7)
    db.add(
        ResearchCache(
            normalized_query=query,
            source="ai_agent",
            payload_json=json.dumps(result_payload),
            expires_at=expires.isoformat(),
        )
    )
    db.commit()
    return {"source": "live", "query": query, "results": result_payload}
