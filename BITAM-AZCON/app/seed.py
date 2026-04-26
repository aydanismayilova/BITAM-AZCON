from app.database import Base, SessionLocal, engine
from app.models import Company, Role, User, Vendor, VendorOffer


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Company).count() > 0:
            print("Seed already exists.")
            return
        
        companies = [
            Company(
                name="Bakı Metropoliteni QSC",
                code="AZC-METRO",
                success_rate=93.5,
                about="Yeraltı nəqliyyat şəbəkəsi və infrastruktura texniki xidmət göstərən dövlət qurumu.",
            ),
            Company(
                name="AZAL",
                code="AZC-AZAL",
                success_rate=90.2,
                about="Aviadaşıma, terminal əməliyyatları və hava limanı logistikası sahəsində fəaliyyət göstərir.",
            ),
            Company(
                name="Aztelekom MMC",
                code="AZC-AZT",
                success_rate=89.1,
                about="Telekommunikasiya infrastrukturu, fiber və enterprise şəbəkə həlləri üzrə ixtisaslaşır.",
            ),
            Company(
                name="Azərbaycan Dəmir Yolları (ADY)",
                code="AZC-ADY",
                success_rate=91.7,
                about="Dəmir yolu yük və sərnişin daşımaları üçün kritik infrastruktur idarəçiliyini aparır.",
            ),
            Company(
                name="Bakı Limanı",
                code="AZC-LIMAN",
                success_rate=88.9,
                about="Dəniz yük daşımaları və konteyner logistikası üçün əsas regional mərkəzdir.",
            ),
        ]
        db.add_all(companies)
        db.flush()

        c1 = companies[0]

        users = [
            User(full_name="General Admin", username="faigtayibov", email="faigtayibov@azcon.ai", password="1234", role=Role.PLATFORM_ADMIN),
            User(full_name="Storage Holder X", username="storageX", email="storageX@azcon.ai", password="pass", role=Role.STORAGE_HOLDER, company_id=c1.id, department="İnfrastruktur"),
            User(full_name="Procurement Decider X", username="deciderX", email="deciderX@azcon.ai", password="pass", role=Role.PROCUREMENT_DECIDER, company_id=c1.id, department="Satınalma"),
            User(full_name="Company Admin X", username="companyadminX", email="companyadminX@azcon.ai", password="pass", role=Role.COMPANY_ADMIN, company_id=c1.id, department="İdarəetmə"),
        ]
        db.add_all(users)

        v1 = Vendor(
            company_name="Caspian Industrial Supply",
            is_trusted=True,
            reliability_score=88,
            quality_score=90,
            delivery_score=80,
            commercial_score=78,
            avg_price_index=72,
            typical_delivery_days=4,
            about="Ağır sənaye və infrastruktur sifarişləri üçün ixtisaslaşmış regional təchizatçı.",
        )
        v2 = Vendor(
            company_name="TransLogistics Tech",
            is_trusted=False,
            reliability_score=70,
            quality_score=72,
            delivery_score=66,
            commercial_score=84,
            avg_price_index=68,
            typical_delivery_days=6,
            about="Müxtəlif dövlət şirkətləri üçün orta və iri həcmli texniki məhsul çatdırılması həyata keçirir.",
        )
        v3 = Vendor(
            company_name="MedService Group",
            is_trusted=True,
            reliability_score=86,
            quality_score=84,
            delivery_score=87,
            commercial_score=76,
            avg_price_index=65,
            typical_delivery_days=3,
            about="Tibbi xidmət və korporativ sağlamlıq paketləri təqdim edən ixtisaslaşmış xidmət təminatçısı.",
        )
        db.add_all([v1, v2, v3])
        db.flush()

        offers = [
            VendorOffer(vendor_id=v1.id, category="eskalator", title="Eskalator ehtiyat hissələri dəsti", price=28000, lead_time_days=7, quality_score=91),
            VendorOffer(vendor_id=v1.id, category="fiber", title="Fiber-optik kabel 1km seqment", price=22000, lead_time_days=5, quality_score=89),
            VendorOffer(vendor_id=v2.id, category="forklift", title="Yük terminalı forklift", price=56000, lead_time_days=9, quality_score=75),
            VendorOffer(vendor_id=v3.id, category="tibbi", title="Korporativ tibbi müayinə xidməti", price=12000, lead_time_days=2, quality_score=88),
        ]
        db.add_all(offers)
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
