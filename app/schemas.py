from pydantic import BaseModel, EmailStr, Field

from app.models import RequestStatus, Role


class CompanyCreate(BaseModel):
    name: str
    code: str


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=4)
    role: Role
    company_id: int | None = None


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=1)


class RegistrationRequestCreate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str = Field(min_length=4)
    company_name: str
    requested_role: Role


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Role
    company_id: int | None

    class Config:
        from_attributes = True


class InventoryCreate(BaseModel):
    name: str
    quantity: int
    min_threshold: int = 10
    unit: str = "unit"


class InventoryUpdate(BaseModel):
    quantity: int


class InventoryUpdateByName(BaseModel):
    item_name: str
    quantity: int


class PurchaseRequestCreate(BaseModel):
    title: str
    description: str
    quantity: int = 1
    budget_min: float | None = None
    budget_max: float | None = None
    required_by: str


class PurchaseRequestOut(BaseModel):
    id: int
    company_id: int
    requested_by: int
    title: str
    description: str
    quantity: int
    budget_min: float | None
    budget_max: float | None
    required_by: str
    status: RequestStatus

    class Config:
        from_attributes = True


class VendorCreate(BaseModel):
    company_name: str
    is_trusted: bool = False
    reliability_score: float = 50.0
    quality_score: float = 50.0
    delivery_score: float = 50.0
    commercial_score: float = 50.0


class VendorOfferCreate(BaseModel):
    vendor_id: int
    category: str
    title: str
    price: float
    currency: str = "USD"
    lead_time_days: int = 7
    quality_score: float = 60.0
