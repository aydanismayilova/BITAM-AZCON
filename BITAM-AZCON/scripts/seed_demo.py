"""One-shot demo seeder.

Wipes purchase requests, vendors, registration requests, users (except the
platform admin) and companies, then rebuilds the full demo dataset:

  - 1 platform admin (faigtayibov / 1234)
  - 13 companies (from COMPANY_CATALOG in app.main)
  - 13 company admins (one per company)
  - 4 department admins per company (IT & Tech, Construction & Heavy,
    Logistics & Aviation, Maritime) -> 52 total
  - 1 procurement decider + 1 storage holder per (company, department)
    -> 104 total
  - ~3 approved vendors per (company, department) -> 156 vendors

All passwords are '1234' for demo simplicity.

Run from the project root:
    py scripts/seed_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so 'app' imports cleanly when run as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine
from app.main import COMPANY_CATALOG, DEPARTMENT_CATEGORIES
from app.models import (
    Company,
    PurchaseRequest,
    RegistrationRequest,
    Role,
    ShipmentBatch,
    User,
    Vendor,
    VendorOffer,
)

# Make sure tables exist before we touch them.
Base.metadata.create_all(bind=engine)

PLATFORM_ADMIN_USERNAME = "faigtayibov"

# Short codes used to build deterministic usernames per department.
DEPT_SHORT = {
    "IT & Tech": "it",
    "Construction & Heavy": "con",
    "Logistics & Aviation": "log",
    "Maritime": "mar",
}

# Vendor templates per department. Each template gets prefixed with the company
# code so vendor names are globally unique while still being readable.
VENDOR_TEMPLATES = {
    "IT & Tech": [
        ("ITGroup", "Enterprise IT, networking and helpdesk", 48.0, 6, 88.0, 90.0),
        ("NetSecure", "Cybersecurity hardware and SOC services", 55.0, 8, 86.0, 84.0),
        ("CloudCorp", "Cloud, SaaS and licensing reseller", 52.0, 5, 84.0, 88.0),
    ],
    "Construction & Heavy": [
        ("BuildAZ", "Civil construction and prefab structures", 60.0, 14, 82.0, 80.0),
        ("HeavyMach", "Heavy machinery rental and parts", 58.0, 10, 85.0, 82.0),
        ("MegaConcrete", "Ready-mix concrete and aggregates", 50.0, 7, 87.0, 86.0),
    ],
    "Logistics & Aviation": [
        ("SkyLogistics", "Air freight and customs clearance", 56.0, 5, 86.0, 88.0),
        ("AvioTrans", "Aviation MRO consumables", 62.0, 9, 84.0, 83.0),
        ("FreightOne", "Multimodal freight forwarding", 50.0, 7, 88.0, 85.0),
    ],
    "Maritime": [
        ("PortServ", "Port logistics and stevedoring", 54.0, 8, 86.0, 84.0),
        ("MarineSupply", "Ship chandlery and spare parts", 58.0, 10, 84.0, 83.0),
        ("OceanCargo", "Containerized ocean shipping", 52.0, 9, 87.0, 86.0),
    ],
}


def _wipe(db) -> None:
    """Delete demo rows but keep the platform admin and the schema intact."""
    # Order matters because of FK constraints.
    db.query(VendorOffer).delete(synchronize_session=False)
    db.query(ShipmentBatch).delete(synchronize_session=False)
    db.query(PurchaseRequest).delete(synchronize_session=False)
    db.query(Vendor).delete(synchronize_session=False)
    db.query(RegistrationRequest).delete(synchronize_session=False)
    db.query(User).filter(User.username != PLATFORM_ADMIN_USERNAME).delete(synchronize_session=False)
    db.query(Company).delete(synchronize_session=False)
    db.commit()


def _ensure_platform_admin(db) -> User:
    admin = db.query(User).filter(User.username == PLATFORM_ADMIN_USERNAME).first()
    if not admin:
        admin = User(
            full_name="General Admin",
            username=PLATFORM_ADMIN_USERNAME,
            email="faigtayibov@azcon.ai",
            password="1234",
            role=Role.PLATFORM_ADMIN,
            department="Platform",
            is_active=True,
        )
        db.add(admin)
    else:
        admin.password = "1234"
        admin.role = Role.PLATFORM_ADMIN
        admin.is_active = True
        admin.department = "Platform"
    db.commit()
    db.refresh(admin)
    return admin


def _create_companies(db) -> dict[str, Company]:
    out: dict[str, Company] = {}
    for entry in COMPANY_CATALOG:
        company = Company(name=entry["name"], code=entry["code"], success_rate=80.0)
        db.add(company)
        db.flush()
        out[entry["code"]] = company
    db.commit()
    return out


def _make_user(db, *, full_name, username, email, role, company_id, department) -> User:
    user = User(
        full_name=full_name,
        username=username,
        email=email,
        password="1234",
        role=role,
        company_id=company_id,
        department=department,
        is_active=True,
    )
    db.add(user)
    return user


def _create_users_and_vendors(db, companies: dict[str, Company]) -> dict[str, int]:
    counts = {"company_admin": 0, "department_admin": 0, "procurement_decider": 0, "storage_holder": 0, "vendors": 0}
    for entry in COMPANY_CATALOG:
        code = entry["code"]
        company = companies[code]
        code_lc = code.lower().replace("-", "_")

        # Company admin
        _make_user(
            db,
            full_name=f"{entry['name']} Company Admin",
            username=f"admin_{code_lc}",
            email=f"admin_{code_lc}@azcon.ai",
            role=Role.COMPANY_ADMIN,
            company_id=company.id,
            department="Administration",
        )
        counts["company_admin"] += 1

        for dept in DEPARTMENT_CATEGORIES:
            if dept == "Others":
                # Skip 'Others' for department staff per spec (4 departments only).
                continue
            short = DEPT_SHORT[dept]

            _make_user(
                db,
                full_name=f"{entry['name']} {dept} Dept Admin",
                username=f"dept_{code_lc}_{short}",
                email=f"dept_{code_lc}_{short}@azcon.ai",
                role=Role.DEPARTMENT_ADMIN,
                company_id=company.id,
                department=dept,
            )
            counts["department_admin"] += 1

            _make_user(
                db,
                full_name=f"{entry['name']} {dept} Procurement",
                username=f"proc_{code_lc}_{short}",
                email=f"proc_{code_lc}_{short}@azcon.ai",
                role=Role.PROCUREMENT_DECIDER,
                company_id=company.id,
                department=dept,
            )
            counts["procurement_decider"] += 1

            _make_user(
                db,
                full_name=f"{entry['name']} {dept} Storage",
                username=f"stor_{code_lc}_{short}",
                email=f"stor_{code_lc}_{short}@azcon.ai",
                role=Role.STORAGE_HOLDER,
                company_id=company.id,
                department=dept,
            )
            counts["storage_holder"] += 1

            # Approved vendors for this (company, department).
            for base, about, price_index, delivery_days, quality, reliability in VENDOR_TEMPLATES[dept]:
                vendor = Vendor(
                    company_id=company.id,
                    company_name=f"{code}-{base}",
                    provided_categories=dept,
                    is_trusted=True,
                    reliability_score=reliability,
                    quality_score=quality,
                    delivery_score=85.0,
                    commercial_score=84.0,
                    about=f"{about} (approved by {entry['name']})",
                    avg_price_index=price_index,
                    typical_delivery_days=delivery_days,
                )
                db.add(vendor)
                counts["vendors"] += 1
    db.commit()
    return counts


def main() -> None:
    db = SessionLocal()
    try:
        print("Wiping demo data ...")
        _wipe(db)
        print("Ensuring platform admin ...")
        _ensure_platform_admin(db)
        print("Recreating companies ...")
        companies = _create_companies(db)
        print(f"Created {len(companies)} companies.")
        print("Seeding users and vendors ...")
        counts = _create_users_and_vendors(db, companies)
        print("Done.")
        for k, v in counts.items():
            print(f"  {k:22s}: {v}")
        total_users = sum(counts[k] for k in ("company_admin", "department_admin", "procurement_decider", "storage_holder")) + 1
        print(f"  total users (incl. PA) : {total_users}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
