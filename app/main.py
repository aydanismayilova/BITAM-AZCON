from pathlib import Path
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

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

COMPANY_DEPARTMENTS = {entry["name"]: ["IT", "Logistics", "TELECOM"] for entry in COMPANY_CATALOG}

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
            ("ALTER TABLE purchase_requests ADD COLUMN sourcing_feedback TEXT", "sourcing_feedback"),
            ("ALTER TABLE purchase_requests ADD COLUMN sourcing_vendor_name VARCHAR(120)", "sourcing_vendor_name"),
            ("ALTER TABLE purchase_requests ADD COLUMN sourcing_vendor_website VARCHAR(255)", "sourcing_vendor_website"),
        ]:
            if col_name not in req_cols:
                conn.execute(text(statement))

        vendor_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(vendors)")).fetchall()]
        for statement, col_name in [
            ("ALTER TABLE vendors ADD COLUMN company_id INTEGER", "company_id"),
            ("ALTER TABLE vendors ADD COLUMN department VARCHAR(120)", "department"),
            ("ALTER TABLE vendors ADD COLUMN website_url VARCHAR(255)", "website_url"),
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
        if payload.department not in ["IT", "Logistics", "TELECOM"]:
            raise HTTPException(status_code=400, detail="Department must be IT, Logistics, or TELECOM")
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
        if payload.department not in ["IT", "Logistics", "TELECOM"]:
            raise HTTPException(status_code=400, detail="Department must be IT, Logistics, or TELECOM")
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
    current_user: User = Depends(require_roles(Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER, Role.COMPANY_ADMIN, Role.DEPARTMENT_ADMIN)),
):
    if current_user.role != Role.PLATFORM_ADMIN and current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User has no company context")
    company_id = current_user.company_id if current_user.role != Role.PLATFORM_ADMIN else 1
    # Procurement deciders can create direct requests without an extra approval step.
    initial_status = RequestStatus.APPROVED if current_user.role == Role.PROCUREMENT_DECIDER else RequestStatus.SUBMITTED
    req = PurchaseRequest(
        company_id=company_id,
        requested_by=current_user.id,
        title=payload.title,
        description=payload.description,
        quantity=payload.quantity,
        budget_min=payload.budget_min,
        budget_max=payload.budget_max,
        required_by=payload.required_by,
        status=initial_status,
        department=payload.department or current_user.department,
        item_type=payload.item_type,
        vendor_id=payload.vendor_id,
        delivery_date=payload.delivery_date or payload.required_by,
        shipping_cost=payload.shipping_cost,
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
        db.query(PurchaseRequest, User, Company)
        .join(User, PurchaseRequest.requested_by == User.id)
        .join(Company, PurchaseRequest.company_id == Company.id)
        .filter(
            PurchaseRequest.company_id == current_user.company_id,
            PurchaseRequest.department == current_user.department,
            User.role == Role.STORAGE_HOLDER,
            PurchaseRequest.status == RequestStatus.SUBMITTED,
        )
        .order_by(PurchaseRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "title": req.title,
            "status": req.status.value,
            "requested_by": requester.full_name,
            "department": req.department,
            "company_name": company.name,
        }
        for req, requester, company in rows
    ]


@app.get("/procurement/request-form-needs")
def list_request_form_needs_for_procurement(
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
            User.role.in_([Role.STORAGE_HOLDER, Role.PROCUREMENT_DECIDER]),
            PurchaseRequest.status == RequestStatus.APPROVED,
        )
        .order_by(PurchaseRequest.id.desc())
        .all()
    )
    return [
        {
            "request_id": req.id,
            "title": req.title,
            "description": req.description,
            "quantity": req.quantity,
            "status": req.status.value,
            "requested_by": requester.full_name,
            "department": req.department,
            "company_name": company.name,
            "vendor_id": req.vendor_id,
            "vendor_name": vendor.company_name if vendor else None,
            "vendor_website": vendor.website_url if vendor else None,
            "sourcing_feedback": req.sourcing_feedback,
            "sourcing_vendor_name": req.sourcing_vendor_name,
            "sourcing_vendor_website": req.sourcing_vendor_website,
        }
        for req, requester, company, vendor in rows
    ]


def _request_tokens(req: PurchaseRequest) -> list[str]:
    text = f"{(req.title or '').lower()} {(req.description or '').lower()} {(req.department or '').lower()}"
    return [token for token in text.replace("/", " ").replace(",", " ").split() if token]


def _vendor_matches_request(vendor: Vendor, req: PurchaseRequest) -> bool:
    if not vendor.provided_categories:
        return False
    categories = vendor.provided_categories.lower()
    return any(token in categories for token in _request_tokens(req))


def _find_vendor_for_accepted_request(db: Session, req: PurchaseRequest):
    same_company_vendors = (
        db.query(Vendor)
        .filter(
            Vendor.company_id == req.company_id,
            Vendor.department == req.department,
            Vendor.is_trusted.is_(True),
        )
        .all()
    )
    for vendor in same_company_vendors:
        if _vendor_matches_request(vendor, req):
            return {
                "strategy": "company_department_approved_vendor",
                "vendor_id": vendor.id,
                "vendor_name": vendor.company_name,
                "vendor_website": vendor.website_url,
                "provided_categories": vendor.provided_categories,
                "message": "Matched from your company's approved vendor list in the same department.",
            }

    cross_company_vendors = (
        db.query(Vendor)
        .filter(
            Vendor.company_id != req.company_id,
            Vendor.department == req.department,
            Vendor.is_trusted.is_(True),
        )
        .all()
    )
    for vendor in cross_company_vendors:
        if _vendor_matches_request(vendor, req):
            return {
                "strategy": "cross_company_same_department_vendor",
                "vendor_id": vendor.id,
                "vendor_name": vendor.company_name,
                "vendor_website": vendor.website_url,
                "provided_categories": vendor.provided_categories,
                "message": "No same-company vendor found in this department; matched from other companies with the same department.",
            }

    return {
        "strategy": "no_approved_vendor_found",
        "message": "Sorry, there is no approved vendor on the platform for this product or service.",
    }


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
    return {"message": "Request accepted and moved to Request Form needs list."}


@app.post("/procurement/requests/{request_id}/search-vendor")
def search_vendor_for_request(
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
    if req.status != RequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only accepted requests can be searched for vendors")

    sourcing = _find_vendor_for_accepted_request(db, req)
    req.sourcing_feedback = sourcing.get("message")
    req.sourcing_vendor_name = sourcing.get("vendor_name")
    req.sourcing_vendor_website = sourcing.get("vendor_website")
    db.commit()

    return {"message": "Vendor search completed", "sourcing": sourcing}


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
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN)),
):
    data = payload.model_dump()
    data["company_id"] = current_user.company_id
    data["department"] = current_user.department
    vendor = Vendor(**data)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@app.get("/company/vendors")
def list_company_vendors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.DEPARTMENT_ADMIN)),
):
    query = db.query(Vendor).filter(Vendor.company_id == current_user.company_id)
    rows = query.order_by(Vendor.company_name.asc()).all()
    return [
        {
            "vendor_id": v.id,
            "vendor_name": v.company_name,
            "vendor_website": v.website_url,
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