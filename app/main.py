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


def run_light_migrations():
    with engine.begin() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
        if "username" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(120)"))


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
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
    }


@app.get("/companies-public")
def list_companies_public(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.name.asc()).all()


@app.post("/auth/register-request")
def create_registration_request(payload: RegistrationRequestCreate, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.name == payload.company_name).first()
    if not company:
        raise HTTPException(status_code=404, detail="Selected company does not exist")

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

    req = RegistrationRequest(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        company_id=company.id,
        requested_role=payload.requested_role,
        status=RegistrationStatus.PENDING,
    )
    db.add(req)
    db.commit()
    return {"message": "Registration request submitted to admin for approval"}


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
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        company_id=payload.company_id,
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
            "company_name": company.name,
            "requested_by": requester.full_name,
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
        .filter(RegistrationRequest.status == RegistrationStatus.PENDING)
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
        is_active=True,
    )
    db.add(user)
    req.status = RegistrationStatus.APPROVED
    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": "Registration approved", "username": user.username}


@app.post("/requests")
def create_purchase_request(
    payload: PurchaseRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    if current_user.role != Role.PLATFORM_ADMIN and current_user.company_id is None:
        raise HTTPException(status_code=400, detail="User has no company context")
    company_id = current_user.company_id if current_user.role != Role.PLATFORM_ADMIN else 1
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
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@app.post("/vendors")
def create_vendor(
    payload: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    vendor = Vendor(**payload.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.PROCUREMENT_DECIDER, Role.COMPANY_ADMIN, Role.PLATFORM_ADMIN)),
):
    req = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    require_same_company_or_admin(req.company_id, current_user)

    recommendation = run_recommendation_pipeline(db, req)
    req.status = RequestStatus.RECOMMENDED
    db.commit()
    return recommendation
