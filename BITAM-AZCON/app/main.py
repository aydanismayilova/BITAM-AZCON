import logging
import os
from pathlib import Path
from datetime import datetime
import importlib.util

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from local .env files so the main app
# can reach SERPER_API_KEY / GOOGLE_API_KEY without manual exports.
_BASE_DIR = Path(__file__).resolve().parents[1]
for _env_path in (
    _BASE_DIR / ".env",
    _BASE_DIR / "azcon-AI" / "azcon-ai-agent" / ".env",
):
    if _env_path.exists():
        load_dotenv(_env_path, override=False)

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
import requests
from pydantic import BaseModel, Field

from app.ai_pipeline import run_recommendation_pipeline
from app.auth import get_current_user, require_roles, require_same_company_or_admin
from app.database import Base, SessionLocal, engine, get_db
from app.models import (
    Company,
    InventoryItem,
    PurchaseRequest,
    RequestStatus,
    RegistrationRequest,
    RegistrationStatus,
    Role,
    ShortageAlert,
    ShipmentBatch,
    User,
    Vendor,
    VendorOffer,
)
from app.schemas import (
    CompanyCreate,
    InventoryCreate,
    InventoryUpdate,
    InventoryUpdateByName,
    LoginRequest,
    PurchaseRequestCreate,
    RegistrationRequestCreate,
    UserCreate,
    UserOut,
    VendorCreate,
    VendorOfferCreate,
)

app = FastAPI(title="AZCON Procurement API", version="0.1.0")

COMPANY_CATALOG = [
    {"name": "Azerbaijan Airlines", "code": "AZAL"},
    {"name": "Azerbaijan Railways", "code": "ADY"},
    {"name": "Azerbaijan Caspian Shipping Company", "code": "ASCO"},
    {"name": "Baku Metro", "code": "BAKU-METRO"},
    {"name": "Baku Bus", "code": "BAKU-BUS"},
    {"name": "Baku Shipyard", "code": "BAKU-SHIPYARD"},
    {"name": "Azercosmos", "code": "AZERCOSMOS"},
    {"name": "Aztelekom", "code": "AZTELEKOM"},
    {"name": "AzInTelecom", "code": "AZINTELECOM"},
    {"name": "Azerpost", "code": "AZERPOST"},
    {"name": "Baku Taxi Service", "code": "BAKU-TAXI"},
    {"name": "Teleradio LLC", "code": "TELERADIO"},
    {"name": "National Artificial Intelligence Center", "code": "NAIC"},
]

# Department options follow the AZCON AI agent's 5 categories so the request form
# and the AI agent share the same vocabulary.
DEPARTMENT_CATEGORIES = [
    "IT & Tech",
    "Construction & Heavy",
    "Logistics & Aviation",
    "Maritime",
    "Others",
]

# Legacy department names that may exist in the DB and need to be mapped to the
# new AI-agent categories.
LEGACY_DEPARTMENT_MAP = {
    "IT": "IT & Tech",
    "Logistics": "Logistics & Aviation",
    "TELECOM": "IT & Tech",
}

COMPANY_DEPARTMENTS = {entry["name"]: list(DEPARTMENT_CATEGORIES) for entry in COMPANY_CATALOG}

EXPENSIVE_NEEDS = {
    "Bakı Metropoliteni QSC": [
        "Eskalator ehtiyat hissələri",
        "Yüksək gərginlikli yeraltı kabellər",
        "Sərnişin nəzarət (turniket) sistemləri",
        "Ventilyasiya motorları",
    ],
    "Aztelekom MMC": [
        "Cisco Enterprise Switch-lər",
        "Fiber-optik kabellər (kilometr qeydi ilə)",
        "Server steykləri",
        "Palo Alto Firewall cihazları",
    ],
    "AZAL": [
        "Yük terminalı üçün avtokarlar (Forklift)",
        "Logistika skanerləri",
        "Anbar işçiləri üçün smart qoruyucu geyimlər",
        "Təhlükəsizlik kameraları şəbəkəsi",
    ],
    "Bakı Limanı": [
        "Yük terminalı üçün avtokarlar (Forklift)",
        "Logistika skanerləri",
        "Anbar işçiləri üçün smart qoruyucu geyimlər",
        "Təhlükəsizlik kameraları şəbəkəsi",
    ],
}

HR_NEEDS = [
    "Herman Miller ofis kresloları",
    "MacBook Pro / Dell noutbukları",
    "Server otağı üçün UPS sistemləri",
]

