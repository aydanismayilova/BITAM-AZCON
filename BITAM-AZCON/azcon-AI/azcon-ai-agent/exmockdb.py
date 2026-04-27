from typing import Any, Dict, List


def inv(item: str, qty: int, price: float, score: float, logistics: str) -> Dict[str, Any]:
    return {
        "item_name": item,
        "quantity_available": qty,
        "price_per_unit": price,
        "reliability_score": score,
        "logistics_info": logistics,
    }


AZCON_COMPANIES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "AZAL": {
        "surplus_inventory": [
            inv("aviation headset", 35, 180.0, 4.6, "Baki hava limani anbari, 2 gun"),
            inv("network switch 48-port", 22, 520.0, 4.5, "Baki daxili catdirilma"),
            inv("server rack cabinet", 12, 950.0, 4.7, "Qurasdirma ile"),
            inv("safety gloves", 500, 6.5, 4.3, "Merkezi anbar, eyni gun"),
            inv("a4 kagiz", 2400, 4.2, 4.4, "Heftelik korporativ catdirilma"),
        ],
        "services": [{"name": "hava logistika xidmeti"}, {"name": "texniki servis"}, {"name": "anbar idareetmesi"}],
    },
    "Baki Metropoliteni": {
        "surplus_inventory": [
            inv("elektrik kabeli", 3500, 2.8, 4.8, "Baki ve region gonderis"),
            inv("CCTV kamera", 120, 145.0, 4.6, "24 saatda teslim"),
            inv("UPS batareya modulu", 80, 210.0, 4.5, "Texniki yoxlama ile"),
            inv("safety helmet", 460, 14.0, 4.4, "Terminal anbari"),
            inv("fiber patch cord", 900, 7.5, 4.5, "B2B sifaris uzre"),
        ],
        "services": [{"name": "tunel texniki xidmeti"}, {"name": "elektrik monitorinq"}, {"name": "tehlukesizlik xidmeti"}],
    },
    "BakuBus": {
        "surplus_inventory": [
            inv("avtobus ehtiyat hissesi", 630, 48.0, 4.5, "Depodan catdirilma"),
            inv("diesel filter", 870, 12.0, 4.4, "Topdan endirim"),
            inv("GPS tracker", 90, 75.0, 4.3, "Qurasdirma desteyi"),
            inv("ticket validator", 40, 390.0, 4.2, "Texniki servis daxildir"),
            inv("a4 kagiz", 1200, 4.0, 4.1, "Ofis depodan"),
        ],
        "services": [{"name": "seher logistika xidmeti"}, {"name": "avtonaqliyyat servis"}, {"name": "fleet monitorinq"}],
    },
    "Azerbaycan Demir Yollari": {
        "surplus_inventory": [
            inv("rels birlesdirici bolt", 1500, 5.5, 4.7, "Stansiya anbari"),
            inv("sinyal kabeli", 2600, 3.2, 4.6, "Regionlara planli gonderis"),
            inv("industrial router", 56, 460.0, 4.5, "Montaj komandasi var"),
            inv("server", 28, 2400.0, 4.8, "Data merkezi transfer"),
            inv("safety gloves", 740, 6.0, 4.3, "B2B topdan"),
        ],
        "services": [{"name": "yuk dasima xidmeti"}, {"name": "infrastruktur texniki xidmeti"}, {"name": "regional logistika"}],
    },
    "Baki Taksi Xidmeti": {
        "surplus_inventory": [
            inv("dash cam", 140, 82.0, 4.2, "Merkezi parkdan"),
            inv("mobil data terminal", 95, 130.0, 4.1, "Qurasdirma desteyi"),
            inv("car charger", 480, 9.5, 4.0, "Ekspress gonderis"),
            inv("printer", 36, 170.0, 4.1, "Ofis depodan"),
            inv("a4 kagiz", 600, 4.3, 4.0, "Daxili sifaris"),
        ],
        "services": [{"name": "seher daxili transport"}, {"name": "kuryer xidmeti"}, {"name": "mobil park idareetmesi"}],
    },
    "ASCO": {
        "surplus_inventory": [
            inv("marine radio", 65, 320.0, 4.6, "Deniz limanindan"),
            inv("satellite antenna", 26, 780.0, 4.5, "Qurasdirma ile"),
            inv("server rack cabinet", 10, 980.0, 4.4, "Məhdud stock"),
            inv("industrial switch", 74, 410.0, 4.5, "Liman gonderisi"),
            inv("safety helmet", 300, 15.0, 4.3, "Topdan satis"),
        ],
        "services": [{"name": "deniz logistika xidmeti"}, {"name": "port texniki xidmeti"}, {"name": "yuk operasyonlari"}],
    },
    "Aztelekom": {
        "surplus_inventory": [
            inv("fiber optic kabel", 5200, 1.9, 4.8, "Regionlara catdirilma"),
            inv("ONU modem", 1100, 29.0, 4.7, "48 saatda teslim"),
            inv("network switch 24-port", 260, 145.0, 4.6, "Topdan endirim"),
            inv("router enterprise", 95, 410.0, 4.7, "Qurasdirma var"),
            inv("pentest xidmeti", 45, 1200.0, 4.7, "SOC komandasi ile"),
        ],
        "services": [{"name": "internet infrastruktur xidmeti"}, {"name": "data center xidmeti"}, {"name": "kibertehlukesizlik xidmeti"}],
    },
    "AzInTelecom": {
        "surplus_inventory": [
            inv("cloud server", 320, 210.0, 4.9, "Operativ aktivlesdirme"),
            inv("GPU server", 42, 4800.0, 4.8, "Data merkezi qurasdirma"),
            inv("firewall appliance", 58, 1300.0, 4.8, "24/7 destek"),
            inv("a4 kagiz", 1800, 3.9, 4.6, "Korporativ satis bolmesi"),
            inv("pentest xidmeti", 60, 1050.0, 4.9, "Red team ve blue team"),
        ],
        "services": [{"name": "cloud xidmeti"}, {"name": "pentest xidmeti"}, {"name": "managed security xidmeti"}],
    },
    "Azerpoct": {
        "surplus_inventory": [
            inv("packaging box", 4300, 0.9, 4.3, "Olke uzre sebeke"),
            inv("label printer", 75, 240.0, 4.2, "Filiallarga gonderis"),
            inv("barcode scanner", 190, 68.0, 4.1, "Eyni gun teslim"),
            inv("a4 kagiz", 1500, 4.1, 4.2, "Ofis levazimati topdan"),
            inv("archive cabinet", 48, 220.0, 4.0, "Marsrutlu catdirilma"),
        ],
        "services": [{"name": "kuryer xidmeti"}, {"name": "poct logistika xidmeti"}, {"name": "sened catdirilma xidmeti"}],
    },
    "Azerkosmos": {
        "surplus_inventory": [
            inv("satellite modem", 44, 640.0, 4.7, "Merkezi texniki anbar"),
            inv("RF transceiver", 31, 980.0, 4.6, "Yoxlama ile catdirilma"),
            inv("secure storage", 25, 720.0, 4.5, "Məhdud partiya"),
            inv("GPU server", 12, 5200.0, 4.8, "Data merkezi qurasdirma"),
            inv("backup server", 20, 2700.0, 4.6, "Planli migrasiya ile"),
        ],
        "services": [{"name": "peyk rabitesi xidmeti"}, {"name": "data transmisiya xidmeti"}, {"name": "kosmik monitorinq xidmeti"}],
    },
    "Teleradio": {
        "surplus_inventory": [
            inv("audio mixer", 58, 410.0, 4.3, "Studiyadan teslim"),
            inv("broadcast camera", 34, 1750.0, 4.4, "Texniki qurasdirma var"),
            inv("wireless microphone", 120, 120.0, 4.2, "Baki daxili gonderis"),
            inv("LED panel", 92, 85.0, 4.1, "Topdan satis imkani"),
            inv("UPS batareya modulu", 66, 190.0, 4.2, "Planli teslim"),
        ],
        "services": [{"name": "media yayim xidmeti"}, {"name": "audio video texniki xidmeti"}, {"name": "studiyo istehsal xidmeti"}],
    },
    "NAIC": {
        "surplus_inventory": [
            inv("AI workstation", 24, 3600.0, 4.9, "Mərkəzi AI laboratoriya"),
            inv("GPU server", 30, 5000.0, 4.9, "HPC infrastruktur ile"),
            inv("NAS storage", 40, 1400.0, 4.7, "Qurasdirma desteği var"),
            inv("MLOps license", 120, 290.0, 4.8, "Illik abonelik"),
            inv("pentest xidmeti", 35, 1100.0, 4.8, "AI security audit daxil"),
        ],
        "services": [{"name": "AI konsaltinq xidmeti"}, {"name": "MLOps xidmeti"}, {"name": "data analitika xidmeti"}],
    },
    "Baki Gemiqayirma Zavodu": {
        "surplus_inventory": [
            inv("metal sheet", 2600, 12.0, 4.5, "Zavod anbarindan"),
            inv("welding machine", 42, 680.0, 4.4, "Texniki yoxlama ile"),
            inv("industrial cable", 2100, 3.8, 4.3, "Baki ve region gonderis"),
            inv("safety boots", 520, 26.0, 4.2, "Partiya ile teslim"),
            inv("generator", 18, 2900.0, 4.5, "Qurasdirma ve test ile"),
        ],
        "services": [{"name": "gemi texniki servis"}, {"name": "agır senaye montaj xidmeti"}, {"name": "metalkonstruksiya xidmeti"}],
    },
}
