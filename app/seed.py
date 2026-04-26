from app.database import Base, SessionLocal, engine
from app.models import Company, Role, User, Vendor, VendorOffer


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Company).count() > 0:
            print("Seed already exists.")
            return
        
        c1 = Company(name="Azerbaijan Airlines- AZAL", code="AZC-01")
        c2 = Company(name="Azebaijan Railways", code="AZC-02")
        c3 = Company(name="Azerbaijan Caspian Shipping Company", code="AZC-03")
        c4 = Company(name="Baku Metro", code="AZC-04")
        c5 = Company(name="Baku Bus", code="AZC-05")
        c6 = Company(name="Baku Shipyard", code="AZC-06")
        c7 = Company(name="Azercosmos", code="AZC-07")
        c8 = Company(name="Aztelekom", code="AZC-08")
        c9 = Company(name="Azerpost", code="AZC-09")
        c10 = Company(name="Baku Taxi Service", code="AZC-10")
        c11 = Company(name='"Teleradio" LLC', code="AZC-11")
        c12 = Company(name="National Artificial Intelligence Center", code="AZC-12")
        db.add_all([c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12])
        db.flush()

        users = [
            User(full_name="General Admin", username="faigtayibov", email="faigtayibov@azcon.ai", password="1234", role=Role.PLATFORM_ADMIN),
            User(full_name="Storage Holder X", username="storageX", email="storageX@azcon.ai", password="pass", role=Role.STORAGE_HOLDER, company_id=c1.id),
            User(full_name="Procurement Decider X", username="deciderX", email="deciderX@azcon.ai", password="pass", role=Role.PROCUREMENT_DECIDER, company_id=c1.id),
            User(full_name="Company Admin X", username="companyadminX", email="companyadminX@azcon.ai", password="pass", role=Role.COMPANY_ADMIN, company_id=c1.id),
        ]
        db.add_all(users)

        v1 = Vendor(
            company_name="Trusted Steel Co",
            is_trusted=True,
            reliability_score=88,
            quality_score=90,
            delivery_score=80,
            commercial_score=78,
        )
        v2 = Vendor(
            company_name="External Supply Hub",
            is_trusted=False,
            reliability_score=70,
            quality_score=72,
            delivery_score=66,
            commercial_score=84,
        )
        db.add_all([v1, v2])
        db.flush()

        offers = [
            VendorOffer(vendor_id=v1.id, category="cement", title="OPC Cement 50kg", price=8.2, lead_time_days=3, quality_score=91),
            VendorOffer(vendor_id=v1.id, category="steel", title="Rebar Grade 60", price=540, lead_time_days=5, quality_score=89),
            VendorOffer(vendor_id=v2.id, category="cement", title="Portland Cement Bulk", price=7.9, lead_time_days=8, quality_score=75),
        ]
        db.add_all(offers)
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