def run_light_migrations():
    with engine.begin() as conn:
        users_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
        if "username" not in users_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(120)"))
        if "department" not in users_cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(120)"))
        company_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(companies)")).fetchall()]
        if "about" not in company_cols:
            conn.execute(text("ALTER TABLE companies ADD COLUMN about TEXT"))
        if "success_rate" not in company_cols:
            conn.execute(text("ALTER TABLE companies ADD COLUMN success_rate FLOAT DEFAULT 75"))

        reg_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(registration_requests)")).fetchall()]
        if reg_cols and "department" not in reg_cols:
            conn.execute(text("ALTER TABLE registration_requests ADD COLUMN department VARCHAR(120) DEFAULT 'Satınalma'"))

        req_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(purchase_requests)")).fetchall()]
        for statement, col_name in [
            ("ALTER TABLE purchase_requests ADD COLUMN department VARCHAR(120)", "department"),
            ("ALTER TABLE purchase_requests ADD COLUMN item_type VARCHAR(20) DEFAULT 'product'", "item_type"),
            ("ALTER TABLE purchase_requests ADD COLUMN vendor_id INTEGER", "vendor_id"),
            ("ALTER TABLE purchase_requests ADD COLUMN delivery_date VARCHAR(40)", "delivery_date"),
            ("ALTER TABLE purchase_requests ADD COLUMN shipping_cost FLOAT DEFAULT 1000", "shipping_cost"),
            ("ALTER TABLE purchase_requests ADD COLUMN shipment_batch_id INTEGER", "shipment_batch_id"),
            # AI-agent aligned columns
            ("ALTER TABLE purchase_requests ADD COLUMN unit VARCHAR(20)", "unit"),
            ("ALTER TABLE purchase_requests ADD COLUMN total_budget FLOAT", "total_budget"),
            ("ALTER TABLE purchase_requests ADD COLUMN min_reliability_score FLOAT", "min_reliability_score"),
            ("ALTER TABLE purchase_requests ADD COLUMN azcon_reference_required BOOLEAN DEFAULT 0", "azcon_reference_required"),
            ("ALTER TABLE purchase_requests ADD COLUMN service_duration VARCHAR(60)", "service_duration"),
            ("ALTER TABLE purchase_requests ADD COLUMN start_date VARCHAR(40)", "start_date"),
            ("ALTER TABLE purchase_requests ADD COLUMN service_level VARCHAR(40)", "service_level"),
        ]:
            if col_name not in req_cols:
                conn.execute(text(statement))

        # Map legacy department strings (IT / Logistics / TELECOM) to the AI-agent
        # category vocabulary so old rows stay compatible with the new dropdowns.
        legacy_map = {
            "IT": "IT & Tech",
            "Logistics": "Logistics & Aviation",
            "TELECOM": "IT & Tech",
        }
        for old_value, new_value in legacy_map.items():
            for table in ("users", "registration_requests", "purchase_requests"):
                conn.execute(
                    text(f"UPDATE {table} SET department = :new WHERE department = :old"),
                    {"old": old_value, "new": new_value},
                )

        # Vendors are scoped per company, so the global UNIQUE index on
        # vendors.company_name is incorrect. Drop it (it lives as a UNIQUE
        # INDEX named ix_vendors_company_name) and recreate as a plain index.
        existing_index = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='index' AND name='ix_vendors_company_name'")
        ).fetchone()
        if existing_index and existing_index[0] and "UNIQUE" in existing_index[0].upper():
            conn.execute(text("DROP INDEX ix_vendors_company_name"))
            conn.execute(text("CREATE INDEX ix_vendors_company_name ON vendors (company_name)"))

        vendor_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(vendors)")).fetchall()]
        for statement, col_name in [
            ("ALTER TABLE vendors ADD COLUMN company_id INTEGER", "company_id"),
            ("ALTER TABLE vendors ADD COLUMN provided_categories VARCHAR(255)", "provided_categories"),
            ("ALTER TABLE vendors ADD COLUMN is_trusted BOOLEAN DEFAULT 0", "is_trusted"),
            ("ALTER TABLE vendors ADD COLUMN reliability_score FLOAT DEFAULT 50", "reliability_score"),
            ("ALTER TABLE vendors ADD COLUMN quality_score FLOAT DEFAULT 50", "quality_score"),
            ("ALTER TABLE vendors ADD COLUMN delivery_score FLOAT DEFAULT 50", "delivery_score"),
            ("ALTER TABLE vendors ADD COLUMN commercial_score FLOAT DEFAULT 50", "commercial_score"),
            ("ALTER TABLE vendors ADD COLUMN about TEXT", "about"),
            ("ALTER TABLE vendors ADD COLUMN avg_price_index FLOAT DEFAULT 50", "avg_price_index"),
            ("ALTER TABLE vendors ADD COLUMN typical_delivery_days INTEGER DEFAULT 7", "typical_delivery_days"),
        ]:
            if col_name not in vendor_cols:
                conn.execute(text(statement))


run_light_migrations()
Base.metadata.create_all(bind=engine)


def ensure_general_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "faigtayibov").first()
        if not admin:
            admin = User(
                full_name="General Admin",
                username="faigtayibov",
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
        db.commit()
    finally:
        db.close()


ensure_general_admin()


def ensure_default_usernames():
    db = SessionLocal()
    try:
        mappings = {
            "storage1@azcon.ai": "storageX",
            "decider1@azcon.ai": "deciderX",
            "companyadmin1@azcon.ai": "companyadminX",
        }
        users = db.query(User).all()
        used_usernames = {u.username for u in users if u.username}
        changed = False
        for u in users:
            if not u.username and u.email in mappings and mappings[u.email] not in used_usernames:
                u.username = mappings[u.email]
                used_usernames.add(u.username)
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


ensure_default_usernames()


def ensure_company_catalog():
    db = SessionLocal()
    try:
        for company_data in COMPANY_CATALOG:
            exists = db.query(Company).filter(Company.name == company_data["name"]).first()
            if not exists:
                db.add(Company(name=company_data["name"], code=company_data["code"], success_rate=75.0))
        db.commit()
    finally:
        db.close()


ensure_company_catalog()

def get_expense_mock(company_name: str):
    return {
        "company_name": company_name,
        "last_year": {"İnfrastruktur": 1_420_000, "Satınalma": 910_000, "HR/İnzibati": 320_000, "IT": 510_000},
        "this_year": {"İnfrastruktur": 1_650_000, "Satınalma": 1_040_000, "HR/İnzibati": 355_000, "IT": 575_000},
    }

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Backward-compatible root asset routes (in case old HTML/cache requests /styles.css etc.)
@app.get("/styles.css")
def legacy_styles():
    return FileResponse(static_dir / "styles.css")


@app.get("/login.js")
def legacy_login_js():
    return FileResponse(static_dir / "login.js")


@app.get("/app.js")
def legacy_app_js():
    return FileResponse(static_dir / "app.js")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def frontend():
    return FileResponse(static_dir / "login.html")


@app.get("/app")
def app_frontend():
    return FileResponse(static_dir / "index.html")


@app.get("/ai-agent")
def ai_agent_frontend():
    ai_index = Path(__file__).resolve().parents[1] / "azcon-AI" / "azcon-ai-agent" / "index.html"
    if not ai_index.exists():
        raise HTTPException(status_code=404, detail="AI agent page not found")
    return FileResponse(ai_index)


class AISearchPayload(BaseModel):
    procurement_type: str = Field(default="product")
    query: str
    category: str = Field(default="Others")
    unit: str | None = None
    total_budget: float = Field(default=50000, gt=0)
    min_reliability_score: float = Field(default=3.5)
    azcon_reference_required: bool = Field(default=False)
    quantity: int | None = None
    deadline: str | None = None
    service_duration: str | None = None
    start_date: str | None = None
    service_level: str | None = None


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.username == payload.username, User.password == payload.password, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    company_name = None
    if user.company_id:
        company = db.query(Company).filter(Company.id == user.company_id).first()
        company_name = company.name if company else None

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "company_id": user.company_id,
        "company_name": company_name,
        "department": user.department,
    }


@app.get("/companies-public")
def list_companies_public(db: Session = Depends(get_db)):
    names = [entry["name"] for entry in COMPANY_CATALOG]
    return db.query(Company).filter(Company.name.in_(names)).order_by(Company.name.asc()).all()

@app.get("/meta/company-departments")
def company_departments():
    return COMPANY_DEPARTMENTS


