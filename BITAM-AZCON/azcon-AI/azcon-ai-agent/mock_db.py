# =============================================================================
#  AZCON HOLDİNQ — BİRLƏŞDİRİLMİŞ VERİLƏNLƏR BAZASI
#  mock_db.py  |  v2.0  |  Smart Procurement & Logistics
#
#  Strukturu:
#    AZCON_COMPANIES  →  əsas lüğət
#    surplus_inventory → item_name, search_tags, quantity_available, unit,
#                        price_per_unit (AZN), logistics_cost_per_unit (AZN),
#                        reliability_score (1-5), logistics_info, notes
#    services          → name, search_tags, type, description, sla
#    active_orders     → vendor, item, expected_delivery, origin_country
#
#  Valyuta: 1 USD = 1.70 AZN (2026 məzənnəsi ilə hesablanmışdır)
# =============================================================================

_USD = 1.70   # AZN konversiya əmsalı — bütün qiymətlər bu əmsal ilə AZN-ə çevrilir

AZCON_COMPANIES = {

    # =========================================================================
    # 1. AZAL — Azərbaycan Hava Yolları
    #    Milli hava daşıyıcısı | 35 təyyarə | 63+ marşrut | Skytrax 4-star
    # =========================================================================
    "AZAL": {
        "surplus_inventory": [
            {
                "item_name": "Aviasiya hidravlik mayesi Skydrol 500B-4",
                "search_tags": [
                    "hidravlik maye", "skydrol", "hydraulic fluid", "aircraft hydraulic",
                    "aviasiya yağı", "aviation oil", "hava gəmisi yağı", "təyyarə yağı"
                ],
                "quantity_available": 3200,
                "unit": "litr",
                "price_per_unit": round(18.50 * _USD, 2),
                "logistics_cost_per_unit": round(0.80 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Bakı anbarından çatdırılma; ADR Sinif 3 (yanıcı maye); xüsusi konteyner tələb olunur",
                "notes": "A320neo texniki xidmət planının dəyişməsi səbəbindən artıq qalmışdır; orijinal qablaşdırmada, yararlılıq müddəti 2027-ə qədər"
            },
            {
                "item_name": "CFM56-5B turbofan mühərrik qanad dəsti (blade set)",
                "search_tags": [
                    "təyyarə mühərriki", "turbofan", "engine blade", "jet engine part",
                    "CFM56", "mühərrik hissəsi", "aircraft engine component", "blade set",
                    "aviasiya ehtiyat hissəsi", "spare parts"
                ],
                "quantity_available": 14,
                "unit": "dəst",
                "price_per_unit": round(4_200 * _USD, 2),
                "logistics_cost_per_unit": round(120 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Havayolu ilə çatdırılma tövsiyə olunur; hər dəst 45 kq; EASA sertifikatlıdır",
                "notes": "A320ceo donanması A320neo ilə əvəzləndiyi üçün artıq qalmışdır; texniki sertifikatlar mövcuddur"
            },
            {
                "item_name": "Aviasiya yanacaq filtrləri Parker Hannifin 15MCPG",
                "search_tags": [
                    "yanacaq filtri", "fuel filter", "aviation filter", "Parker filter",
                    "aviasiya filtrləri", "jet fuel filter", "aircraft filter", "15MCPG"
                ],
                "quantity_available": 480,
                "unit": "ədəd",
                "price_per_unit": round(95 * _USD, 2),
                "logistics_cost_per_unit": round(2.50 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Standart qutularda; hər qutuda 12 ədəd; palet ilə göndərilə bilər",
                "notes": "Standart dəyişikliyi ilə artıqlıq yaranmışdır; yararlılıq müddəti 2028"
            },
            {
                "item_name": "Business class dəri oturacaq A320 spec",
                "search_tags": [
                    "oturacaq", "seat", "business class seat", "aircraft seat",
                    "cabin seat", "dəri oturacaq", "leather seat", "aviasiya oturacağı",
                    "təyyarə oturacağı", "kreslo"
                ],
                "quantity_available": 36,
                "unit": "ədəd",
                "price_per_unit": round(1_800 * _USD, 2),
                "logistics_cost_per_unit": round(45 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Böyük həcmli yük; qorunan qablaşdırma tələb olunur; EASA STC sənədi mövcuddur",
                "notes": "Kabinə yenilənməsi zamanı çıxarılmışdır; salamat, temiz vəziyyətdədir"
            },
            {
                "item_name": "Aviasiya təkəri Boeing/Airbus uyğun (Dunlop APW08-7)",
                "search_tags": [
                    "təyyarə təkəri", "aircraft tire", "airplane wheel", "aviation tire",
                    "dunlop", "təkər", "şin", "tire", "wheel", "landing gear tire"
                ],
                "quantity_available": 24,
                "unit": "ədəd",
                "price_per_unit": round(800 * _USD, 2),
                "logistics_cost_per_unit": round(50 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Xüsusi nəqliyyat çərçivəsi tələb olunur; çatdırılma 3-5 iş günü",
                "notes": "Donanma yeniləməsindən sonra artıq qalan ehtiyat; FAA/EASA sertifikatlı"
            },
        ],
        "services": [
            {
                "name": "Hava yük daşıma xidməti (AZCON daxili)",
                "search_tags": [
                    "hava yük", "air cargo", "freight", "cargo transport", "yük daşıma",
                    "aviation logistics", "air freight", "charter cargo", "hava nəqliyyatı"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin kiçik həcmli yüklərini (sənəd, hissə, avadanlıq) "
                    "AZAL-ın mövcud 63+ beynəlxalq marşrutu üzərindən daşıma. "
                    "Scope: sifariş qəbulu, yük sığortası, gömrük bəyannaməsi dəstəyi, "
                    "real-vaxt izləmə. Tarifə kargo növü və çəkisi təsir edir."
                ),
                "sla": "Sifarişdən 48 saat ərzində yükləmə; transit müddəti marşruta görə 1-3 gün"
            },
            {
                "name": "Pilot və sürücü tibbi sertifikasiyası (GCAA standartı)",
                "search_tags": [
                    "tibbi sertifikat", "medical certification", "driver medical", "pilot exam",
                    "psixomotor sınaq", "psychomotor test", "sürücü yoxlaması", "health check",
                    "GCAA", "tibbi müayinə", "sağlamlıq yoxlanışı"
                ],
                "type": "monthly",
                "description": (
                    "AZAL-ın lisenziyalı tibbi heyəti BakuBus, Bakı Taksi Xidməti və ADY "
                    "sürücüləri üçün PSİXOMOTOR sınaqlar keçirir. "
                    "Scope: dərin diqqət, reaksiya müddəti, görmə testi, eşitmə testi, "
                    "rəsmi tibbi arayış verilməsi."
                ),
                "sla": "Müayinə günündən 24 saat ərzində rəsmi nəticə; 50 nəfərə qədər aylıq paket"
            },
            {
                "name": "Heydar Əliyev Aeroportu temperatur nəzarətli anbar icarəsi",
                "search_tags": [
                    "anbar icarəsi", "warehouse rental", "airport warehouse", "cold storage",
                    "temperatur nəzarəti", "temperature controlled", "aeroport anbarı",
                    "storage lease", "depo", "saxlama sahəsi"
                ],
                "type": "monthly",
                "description": (
                    "Aeroportdakı temperatur nəzarətli anbar otaqlarının AZCON şirkətlərinə "
                    "icarəyə verilməsi (min. 200 m²). "
                    "Scope: 24/7 kamera müşahidəsi, giriş nəzarəti, soyuq saxlama (+2°C/+25°C), "
                    "yanğın sönmə sistemi, gömrük nəzarəti altında çalışma imkanı."
                ),
                "sla": "7/24 giriş; aylıq hesabat; 48 saatlıq xəbərdarlıqla imtina imkanı"
            },
        ],
        "active_orders": [
            {
                "vendor": "AerCap Holdings (İrlandiya)",
                "item": "Airbus A321neo icarəsi — 6 ədəd (AerCap+CDB Aviation portfeli)",
                "expected_delivery": "2026-Q2",
                "origin_country": "Fransa"
            },
            {
                "vendor": "CFM International (ABŞ / Fransa ortaq müəssisə)",
                "item": "LEAP-1A mühərrik texniki xidmət paketi (A320neo donanması üçün)",
                "expected_delivery": "2026-Q1",
                "origin_country": "ABŞ"
            },
            {
                "vendor": "Rolls-Royce (Birləşmiş Krallıq)",
                "item": "Boeing 787-8 Trent 1000 mühərrik overhaul dəsti",
                "expected_delivery": "2026-Q3",
                "origin_country": "Birləşmiş Krallıq"
            },
        ]
    },

    # =========================================================================
    # 2. BAKI METROPOLİTENİ
    #    40.7 km | 3 xətt | 27 stansiya | 627,000+ gündəlik sərnişin
    # =========================================================================
    "Baki_Metropoliteni": {
        "surplus_inventory": [
            {
                "item_name": "81-540 seriyalı köhnə metro vaqonu texniki hissə dəsti",
                "search_tags": [
                    "metro vaqonu", "metro car", "rail car", "vaqon hissəsi",
                    "train spare parts", "metro hissə", "railway car component",
                    "81-540", "metro ehtiyat hissəsi"
                ],
                "quantity_available": 8,
                "unit": "vaqon ekvivalenti",
                "price_per_unit": round(15_000 * _USD, 2),
                "logistics_cost_per_unit": round(2_500 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Narimanov depodan götürülür; ağır yük nəqliyyatı tələb olunur; ADY platforması ilə uyğun",
                "notes": "81-765B/766B seriyası ilə əvəzlənmiş; hissə olaraq istifadəyə yararlıdır; qiymət danışıq əsasında"
            },
            {
                "item_name": "Polad rels UIC60 standartı",
                "search_tags": [
                    "rels", "rail", "railway rail", "polad rels", "steel rail",
                    "UIC60", "yol relsi", "dəmir yolu relsi", "track rail",
                    "train track", "metal rail"
                ],
                "quantity_available": 1200,
                "unit": "metr",
                "price_per_unit": round(38 * _USD, 2),
                "logistics_cost_per_unit": round(1.20 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Palet və ya düz yük vasitəsilə; ADY platformasında da uyğundur",
                "notes": "Körpü bölməsinin dəyişdirilməsindən artıq qalan; sertifikatlı EN 13674-1"
            },
            {
                "item_name": "LED perrona işıqlandırma modulu Philips Fortimo",
                "search_tags": [
                    "LED işıq", "LED light", "platform lighting", "peron işığı",
                    "Philips Fortimo", "stansiya işıqlandırması", "underground lighting",
                    "işıq modulu", "lighting module", "led modul"
                ],
                "quantity_available": 340,
                "unit": "ədəd",
                "price_per_unit": round(72 * _USD, 2),
                "logistics_cost_per_unit": round(3 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Standart qutularda; fragil işarəsi; 5 iş günündə çatdırılma",
                "notes": "Stansiya bərpası zamanı planlaşdırılandan çox alınmışdır; yararlılıq müddəti 50,000 saat"
            },
            {
                "item_name": "Eskalator elektrik mühərriki (1.5 kW, 50Hz)",
                "search_tags": [
                    "eskalator", "escalator", "escalator motor", "metro eskalator",
                    "eskalator mühərriki", "moving staircase", "elevator motor",
                    "elektrik mühərriki", "electric motor"
                ],
                "quantity_available": 12,
                "unit": "ədəd",
                "price_per_unit": round(2_000 * _USD, 2),
                "logistics_cost_per_unit": round(100 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Ağır avadanlıq; forklift tələb olunur; 7-10 gün çatdırılma",
                "notes": "Stansiya eskalator sisteminin yenilənməsindən çıxarılmışdır; yaxşı vəziyyətdədir"
            },
        ],
        "services": [
            {
                "name": "Elektrik enerjisi istehlak auditi və analitikası",
                "search_tags": [
                    "elektrik auditi", "energy audit", "power consumption", "enerji analizi",
                    "elektrik qənaəti", "energy saving", "utility audit", "istehlak analizi",
                    "substansiya yoxlanışı", "electrical inspection"
                ],
                "type": "monthly",
                "description": (
                    "Metro-nun 110kV yeraltı elektrik infrastrukturu mühəndisləri "
                    "AZCON şirkətlərinin (BakuBus, ADY, ASCO) elektrik sistemlərini audit edir. "
                    "Scope: enerji ölçümü, güc faktoru analizi, israf nöqtələrinin müəyyən edilməsi, "
                    "tövsiyə hesabatı, ISO 50001 uyğunluq dəstəyi."
                ),
                "sla": "Aylıq hesabat çatdırılması; müddəti 30 gündən artıq olmamaq şərtilə"
            },
            {
                "name": "Yeraltı metro tuneli kabel kanalı infrastrukturu icarəsi",
                "search_tags": [
                    "tunel icarəsi", "tunnel lease", "cable duct", "kabel kanalı",
                    "underground cable", "metro tunel", "fiber optik yol", "duct rental",
                    "subway tunnel", "infrastructure lease"
                ],
                "type": "monthly",
                "description": (
                    "Metro tunellərindəki boş kabel kanallarının Aztelekom və ya "
                    "AzInTelecom-a fiber-optik xətt çəkmək üçün icarəyə verilməsi. "
                    "Scope: hüquqi icazə, fiziki giriş koordinasiyası, texniki monitoring, "
                    "hər km üçün fərdi razılaşma."
                ),
                "sla": "Giriş 48 saatlıq əvvəldən bildiriş ilə; aylıq texniki hesabat"
            },
            {
                "name": "Tunel tikintisi konsaltinq xidməti",
                "search_tags": [
                    "tunel tikintisi", "tunnel construction", "underground construction",
                    "metro genişlənməsi", "metro expansion", "subway consulting",
                    "tikinti məsləhəti", "engineering consulting", "civil engineering"
                ],
                "type": "project-based",
                "description": (
                    "Metro mühəndis komandası yeraltı tikinti layihələri üçün texniki məsləhət verir. "
                    "Scope: geoloji şərait analizi, struktur dizayn tövsiyəsi, "
                    "TBM (tunnel boring machine) istifadəsi üzrə məsləhət."
                ),
                "sla": "Layihə müddəti və çatdırılma qrafiki fərdi müqavilədə müəyyənləşdirilir"
            },
        ],
        "active_orders": [
            {
                "vendor": "Metrovagonmash / Global Transport Solutions (Rusiya-Azərbaycan JV)",
                "item": "81-765B/766B metro qatarı dəsti — qalan 6 qatarın hissələri",
                "expected_delivery": "2026-Q4",
                "origin_country": "Rusiya"
            },
            {
                "vendor": "Alstom (Fransa)",
                "item": "CBTC siqnalizasiya sistemi yeniləmə paketi",
                "expected_delivery": "2026-Q3",
                "origin_country": "Fransa"
            },
        ]
    },

    # =========================================================================
    # 3. BAKUBUSs
    #    Bakı şəhəri dövlət avtobus operatoru | 350,000+ gündəlik sərnişin
    # =========================================================================
    "BakuBus": {
        "surplus_inventory": [
            {
                "item_name": "Yutong ZK6126HG dizel avtobus (2019 model)",
                "search_tags": [
                    "avtobus", "bus", "city bus", "transit bus", "şəhər avtobusu",
                    "Yutong", "dizel avtobus", "diesel bus", "passenger bus",
                    "ictimai nəqliyyat", "public transport vehicle"
                ],
                "quantity_available": 12,
                "unit": "ədəd",
                "price_per_unit": round(180_000 * _USD, 2),
                "logistics_cost_per_unit": round(1_500 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Öz gücüylə hərəkət edə bilər; sürücü tələb olunur; bütün yerli nəql marşrutlarına uyğun",
                "notes": "Elektrik avtobus alınması ilə bu dizel avtobuslar dövrədən çıxmışdır; yaxşı texniki vəziyyətdədir; mileage < 180,000 km"
            },
            {
                "item_name": "Avtobus ehtiyat dizel mühərrik yağı 10W-40 (bulk)",
                "search_tags": [
                    "motor yağı", "engine oil", "dizel yağı", "diesel oil",
                    "mühərrik yağı", "lubricant", "yağlayıcı", "10W-40",
                    "bus oil", "avtobus yağı"
                ],
                "quantity_available": 15_000,
                "unit": "litr",
                "price_per_unit": round(1.10 * _USD, 2),
                "logistics_cost_per_unit": round(0.08 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Tank konteyner ilə çatdırılma; ADR Sinif 3; Bakı depodan",
                "notes": "Elektrik avtobuslara keçid ilə dizel yağ ehtiyatı artmışdır; yararlılıq müddəti 2027"
            },
            {
                "item_name": "Avtobus təkəri Bridgestone R22.5 (yeni)",
                "search_tags": [
                    "avtobus təkəri", "bus tire", "truck tire", "R22.5", "Bridgestone",
                    "təkər", "şin", "tire", "wheel", "rubber tire", "avtomobil şini"
                ],
                "quantity_available": 96,
                "unit": "ədəd",
                "price_per_unit": round(300 * _USD, 2),
                "logistics_cost_per_unit": round(20 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Palet ilə; hər paletdə 4 ədəd; standart yük vasitəsi ilə çatdırılma",
                "notes": "Yeni modelli avtobusların fərqli ölçülü şin istifadə etməsi ilə artıq qalmışdır"
            },
            {
                "item_name": "BakıKart NFC oxuyucusu köhnə model",
                "search_tags": [
                    "kart oxuyucu", "card reader", "NFC reader", "BakıKart",
                    "ticket reader", "bilet oxuyucu", "contactless reader",
                    "payment terminal", "ödəniş cihazı"
                ],
                "quantity_available": 150,
                "unit": "ədəd",
                "price_per_unit": round(310 * _USD, 2),
                "logistics_cost_per_unit": round(8 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Standart koli qabı; 3-5 iş günü çatdırılma",
                "notes": "Yeni avtobuslarda yeni oxuyucu sistemi quraşdırılıb; köhnə model fəaliyyəti davam etdirir"
            },
        ],
        "services": [
            {
                "name": "GPS izləmə və sürücü məlumat sistemi inteqrasiyası",
                "search_tags": [
                    "GPS izləmə", "GPS tracking", "fleet management", "donanma idarəetməsi",
                    "sürücü sistemi", "driver information", "route management",
                    "marşrut idarəetməsi", "vehicle tracking", "avtomobil izləmə"
                ],
                "type": "one-time",
                "description": (
                    "BakuBus-un mövcud GPS-izləmə və sürücü məlumat platformasını "
                    "Bakı Taksi Xidmətinə və ya ADY-yə inteqrasiya etmək. "
                    "Scope: API inteqrasiyası, sürücü interfeysi konfiqurasiyası, "
                    "texniki öyrədim, sınaq dövrü."
                ),
                "sla": "Quraşdırma 5 iş günü; texniki dəstək ilk 3 ay pulsuz"
            },
            {
                "name": "Avtomobil parklarına planlı texniki baxış (PMI)",
                "search_tags": [
                    "texniki baxış", "maintenance", "PMI", "planned maintenance",
                    "vehicle service", "avtobus texniki", "mühərrik baxışı",
                    "service inspection", "fleet maintenance", "repair service"
                ],
                "type": "monthly",
                "description": (
                    "BakuBus-un 3 depo mühəndis komandası Bakı Taksi Xidmətinin "
                    "avtomobil parklarına planlı texniki xidmət göstərir. "
                    "Scope: motor, ötürücü, əyləc sistemi yoxlanışı; sürücü kabin sınağı; "
                    "yazılı hesabat."
                ),
                "sla": "Avtomobil başına 4 saatdan çox olmayan xidmət; aylıq hesabat"
            },
            {
                "name": "Elektrik avtobus şarj infrastrukturu layihəsi",
                "search_tags": [
                    "EV şarj", "electric vehicle charging", "charging station",
                    "şarj stansiyası", "elektrik avtobus", "EV infrastructure",
                    "bus depot charging", "elektrik nəqliyyat", "green transport"
                ],
                "type": "project-based",
                "description": (
                    "BakuBus-un elektrik avtobus əməliyyatı təcrübəsindən istifadə edərək "
                    "digər AZCON şirkətlərinin depot sahələrində EV şarj stansiyaları dizayn "
                    "etmək və quraşdırmaq. Scope: güc hesablaması, AC/DC şarj bloklarının "
                    "seçimi, quraşdırma, komissiya."
                ),
                "sla": "Layihə başından 60 iş günü ərzində komissiya"
            },
            {
                "name": "Avtobus icarəsi (event və korporativ turlar)",
                "search_tags": [
                    "avtobus icarəsi", "bus rental", "charter bus", "korporativ tur",
                    "corporate transport", "event bus", "tədbir avtobusu",
                    "group transport", "qrup daşıma"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin korporativ tədbirləri, işçi köçürməsi, "
                    "şəhərlərarası qrup daşıma üçün sürücülü avtobus icarəsi. "
                    "Scope: 12–60 oturacaqlı seçimlər; sürücü, yanacaq, sığorta daxildir."
                ),
                "sla": "48 saatlıq əvvəldən sifariş; imtina 24 saat əvvələ qədər pulsuz"
            },
        ],
        "active_orders": [
            {
                "vendor": "BYD Auto Co. Ltd. (Çin)",
                "item": "BYD K9 elektrik transit avtobusu — 50 ədəd",
                "expected_delivery": "2026-Q2",
                "origin_country": "Çin"
            },
            {
                "vendor": "Knorr-Bremse AG (Almaniya)",
                "item": "Avtobus əyləc sistemi yeniləmə dəsti — 150 avtobus üçün",
                "expected_delivery": "2026-Q1",
                "origin_country": "Almaniya"
            },
        ]
    },

    # =========================================================================
    # 4. ADY — Azərbaycan Dəmir Yolları
    #    176 stansiya | 5,795 vaqon | BTK (Bakı-Tbilisi-Qars) | Orta Dəhliz
    # =========================================================================
    "ADY": {
        "surplus_inventory": [
            {
                "item_name": "TE10M dizel lokomotiv ehtiyat mühərriki",
                "search_tags": [
                    "lokomotiv mühərriki", "locomotive engine", "diesel engine", "TE10M",
                    "dizel mühərrik", "train engine", "railway engine", "mühərrik ehtiyatı",
                    "locomotive spare", "rail engine"
                ],
                "quantity_available": 4,
                "unit": "ədəd",
                "price_per_unit": round(85_000 * _USD, 2),
                "logistics_cost_per_unit": round(4_200 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Ağır yük nəqliyyatı; ADY-nin öz platforması mövcuddur; yerli daşıma üstünlüklüdür",
                "notes": "Yeni AC elektrik lokomotivlərə keçid ilə artıq qalmışdır; iş saatı < 40,000"
            },
            {
                "item_name": "Dəmir yolu relsi UIC60 (60 kq/m polad rels)",
                "search_tags": [
                    "rels", "rail", "railway rail", "UIC60", "polad rels", "steel rail",
                    "train track", "yol relsi", "dəmir yolu", "track component",
                    "60kg rail", "rail steel"
                ],
                "quantity_available": 8_500,
                "unit": "metr",
                "price_per_unit": round(42 * _USD, 2),
                "logistics_cost_per_unit": round(1.50 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "ADY-nin öz platforması ilə daşıma; dəmir yolu ilə çatdırılma üstünlüklüdür",
                "notes": "Ucar-Hacıqabul elektrikləşdirmə layihəsindən qalan; EN 13674-1 sertifikatlı"
            },
            {
                "item_name": "Yük vagonu podşipnik dəsti SKF 130x230x64",
                "search_tags": [
                    "podşipnik", "bearing", "wheel bearing", "vaqon podşipniki",
                    "SKF", "railway bearing", "axle bearing", "train bearing",
                    "dəmir yolu ehtiyat hissəsi", "wagon spare part"
                ],
                "quantity_available": 620,
                "unit": "dəst",
                "price_per_unit": round(185 * _USD, 2),
                "logistics_cost_per_unit": round(4 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Standart sənaye qablaşdırması; palet ilə; 3-5 gün çatdırılma",
                "notes": "Yeni vaqonlar üçün fərqli standart tətbiq edilib; OEM sertifikatlıdır"
            },
            {
                "item_name": "Dəmir yolu yataq ağacı (şpal, polimer kompozit)",
                "search_tags": [
                    "şpal", "railway sleeper", "rail tie", "yataq ağacı",
                    "concrete sleeper", "polimer şpal", "track sleeper",
                    "dəmir yolu elementi", "railway component"
                ],
                "quantity_available": 3_200,
                "unit": "ədəd",
                "price_per_unit": round(50 * _USD, 2),
                "logistics_cost_per_unit": round(5 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Düz yük vasitəsilə; palet ilə; ADY platforması üçün tam uyğun",
                "notes": "Yol bərpasından artıq qalan; standarta tam uyğun, istifadəyə hazır"
            },
            {
                "item_name": "Lokomotiv əyləc bəndi dəsti (Knorr-Bremse uyğun)",
                "search_tags": [
                    "əyləc", "brake", "brake pad", "locomotive brake", "train brake",
                    "Knorr-Bremse", "əyləc bəndi", "brake lining", "friction material",
                    "dəmir yolu əyləci"
                ],
                "quantity_available": 180,
                "unit": "dəst",
                "price_per_unit": round(1_000 * _USD, 2),
                "logistics_cost_per_unit": round(50 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Standart sənaye qablaşdırması; həm lokomotiv, həm vaqona uyğundur",
                "notes": "Dizel lokomotiv sayının azalması ilə artıq ehtiyat; BakuBus-un avtobus əyləcləri ilə uyğun deyil"
            },
        ],
        "services": [
            {
                "name": "Konteyner terminal idarəetmə konsaltinqi (TMS)",
                "search_tags": [
                    "konteyner terminal", "container terminal", "TMS", "terminal management",
                    "liman idarəetməsi", "port management", "logistics consulting",
                    "yük idarəetməsi", "cargo management", "freight terminal"
                ],
                "type": "monthly",
                "description": (
                    "ADY-nin Bakı konteyner terminalı və Xi'an nümayəndəliyinin "
                    "toplanmış əməliyyat biliyindən istifadə edərək ASCO-nun Alyat limanı "
                    "yük hərəkətlərinin optimallaşdırılması. "
                    "Scope: TMS konfiqurasiyası, heyət öyrədimi, KPI hesabatı, "
                    "marşrut optimizasiyası."
                ),
                "sla": "Aylıq KPI hesabatı; dəstək SLA 4 iş saatı ərzində cavab"
            },
            {
                "name": "Dəmir yolu xətti diaqnostikası MRM sistemi ilə",
                "search_tags": [
                    "xətt yoxlaması", "track inspection", "rail diagnostics", "MRM",
                    "yol diaqnostikası", "railway inspection", "infrastructure audit",
                    "track geometry", "dəmir yolu auditi", "rail condition check"
                ],
                "type": "project-based",
                "description": (
                    "ADY-nin MRM (Moving Reference Machine) sistemi ilə Bakı Metro, "
                    "BakuBus depo yolları da daxil olmaqla AZCON-a məxsus relsli "
                    "infrastrukturun diaqnostikası. "
                    "Scope: 40+ parametr ölçümü, çatlaq aşkarlama, deformasiya analizi, "
                    "texniki hesabat."
                ),
                "sla": "Sahə işindən 5 iş günü ərzində hesabat; 100 km minimum həcm"
            },
            {
                "name": "BTK marşrutu üzrə yük tranzit xidməti (AZCON paketi)",
                "search_tags": [
                    "BTK", "Bakı-Tbilisi-Qars", "tranzit yük", "freight transit",
                    "rail freight", "dəmir yolu yük", "cargo rail", "multimodal",
                    "Middle Corridor", "Orta Dəhliz", "container transport"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin xarici sifarişlərini BTK xətti vasitəsilə "
                    "Avropadan/Türkiyədən Bakıya daşıma. "
                    "Scope: gömrük klirens, multimodal sənəd, nəqliyyat sığortası, "
                    "real-vaxt yük izləmə."
                ),
                "sla": "Avropadan Bakıya 12-15 gün; Xi'andan Bakıya 11-13 gün"
            },
            {
                "name": "Yük daşıma xidməti (daxili marşrutlar)",
                "search_tags": [
                    "daxili yük", "domestic freight", "rail cargo", "cargo haulage",
                    "yük daşıma", "freight transport", "dəmir yolu yük daşıma",
                    "bulk cargo", "vaqon icarəsi", "wagon rental"
                ],
                "type": "one-time",
                "description": (
                    "ADY-nin 122 yük stansiyası şəbəkəsi üzərindən Azərbaycan daxilindəki "
                    "AZCON obyektləri arasında avadanlıq, material, container daşıma. "
                    "Scope: vaqon planlaşdırması, yükləmə/boşaltma koordinasiyası."
                ),
                "sla": "Sifariş konfirmasiyasından 72 saat ərzində yükləmə"
            },
        ],
        "active_orders": [
            {
                "vendor": "CRRC Ziyang Co. Ltd. (Çin)",
                "item": "AC50 dizel-elektrik mainline lokomotiv — 7 ədəd (+ 14 ədəd növbəti mərhələ)",
                "expected_delivery": "2026-Q3",
                "origin_country": "Çin"
            },
            {
                "vendor": "Stadler Rail AG (İsveçrə)",
                "item": "FLIRT 5-vaqonlu elektrik qatarı — 10 ədəd (€115M müqavilə)",
                "expected_delivery": "2026-Q2",
                "origin_country": "İsveçrə"
            },
        ]
    },

    # =========================================================================
    # 5. BAKI TAKSİ XİDMƏTİ
    #    Bakı rəsmi dövlət taksi operatoru | hava limanı transferi | şəhərdaxili
    # =========================================================================
    "Baki_Taksi_Xidmeti": {
        "surplus_inventory": [
            {
                "item_name": "Hyundai Sonata 2020 taksi avtomobili (dizel)",
                "search_tags": [
                    "avtomobil", "car", "taxi car", "Hyundai Sonata", "sedan",
                    "taksi", "taxi", "passenger car", "minik avtomobili",
                    "vehicle", "used car", "ikinci əl avtomobil"
                ],
                "quantity_available": 18,
                "unit": "ədəd",
                "price_per_unit": round(22_000 * _USD, 2),
                "logistics_cost_per_unit": round(300 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Öz gücüylə hərəkət; sürücü tələb olunur; avto-daşıma da mümkündür",
                "notes": "Elektrik taksi proqramına keçiddə əvəzlənmiş; mileage < 120,000 km; yaxşı texniki vəziyyət"
            },
            {
                "item_name": "Taksi taximetri Hale Electronic JY-20",
                "search_tags": [
                    "taximetr", "taximeter", "fare meter", "taxi meter",
                    "ödəniş sayğacı", "ücret ölçən", "digital taximeter",
                    "JY-20", "taksi avadanlığı", "taxi equipment"
                ],
                "quantity_available": 75,
                "unit": "ədəd",
                "price_per_unit": round(145 * _USD, 2),
                "logistics_cost_per_unit": round(5 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Kiçik qablaşdırma; standart kargo ilə çatdırılma",
                "notes": "Rəqəmsal ödəniş sisteminə keçidlə taximetrlər istifadədən çıxmışdır; funksional vəziyyətdədir"
            },
            {
                "item_name": "Avtomobil bort DVR kamera sistemi 4K",
                "search_tags": [
                    "kamera", "camera", "dashcam", "DVR", "dash camera",
                    "bort kamerası", "vehicle camera", "car recorder",
                    "avtomobil kamerası", "surveillance camera", "4K camera"
                ],
                "quantity_available": 40,
                "unit": "ədəd",
                "price_per_unit": round(220 * _USD, 2),
                "logistics_cost_per_unit": round(8 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Kiçik elektronika; özel qablaşdırma; 2-3 gün çatdırılma",
                "notes": "Yeni model ilə uyğunsuz olduğu üçün anbarda qalmışdır; yaxşı vəziyyətdədir"
            },
            {
                "item_name": "Avtomobil ehtiyat təkəri 215/60R16 (Michelin)",
                "search_tags": [
                    "təkər", "şin", "tire", "car tire", "Michelin",
                    "215/60R16", "passenger tire", "sedan tire",
                    "avtomobil şini", "rubber", "wheel"
                ],
                "quantity_available": 60,
                "unit": "ədəd",
                "price_per_unit": round(250 * _USD, 2),
                "logistics_cost_per_unit": round(15 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Palet ilə; hər paletdə 8 ədəd; standart kargo",
                "notes": "EV keçidindən sonra Hyundai Sonata üçün artıq ehtiyat yaranmışdır"
            },
        ],
        "services": [
            {
                "name": "VİP hava limanı transfer xidməti (AZCON korporativ paketi)",
                "search_tags": [
                    "VIP transfer", "airport transfer", "hava limanı transfer",
                    "korporativ taksi", "corporate taxi", "executive transport",
                    "premium taxi", "business transfer", "şofer xidməti"
                ],
                "type": "monthly",
                "description": (
                    "AZCON holdinq rəhbər heyəti və ezamiyyət qonaqları üçün "
                    "Heydar Əliyev Hava Limanına/limanından premium transfer xidməti. "
                    "Scope: 24/7 dispetçer, sertifikatlı sürücü, su/nəşr dəsti, "
                    "korporativ faktura, uçuş izləmə."
                ),
                "sla": "Uçuşdan 15 dəqiqə əvvəl gəliş; 10 aylıq gündəlik sifariş limitinə qədər"
            },
            {
                "name": "Şəhərdaxili kuryer daşıma (sənəd və kiçik bağlama)",
                "search_tags": [
                    "kuryer", "courier", "delivery", "şəhərdaxili çatdırılma",
                    "same day delivery", "urgent delivery", "bağlama daşıma",
                    "sənəd çatdırılma", "document delivery", "express courier"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin Bakı daxilindəki ofisləri arasında sürətli "
                    "sənəd/bağlama daşınması (Azərpoçtla rəqabətli alternativ). "
                    "Scope: GPS izləmə, elektron imza, 2 saatlıq çatdırılma zəmanəti, "
                    "korporativ faktura."
                ),
                "sla": "Sifariş qəbulundan 2 saat ərzində çatdırılma; 09:00-20:00 arası"
            },
            {
                "name": "Korporativ taksi abunə paketi (aylıq)",
                "search_tags": [
                    "korporativ abunə", "corporate subscription", "fleet taxi",
                    "monthly taxi", "employee transport", "işçi daşıma",
                    "taksi abunəsi", "corporate account", "business taxi"
                ],
                "type": "monthly",
                "description": (
                    "AZCON şirkəti işçiləri üçün əvvəldən planlaşdırılmış taksi xidməti. "
                    "Scope: aylıq limiit sistemi, çağrı prioriteti, faktura, sürücü reytinqi."
                ),
                "sla": "Sifariş qəbulundan 10 dəqiqə ərzində avtomobil; 7/24 xidmət"
            },
        ],
        "active_orders": [
            {
                "vendor": "BYD Auto Co. Ltd. (Çin)",
                "item": "BYD Han EV elektrik taksisi — 30 ədəd",
                "expected_delivery": "2026-Q1",
                "origin_country": "Çin"
            },
            {
                "vendor": "Michelin (Fransa)",
                "item": "EV donanması üçün Michelin e.Primacy təkər dəsti (120 ədəd)",
                "expected_delivery": "2026-Q1",
                "origin_country": "Fransa"
            },
        ]
    },

    # =========================================================================
    # 6. ASCO — Azərbaycan Xəzər Dəniz Gəmiçiliyi
    #    250+ gəmi | 51 nəqliyyat gəmisi | 2 tərsanə | 9,200 işçi
    # =========================================================================
    "ASCO": {
        "surplus_inventory": [
            {
                "item_name": "Gəmi dizel mühərrik yağı Shell Alexia S4 SAE 30",
                "search_tags": [
                    "gəmi yağı", "marine oil", "ship oil", "Shell Alexia",
                    "dəniz mühərrik yağı", "marine lubricant", "SAE 30",
                    "mühərrik yağı", "engine oil", "vessel oil", "ship engine oil"
                ],
                "quantity_available": 45_000,
                "unit": "litr",
                "price_per_unit": round(3.80 * _USD, 2),
                "logistics_cost_per_unit": round(0.12 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Alyat liman anbarından; tank konteyner ilə çatdırılma; ADR Sinif 3",
                "notes": "Yeni gəmilərin sintetik yağ standartına keçməsi ilə artıq qalmışdır; yararlılıq müddəti 2028"
            },
            {
                "item_name": "Dəniz lövbər zənciri studlink 42mm K3 polad",
                "search_tags": [
                    "lövbər zənciri", "anchor chain", "marine chain", "ship anchor",
                    "studlink chain", "42mm chain", "K3 steel", "dəniz lövbəri",
                    "gəmi zənciri", "mooring chain", "vessel anchor"
                ],
                "quantity_available": 280,
                "unit": "metr",
                "price_per_unit": round(145 * _USD, 2),
                "logistics_cost_per_unit": round(6 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Ağır yük; dəniz nəqliyyatı tövsiyə olunur; bağlama xüsusi çarx ilə",
                "notes": "Köhnə bərə gəmilərinin overhaulundan sonra əvəzlənmiş; DNV sertifikatlı"
            },
            {
                "item_name": "Dəniz köpük yanğınsöndürən konsentrat AFFF 3%",
                "search_tags": [
                    "yanğınsöndürən", "fire suppressant", "AFFF", "foam concentrate",
                    "marine fire", "ship fire suppression", "yanğın köpüyü",
                    "fire foam", "SOLAS", "dəniz yanğın sistemi"
                ],
                "quantity_available": 8_500,
                "unit": "litr",
                "price_per_unit": round(7.20 * _USD, 2),
                "logistics_cost_per_unit": round(0.25 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Tank konteyner; ADR Sinif 9; gəmi daşımasına uyğun",
                "notes": "SOLAS tələbi dəyişikliyi ilə müəyyən həcm artıq anbarda qalmışdır; MFPA sertifikatlı"
            },
            {
                "item_name": "Gəmi sualtı qaldırma pompası Grundfos SP77-3N",
                "search_tags": [
                    "pompa", "pump", "ship pump", "bilge pump", "marine pump",
                    "Grundfos", "sualtı pompa", "submersible pump", "gəmi pompası",
                    "vessel pump", "drainage pump"
                ],
                "quantity_available": 8,
                "unit": "ədəd",
                "price_per_unit": round(2_000 * _USD, 2),
                "logistics_cost_per_unit": round(100 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Standart industrial qablaşdırma; 5-7 gün çatdırılma",
                "notes": "Gəmi modernizasiyasından çıxarılmışdır; yaxşı texniki vəziyyətdədir"
            },
        ],
        "services": [
            {
                "name": "Xəzər dənizi yük daşıma xidməti (Bakı–Turkmənbaşı / Aktau)",
                "search_tags": [
                    "bərə", "ferry", "Caspian shipping", "Xəzər daşıma",
                    "Trans-Caspian", "cargo ferry", "sea freight", "dəniz yük",
                    "TRACECA", "Bakı-Turkmənbaşı", "Bakı-Aktau"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin Orta Asiyaya göndərəcəyi avadanlıq, "
                    "material, konteynerləri ASCO bərə gəmiləri ilə daşıma. "
                    "Scope: yükləmə, sənədləşdirmə, gömrük koordinasiyası, "
                    "sığorta, portdan porta xidmət."
                ),
                "sla": "Hər həftə müntəzəm sefer; Bakı–Turkmənbaşı ~14 saat"
            },
            {
                "name": "Offshore dəstək gəmisi icarəsi (neft-qaz platformaları üçün)",
                "search_tags": [
                    "offshore", "support vessel", "OSV", "gəmi icarəsi",
                    "vessel charter", "platform supply", "PSV", "dəniz dəstəyi",
                    "oil platform support", "Caspian offshore"
                ],
                "type": "monthly",
                "description": (
                    "ASCO-nun offshore dəstək donanmasından gəmi icarəsi: "
                    "supply vessel, kran gəmisi, yanğınsöndürən gəmi. "
                    "Scope: gəmi, kapitan, heyət, yanacaq, sığorta daxildir."
                ),
                "sla": "Sifariş qəbulundan 72 saat ərzində gəmi hazırlığı"
            },
            {
                "name": "Gəmi texniki baxışı və klassifikasiya sertifikatlaşdırması",
                "search_tags": [
                    "gəmi baxışı", "ship inspection", "vessel survey", "classification",
                    "Lloyd's", "BV", "DNV", "gəmi sertifikatı", "maritime inspection",
                    "hull inspection", "gövdə baxışı"
                ],
                "type": "project-based",
                "description": (
                    "ASCO-nun dənizçilik mühəndislərinin Bakı Gəmiqayırma Zavodunda "
                    "gəmilərin texniki inspeksiyasını həyata keçirməsi. "
                    "Scope: gövdə yoxlanışı, mexanik sınaqlar, Lloyd's/BV/DNV "
                    "standartlarına uyğunluq hesabatı."
                ),
                "sla": "Baxışdan 5 iş günü ərzində rəsmi sertifikat"
            },
        ],
        "active_orders": [
            {
                "vendor": "Wärtsilä Finland Oy (Finlandiya)",
                "item": "4 tanker üçün mühərrik yeniləmə paketi (Wärtsilä 32)",
                "expected_delivery": "2026-Q2",
                "origin_country": "Finlandiya"
            },
            {
                "vendor": "Bakı Gəmiqayırma Zavodu (Azərbaycan — yerli)",
                "item": "2 ədəd tanker + 3 ədəd dalğıc dəstəyi gəmisi inşası",
                "expected_delivery": "2027-Q1",
                "origin_country": "Azərbaycan"
            },
        ]
    },

    # =========================================================================
    # 7. AZTELEKOM
    #    Milli rabitə operatoru | 57 regional ofis | GPON şəbəkəsi | AZCON altı
    # =========================================================================
    "Aztelekom": {
        "surplus_inventory": [
            {
                "item_name": "Fiber-optik kabel single-mode G.652D 48-damar",
                "search_tags": [
                    "fiber optik", "fiber optic cable", "optical cable", "G.652D",
                    "single mode fiber", "48-core", "GPON kabel", "telekommunikasiya kabeli",
                    "fiber kabel", "FOC", "optik xətt", "optical fiber"
                ],
                "quantity_available": 85_000,
                "unit": "metr",
                "price_per_unit": round(0.65 * _USD, 2),
                "logistics_cost_per_unit": round(0.02 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Kabel çarxı ilə; 2000m/çarx; ağır yük kimi qiymətləndirilir",
                "notes": "Qarabağ layihəsinin 2025 fazasından artıq qalmışdır; ITU-T G.652D standartı"
            },
            {
                "item_name": "OLT cihazı Huawei MA5800-X7 GPON",
                "search_tags": [
                    "OLT", "optical line terminal", "GPON cihazı", "Huawei OLT",
                    "MA5800", "network equipment", "şəbəkə avadanlığı",
                    "fiber access", "broadband equipment", "telecom equipment"
                ],
                "quantity_available": 12,
                "unit": "ədəd",
                "price_per_unit": round(8_500 * _USD, 2),
                "logistics_cost_per_unit": round(180 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Xüsusi elektronika qablaşdırması; quru mühit tələb olunur; 5-7 gün çatdırılma",
                "notes": "Region quruluşunun dəyişməsi ilə planlaşdırılan yerləşdirmə ləğv edilmişdir; yeni, qutusundadır"
            },
            {
                "item_name": "Şəbəkə kommutator switch (enterprise sinif, 48-port)",
                "search_tags": [
                    "switch", "network switch", "Ethernet switch", "kommutator",
                    "48-port switch", "LAN switch", "şəbəkə avadanlığı",
                    "network device", "cisco switch", "managed switch"
                ],
                "quantity_available": 35,
                "unit": "ədəd",
                "price_per_unit": round(3_000 * _USD, 2),
                "logistics_cost_per_unit": round(150 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Elektronika qablaşdırması; rack-mount; 3-5 gün çatdırılma",
                "notes": "Ofis konsolidasiyasından artıq qalmışdır; SDN-uyğun modellər"
            },
            {
                "item_name": "IP telefon aparatı (VoIP, PoE dəstəkli)",
                "search_tags": [
                    "IP telefon", "IP phone", "VoIP", "office phone", "ofis telefonu",
                    "PoE phone", "desk phone", "SIP telefon", "korporativ telefon",
                    "telephone set"
                ],
                "quantity_available": 280,
                "unit": "ədəd",
                "price_per_unit": round(200 * _USD, 2),
                "logistics_cost_per_unit": round(10 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Kiçik qablaşdırma; standart kargo; 3 gün çatdırılma",
                "notes": "Ofis strukturunun dəyişməsi ilə artıq qalmışdır; SIP protokol dəstəkli"
            },
        ],
        "services": [
            {
                "name": "Korporativ fiber-optik xətt quraşdırma",
                "search_tags": [
                    "fiber quraşdırma", "fiber installation", "internet xətti",
                    "broadband installation", "optical line", "FTTB", "FTTO",
                    "korporativ internet", "dedicated line", "xüsusi xətt"
                ],
                "type": "one-time",
                "description": (
                    "Aztelekom mühəndis komandası AZCON şirkətlərinin hər hansı "
                    "ofisinə/deposuna birbaşa fiber-optik bağlantı qurur. "
                    "Scope: xətt çəkilməsi, splice (qaynaq), OTDR testi, "
                    "aktivasiya, 1 il zəmanət."
                ),
                "sla": "Layihədən 10 iş günü ərzində aktivasiya; 99.9% uptime SLA"
            },
            {
                "name": "Dedicated Internet Access (DIA) korporativ tarif",
                "search_tags": [
                    "DIA", "dedicated internet", "korporativ internet", "business internet",
                    "fiber internet", "SLA internet", "sabit IP", "static IP",
                    "enterprise internet", "high speed internet"
                ],
                "type": "monthly",
                "description": (
                    "AZCON şirkətlərinə simmetrik, sabit IP-li, SLA ilə güvəncli "
                    "biznes internet bağlantısı. "
                    "Scope: 99.9% uptime SLA, 24/7 NOC monitorinq, "
                    "texniki dəstək, aylıq hesabat."
                ),
                "sla": "99.9% uptime; nasazlıq halında 4 saat ərzində bərpa"
            },
            {
                "name": "Telekommunikasiya infrastrukturu texniki baxış və təmir",
                "search_tags": [
                    "şəbəkə baxışı", "network maintenance", "telecom repair",
                    "infrastructure maintenance", "NOC", "texniki dəstək",
                    "technical support", "network monitoring", "şəbəkə monitorinqi"
                ],
                "type": "monthly",
                "description": (
                    "Aztelekom-un texnik heyəti AZCON şirkətlərinin telekommunikasiya "
                    "infrastrukturuna planlı baxış və sürətli təmir xidməti göstərir. "
                    "Scope: sahə müayinəsi, konfiqurasiya yoxlaması, hesabat."
                ),
                "sla": "Planlaşdırılmış baxış: aylıq; nasazlıq: 4 saatlıq cavab"
            },
        ],
        "active_orders": [
            {
                "vendor": "Cisco Systems Inc. (ABŞ)",
                "item": "Cisco ASR 9922 core router + aksesuar dəsti",
                "expected_delivery": "2026-Q1",
                "origin_country": "ABŞ"
            },
            {
                "vendor": "Ericsson AB (İsveç)",
                "item": "5G Radio Access Network (RAN) avadanlığı — pilot şəbəkə",
                "expected_delivery": "2026-Q2",
                "origin_country": "İsveç"
            },
            {
                "vendor": "Huawei Technologies (Çin)",
                "item": "Fiber-optik transiverlər (SFP+ 10G, 1000 ədəd)",
                "expected_delivery": "2026-Q2",
                "origin_country": "Çin"
            },
        ]
    },

    # =========================================================================
    # 8. AZİNTELEKOM
    #    Dövlət rəqəmsal xidmətlər | bulud, kiber-təhlükəsizlik, e-imza, İT konsaltinq
    # =========================================================================
    "AzInTelecom": {
        "surplus_inventory": [
            {
                "item_name": "Dell PowerEdge R750 server (konfiqurasiya edilmiş)",
                "search_tags": [
                    "server", "Dell server", "PowerEdge", "rack server",
                    "enterprise server", "data center server", "servər",
                    "R750", "2U server", "fiziki server"
                ],
                "quantity_available": 8,
                "unit": "ədəd",
                "price_per_unit": round(12_500 * _USD, 2),
                "logistics_cost_per_unit": round(220 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Xüsusi server nəqliyyatı; ESD qablaşdırma; 5 gün çatdırılma",
                "notes": "Data center konsolidasiyası layihəsindən sonra anbarda qalmışdır; yeni, qutusundadır"
            },
            {
                "item_name": "Cisco UCS B200 M6 blade server modulu",
                "search_tags": [
                    "blade server", "UCS", "Cisco blade", "B200 M6", "server modulu",
                    "enterprise server", "virtualization server", "blade modul",
                    "data center hardware", "computing module"
                ],
                "quantity_available": 16,
                "unit": "ədəd",
                "price_per_unit": round(9_800 * _USD, 2),
                "logistics_cost_per_unit": round(150 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "ESD qablaşdırma; chassis tələb olunur; 5-7 gün çatdırılma",
                "notes": "Bulud miqrasiyası zamanı on-premise serverlər azaldılmışdır; yeni, qutusundadır"
            },
            {
                "item_name": "Fortinet FortiGate 600E Next-Gen Firewall",
                "search_tags": [
                    "firewall", "FortiGate", "Fortinet", "NGFW", "network security",
                    "şəbəkə təhlükəsizliyi", "security appliance", "IPS", "UTM",
                    "cyber security device", "güvənlik cihazı"
                ],
                "quantity_available": 6,
                "unit": "ədəd",
                "price_per_unit": round(14_200 * _USD, 2),
                "logistics_cost_per_unit": round(85 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Elektronika qablaşdırması; lisenziya transferi tələb olunur; 3-5 gün",
                "notes": "Yeni nesil platformaya keçidlə artıq anbarda qalmışdır; lisenziya müzakirəsi mümkündür"
            },
            {
                "item_name": "Server rack dolabı 42U tam komplekt",
                "search_tags": [
                    "rack", "server rack", "19-inch rack", "data center rack",
                    "rack kabineti", "42U rack", "şkaf", "server dolabı",
                    "network cabinet", "equipment rack"
                ],
                "quantity_available": 14,
                "unit": "ədəd",
                "price_per_unit": round(2_000 * _USD, 2),
                "logistics_cost_per_unit": round(100 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Ağır yük; söküb yığmaq mümkündür; 3-5 gün çatdırılma",
                "notes": "Data center yenidənqurulmasından artıq qalmışdır; PDU daxildir"
            },
            {
                "item_name": "GPU kartı köhnə nəsil (NVIDIA RTX 3090, 24GB)",
                "search_tags": [
                    "GPU", "graphics card", "RTX 3090", "NVIDIA GPU", "AI GPU",
                    "machine learning GPU", "qrafik kart", "hesablama GPU",
                    "video card", "compute card", "ML hardware"
                ],
                "quantity_available": 20,
                "unit": "ədəd",
                "price_per_unit": round(500 * _USD, 2),
                "logistics_cost_per_unit": round(50 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "ESD qablaşdırma; kiçik elektronika; 2-3 gün çatdırılma",
                "notes": "H100 modernizasiyası ilə köhnəlmiş; NAIC və ya AzInTelecom test mühiti üçün uyğundur"
            },
        ],
        "services": [
            {
                "name": "ASAN İmza elektron imza inteqrasiyası",
                "search_tags": [
                    "elektron imza", "e-imza", "digital signature", "ASAN imza",
                    "e-signature", "PKI", "rəqəmsal imza", "electronic signature",
                    "e-hökumət", "e-government integration"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin daxili sənəd dövriyyəsi sistemlərinə "
                    "hüquqi qüvvəli elektron imza funksionalının inteqrasiyası. "
                    "Scope: API inteqrasiyası, istifadəçi öyrədimi, sertifikat idarəetməsi, "
                    "texniki sənədləşdirmə."
                ),
                "sla": "Layihədən 15 iş günü ərzində canlı keçid"
            },
            {
                "name": "Kiber-təhlükəsizlik auditi ISO 27001 bazalı",
                "search_tags": [
                    "kibertəhlükəsizlik", "cybersecurity", "security audit", "pentest",
                    "penetration test", "ISO 27001", "vulnerability scan",
                    "təhlükəsizlik yoxlaması", "information security", "IT audit"
                ],
                "type": "one-time",
                "description": (
                    "AzInTelecom-un kiber-təhlükəsizlik mütəxəssislərinin "
                    "AZCON şirkətlərinin İT infrastrukturunu skanlaması. "
                    "Scope: zəiflik skanı, penetrasyon testi, sosial mühəndislik testi, "
                    "icraiyyə hesabatı, prioritetli tövsiyə planı."
                ),
                "sla": "Sahə işindən 10 iş günü ərzində tam hesabat"
            },
            {
                "name": "Dövlət Bulud (G-Cloud) miqrasiya dəstəyi",
                "search_tags": [
                    "bulud miqrasiyası", "cloud migration", "G-Cloud", "government cloud",
                    "IaaS", "SaaS migration", "cloud computing", "buludlaşdırma",
                    "data migration", "infrastructure migration"
                ],
                "type": "project-based",
                "description": (
                    "AzInTelecom-un mövcud hökumət bulud infrastrukturuna AZCON "
                    "şirkətlərinin iş yüklərinin köçürülməsi. "
                    "Scope: arxitektura analizi, miqrasiya planı, test, canlı keçid, "
                    "6 aylıq post-miqrasiya dəstəyi."
                ),
                "sla": "Layihə tamamlanmasından 30 gün ərzində tam dəstək"
            },
            {
                "name": "Bulud hesablama resursları (IaaS/VPS icarəsi)",
                "search_tags": [
                    "VPS", "virtual machine", "cloud hosting", "IaaS", "VM icarəsi",
                    "computing resources", "server icarəsi", "hosting",
                    "virtual server", "buludda hosting"
                ],
                "type": "monthly",
                "description": (
                    "AZCON şirkətlərinin tətbiqləri üçün AzInTelecom-un dövlət data "
                    "mərkəzindəki virtual maşın və saxlama resursları icarəsi. "
                    "Scope: vCPU, RAM, SSD, backup, monitorinq daxildir."
                ),
                "sla": "99.95% uptime SLA; texniki dəstək 7/24"
            },
        ],
        "active_orders": [
            {
                "vendor": "Hewlett Packard Enterprise (ABŞ)",
                "item": "HPE GreenLake data center genişlənmə dəsti",
                "expected_delivery": "2026-Q1",
                "origin_country": "ABŞ"
            },
            {
                "vendor": "Thales Group (Fransa)",
                "item": "HSM (Hardware Security Module) — PKI infrastrukturu üçün",
                "expected_delivery": "2026-Q2",
                "origin_country": "Fransa"
            },
            {
                "vendor": "Lenovo Group (Çin)",
                "item": "ThinkSystem SR650 V3 server dəsti — AI klaster genişlənməsi",
                "expected_delivery": "2026-Q1",
                "origin_country": "Çin"
            },
        ]
    },

    # =========================================================================
    # 8. AZƏRPOÇT
    #    Milli poçt xidməti | UPU üzvü | 1,200+ şöbə şəbəkəsi
    # =========================================================================
    "Azarpoct": {
        "surplus_inventory": [
            {
                "item_name": "Poçt çeşidləmə sistemi konveyer modulu",
                "search_tags": [
                    "konveyer", "conveyor", "sorting system", "çeşidləmə",
                    "mail sorting", "parcel sorting", "postal equipment",
                    "poçt avadanlığı", "logistics equipment", "sorting line"
                ],
                "quantity_available": 24,
                "unit": "modul",
                "price_per_unit": round(1_850 * _USD, 2),
                "logistics_cost_per_unit": round(65 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Ağır avadanlıq; forklift tələb olunur; sökülüb yığılır; 7-10 gün",
                "notes": "Avtomatlaşdırılmış çeşidləmə sistemi ilə köhnə xətt istifadədən çıxmışdır"
            },
            {
                "item_name": "Poçt çantası su keçirməz 50 litr",
                "search_tags": [
                    "poçt çantası", "mail bag", "postal bag", "delivery bag",
                    "kuryer çantası", "waterproof bag", "su keçirməz çanta",
                    "50L bag", "messenger bag", "postman bag"
                ],
                "quantity_available": 1_800,
                "unit": "ədəd",
                "price_per_unit": round(22 * _USD, 2),
                "logistics_cost_per_unit": round(0.80 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Yüngül; standart kargo; palet ilə; 2-3 gün",
                "notes": "Yeni loqolu çanta seriyasına keçid zamanı artıq ehtiyat yaranmışdır"
            },
            {
                "item_name": "Barkod skaneri (Zebra DS9308, 1D/2D)",
                "search_tags": [
                    "barkod skaneri", "barcode scanner", "QR kod oxuyucu",
                    "Zebra scanner", "DS9308", "handheld scanner",
                    "inventory scanner", "postal scanner", "POS scanner"
                ],
                "quantity_available": 85,
                "unit": "ədəd",
                "price_per_unit": round(380 * _USD, 2),
                "logistics_cost_per_unit": round(12 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Elektronika qablaşdırması; standart kargo; 3-5 gün",
                "notes": "Yeni NFC/RFID inteqrasiyalı modellər ilə əvəzlənmişdir; funksional vəziyyətdədir"
            },
            {
                "item_name": "Poçt stansiyası POS ödəniş terminalı (köhnə model)",
                "search_tags": [
                    "POS terminal", "payment terminal", "ödəniş cihazı", "kassa",
                    "card payment", "kart oxuyucu", "verisign terminal",
                    "cash register", "checkout terminal", "banking terminal"
                ],
                "quantity_available": 35,
                "unit": "ədəd",
                "price_per_unit": round(680 * _USD, 2),
                "logistics_cost_per_unit": round(25 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Elektronika qablaşdırması; sertifikat köçürmə lazımdır",
                "notes": "Yeni rəqəmsal ödəniş inteqrasiyası ilə anbarda qalmışdır; PCI-DSS uyğunluğu yoxlanılmalıdır"
            },
        ],
        "services": [
            {
                "name": "Son mil çatdırılma şəbəkəsi (AZCON daxili logistika)",
                "search_tags": [
                    "son mil", "last mile", "delivery network", "poçt çatdırılma",
                    "şöbə şəbəkəsi", "logistics network", "parcel delivery",
                    "bağlama çatdırılma", "domestic delivery", "kargo xidməti"
                ],
                "type": "one-time",
                "description": (
                    "Azərpoçt-un 1,200+ şöbə şəbəkəsindən istifadə edərək AZCON "
                    "şirkətlərinin sənəd, kiçik bağlama, korporativ göndərişlərinin "
                    "ölkənin bütün bölgələrinə çatdırılması. "
                    "Scope: sürətli, adi, soyuq saxlanılan seçimlər; izləmə kodu."
                ),
                "sla": "Bakı daxili: 24 saat; rayonlara: 2-3 iş günü"
            },
            {
                "name": "Korporativ poçt qutusu xidməti (P.O. Box)",
                "search_tags": [
                    "P.O. Box", "poçt qutusu", "mail box", "korporativ ünvan",
                    "corporate address", "mail forwarding", "poçt ünvanı",
                    "registered address", "business address"
                ],
                "type": "monthly",
                "description": (
                    "AZCON şirkətlərinin Azərpoçt-un mərkəzi Bakı şöbəsindəki "
                    "ayrılmış poçt qutusu: adres xidməti, rəqəmsal skan, elektron bildiriş. "
                    "Scope: bütün daxil olan poçtun skanlanaraq e-mail ilə göndərilməsi."
                ),
                "sla": "Gün ərzində gələn poçt: 24 saat ərzində skan"
            },
            {
                "name": "Beynəlxalq poçt daşıma xidməti (UPU şəbəkəsi)",
                "search_tags": [
                    "beynəlxalq poçt", "international mail", "UPU", "EMS",
                    "express mail", "international parcel", "global delivery",
                    "xarici ölkəyə göndəriş", "cross-border delivery"
                ],
                "type": "one-time",
                "description": (
                    "AZCON şirkətlərinin xarici tərəflərinə UPU şəbəkəsi üzərindən "
                    "sənəd, nümunə, kiçik bağlama göndərmə. "
                    "Scope: gömrük bəyannaməsi, izləmə, sığorta seçimi."
                ),
                "sla": "EMS: 3-7 iş günü beynəlxalq çatdırılma"
            },
        ],
        "active_orders": [
            {
                "vendor": "Neopost / Quadient (Fransa)",
                "item": "Avtomatik poçt işləmə sistemi (AMS) — Bakı MPS üçün",
                "expected_delivery": "2026-Q2",
                "origin_country": "Fransa"
            },
            {
                "vendor": "Zebra Technologies (ABŞ)",
                "item": "Barkod skaneri və etiket printeri dəsti — 600 ədəd şöbə üçün",
                "expected_delivery": "2026-Q1",
                "origin_country": "ABŞ"
            },
            {
                "vendor": "Renault Trucks (Fransa)",
                "item": "Yüngül çatdırılma yük maşını (Renault Master) — 25 ədəd",
                "expected_delivery": "2026-Q2",
                "origin_country": "Fransa"
            },
        ]
    },

    # =========================================================================
    # 9. AZƏRKOSMOS
    #    Azərbaycan Kosmik Agentliyi | Azerspace-1/2 | Azersky | R&D
    # =========================================================================
    "Azarkosmos": {
        "surplus_inventory": [
            {
                "item_name": "Azerspace-2 Ku-band transponder kapasitəsi (icarəyə açıq)",
                "search_tags": [
                    "transponder", "satellite capacity", "Ku-band", "peyk kapasitəsi",
                    "bandwidth lease", "satellite bandwidth", "transponder icarəsi",
                    "VSAT capacity", "broadcast capacity", "satellite lease"
                ],
                "quantity_available": 4,
                "unit": "transponder (36 MHz)",
                "price_per_unit": round(70_000 * _USD, 2),
                "logistics_cost_per_unit": 0.0,
                "reliability_score": 5,
                "logistics_info": "Rəqəmsal xidmət — fiziki çatdırılma tələb olunmur; texniki aktivasiya 48 saat",
                "notes": "Azerspace-2-nin doldurulmamış kommersiya kapasitəsi; həm TV broadcast, həm data üçün uyğundur"
            },
            {
                "item_name": "VSAT peyk antena dəsti 1.2m Ku-band (quraşdırılmamış)",
                "search_tags": [
                    "peyk antena", "satellite dish", "VSAT", "antenna", "dish",
                    "Ku-band antenna", "1.2m dish", "satellite antenna",
                    "ground station", "peyk stansiyası"
                ],
                "quantity_available": 18,
                "unit": "ədəd",
                "price_per_unit": round(2_800 * _USD, 2),
                "logistics_cost_per_unit": round(95 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Xüsusi qablaşdırma; fragil; 5-7 gün çatdırılma",
                "notes": "Pilot layihə ləğv edildiyi üçün anbarda qalmışdır; Azerspace-1/2 ilə tam uyğundur"
            },
            {
                "item_name": "Ground station RF gücləndiricisi Comtech EF Data 400W",
                "search_tags": [
                    "RF amplifier", "gücləndrici", "ground station equipment",
                    "Comtech", "HPA", "high power amplifier", "satellite uplink",
                    "uplink amplifier", "RF equipment", "yerüstü stansiya avadanlığı"
                ],
                "quantity_available": 5,
                "unit": "ədəd",
                "price_per_unit": round(9_200 * _USD, 2),
                "logistics_cost_per_unit": round(200 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Ağır elektronika; özel qablaşdırma; 7-10 gün çatdırılma",
                "notes": "Baku Teleport genişlənməsindən sonra artıq qalan avadanlıq; Teleradio üçün uyğun ola bilər"
            },
        ],
        "services": [
            {
                "name": "Peyk üzərindən genişzolaqlı internet (AZCON uzaq obyektlər)",
                "search_tags": [
                    "peyk internet", "satellite internet", "VSAT internet", "remote connectivity",
                    "uzaq ərazilər", "offshore internet", "satellite broadband",
                    "Azerspace", "peyk bağlantı", "remote internet"
                ],
                "type": "monthly",
                "description": (
                    "Azerspace-1/2 vasitəsilə Aztelekom fiber şəbəkəsinin çatmadığı "
                    "AZCON obyektlərinə (ASCO offshore platformalar, ADY uzaq stansiyalar) "
                    "peyk internet bağlantısı. "
                    "Scope: VSAT quraşdırma, 99.5% uptime SLA, 24/7 NOC, aylıq hesabat."
                ),
                "sla": "99.5% uptime; nasazlıq halında 8 saat ərzində bərpa"
            },
            {
                "name": "Azersky peyki ilə yer müşahidəsi xidməti",
                "search_tags": [
                    "yer müşahidəsi", "earth observation", "satellite imagery",
                    "remote sensing", "peyk şəkli", "aerial view",
                    "geospatial data", "infrastructure monitoring", "Azersky"
                ],
                "type": "project-based",
                "description": (
                    "Yüksək çözünürlüklü kosmik şəkillərin ADY dəmir yolu xətlərinin, "
                    "ASCO liman infrastrukturunun, BakuBus marşrutlarının monitorinqi üçün "
                    "istifadəsi. "
                    "Scope: şəkil çəkilməsi, coğrafi analiz, dəyişiklik aşkarlama hesabatı."
                ),
                "sla": "Şəkil tələbindən 48 saat ərzində çatdırılma"
            },
            {
                "name": "Transponder kapasitəsi icarəsi (TV yayımı / data)",
                "search_tags": [
                    "transponder icarəsi", "satellite lease", "bandwidth rental",
                    "TV broadcast", "satellite TV", "peyk yayımı",
                    "data uplink", "Ku-band lease", "C-band capacity"
                ],
                "type": "monthly",
                "description": (
                    "Azerspace-1 (C-band/Ku-band) və Azerspace-2 (Ku-band) peyklərindəki "
                    "boş transponder kapasitəsinin Teleradio, AzInTelecom və ya "
                    "digər AZCON şirkətlərinə icarəsi. "
                    "Scope: NOC monitorinqi, texniki aktivasiya, SLA."
                ),
                "sla": "Aktivasiya: 48 saat; 99.9% peyk uptime zəmanəti"
            },
            {
                "name": "AI əsaslı peyk şəkil analizi (NAIC ilə birgə xidmət)",
                "search_tags": [
                    "AI analiz", "satellite AI", "image analysis", "machine learning",
                    "smart monitoring", "infrastructure AI", "peyk AI",
                    "change detection", "dəyişiklik aşkarlama", "computer vision"
                ],
                "type": "project-based",
                "description": (
                    "Azərkosmos-NAIC birgə xidmət: Azersky şəkilləri NAIC AI "
                    "modellərindən keçirilərək infrastruktur zədəsi, su daşqını, "
                    "yol deformasiyası kimi hadisələr avtomatik müəyyən edilir. "
                    "Scope: model konfiqurasiyası, real-vaxt bildiriş API, hesabat."
                ),
                "sla": "Xidmət razılaşmasına uyğun; tipik 24-72 saat analiz dövrü"
            },
        ],
        "active_orders": [
            {
                "vendor": "Airbus Defence & Space (Fransa)",
                "item": "Azersky-2 yer müşahidəsi peyki texniki sənəd paketi",
                "expected_delivery": "2026-Q4",
                "origin_country": "Fransa"
            },
            {
                "vendor": "SpaceX (ABŞ)",
                "item": "Azerspace-3 peyk buraxılış müqaviləsi (Falcon 9)",
                "expected_delivery": "2027-Q1",
                "origin_country": "ABŞ"
            },
        ]
    },

    # =========================================================================
    # 10. TELERADIO (Radioteleviziyanın Yayımı və Peyk Rabitəsi MMC)
    #     DVB-T/T2 yayımı | FM/DAB+ radio | 310m Bakı TV qülləsi | IPTV
    # =========================================================================
    "Teleradio": {
        "surplus_inventory": [
            {
                "item_name": "Harris Maxiva UAX 10kW DVB-T analoq ötürücü (köhnə)",
                "search_tags": [
                    "ötürücü", "transmitter", "TV transmitter", "broadcast transmitter",
                    "Harris", "DVB-T", "analog transmitter", "yayım avadanlığı",
                    "televiziya ötürücüsü", "broadcasting equipment"
                ],
                "quantity_available": 7,
                "unit": "ədəd",
                "price_per_unit": round(15_000 * _USD, 2),
                "logistics_cost_per_unit": round(800 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Ağır avadanlıq; xüsusi elektrik tələb olunur; 7-14 gün çatdırılma",
                "notes": "2016-cı ildə rəqəmsal yayıma keçiddə istifadədən çıxmışdır; FM ötürücü olaraq dəyişdirmə mümkündür"
            },
            {
                "item_name": "FM broadcast ötürücüsü 5kW (köhnə model)",
                "search_tags": [
                    "FM ötürücü", "FM transmitter", "radio transmitter", "5kW transmitter",
                    "broadcast FM", "radio equipment", "FM yayım", "radio broadcasting",
                    "frequency modulation", "radio station equipment"
                ],
                "quantity_available": 4,
                "unit": "ədəd",
                "price_per_unit": round(5_000 * _USD, 2),
                "logistics_cost_per_unit": round(300 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Ağır avadanlıq; xüsusi qablaşdırma; 7-10 gün",
                "notes": "DAB+ keçidindən sonra artıq qalmışdır; Qarabağ bölgəsi üçün əvəzedici olaraq uyğundur"
            },
            {
                "item_name": "RF heliax kabel Andrew LDF5-50A (½ inch)",
                "search_tags": [
                    "RF kabel", "RF cable", "heliax", "coaxial cable", "antenna cable",
                    "LDF5", "Andrew cable", "koaksial kabel", "transmission line",
                    "broadcast cable", "yayım kabeli"
                ],
                "quantity_available": 4_200,
                "unit": "metr",
                "price_per_unit": round(18 * _USD, 2),
                "logistics_cost_per_unit": round(0.60 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Kabel çarxı; ağır; xüsusi kargo tələb olunur",
                "notes": "Qülləyə yenidən kabel çəkilməsindən sonra artıq qalmışdır; geniş tətbiq sahəsi var"
            },
            {
                "item_name": "SDH optik multipleksor Ericsson Mini-Link STM-1",
                "search_tags": [
                    "SDH", "multiplexer", "Ericsson Mini-Link", "optical transport",
                    "STM-1", "telecom equipment", "transmission equipment",
                    "şəbəkə avadanlığı", "microwave backhaul", "network node"
                ],
                "quantity_available": 9,
                "unit": "ədəd",
                "price_per_unit": round(4_500 * _USD, 2),
                "logistics_cost_per_unit": round(90 * _USD, 2),
                "reliability_score": 3,
                "logistics_info": "Elektronika qablaşdırması; 3-5 gün çatdırılma",
                "notes": "IP/MPLS şəbəkəsinə keçid zamanı köhnə SDH avadanlığı əvəzlənmişdir"
            },
        ],
        "services": [
            {
                "name": "Yer-peyk uplink xidməti (Azerspace-1 / Hot Bird)",
                "search_tags": [
                    "uplink", "satellite uplink", "TV uplink", "peyk uplink",
                    "broadcast uplink", "signal transmission", "TV broadcast",
                    "yayım xidməti", "signal relay", "media distribution"
                ],
                "type": "monthly",
                "description": (
                    "Teleradio-nun Bakı TV Qüllə kompleksindəki rəqəmsal uplink stansiyasından "
                    "AZCON şirkətlərinin korporativ media/məzmununun peykə ötürülməsi. "
                    "Scope: siqnal gücləndirici, modulyasiya, peyk koordinasiyası, "
                    "24/7 NOC monitorinqi."
                ),
                "sla": "99.9% uptime; nasazlıqda 2 saat ərzində bərpa"
            },
            {
                "name": "Yayım qülləsi icarəsi (radio/TV antena yerləşdirilməsi)",
                "search_tags": [
                    "qüllə icarəsi", "tower lease", "antenna placement", "mast rental",
                    "broadcast tower", "radio tower", "antenna colocation",
                    "cell tower", "telecom tower", "qüllə"
                ],
                "type": "monthly",
                "description": (
                    "310m Bakı TV Qülləsi və regional istasyonlardakı yerlərin "
                    "Aztelekom, NAIC, digər AZCON şirkətlərinə antenna/avadanlıq "
                    "yerləşdirmək üçün icarəsi. "
                    "Scope: fiziki yer, elektrik qidaması, giriş nəzarəti."
                ),
                "sla": "Aylıq müqavilə; 48 saatlıq xəbərdarlıqla giriş"
            },
            {
                "name": "FM/DAB+ radio yayımı (AZCON korporativ elan paketi)",
                "search_tags": [
                    "radio elan", "radio advertising", "FM reklam", "DAB+ yayım",
                    "radio broadcast", "korporativ elan", "public announcement",
                    "radio məlumat", "FM xidmət", "radio communication"
                ],
                "type": "monthly",
                "description": (
                    "Azərbaycan Radio şəbəkəsi üzərindən AZCON şirkətlərinin xidmət "
                    "elanları, tender bildirişlərinin yayımı. "
                    "Scope: 99% ərazi əhatəsi, tezlik planlaşdırması, yayım sertifikatı."
                ),
                "sla": "Sifariş təsdiqlənməsindən 48 saat ərzində efirə çıxma"
            },
        ],
        "active_orders": [
            {
                "vendor": "Rohde & Schwarz GmbH (Almaniya)",
                "item": "THR9 DVB-T2 ötürücü sistemi — Qarabağ şəbəkəsi üçün 10 ədəd",
                "expected_delivery": "2026-Q2",
                "origin_country": "Almaniya"
            },
            {
                "vendor": "Eutelsat Communications (Fransa)",
                "item": "Peyk yayım kapasitəsi icarəsi (Hot Bird uydu pozisyonu)",
                "expected_delivery": "2026-Q1",
                "origin_country": "Fransa"
            },
        ]
    },

    # =========================================================================
    # 11. NAIC — Milli Süni İntellekt Mərkəzi
    #     AZCON AI mərkəzi | AI Academy | Datarace.ai | E-Qanun.ai | R&D
    # =========================================================================
    "NAIC": {
        "surplus_inventory": [
            {
                "item_name": "NVIDIA A100 80GB GPU server nodu (4x GPU konfiqurasiya)",
                "search_tags": [
                    "GPU server", "AI server", "NVIDIA A100", "machine learning server",
                    "deep learning hardware", "AI hardware", "GPU computing",
                    "A100", "HPC", "high performance computing", "AI cluster node"
                ],
                "quantity_available": 3,
                "unit": "server nodu",
                "price_per_unit": round(145_000 * _USD, 2),
                "logistics_cost_per_unit": round(500 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Xüsusi server nəqliyyatı; ESD; iqlim nəzarəti; 5-7 gün çatdırılma",
                "notes": "H100 modernizasiyası ilə A100 nodu ehtiyat fonduna keçmişdir; performance hələ yüksəkdir"
            },
            {
                "item_name": "AI iş stansiyası NVIDIA RTX 4090 128GB RAM",
                "search_tags": [
                    "AI workstation", "iş stansiyası", "RTX 4090", "workstation",
                    "GPU workstation", "ML workstation", "desktop AI", "developer machine",
                    "high-end PC", "AI development PC"
                ],
                "quantity_available": 8,
                "unit": "ədəd",
                "price_per_unit": round(9_500 * _USD, 2),
                "logistics_cost_per_unit": round(80 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "ESD qablaşdırma; standart kargo; 3-5 gün",
                "notes": "AI Academy pilot buraxılışından sonra əlavə satınalmada artıqlıq yaranmışdır; yeni, qutusundadır"
            },
            {
                "item_name": "3D LiDAR skaneri (Velodyne VLP-32C)",
                "search_tags": [
                    "LiDAR", "3D scanner", "point cloud", "Velodyne", "VLP-32C",
                    "depth sensor", "3D lidar", "autonomous sensor",
                    "robotic sensor", "spatial scanning", "3d skan"
                ],
                "quantity_available": 6,
                "unit": "ədəd",
                "price_per_unit": round(300 * _USD, 2),
                "logistics_cost_per_unit": round(50 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Həssas optik avadanlıq; xüsusi qablaşdırma; 3-5 gün",
                "notes": "Pilot robot layihəsindən artıq qalan; NAIC-in Azərkosmos ilə birgə layihəsinə uyğundur"
            },
        ],
        "services": [
            {
                "name": "AI server infrastruktur auditi",
                "search_tags": [
                    "AI audit", "server audit", "GPU audit", "AI infrastructure",
                    "performance audit", "ML audit", "hardware audit",
                    "AI optimallaşdırma", "server optimization", "AI assessment"
                ],
                "type": "one-time",
                "description": (
                    "NAIC mühəndislərinin AzInTelecom, Aztelekom, digər AZCON şirkətlərinin "
                    "AI/ML server infrastrukturunu yoxlaması. "
                    "Scope: GPU istehlak analizi, model effektivliyi, enerji optimallaşdırması, "
                    "hesabat + 3 aylıq tövsiyə planı."
                ),
                "sla": "Sahə işindən 7 iş günü ərzində tam hesabat"
            },
            {
                "name": "Xüsusi AI tətbiqi inkişaf etdirilməsi (AZCON layihələri)",
                "search_tags": [
                    "AI inkişaf", "AI development", "ML model", "custom AI",
                    "machine learning project", "AI solution", "süni intellekt tətbiqi",
                    "data science", "predictive analytics", "AI consulting"
                ],
                "type": "project-based",
                "description": (
                    "NAIC-in AI mühəndis komandası AZCON şirkətlərinin spesifik "
                    "biznes problemlərini həll etmək üçün xüsusi ML modeli inkişaf etdirir. "
                    "Scope: tələb analizi, model dizaynı, tənzimləmə, yerləşdirmə, sənədləşdirmə. "
                    "Nümunə: ASCO üçün predictive maintenance, ADY üçün trafik proqnozu."
                ),
                "sla": "Sprint əsaslı çatdırılma; hər 2 həftədə demo; müqavilə ilə müddət"
            },
            {
                "name": "AI Academy korporativ öyrədim proqramı",
                "search_tags": [
                    "AI öyrədim", "AI training", "machine learning course", "AI Academy",
                    "korporativ öyrədim", "corporate training", "data science course",
                    "Python öyrədim", "ML sertifikat", "AI certification"
                ],
                "type": "monthly",
                "description": (
                    "AZCON şirkətlərinin texniki heyəti üçün NAIC-in AI Academy "
                    "platformasında fərdiləşdirilmiş kurs: Python, ML, data analizi, NLP. "
                    "Scope: onlayn modul + praktik layihə + sertifikat + mentorluq."
                ),
                "sla": "Aylıq proqres hesabatı; kurs sonunda sertifikat 48 saatda"
            },
            {
                "name": "Data analitika tədqiqat xidməti",
                "search_tags": [
                    "data analitika", "data analytics", "big data", "business intelligence",
                    "BI", "data research", "analytics consulting", "məlumat analizi",
                    "statistical analysis", "market analysis"
                ],
                "type": "project-based",
                "description": (
                    "NAIC tədqiqat komandası AZCON şirkətlərinin biznes məlumatlarını "
                    "analiz edərək qərar dəstəyi üçün hesabat hazırlayır. "
                    "Scope: məlumat təmizlənməsi, vizuallaşdırma, statistik analiz, icraiyyə hesabatı."
                ),
                "sla": "Layihəyə görə; tipik 2-4 həftə"
            },
        ],
        "active_orders": [
            {
                "vendor": "NVIDIA Corporation (ABŞ)",
                "item": "NVIDIA DGX H100 — 16x H100 SXM5 80GB GPU klaster",
                "expected_delivery": "2026-Q1",
                "origin_country": "ABŞ"
            },
            {
                "vendor": "IBM Corporation (ABŞ)",
                "item": "IBM Power10 enterprise server dəsti",
                "expected_delivery": "2026-Q1",
                "origin_country": "ABŞ"
            },
        ]
    },

    # =========================================================================
    # 12. BAKI GƏMİQAYIRMA ZAVODU
    #     168x50m üzən dok | 25,000 ton/il | 80-100 gəmi təmiri/il | 1,500 işçi
    # =========================================================================
    "Baki_Gemiqayrma_Zavodu": {
        "surplus_inventory": [
            {
                "item_name": "Gəmiqayırma polad lövhəsi DH36 20mm",
                "search_tags": [
                    "polad lövhə", "steel plate", "DH36", "marine steel", "ship steel",
                    "shipbuilding steel", "hull steel", "gəmi polad", "structural steel",
                    "offshore steel", "lövhə"
                ],
                "quantity_available": 380,
                "unit": "ton",
                "price_per_unit": round(920 * _USD, 2),
                "logistics_cost_per_unit": round(28 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Ağır yük; düz yük vasitəsi; liman üzərindən çatdırılma mümkündür",
                "notes": "Tanker 'Zəngilan' layihəsindən sonra artıq anbar ehtiyatı; ABS/DNV sertifikatlı"
            },
            {
                "item_name": "Qaynaq elektrodu (E7018, 4mm, karbon polad üçün)",
                "search_tags": [
                    "qaynaq", "welding", "electrode", "welding rod", "qaynaq elektrodu",
                    "E7018", "MMA welding", "stick electrode", "metal joining",
                    "welding consumable", "qaynaq materialı"
                ],
                "quantity_available": 8_500,
                "unit": "kq",
                "price_per_unit": round(2.80 * _USD, 2),
                "logistics_cost_per_unit": round(0.15 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Quru mühit tələb olunur; palet ilə; 3-5 gün",
                "notes": "Layihənin tamamlanmasından artıq qalan; AWS E7018 sertifikatlı"
            },
            {
                "item_name": "Gəmi elektrik kabeli PRXSP-HF 4x16mm² dəniz standartı",
                "search_tags": [
                    "gəmi kabeli", "marine cable", "ship cable", "electrical cable",
                    "PRXSP-HF", "marine electrical", "offshore cable", "vessel cable",
                    "halogen-free cable", "fire resistant cable"
                ],
                "quantity_available": 6_800,
                "unit": "metr",
                "price_per_unit": round(12.50 * _USD, 2),
                "logistics_cost_per_unit": round(0.40 * _USD, 2),
                "reliability_score": 5,
                "logistics_info": "Kabel çarxı; IEC 60092 standartı; 3-5 gün",
                "notes": "SCV layihəsindən artıq qalan; SOLAS, MARPOL uyğundur"
            },
            {
                "item_name": "Hidravlik qaldırıcı silindr Parker 250 ton",
                "search_tags": [
                    "hidravlik silindr", "hydraulic cylinder", "lifting cylinder",
                    "Parker", "heavy lift", "qaldırıcı", "hydraulic jack",
                    "crane hydraulic", "marine hydraulic", "offshore hydraulic"
                ],
                "quantity_available": 6,
                "unit": "ədəd",
                "price_per_unit": round(18_500 * _USD, 2),
                "logistics_cost_per_unit": round(800 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Ağır avadanlıq; özel nəqliyyat; liman üzərindən 7-10 gün",
                "notes": "Üzən dok modernizasiyasından çıxarılmış; sərfəli texniki vəziyyət; Parker sertifikatlı"
            },
            {
                "item_name": "Kran komponenti qaldırma dəsti (Liebherr uyğun)",
                "search_tags": [
                    "kran", "crane", "lifting equipment", "crane component",
                    "Liebherr", "marine crane", "offshore crane", "hoisting",
                    "qaldırma avadanlığı", "crane spare"
                ],
                "quantity_available": 4,
                "unit": "dəst",
                "price_per_unit": round(10_000 * _USD, 2),
                "logistics_cost_per_unit": round(500 * _USD, 2),
                "reliability_score": 4,
                "logistics_info": "Ağır avadanlıq; xüsusi nəqliyyat; 7-14 gün çatdırılma",
                "notes": "Offshore kran gəmiləri yenilənməsindən çıxarılmışdır; texniki sertifikatlar mövcuddur"
            },
        ],
        "services": [
            {
                "name": "Üzən dok icarəsi (gəmi gövdəsi baxışı və boyama)",
                "search_tags": [
                    "üzən dok", "floating dock", "dry dock", "drydock",
                    "gəmi təmiri", "ship repair", "vessel drydock", "hull inspection",
                    "gövdə boyama", "antifouling", "blasting and painting"
                ],
                "type": "project-based",
                "description": (
                    "168x50m üzən dokun ASCO tanker/bərə gəmilərinin texniki baxışı "
                    "və gövdə boyaması üçün icarəsi. "
                    "Scope: dok hazırlığı, sualtı qum püskürtmə (sandblasting), "
                    "epoksi antifouling boyama, xidmət heyəti."
                ),
                "sla": "Sifariş qəbulundan 72 saat ərzində dok hazırlığı; layihə müddəti müqavilə ilə"
            },
            {
                "name": "Yeni gəmi inşası (tanker, bərə, offshore gəmi)",
                "search_tags": [
                    "gəmi inşası", "ship construction", "newbuild", "vessel construction",
                    "tanker inşa", "ferry build", "offshore vessel", "shipbuilding",
                    "marine construction", "custom vessel"
                ],
                "type": "project-based",
                "description": (
                    "Bakı Gəmiqayırma Zavodu-nun mühəndis komandası ASCO, AZCON "
                    "tərəfindən sifariş edilən gəmiləri dizayn edir və inşa edir. "
                    "Scope: 3D model, gövdə fabrikasiyası, sistem quraşdırılması, "
                    "klassifikasiya, sınaq, komissiya."
                ),
                "sla": "Müqavilə ilə müəyyənləşdirilir; tipik 18-36 ay"
            },
            {
                "name": "Gəmi təmiri və konversiya xidməti",
                "search_tags": [
                    "gəmi təmiri", "ship repair", "vessel repair", "conversion",
                    "refit", "overhaul", "docking repair", "gəmi bərpası",
                    "ship maintenance", "marine repair"
                ],
                "type": "project-based",
                "description": (
                    "80-100 gəmini illik idarə edən zavodun tam gəmi təmiri, "
                    "sistem yeniləməsi və konversiya xidmətləri. "
                    "Scope: gövdə, mexanik, elektrik, naviqasiya sistemləri."
                ),
                "sla": "Baxış həcmindən asılı olaraq 2-12 həftə"
            },
            {
                "name": "Polad konstruksiya fabrikasiyası (qeyri-dəniz sektoru)",
                "search_tags": [
                    "polad fabrikasiya", "steel fabrication", "metal works", "CNC kəsmə",
                    "welding service", "qaynaq xidməti", "structural steel", "metal construction",
                    "industrial fabrication", "custom metalwork"
                ],
                "type": "project-based",
                "description": (
                    "Zavodun CNC kəsmə, qaynaq, çelik fabrikasiya infrastrukturundan "
                    "ADY körpü konstruksiyaları, metro hissələri kimi AZCON layihələri üçün "
                    "subpodrat xidmətləri. "
                    "Scope: material analizi, fabrikasiya, NDT testi, çatdırılma."
                ),
                "sla": "Texniki TZ qəbulundan 5 iş günündə qiymət; istehsal müddəti həcmə görə"
            },
        ],
        "active_orders": [
            {
                "vendor": "SSAB AB (İsveç)",
                "item": "Hardox 400 yüksək möhkəmlikli gəmiqayırma polad — 120 ton",
                "expected_delivery": "2026-Q2",
                "origin_country": "İsveç"
            },
            {
                "vendor": "MAN Energy Solutions (Almaniya)",
                "item": "Tanker baş mühərrikləri MAN B&W 6S50ME-C — 2 ədəd",
                "expected_delivery": "2026-Q3",
                "origin_country": "Almaniya"
            },
        ]
    },

}  # ─── AZCON_COMPANIES sonu ─────────────────────────────────────────────────


# =============================================================================
#  YARDIMÇI FUNKSIYALAR
# =============================================================================

def get_company(name: str) -> dict:
    """Şirkət adına görə tam məlumat lüğətini qaytarır."""
    return AZCON_COMPANIES.get(name, {})


def list_companies() -> list:
    """Bütün şirkət açarlarını siyahı kimi qaytarır."""
    return list(AZCON_COMPANIES.keys())


def search_inventory(keyword: str) -> list:
    """
    search_tags-ə görə bütün şirkətlərin surplus_inventory-sini axtarır.
    Həm Azərbaycan, həm ingilis axtarışlarına cavab verir.
    """
    keyword_lower = keyword.lower()
    results = []
    for company, data in AZCON_COMPANIES.items():
        for item in data.get("surplus_inventory", []):
            tags = [t.lower() for t in item.get("search_tags", [])]
            name_lower = item.get("item_name", "").lower()
            if keyword_lower in name_lower or any(keyword_lower in t for t in tags):
                results.append({
                    "company": company,
                    "item_name": item["item_name"],
                    "quantity_available": item["quantity_available"],
                    "unit": item["unit"],
                    "price_per_unit_azn": item["price_per_unit"],
                    "reliability_score": item["reliability_score"],
                })
    return results


def search_services(keyword: str) -> list:
    """
    search_tags-ə görə bütün şirkətlərin services-ini axtarır.
    """
    keyword_lower = keyword.lower()
    results = []
    for company, data in AZCON_COMPANIES.items():
        for svc in data.get("services", []):
            tags = [t.lower() for t in svc.get("search_tags", [])]
            name_lower = svc.get("name", "").lower()
            if keyword_lower in name_lower or any(keyword_lower in t for t in tags):
                results.append({
                    "company": company,
                    "service_name": svc["name"],
                    "type": svc["type"],
                    "sla": svc.get("sla", ""),
                })
    return results


def find_batching_opportunities() -> dict:
    """
    Smart Batching: bütün active_orders-i origin_country-yə görə qruplaşdırır.
    2+ şirkətin eyni ölkədən sifarişi varsa batching fürsəti mövcuddur.
    """
    batching_map: dict = {}
    for company, data in AZCON_COMPANIES.items():
        for order in data.get("active_orders", []):
            origin = order.get("origin_country", "Naməlum")
            if origin not in batching_map:
                batching_map[origin] = []
            batching_map[origin].append({
                "company": company,
                "vendor": order.get("vendor"),
                "item": order.get("item"),
                "delivery": order.get("expected_delivery"),
            })
    return {k: v for k, v in batching_map.items() if len(v) >= 2}


def get_surplus_total_value_azn(name: str) -> float:
    """Şirkətin anbar ehtiyatlarının ümumi AZN dəyərini hesablayır."""
    company = AZCON_COMPANIES.get(name, {})
    return sum(
        item.get("price_per_unit", 0) * item.get("quantity_available", 0)
        for item in company.get("surplus_inventory", [])
    )


if __name__ == "__main__":
    import json

    print("=" * 70)
    print("  AZCON HOLDİNQ — Şirkət Anbar Dəyərləri (AZN)")
    print("=" * 70)
    for c in list_companies():
        val = get_surplus_total_value_azn(c)
        print(f"  {c:38s} | {val:>14,.0f} AZN")

    print("\n" + "=" * 70)
    print("  Smart Batching Fürsətləri (2+ şirkət, eyni mənşə ölkə)")
    print("=" * 70)
    print(json.dumps(find_batching_opportunities(), ensure_ascii=False, indent=2))

    print("\n" + "=" * 70)
    print("  Axtarış nümunəsi: 'fiber' — inventar")
    print("=" * 70)
    for r in search_inventory("fiber"):
        print(f"  [{r['company']}] {r['item_name']} — {r['quantity_available']} {r['unit']} @ {r['price_per_unit_azn']} AZN")

    print("\n" + "=" * 70)
    print("  Axtarış nümunəsi: 'maintenance' — xidmətlər")
    print("=" * 70)
    for r in search_services("maintenance"):
        print(f"  [{r['company']}] {r['service_name']} ({r['type']})")
