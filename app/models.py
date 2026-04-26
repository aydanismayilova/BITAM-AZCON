import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    STORAGE_HOLDER = "storage_holder"
    PROCUREMENT_DECIDER = "procurement_decider"
    DEPARTMENT_ADMIN = "department_admin"
    COMPANY_ADMIN = "company_admin"
    PLATFORM_ADMIN = "platform_admin"
    VENDOR_USER = "vendor_user"


class RequestStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    REJECTED = "rejected"
    DONE = "done"


class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_rate: Mapped[float] = mapped_column(Float, default=75.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="company")
    inventory_items = relationship("InventoryItem", back_populates="company")
    purchase_requests = relationship("PurchaseRequest", back_populates="company")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    username: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company = relationship("Company", back_populates="users")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    min_threshold: Mapped[int] = mapped_column(Integer, default=10)
    unit: Mapped[str] = mapped_column(String(20), default="unit")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="inventory_items")


class ShortageAlert(Base):
    __tablename__ = "shortage_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), index=True)
    triggered_quantity: Mapped[int] = mapped_column(Integer)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    required_by: Mapped[str] = mapped_column(String(40))
    department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    item_type: Mapped[str] = mapped_column(String(20), default="product")
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True, index=True)
    delivery_date: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    shipping_cost: Mapped[float] = mapped_column(Float, default=1000.0)
    shipment_batch_id: Mapped[int | None] = mapped_column(ForeignKey("shipment_batches.id"), nullable=True, index=True)
    sourcing_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    sourcing_vendor_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sourcing_vendor_website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.SUBMITTED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="purchase_requests")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    company_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provided_categories: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    reliability_score: Mapped[float] = mapped_column(Float, default=50.0)
    quality_score: Mapped[float] = mapped_column(Float, default=50.0)
    delivery_score: Mapped[float] = mapped_column(Float, default=50.0)
    commercial_score: Mapped[float] = mapped_column(Float, default=50.0)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    avg_price_index: Mapped[float] = mapped_column(Float, default=50.0)
    typical_delivery_days: Mapped[int] = mapped_column(Integer, default=7)


class VendorOffer(Base):
    __tablename__ = "vendor_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(120))
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(5), default="USD")
    lead_time_days: Mapped[int] = mapped_column(Integer, default=7)
    quality_score: Mapped[float] = mapped_column(Float, default=60.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ResearchCache(Base):
    __tablename__ = "research_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    normalized_query: Mapped[str] = mapped_column(String(200), index=True)
    source: Mapped[str] = mapped_column(String(30), default="ai_agent")
    payload_json: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RegistrationRequest(Base):
    __tablename__ = "registration_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(120))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    department: Mapped[str] = mapped_column(String(120))
    requested_role: Mapped[Role] = mapped_column(Enum(Role))
    status: Mapped[RegistrationStatus] = mapped_column(Enum(RegistrationStatus), default=RegistrationStatus.PENDING)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ShipmentBatch(Base):
    __tablename__ = "shipment_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), index=True)
    delivery_date: Mapped[str] = mapped_column(String(40), index=True)
    shipping_discount_ratio: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