@app.post("/auth/register-request")
def create_registration_request(payload: RegistrationRequestCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.name == payload.company_name).first()
    if not company:
        raise HTTPException(status_code=404, detail="Selected company does not exist")

    if payload.requested_role not in [Role.COMPANY_ADMIN, Role.DEPARTMENT_ADMIN, Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER]:
        raise HTTPException(
            status_code=400,
            detail="You can register only as company admin, department admin, storage holder, or procurement decider",
        )

    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    if (
        db.query(RegistrationRequest)
        .filter(
            RegistrationRequest.status == RegistrationStatus.PENDING,
            (RegistrationRequest.username == payload.username) | (RegistrationRequest.email == payload.email),
        )
        .first()
    ):
        raise HTTPException(status_code=400, detail="A pending request already exists for this username or email")

    existing_company_admin = (
        db.query(User)
        .filter(
            User.company_id == company.id,
            User.role == Role.COMPANY_ADMIN,
            User.is_active.is_(True),
        )
        .first()
    )

    if payload.requested_role == Role.COMPANY_ADMIN:
        if existing_company_admin:
            raise HTTPException(status_code=400, detail="This company already has a company admin")
        pending_admin = (
            db.query(RegistrationRequest)
            .filter(
                RegistrationRequest.company_id == company.id,
                RegistrationRequest.requested_role == Role.COMPANY_ADMIN,
                RegistrationRequest.status == RegistrationStatus.PENDING,
            )
            .first()
        )
        if pending_admin:
            raise HTTPException(status_code=400, detail="A company admin request for this company is already pending")
        department = "Administration"
        reviewer = "platform admin"
    elif payload.requested_role == Role.DEPARTMENT_ADMIN:
        if not existing_company_admin:
            raise HTTPException(status_code=400, detail="This company has no approved company admin yet")
        if payload.department not in DEPARTMENT_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Department must be one of: {', '.join(DEPARTMENT_CATEGORIES)}",
            )
        existing_department_admin = (
            db.query(User)
            .filter(
                User.company_id == company.id,
                User.role == Role.DEPARTMENT_ADMIN,
                User.department == payload.department,
                User.is_active.is_(True),
            )
            .first()
        )
        if existing_department_admin:
            raise HTTPException(status_code=400, detail="This department already has a department admin")
        pending_department_admin = (
            db.query(RegistrationRequest)
            .filter(
                RegistrationRequest.company_id == company.id,
                RegistrationRequest.requested_role == Role.DEPARTMENT_ADMIN,
                RegistrationRequest.department == payload.department,
                RegistrationRequest.status == RegistrationStatus.PENDING,
            )
            .first()
        )
        if pending_department_admin:
            raise HTTPException(status_code=400, detail="A department admin request for this department is already pending")
        department = payload.department
        reviewer = "company admin"
    else:
        if payload.department not in DEPARTMENT_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Department must be one of: {', '.join(DEPARTMENT_CATEGORIES)}",
            )
        existing_department_admin = (
            db.query(User)
            .filter(
                User.company_id == company.id,
                User.role == Role.DEPARTMENT_ADMIN,
                User.department == payload.department,
                User.is_active.is_(True),
            )
            .first()
        )
        if not existing_department_admin:
            raise HTTPException(status_code=400, detail="Selected department has no approved department admin yet")
        department = payload.department
        reviewer = "department admin"

    req = RegistrationRequest(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        company_id=company.id,
        department=department,
        requested_role=payload.requested_role,
        status=RegistrationStatus.PENDING,
    )
    db.add(req)
    db.commit()
    return {"message": f"Registration request submitted. It will be reviewed by {reviewer}."}


@app.post("/companies")
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(name=payload.name, code=payload.code)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role != Role.PLATFORM_ADMIN and not payload.company_id:
        raise HTTPException(status_code=400, detail="company_id is required for non platform admins")
    if payload.role == Role.PLATFORM_ADMIN:
        existing_platform_admin = db.query(User).filter(User.role == Role.PLATFORM_ADMIN, User.is_active.is_(True)).first()
        if existing_platform_admin:
            raise HTTPException(status_code=400, detail="Only one platform admin is allowed")
    if payload.role == Role.COMPANY_ADMIN:
        company_admin_exists = (
            db.query(User)
            .filter(User.company_id == payload.company_id, User.role == Role.COMPANY_ADMIN, User.is_active.is_(True))
            .first()
        )
        if company_admin_exists:
            raise HTTPException(status_code=400, detail="Only one company admin is allowed per company")
    if payload.role == Role.DEPARTMENT_ADMIN:
        if payload.department not in ["IT", "Logistics", "TELECOM"]:
            raise HTTPException(status_code=400, detail="Department admin must belong to IT, Logistics, or TELECOM")
        department_admin_exists = (
            db.query(User)
            .filter(
                User.company_id == payload.company_id,
                User.role == Role.DEPARTMENT_ADMIN,
                User.department == payload.department,
                User.is_active.is_(True),
            )
            .first()
        )
        if department_admin_exists:
            raise HTTPException(status_code=400, detail="Only one department admin is allowed for each department")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        company_id=payload.company_id,
        department=payload.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/inventory")
def list_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(InventoryItem, Company).join(Company, InventoryItem.company_id == Company.id)
    if current_user.role != Role.PLATFORM_ADMIN:
        query = query.filter(InventoryItem.company_id == current_user.company_id)

    items = query.order_by(InventoryItem.name.asc()).all()
    return [
        {
            "item_id": item.id,
            "item_name": item.name,
            "company_name": company.name,
            "quantity": item.quantity,
            "min_threshold": item.min_threshold,
            "unit": item.unit,
        }
        for item, company in items
    ]


@app.post("/inventory")
def create_inventory_item(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.STORAGE_HOLDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    if current_user.role != Role.PLATFORM_ADMIN and current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User has no company context")
    company_id = current_user.company_id if current_user.role != Role.PLATFORM_ADMIN else 1
    item = InventoryItem(
        company_id=company_id,
        name=payload.name,
        quantity=payload.quantity,
        min_threshold=payload.min_threshold,
        unit=payload.unit,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/inventory/id/{item_id}")
def update_inventory(
    item_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.STORAGE_HOLDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    require_same_company_or_admin(item.company_id, current_user)
    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)

    alert_created = False
    if item.quantity < item.min_threshold:
        db.add(
            ShortageAlert(
                company_id=item.company_id,
                inventory_item_id=item.id,
                triggered_quantity=item.quantity,
            )
        )
        db.commit()
        alert_created = True

    return {"item": item, "shortage_alert_created": alert_created}


@app.patch("/inventory/update-by-name")
def update_inventory_by_name(
    payload: InventoryUpdateByName,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.STORAGE_HOLDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    query = db.query(InventoryItem).filter(InventoryItem.name.ilike(payload.item_name))
    if current_user.role != Role.PLATFORM_ADMIN:
        query = query.filter(InventoryItem.company_id == current_user.company_id)

    item = query.order_by(InventoryItem.id.desc()).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found for selected company")

    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)

    alert_created = False
    if item.quantity < item.min_threshold:
        db.add(
            ShortageAlert(
                company_id=item.company_id,
                inventory_item_id=item.id,
                triggered_quantity=item.quantity,
            )
        )
        db.commit()
        alert_created = True

    company = db.query(Company).filter(Company.id == item.company_id).first()
    return {
        "item_name": item.name,
        "company_name": company.name if company else "Unknown",
        "quantity": item.quantity,
        "min_threshold": item.min_threshold,
        "shortage_alert_created": alert_created,
    }


@app.get("/shortages")
def list_shortages(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    query = (
        db.query(ShortageAlert, InventoryItem, Company)
        .join(InventoryItem, ShortageAlert.inventory_item_id == InventoryItem.id)
        .join(Company, ShortageAlert.company_id == Company.id)
        .filter(ShortageAlert.is_resolved.is_(False))
    )
    if current_user.role != Role.PLATFORM_ADMIN:
        query = query.filter(ShortageAlert.company_id == current_user.company_id)
    records = query.order_by(ShortageAlert.id.desc()).all()
    return [
        {
            "alert_id": alert.id,
            "item_name": item.name,
            "company_name": company.name,
            "current_quantity": alert.triggered_quantity,
            "minimum_quantity": item.min_threshold,
            "created_at": alert.created_at.isoformat(),
        }
        for alert, item, company in records
    ]


@app.get("/requests")
def list_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(PurchaseRequest, Company, User)
        .join(Company, PurchaseRequest.company_id == Company.id)
        .join(User, PurchaseRequest.requested_by == User.id)
    )
    if current_user.role != Role.PLATFORM_ADMIN:
        query = query.filter(PurchaseRequest.company_id == current_user.company_id)
    rows = query.order_by(PurchaseRequest.id.desc()).all()
    return [
        {
            "request_id": req.id,
            "title": req.title,
            "status": req.status.value,
            "quantity": req.quantity,
            "required_by": req.required_by,
            "department": req.department,
            "delivery_date": req.delivery_date,
            "shipping_cost": req.shipping_cost,
            "vendor_id": req.vendor_id,
            "company_name": company.name,
            "requested_by": requester.full_name,
            "requested_by_role": requester.role.value,
        }
        for req, company, requester in rows
    ]


@app.get("/admin/registration-requests")
def list_registration_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
):
    rows = (
        db.query(RegistrationRequest, Company)
        .join(Company, RegistrationRequest.company_id == Company.id)
        .filter(
            RegistrationRequest.status == RegistrationStatus.PENDING,
            RegistrationRequest.requested_role == Role.COMPANY_ADMIN,
        )
        .order_by(RegistrationRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "full_name": req.full_name,
            "username": req.username,
            "email": req.email,
            "company_name": company.name,
            "department": req.department,
            "requested_role": req.requested_role.value,
            "created_at": req.created_at.isoformat(),
        }
        for req, company in rows
    ]


@app.get("/company-admin/registration-requests")
def list_company_admin_registration_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.COMPANY_ADMIN)),
):
    rows = (
        db.query(RegistrationRequest, Company)
        .join(Company, RegistrationRequest.company_id == Company.id)
        .filter(
            RegistrationRequest.status == RegistrationStatus.PENDING,
            RegistrationRequest.company_id == current_user.company_id,
            RegistrationRequest.requested_role == Role.DEPARTMENT_ADMIN,
        )
        .order_by(RegistrationRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "full_name": req.full_name,
            "username": req.username,
            "email": req.email,
            "company_name": company.name,
            "department": req.department,
            "requested_role": req.requested_role.value,
            "created_at": req.created_at.isoformat(),
        }
        for req, company in rows
    ]


@app.post("/admin/registration-requests/{request_id}/approve")
def approve_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
):
    req = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RegistrationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is already processed")
    if req.requested_role != Role.COMPANY_ADMIN:
        raise HTTPException(status_code=400, detail="Platform admin can only approve company admin requests")

    if req.requested_role == Role.COMPANY_ADMIN:
        existing_admin = (
            db.query(User)
            .filter(User.company_id == req.company_id, User.role == Role.COMPANY_ADMIN, User.is_active.is_(True))
            .first()
        )
        if existing_admin:
            raise HTTPException(status_code=400, detail="This company already has a company admin")

    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        req.status = RegistrationStatus.REJECTED
        req.reviewed_by = current_user.id
        req.reviewed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="Username or email already exists in users")

    user = User(
        full_name=req.full_name,
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.requested_role,
        company_id=req.company_id,
        department=req.department,
        is_active=True,
    )
    db.add(user)
    req.status = RegistrationStatus.APPROVED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration approved", "username": user.username}


@app.post("/admin/registration-requests/{request_id}/reject")
def reject_registration_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
):
    req = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RegistrationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is already processed")
    if req.requested_role != Role.COMPANY_ADMIN:
        raise HTTPException(status_code=400, detail="Platform admin can only reject company admin requests")

    req.status = RegistrationStatus.REJECTED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration rejected"}


@app.get("/admin/users")
def list_all_users_for_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "username": u.username,
            "email": u.email,
            "role": u.role.value,
            "company_id": u.company_id,
            "department": u.department,
            "is_active": u.is_active,
        }
        for u in users
    ]


@app.delete("/admin/users/{user_id}")
def delete_user_by_platform_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PLATFORM_ADMIN)),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Platform admin cannot delete own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@app.post("/company-admin/registration-requests/{request_id}/approve")
def approve_registration_request_by_company_admin(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.COMPANY_ADMIN)),
):
    req = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RegistrationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is already processed")
    if req.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="You can approve requests only for your company")
    if req.requested_role != Role.DEPARTMENT_ADMIN:
        raise HTTPException(status_code=400, detail="Company admin can only approve department admin requests")
    existing_department_admin = (
        db.query(User)
        .filter(
            User.company_id == req.company_id,
            User.role == Role.DEPARTMENT_ADMIN,
            User.department == req.department,
            User.is_active.is_(True),
        )
        .first()
    )
    if existing_department_admin:
        raise HTTPException(status_code=400, detail="This department already has a department admin")

    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        req.status = RegistrationStatus.REJECTED
        req.reviewed_by = current_user.id
        req.reviewed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="Username or email already exists in users")

    user = User(
        full_name=req.full_name,
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.requested_role,
        company_id=req.company_id,
        department=req.department,
        is_active=True,
    )
    db.add(user)
    req.status = RegistrationStatus.APPROVED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration approved", "username": user.username}


@app.post("/company-admin/registration-requests/{request_id}/reject")
def reject_registration_request_by_company_admin(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.COMPANY_ADMIN)),
):
    req = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RegistrationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is already processed")
    if req.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="You can review requests only for your company")
    if req.requested_role != Role.DEPARTMENT_ADMIN:
        raise HTTPException(status_code=400, detail="Company admin can only review department admin requests")

    req.status = RegistrationStatus.REJECTED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration rejected"}


@app.get("/department-admin/registration-requests")
def list_department_admin_registration_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN)),
):
    rows = (
        db.query(RegistrationRequest, Company)
        .join(Company, RegistrationRequest.company_id == Company.id)
        .filter(
            RegistrationRequest.status == RegistrationStatus.PENDING,
            RegistrationRequest.company_id == current_user.company_id,
            RegistrationRequest.department == current_user.department,
            RegistrationRequest.requested_role.in_([Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER]),
        )
        .order_by(RegistrationRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "full_name": req.full_name,
            "username": req.username,
            "email": req.email,
            "company_name": company.name,
            "department": req.department,
            "requested_role": req.requested_role.value,
            "created_at": req.created_at.isoformat(),
        }
        for req, company in rows
    ]


@app.post("/department-admin/registration-requests/{request_id}/approve")
def approve_registration_request_by_department_admin(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN)),
):
    req = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RegistrationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is already processed")
    if req.company_id != current_user.company_id or req.department != current_user.department:
        raise HTTPException(status_code=403, detail="You can approve only requests in your department")
    if req.requested_role not in [Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER]:
        raise HTTPException(status_code=400, detail="Department admin can only approve storage/procurement requests")
    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        req.status = RegistrationStatus.REJECTED
        req.reviewed_by = current_user.id
        req.reviewed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="Username or email already exists in users")

    user = User(
        full_name=req.full_name,
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.requested_role,
        company_id=req.company_id,
        department=req.department,
        is_active=True,
    )
    db.add(user)
    req.status = RegistrationStatus.APPROVED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration approved", "username": user.username}


@app.post("/department-admin/registration-requests/{request_id}/reject")
def reject_registration_request_by_department_admin(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN)),
):
    req = db.query(RegistrationRequest).filter(RegistrationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != RegistrationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is already processed")
    if req.company_id != current_user.company_id or req.department != current_user.department:
        raise HTTPException(status_code=403, detail="You can reject only requests in your department")
    if req.requested_role not in [Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER]:
        raise HTTPException(status_code=400, detail="Department admin can only review storage/procurement requests")
    req.status = RegistrationStatus.REJECTED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration rejected"}


@app.post("/requests")
def create_purchase_request(
    payload: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER)),
):
    if current_user.role != Role.PLATFORM_ADMIN and current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User has no company context")
    company_id = current_user.company_id if current_user.role != Role.PLATFORM_ADMIN else 1
    # Storage holders cannot decide vendor during request creation.
    selected_vendor_id = payload.vendor_id if current_user.role != Role.STORAGE_HOLDER else None
    req = PurchaseRequest(
        company_id=company_id,
        requested_by=current_user.id,
        title=payload.title,
        description=payload.description,
        quantity=payload.quantity,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        required_by=payload.required_by,
        status=RequestStatus.SUBMITTED,
        department=payload.department or current_user.department,
        item_type=payload.item_type,
        vendor_id=selected_vendor_id,
        delivery_date=payload.delivery_date or payload.required_by,
        shipping_cost=payload.shipping_cost,
        unit=payload.unit,
        total_budget=payload.total_budget if payload.total_budget is not None else payload.budget_max,
        min_reliability_score=payload.min_reliability_score,
        azcon_reference_required=bool(payload.azcon_reference_required),
        service_duration=payload.service_duration,
        start_date=payload.start_date,
        service_level=payload.service_level,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    batch_message = None
    if req.vendor_id and req.delivery_date:
        existing = (
            db.query(PurchaseRequest)
            .filter(
                PurchaseRequest.vendor_id == req.vendor_id,
                PurchaseRequest.delivery_date == req.delivery_date,
                PurchaseRequest.company_id != req.company_id,
            )
            .order_by(PurchaseRequest.id.desc())
            .first()
        )
        if existing:
            batch_id = existing.shipment_batch_id
            if not batch_id:
                batch = ShipmentBatch(vendor_id=req.vendor_id, delivery_date=req.delivery_date, shipping_discount_ratio=0.5)
                db.add(batch)
                db.commit()
                db.refresh(batch)
                existing.shipment_batch_id = batch.id
                existing.shipping_cost = round(existing.shipping_cost * 0.5, 2)
                batch_id = batch.id
            req.shipment_batch_id = batch_id
            req.shipping_cost = round(req.shipping_cost * 0.5, 2)
            db.commit()
            batch_message = "📦 Ortaq Çatdırılma: Digər departamentlə eyni vaxta düşdüyü üçün karqo xərci 50% azaldı!"

    return {
        "request_id": req.id,
        "title": req.title,
        "shipping_cost": req.shipping_cost,
        "shipment_batch_id": req.shipment_batch_id,
        "shared_logistics_badge": batch_message,
    }


@app.get("/procurement/storage-requests")
def list_storage_holder_requests_for_procurement(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER)),
):
    rows = (
        db.query(PurchaseRequest, User, Company, Vendor)
        .join(User, PurchaseRequest.requested_by == User.id)
        .join(Company, PurchaseRequest.company_id == Company.id)
        .outerjoin(Vendor, PurchaseRequest.vendor_id == Vendor.id)
        .filter(
            PurchaseRequest.company_id == current_user.company_id,
            PurchaseRequest.department == current_user.department,
            PurchaseRequest.status.in_([RequestStatus.SUBMITTED, RequestStatus.APPROVED]),
            User.role.in_([Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER]),
        )
        .order_by(PurchaseRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "title": req.title,
            "description": req.description,
            "status": req.status.value,
            "quantity": req.quantity,
            "item_type": req.item_type,
            "delivery_date": req.delivery_date,
            "required_by": req.required_by,
            "budget_min": req.budget_min,
            "budget_max": req.budget_max,
            "requested_by": requester.full_name,
            "requested_by_role": requester.role.value,
            "department": req.department,
            "company_name": company.name,
            "vendor_id": req.vendor_id,
            "vendor_name": vendor.company_name if vendor else None,
            # AI-agent aligned fields (used to pre-fill the /ai-agent page)
            "unit": req.unit,
            "total_budget": req.total_budget,
            "min_reliability_score": req.min_reliability_score,
            "azcon_reference_required": bool(req.azcon_reference_required),
            "service_duration": req.service_duration,
            "start_date": req.start_date,
            "service_level": req.service_level,
        }
        for req, requester, company, vendor in rows
    ]


@app.get("/department-admin/procurements")
def list_department_procurements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN)),
):
    """Procurement history (decided/completed/declined/recommended) for a
    department admin: every request submitted in their department, with
    decision metadata so they can audit what was bought, from whom, by whom,
    and at what price."""
    rows = (
        db.query(PurchaseRequest, User, Company, Vendor)
        .join(User, PurchaseRequest.requested_by == User.id)
        .join(Company, PurchaseRequest.company_id == Company.id)
        .outerjoin(Vendor, PurchaseRequest.vendor_id == Vendor.id)
        .filter(
            PurchaseRequest.company_id == current_user.company_id,
            PurchaseRequest.department == current_user.department,
        )
        .order_by(PurchaseRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "title": req.title,
            "description": req.description,
            "status": req.status.value,
            "item_type": req.item_type,
            "quantity": req.quantity,
            "unit": req.unit,
            "total_budget": req.total_budget if req.total_budget is not None else req.budget_max,
            "shipping_cost": req.shipping_cost,
            "delivery_date": req.delivery_date,
            "required_by": req.required_by,
            "service_duration": req.service_duration,
            "service_level": req.service_level,
            "department": req.department,
            "company_name": company.name,
            "requested_by": requester.full_name,
            "requested_by_role": requester.role.value,
            "vendor_id": req.vendor_id,
            "vendor_name": vendor.company_name if vendor else None,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        }
        for req, requester, company, vendor in rows
    ]


@app.get("/company-admin/department-activity")
def company_admin_department_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.COMPANY_ADMIN)),
):
    """Cross-department overview for a company admin: per-department admin,
    request volume by status, total spend so far, and the most recent
    decisions in each department."""
    company_id = current_user.company_id

    # Look up department admins of this company.
    dept_admins = (
        db.query(User)
        .filter(
            User.company_id == company_id,
            User.role == Role.DEPARTMENT_ADMIN,
            User.is_active.is_(True),
        )
        .all()
    )
    dept_admin_by_dept = {u.department: u for u in dept_admins}

    overview: list[dict] = []
    for dept in DEPARTMENT_CATEGORIES:
        dept_requests = (
            db.query(PurchaseRequest)
            .filter(
                PurchaseRequest.company_id == company_id,
                PurchaseRequest.department == dept,
            )
            .all()
        )
        if not dept_requests and dept not in dept_admin_by_dept:
            # Hide empty 'Others' bucket etc. when there's no admin and no data.
            continue

        status_counts: dict[str, int] = {}
        total_spend = 0.0
        for r in dept_requests:
            status_counts[r.status.value] = status_counts.get(r.status.value, 0) + 1
            if r.status == RequestStatus.DONE:
                total_spend += float(r.total_budget or r.budget_max or 0.0) + float(r.shipping_cost or 0.0)

        recent = (
            db.query(PurchaseRequest, Vendor)
            .outerjoin(Vendor, PurchaseRequest.vendor_id == Vendor.id)
            .filter(
                PurchaseRequest.company_id == company_id,
                PurchaseRequest.department == dept,
            )
            .order_by(PurchaseRequest.id.desc())
            .limit(5)
            .all()
        )
        admin = dept_admin_by_dept.get(dept)
        overview.append(
            {
                "department": dept,
                "department_admin": admin.full_name if admin else None,
                "department_admin_username": admin.username if admin else None,
                "total_requests": len(dept_requests),
                "status_counts": status_counts,
                "total_spend_done": round(total_spend, 2),
                "recent": [
                    {
                        "request_id": r.id,
                        "title": r.title,
                        "status": r.status.value,
                        "vendor_name": v.company_name if v else None,
                        "total_budget": r.total_budget if r.total_budget is not None else r.budget_max,
                        "delivery_date": r.delivery_date,
                    }
                    for r, v in recent
                ],
            }
        )
    return overview


def _request_tokens(req: PurchaseRequest) -> list[str]:
    text = f"{(req.title or '').lower()} {(req.description or '').lower()} {(req.department or '').lower()}"
    return [token for token in text.replace("/", " ").replace(",", " ").split() if token]


def _vendor_matches_request(vendor: Vendor, req: PurchaseRequest) -> bool:
    if not vendor.provided_categories:
        return False
    categories = vendor.provided_categories.lower()
    return any(token in categories for token in _request_tokens(req))


def _vendor_matches_department(vendor: Vendor, req: PurchaseRequest) -> bool:
    if not req.department:
        return True
    if not vendor.provided_categories:
        return False
    target = req.department.strip().lower()
    if not target:
        return True
    tokens = {
        token.strip().lower()
        for token in vendor.provided_categories.replace("/", ",").split(",")
        if token.strip()
    }
    return target in tokens


def _score_vendor(vendor: Vendor) -> float:
    # Lower price index + lower delivery days + higher quality should rank better.
    money_score = max(0.0, 100.0 - float(vendor.avg_price_index or 50.0))
    time_score = max(0.0, 100.0 - min(100.0, float(vendor.typical_delivery_days or 7) * 10.0))
    quality_score = max(0.0, min(100.0, float(vendor.quality_score or 50.0)))
    return round(0.4 * money_score + 0.3 * time_score + 0.3 * quality_score, 2)


def _rank_vendors(vendors: list[Vendor]) -> list[Vendor]:
    return sorted(
        vendors,
        key=lambda v: (
            -_score_vendor(v),
            float(v.avg_price_index or 50.0),
            int(v.typical_delivery_days or 7),
            -float(v.quality_score or 50.0),
        ),
    )


def _load_embedded_ai_companies() -> dict:
    mock_db_path = Path(__file__).resolve().parents[1] / "azcon-AI" / "azcon-ai-agent" / "mock_db.py"
    if not mock_db_path.exists():
        return {}
    spec = importlib.util.spec_from_file_location("embedded_azcon_ai_mock_db", mock_db_path)
    if not spec or not spec.loader:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "AZCON_COMPANIES", {}) or {}


def _build_internal_ai_choices(req: PurchaseRequest) -> list[dict]:
    companies = _load_embedded_ai_companies()
    if not companies:
        return []
    query = (req.title or "").strip().lower()
    qty = max(1, int(req.quantity or 1))
    choices: list[dict] = []
    for company_name, company_data in companies.items():
        for item in company_data.get("surplus_inventory", []):
            item_name = str(item.get("item_name", "")).lower()
            tags = [str(t).lower() for t in item.get("search_tags", [])]
            if query and query not in item_name and query not in tags:
                continue
            unit_price = float(item.get("price_per_unit", 0.0) or 0.0)
            reliability = float(item.get("reliability_score", 3.5) or 3.5)
            total_price = round(unit_price * qty, 2)
            choices.append(
                {
                    "source_type": "Internal AZCON",
                    "vendor_name": company_name,
                    "company_name": company_name,
                    "item_name": item.get("item_name", req.title),
                    "price_per_unit": unit_price,
                    "total_price": total_price,
                    "reliability_score": reliability,
                    "logistics_info": item.get("logistics_info", "AZCON internal logistics"),
                    "logistics_cost": 0.0,
                }
            )
    return choices


_TOP_TIER_DOMAINS = (
    "alibaba", "cdw.com", "cisco.com", "amazon.com", "amazon.", "made-in-china",
    "globalsources", "thomasnet", "dhl.com", "maersk.com", "freightos",
    "aws.amazon.com", "azure.microsoft.com", "cloudflare.com",
)
_KNOWN_B2B_DOMAINS = (
    "ebay.com", "homedepot.com", "lowes.com", "grainger.com", "indiamart.com",
    "tradeindia.com", "europages.", "kompass.com", "globalspec.com",
)


def _score_external_reliability(link: str) -> float:
    from urllib.parse import urlparse

    host = urlparse(link).netloc.lower()
    if any(domain in host for domain in _TOP_TIER_DOMAINS):
        return 4.8
    if any(domain in host for domain in _KNOWN_B2B_DOMAINS):
        return 4.4
    if link.lower().startswith("https://"):
        return 4.0
    return 3.2


def _build_external_ai_choices(req: PurchaseRequest) -> list[dict]:
    serper_key = os.getenv("SERPER_API_KEY")
    if not serper_key:
        logger.warning("SERPER_API_KEY not set; AI internet search disabled.")
        return []
    query = f"{req.title} supplier company price delivery"
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
            json={"q": query, "num": 10},
            timeout=20,
        )
        if resp.status_code >= 400:
            logger.error("Serper search failed: %s %s", resp.status_code, resp.text[:200])
            return []
        data = resp.json()
    except Exception as exc:
        logger.exception("Serper search raised: %s", exc)
        return []
    qty = max(1, int(req.quantity or 1))
    max_budget = float(req.budget_max or req.budget_min or 50000)
    unit_budget = max_budget / qty
    choices: list[dict] = []
    for result in data.get("organic", [])[:10]:
        title = str(result.get("title", "")).strip() or "External Vendor"
        snippet = str(result.get("snippet", "")).strip()
        link = str(result.get("link", "")).strip()
        if not link:
            continue
        # simple deterministic estimation for ranking dimensions
        price_per_unit = round(max(1.0, unit_budget * 0.85), 2)
        logistics_cost = round(max(20.0, qty * 1.8), 2)
        reliability = _score_external_reliability(link)
        choices.append(
            {
                "source_type": "External Web",
                "vendor_name": title[:80],
                "company_name": title[:80],
                "item_name": req.title,
                "price_per_unit": price_per_unit,
                "total_price": round(price_per_unit * qty + logistics_cost, 2),
                "reliability_score": reliability,
                "logistics_info": snippet[:160] or "External sourcing",
                "logistics_cost": logistics_cost,
                "source_link": link,
            }
        )
    return choices


def _search_internet_with_ai_agent(req: PurchaseRequest) -> dict:
    # Step 3 of the sourcing workflow: the AI agent must look at the public internet
    # (not internal AZCON inventory) and bring back the best options.
    offers = _build_external_ai_choices(req)
    if not offers:
        return {
            "strategy": "internet_search_unavailable",
            "message": "AI internet search returned no results (check SERPER_API_KEY or query).",
            "choices": [],
        }

    choices = sorted(
        offers,
        key=lambda o: (
            float(o.get("total_price", 10**12)),
            float(o.get("logistics_cost", 10**12)),
            -float(o.get("reliability_score", 0.0)),
        ),
    )[:5]
    if not choices:
        return {"strategy": "internet_search_no_results", "message": "AI internet search returned no choices.", "choices": []}
    top = choices[0]
    return {
        "strategy": "internet_search_top_choices",
        "message": "Top internet choices ranked by money, time, and quality.",
        "vendor_name": top.get("vendor_name") or top.get("company_name"),
        "choices": choices,
    }


def _find_vendor_for_accepted_request(db: Session, req: PurchaseRequest):
    # 1) Check approved vendor list of the same department in the requesting company.
    same_company = db.query(Vendor).filter(Vendor.company_id == req.company_id).all()
    same_company = [v for v in same_company if _vendor_matches_department(v, req)]
    ranked_same_company = _rank_vendors(same_company)
    if ranked_same_company:
        best = ranked_same_company[0]
        return {
            "strategy": "same_company_same_department",
            "vendor_id": best.id,
            "vendor_name": best.company_name,
            "provided_categories": best.provided_categories,
            "message": "Matched from your company's approved vendor list for this department.",
            "choices": [
                {"vendor_id": v.id, "vendor_name": v.company_name, "score": _score_vendor(v)}
                for v in ranked_same_company[:5]
            ],
        }

    # 2) Check approved vendor lists of the same department across other AZCON companies.
    cross_company = (
        db.query(Vendor)
        .filter(Vendor.company_id != req.company_id, Vendor.company_id.is_not(None))
        .all()
    )
    cross_company = [v for v in cross_company if _vendor_matches_department(v, req)]
    ranked_cross_company = _rank_vendors(cross_company)
    if ranked_cross_company:
        best = ranked_cross_company[0]
        return {
            "strategy": "cross_company_same_department",
            "vendor_id": best.id,
            "vendor_name": best.company_name,
            "provided_categories": best.provided_categories,
            "message": "No local match. Matched from the same department's approved vendors in other AZCON companies.",
            "choices": [
                {"vendor_id": v.id, "vendor_name": v.company_name, "score": _score_vendor(v)}
                for v in ranked_cross_company[:5]
            ],
        }

    # 3) Nothing approved anywhere — let the AI agent search the internet for best options.
    internet = _search_internet_with_ai_agent(req)
    top_choice = (internet.get("choices") or [{}])[0] if internet.get("choices") else {}
    vendor_name = internet.get("vendor_name") or top_choice.get("vendor_name") or top_choice.get("company_name")
    if vendor_name:
        vendor_name = str(vendor_name)
        vendor = db.query(Vendor).filter(Vendor.company_name == vendor_name).first()
        if not vendor:
            vendor = Vendor(
                company_id=req.company_id,
                company_name=vendor_name,
                provided_categories=req.department or req.title,
                is_trusted=False,
                reliability_score=70.0,
                quality_score=70.0,
                delivery_score=70.0,
                commercial_score=70.0,
                about="Discovered by AZCON AI internet search",
                avg_price_index=50.0,
                typical_delivery_days=7,
            )
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
        internet["vendor_id"] = vendor.id
        internet["vendor_name"] = vendor_name
        internet.setdefault("provided_categories", vendor.provided_categories)
        internet.setdefault(
            "message",
            "No approved vendor matched. AI internet search returned the best options.",
        )
    else:
        internet.setdefault(
            "message",
            "No approved vendor matched and AI internet search returned no usable options.",
        )
    internet.setdefault("strategy", "internet_search")
    return internet


@app.post("/procurement/requests/{request_id}/search-vendor")
def search_vendor_for_storage_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER)),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    require_same_company_or_admin(req.company_id, current_user)
    if req.department != current_user.department:
        raise HTTPException(status_code=403, detail="You can search vendors only for requests from your department")
    if req.status not in [RequestStatus.SUBMITTED, RequestStatus.APPROVED]:
        raise HTTPException(status_code=400, detail="Only submitted or accepted requests are eligible for vendor search")

    sourcing = _find_vendor_for_accepted_request(db, req)
    if sourcing.get("vendor_id"):
        req.vendor_id = sourcing["vendor_id"]
        db.commit()

    return {"message": "Vendor search completed", "sourcing": sourcing}


@app.post("/procurement/requests/{request_id}/accept")
def accept_storage_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER)),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    require_same_company_or_admin(req.company_id, current_user)
    if req.department != current_user.department:
        raise HTTPException(status_code=403, detail="You can accept only requests from your department")
    if req.status != RequestStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only submitted requests can be accepted")
    req.status = RequestStatus.APPROVED
    db.commit()
    return {"message": "Request accepted", "vendor_id": req.vendor_id}


@app.post("/procurement/requests/{request_id}/decline")
def decline_storage_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER)),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    require_same_company_or_admin(req.company_id, current_user)
    if req.department != current_user.department:
        raise HTTPException(status_code=403, detail="You can decline only requests from your department")
    if req.status not in [RequestStatus.SUBMITTED, RequestStatus.APPROVED]:
        raise HTTPException(status_code=400, detail="Only submitted or accepted requests can be declined")
    req.status = RequestStatus.REJECTED
    db.commit()
    return {"message": "Request declined"}


@app.post("/procurement/requests/{request_id}/done")
def mark_storage_request_done(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER)),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    require_same_company_or_admin(req.company_id, current_user)
    if req.status != RequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only accepted requests can be marked done")
    req.status = RequestStatus.DONE
    db.commit()
    return {"message": "Request marked as done"}


@app.post("/vendors")
def create_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN, Role.PLATFORM_ADMIN)),
):
    data = payload.model_dump()
    if current_user.role == Role.DEPARTMENT_ADMIN:
        data["company_id"] = current_user.company_id
        # Department admins curate their own department's vendor list, so the
        # admin's department must always be one of the provided categories.
        # Otherwise the GET filter would hide the vendor from the very admin
        # who just created it.
        dept = (current_user.department or "").strip()
        existing = (data.get("provided_categories") or "").strip()
        if not existing:
            data["provided_categories"] = dept
        else:
            existing_tokens = {
                token.strip().lower()
                for token in existing.replace("/", ",").split(",")
                if token.strip()
            }
            if dept and dept.lower() not in existing_tokens:
                data["provided_categories"] = f"{dept}, {existing}"

    # If a vendor with the same name already exists for this company, merge the
    # new categories in instead of failing on duplicate inserts. Vendors are
    # scoped per company so two companies may share the same vendor name.
    existing_vendor = (
        db.query(Vendor)
        .filter(
            Vendor.company_id == data.get("company_id"),
            Vendor.company_name == data["company_name"],
        )
        .first()
    )
    if existing_vendor:
        new_cats = (data.get("provided_categories") or "").strip()
        if new_cats:
            current_cats = (existing_vendor.provided_categories or "").strip()
            current_tokens = {
                token.strip().lower()
                for token in current_cats.replace("/", ",").split(",")
                if token.strip()
            }
            for cat in [c.strip() for c in new_cats.split(",") if c.strip()]:
                if cat.lower() not in current_tokens:
                    current_cats = f"{current_cats}, {cat}" if current_cats else cat
                    current_tokens.add(cat.lower())
            existing_vendor.provided_categories = current_cats
        if data.get("is_trusted") is not None:
            existing_vendor.is_trusted = bool(data["is_trusted"])
        db.commit()
        db.refresh(existing_vendor)
        return existing_vendor

    vendor = Vendor(**data)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@app.get("/company/vendors")
def list_company_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN, Role.PLATFORM_ADMIN)),
):
    query = db.query(Vendor)
    if current_user.role == Role.DEPARTMENT_ADMIN:
        # Department admins manage their company's approved vendor list as a
        # whole. Every vendor they add is auto-tagged with their department so
        # the AI matching still works, but the list view is company-wide so
        # nothing they create can ever be accidentally hidden from them.
        query = query.filter(Vendor.company_id == current_user.company_id)
    rows = query.order_by(Vendor.company_name.asc()).all()
    return [
        {
            "vendor_id": v.id,
            "vendor_name": v.company_name,
            "is_trusted": v.is_trusted,
            "provided_categories": v.provided_categories,
        }
        for v in rows
    ]


@app.post("/vendor-offers")
def create_vendor_offer(
    payload: VendorOfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    offer = VendorOffer(**payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@app.post("/requests/{request_id}/recommend")
def recommend_for_request(
    request_id: int,
    top_n: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    require_same_company_or_admin(req.company_id, current_user)

    recommendation = run_recommendation_pipeline(db, req, top_n=top_n)
    req.status = RequestStatus.RECOMMENDED
    db.commit()
    return recommendation


@app.post("/api/search")
def embedded_ai_search(payload: AISearchPayload):
    # Embedded AI endpoint so the AI subpage works under same uvicorn process.
    req_like = PurchaseRequest(
        title=payload.query,
        description=payload.query,
        quantity=payload.quantity or 1,
        budget_min=payload.total_budget,
        budget_max=payload.total_budget,
        required_by=payload.deadline or payload.start_date or datetime.utcnow().date().isoformat(),
        department=payload.category or "Others",
        item_type=payload.procurement_type if payload.procurement_type in ["product", "service"] else "product",
    )
    internal = _build_internal_ai_choices(req_like)
    external = [] if payload.azcon_reference_required else _build_external_ai_choices(req_like)
    offers = internal + external
    offers = [o for o in offers if float(o.get("reliability_score", 0.0)) >= float(payload.min_reliability_score or 0.0)]
    offers = sorted(
        offers,
        key=lambda o: (
            float(o.get("total_price", 10**12)),
            float(o.get("logistics_cost", 10**12)),
            -float(o.get("reliability_score", 0.0)),
        ),
    )
    return {"query": payload.query, "procurement_type": req_like.item_type, "offers": offers[:10]}


@app.get("/catalog/expensive-items")
def expensive_items(company_name: str, department: str):
    company_specific = EXPENSIVE_NEEDS.get(company_name, [])
    if department.lower().startswith("hr"):
        company_specific = company_specific + HR_NEEDS
    return {"company_name": company_name, "department": department, "items": company_specific, "manual_input_label": "➕ Digər ehtiyac (Əllə daxil et)"}


@app.get("/analytics/company-expenses")
def company_expenses(company_name: str):
    return get_expense_mock(company_name)


@app.get("/vendors-marketplace")
def vendors_marketplace(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).order_by(Vendor.company_name.asc()).all()
    return [
        {
            "vendor_id": v.id,
            "vendor_name": v.company_name,
            "success_rate": round((v.reliability_score + v.quality_score + v.delivery_score + v.commercial_score) / 4, 2),
            "about": v.about,
        }
        for v in vendors
    ]


@app.get("/vendors/{vendor_id}/profile")
def vendor_profile(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.company_name,
        "about": vendor.about,
        "feedback": [
            {"buyer": "Bakı Metropoliteni QSC", "comment": "Vaxtında çatdırılma və yüksək keyfiyyət.", "rating": 5},
            {"buyer": "Azərbaycan Dəmir Yolları (ADY)", "comment": "Qiymət/performans balansı yaxşıdır.", "rating": 4},
        ],
        "previous_sales": [
            {"company": "AZAL", "what_sold": "Terminal logistika skanerləri"},
            {"company": "Bakı Limanı", "what_sold": "Forklift ehtiyat hissələri"},
        ],
    }