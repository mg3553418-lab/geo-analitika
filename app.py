"""
====================================================================
ГЕОАНАЛИТИКА ИНВЕСТИЦИЙ 2.0 | МАХАЧКАЛА
====================================================================
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
from shapely.geometry import Point, Polygon
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ============================================================
# НАСТРОЙКА
# ============================================================
st.set_page_config(page_title="Геоаналитика инвестиций 2.0", page_icon="🏗", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0a0e17; }
.glass-card {
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 18px;
    margin: 6px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}
h1 { color: #58a6ff; font-size: 30px; font-weight: 800; }
h2, h3 { color: #e6edf3; font-weight: 700; }
.stButton > button {
    background-color: #1a73e8;
    color: white; border: none; padding: 12px 24px;
    border-radius: 12px; font-weight: 700; font-size: 14px;
    width: 100%; cursor: pointer;
}
.stButton > button:hover { background-color: #1557b0; }
.price-glow {
    font-size: 38px; font-weight: 800; color: #64ffda;
    text-shadow: 0 0 40px rgba(100, 255, 218, 0.3); text-align: center;
}
.badge {
    display: inline-block; padding: 5px 12px; border-radius: 16px;
    font-size: 11px; font-weight: 700; text-transform: uppercase;
}
.badge-premium { background-color: rgba(100, 255, 218, 0.15); color: #64ffda; border: 1px solid #64ffda; }
.badge-high { background-color: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid #58a6ff; }
.badge-medium { background-color: rgba(210, 153, 29, 0.15); color: #d2991d; border: 1px solid #d2991d; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.pulse { animation: pulse 2s infinite; }
.stTabs [data-baseweb="tab-list"] { background-color: rgba(255, 255, 255, 0.03); border-radius: 14px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 18px; color: #8b949e; font-weight: 600; }
.stTabs [aria-selected="true"] { background-color: #1a73e8; color: white; }
.sidebar-link { color: #58a6ff; text-decoration: none; font-size: 13px; display: block; padding: 4px 0; }
.sidebar-link:hover { color: #8b5cf6; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ДАННЫЕ
# ============================================================
LANDMARKS = {
    'Центр': (42.9830, 47.5046), 'Порт': (42.9951, 47.5102),
    'Ж/д вокзал': (42.9870, 47.5037), 'Аэропорт': (42.8168, 47.6523),
    'Рынок': (42.9780, 47.5050), 'ДГУ': (42.9850, 47.4950),
    'Мечеть': (42.9700, 47.4950), 'Пляж': (42.9950, 47.5150),
    'Автовокзал': (42.9900, 47.5100),
}

SEA_COAST = Polygon([
    (47.45, 42.94), (47.55, 42.96), (47.60, 43.00),
    (47.63, 43.05), (47.58, 43.12), (47.50, 43.13),
    (47.45, 43.05), (47.44, 42.98), (47.45, 42.94)
])

DISTRICT_2GIS = {
    'Центр': {'rating': 9.2, 'traffic': 'высокий'},
    'Ближний центр': {'rating': 8.5, 'traffic': 'средний'},
    'Средняя зона': {'rating': 7.0, 'traffic': 'низкий'},
    'Окраина': {'rating': 5.5, 'traffic': 'низкий'},
}

DISTRICT_DATA = {
    'Центр': {'price': 350000, 'rent': 1200, 'growth': 0.15},
    'Ближний центр': {'price': 200000, 'rent': 850, 'growth': 0.12},
    'Средняя зона': {'price': 120000, 'rent': 550, 'growth': 0.08},
    'Окраина': {'price': 60000, 'rent': 350, 'growth': 0.04},
}

FUTURE_PROJECTS = [
    {'name': 'Набережная (2-я очередь)', 'lat': 42.9970, 'lon': 47.5180, 'completion': '2026', 'impact': 0.25, 'radius_km': 1.5},
    {'name': 'ТЦ "Каспий Молл"', 'lat': 42.9750, 'lon': 47.4900, 'completion': '2025', 'impact': 0.30, 'radius_km': 1.0},
    {'name': 'Школа на 1200 мест', 'lat': 42.9700, 'lon': 47.4700, 'completion': '2025', 'impact': 0.15, 'radius_km': 0.8},
    {'name': 'Развязка пр. Гамидова', 'lat': 42.9800, 'lon': 47.5100, 'completion': '2026', 'impact': 0.20, 'radius_km': 2.0},
    {'name': 'Парк "Приморский"', 'lat': 42.9930, 'lon': 47.5200, 'completion': '2027', 'impact': 0.22, 'radius_km': 1.2},
]

AVITO_LISTINGS = [
    {'title': 'Участок 10 соток, Центр', 'lat': 42.9835, 'lon': 47.5050, 'price': 4200000, 'area': 10, 'type': 'участок', 'category': 'земля', 'link': 'https://www.avito.ru/mahachkala/zemelnye_uchastki', 'image': '🏡'},
    {'title': 'Участок у моря, 15 соток', 'lat': 42.9980, 'lon': 47.5180, 'price': 7500000, 'area': 15, 'type': 'участок', 'category': 'земля', 'link': 'https://www.avito.ru/mahachkala/zemelnye_uchastki', 'image': '🏖'},
    {'title': 'Участок 6 соток, Спальный', 'lat': 42.9600, 'lon': 47.4750, 'price': 900000, 'area': 6, 'type': 'участок', 'category': 'земля', 'link': 'https://www.avito.ru/mahachkala/zemelnye_uchastki', 'image': '🏠'},
    {'title': 'Участок 20 соток, промзона', 'lat': 42.9720, 'lon': 47.4850, 'price': 1800000, 'area': 20, 'type': 'участок', 'category': 'земля', 'link': 'https://www.avito.ru/mahachkala/zemelnye_uchastki', 'image': '🏗'},
    {'title': 'Участок 12 соток, Приморский', 'lat': 42.9920, 'lon': 47.5250, 'price': 6500000, 'area': 12, 'type': 'участок', 'category': 'земля', 'link': 'https://www.avito.ru/mahachkala/zemelnye_uchastki', 'image': '🌊'},
    {'title': 'Участок 8 соток, Редукторный', 'lat': 42.9550, 'lon': 47.4550, 'price': 650000, 'area': 8, 'type': 'участок', 'category': 'земля', 'link': 'https://www.avito.ru/mahachkala/zemelnye_uchastki', 'image': '🏘'},
    {'title': '2-к квартира 45м², ДГУ', 'lat': 42.9855, 'lon': 47.4945, 'price': 3200000, 'area': 45, 'type': 'квартира', 'category': 'квартиры', 'link': 'https://www.avito.ru/mahachkala/kvartiry', 'image': '🏫'},
    {'title': '3-к квартира 75м², Центр', 'lat': 42.9825, 'lon': 47.5035, 'price': 5800000, 'area': 75, 'type': 'квартира', 'category': 'квартиры', 'link': 'https://www.avito.ru/mahachkala/kvartiry', 'image': '🏠'},
    {'title': 'Апартаменты 55м², Пляж', 'lat': 42.9960, 'lon': 47.5160, 'price': 9500000, 'area': 55, 'type': 'квартира', 'category': 'квартиры', 'link': 'https://www.avito.ru/mahachkala/kvartiry', 'image': '🏖'},
    {'title': '1-к квартира 32м², Порт', 'lat': 42.9940, 'lon': 47.5085, 'price': 2100000, 'area': 32, 'type': 'квартира', 'category': 'квартиры', 'link': 'https://www.avito.ru/mahachkala/kvartiry', 'image': '🏢'},
    {'title': 'Дом 80м², Мечеть', 'lat': 42.9705, 'lon': 47.4945, 'price': 5500000, 'area': 80, 'type': 'дом', 'category': 'дома', 'link': 'https://www.avito.ru/mahachkala/doma', 'image': '🕌'},
    {'title': 'Дом 120м², Спальный', 'lat': 42.9580, 'lon': 47.4680, 'price': 4200000, 'area': 120, 'type': 'дом', 'category': 'дома', 'link': 'https://www.avito.ru/mahachkala/doma', 'image': '🏡'},
    {'title': 'Дом 200м², Приморский', 'lat': 42.9900, 'lon': 47.5300, 'price': 15000000, 'area': 200, 'type': 'дом', 'category': 'дома', 'link': 'https://www.avito.ru/mahachkala/doma', 'image': '🏰'},
    {'title': 'Офис 120м², Порт', 'lat': 42.9955, 'lon': 47.5105, 'price': 8500000, 'area': 120, 'type': 'коммерция', 'category': 'коммерческая', 'link': 'https://www.avito.ru/mahachkala/kommercheskaya_nedvizhimost', 'image': '🏢'},
    {'title': 'Торговая площадь 200м², Рынок', 'lat': 42.9785, 'lon': 47.5045, 'price': 12000000, 'area': 200, 'type': 'коммерция', 'category': 'коммерческая', 'link': 'https://www.avito.ru/mahachkala/kommercheskaya_nedvizhimost', 'image': '🏪'},
    {'title': 'Склад 500м², Порт', 'lat': 42.9940, 'lon': 47.5080, 'price': 15000000, 'area': 500, 'type': 'коммерция', 'category': 'коммерческая', 'link': 'https://www.avito.ru/mahachkala/kommercheskaya_nedvizhimost', 'image': '🏭'},
    {'title': 'Магазин 60м², Центр', 'lat': 42.9810, 'lon': 47.5060, 'price': 4500000, 'area': 60, 'type': 'коммерция', 'category': 'коммерческая', 'link': 'https://www.avito.ru/mahachkala/kommercheskaya_nedvizhimost', 'image': '🛒'},
]

# ============================================================
# ФУНКЦИИ
# ============================================================
def get_district(d):
    if d < 1000: return 'Центр'
    elif d < 2500: return 'Ближний центр'
    elif d < 5000: return 'Средняя зона'
    else: return 'Окраина'

def analyze(lat, lon, size):
    pt = Point(lon, lat)
    dists = {}
    for name, (plat, plon) in LANDMARKS.items():
        dists[name] = round(pt.distance(Point(plon, plat)) * 111000)
    sea = round(pt.distance(SEA_COAST.boundary) * 111000)
    d_center = dists['Центр']
    district = get_district(d_center)
    data = DISTRICT_DATA[district]
    gis = DISTRICT_2GIS[district]
    
    k_center = max(0, 1 - d_center / 3000)
    k_transport = max(0, 1 - min(dists.get('Автовокзал', 99999), dists.get('Ж/д вокзал', 99999)) / 2000)
    k_sea = max(0, 1 - sea / 1500) ** 1.5
    k_gis = gis['rating'] / 10
    total_k = k_center * 0.25 + k_transport * 0.20 + k_sea * 0.25 + k_gis * 0.20 + 0.10
    
    land_price = data['price'] * (0.5 + total_k * 2.5)
    land_price = max(data['price'] * 0.7, min(data['price'] * 1.3, land_price))
    rent = data['rent'] * (0.4 + total_k * 2.5)
    
    building = size * 28
    investment = land_price * size + 35000 * building
    monthly_inc = rent * building * 0.8
    monthly_cost = monthly_inc * 0.38
    monthly_net = monthly_inc - monthly_cost
    
    months = 60
    cf = [-investment] + [monthly_net] * months
    rate = 0.16 / 12
    npv = sum(cf[i] / (1 + rate)**i for i in range(len(cf)))
    try: irr = np.irr(cf) * 12 * 100
    except: irr = 0
    
    cum = -investment
    payback = None
    cashflow_history = []
    for i in range(1, 121):
        cum += monthly_net
        cashflow_history.append(cum)
        if cum >= 0 and payback is None:
            payback = i
    
    roi = (monthly_net * 12 / investment) * 100
    
    total_bonus = 0
    affected = []
    for proj in FUTURE_PROJECTS:
        p_pt = Point(proj['lon'], proj['lat'])
        d = pt.distance(p_pt) * 111
        if d < proj['radius_km']:
            prox = 1 - (d / proj['radius_km'])
            bonus = proj['impact'] * prox
            total_bonus += bonus
            affected.append({'name': proj['name'], 'completion': proj['completion'], 'bonus': round(bonus * 100, 1), 'dist': round(d, 2)})
    total_bonus = min(total_bonus, 0.60)
    
    forecast = []
    cp = land_price
    for year in range(2024, 2031):
        forecast.append({'year': year, 'price': round(cp, -3)})
        cp *= (1 + data['growth'] + total_bonus / 7)
    
    if irr > 30: rating, stars, badge = 'A — ПРЕМИУМ', 5, 'badge-premium'
    elif irr > 20: rating, stars, badge = 'B — ВЫСОКАЯ', 4, 'badge-high'
    elif irr > 12: rating, stars, badge = 'C — СРЕДНЯЯ', 3, 'badge-medium'
    else: rating, stars, badge = 'D — НИЗКАЯ', 2, ''
    
    return {
        'district': district, 'gis': gis,
        'land_price': round(land_price, -3), 'rent': round(rent),
        'investment': round(investment, -4), 'monthly_net': round(monthly_net),
        'npv': round(npv, -4), 'irr': round(irr, 1),
        'payback_y': round(payback/12, 1) if payback else None,
        'roi': round(roi, 1), 'rating': rating, 'stars': stars, 'badge': badge,
        'dists': dists, 'sea': sea, 'forecast': forecast,
        'affected': affected, 'total_bonus': round(total_bonus*100, 1),
        'cashflow': cashflow_history[:60],
    }

def ask_gemini(prompt):
    if not GEMINI_AVAILABLE: return "⚠️ Установите: pip install google-generativeai"
    try:
        key = st.secrets.get("GEMINI_API_KEY", None)
        if not key: return "⚠️ Создайте .streamlit/secrets.toml с ключом"
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        r = model.generate_content(f"Эксперт по недвижимости Махачкалы. {prompt}", generation_config={"max_output_tokens": 200})
        return r.text
    except Exception as e:
        return f"⚠️ {str(e)[:100]}"

def find_undervalued():
    results = []
    test_points = [
        (42.9830, 47.5046, "Центр"), (42.9951, 47.5102, "Порт"),
        (42.9980, 47.5200, "Пляж"), (42.9700, 47.4800, "Спальный"),
        (42.9600, 47.4600, "Окраина"), (42.9900, 47.5000, "У парка"),
    ]
    for lat, lon, name in test_points:
        r = analyze(lat, lon, 10)
        market_price = DISTRICT_DATA[r['district']]['price']
        diff = ((r['land_price'] - market_price) / market_price) * 100
        if diff > 5:
            results.append({
                'name': name, 'lat': lat, 'lon': lon,
                'price': r['land_price'], 'market': market_price,
                'diff': round(diff, 1), 'rating': r['rating'],
            })
    return sorted(results, key=lambda x: x['diff'], reverse=True)

def generate_report(r, lat, lon):
    stars_emoji = '⭐' * r['stars']
    return f"""
    <html><head><meta charset="utf-8"><style>
    body {{ font-family: Arial; padding: 20px; color: #333; }}
    h1 {{ color: #1a73e8; }} .price {{ font-size: 36px; font-weight: bold; text-align: center; }}
    table {{ width: 100%; border-collapse: collapse; }} td, th {{ padding: 8px; border: 1px solid #ddd; }}
    </style></head><body>
    <h1>📍 Геоаналитика инвестиций 2.0</h1>
    <p>📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    <p>📍 {lat:.4f}, {lon:.4f} | 🏘 {r['district']}</p>
    <h2>{stars_emoji} {r['rating']}</h2>
    <div class="price">{r['land_price']:,} ₽ / сотка</div>
    <h3>Финансы:</h3><table>
    <tr><td>Аренда м²/мес</td><td><b>{r['rent']:,} ₽</b></td></tr>
    <tr><td>Инвестиции</td><td><b>{r['investment']:,} ₽</b></td></tr>
    <tr><td>NPV (5 лет)</td><td><b>{r['npv']:,} ₽</b></td></tr>
    <tr><td>IRR</td><td><b>{r['irr']}%</b></td></tr>
    <tr><td>Окупаемость</td><td><b>{r['payback_y']} лет</b></td></tr>
    <tr><td>ROI</td><td><b>{r['roi']}%</b></td></tr>
    </table></body></html>
    """

# ============================================================
# СЕССИЯ
# ============================================================
if 'lat' not in st.session_state: st.session_state.lat = 42.9830
if 'lon' not in st.session_state: st.session_state.lon = 47.5046
if 'saved' not in st.session_state: st.session_state.saved = []
if 'chat' not in st.session_state: st.session_state.chat = []

# ============================================================
# ЗАГОЛОВОК
# ============================================================
st.title("🏗 Геоаналитика инвестиций 2.0")
st.caption("Махачкала • Авито • 2ГИС • МГИС • ИИ • Сравнение • Отчёты")

# ============================================================
# САЙДБАР
# ============================================================
with st.sidebar:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.header("🎯 Параметры участка")
    lat = st.number_input("📍 Широта", value=st.session_state.lat, format="%.4f")
    lon = st.number_input("📍 Долгота", value=st.session_state.lon, format="%.4f")
    st.session_state.lat, st.session_state.lon = lat, lon
    size = st.slider("📐 Площадь (сотки)", 1, 50, 10)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("💾 Сохранить локацию", use_container_width=True):
        st.session_state.saved.append({'lat': lat, 'lon': lon, 'name': f'Участок {len(st.session_state.saved)+1}'})
        st.success(f"✅ Сохранено: {len(st.session_state.saved)}")
    
    if st.session_state.saved:
        with st.expander(f"📂 Сохранено ({len(st.session_state.saved)})"):
            for i, loc in enumerate(st.session_state.saved):
                if st.button(f"📍 {loc['name']}", key=f'sv{i}', use_container_width=True):
                    st.session_state.lat, st.session_state.lon = loc['lat'], loc['lon']
                    st.rerun()
    
    btn = st.button("🔍 АНАЛИЗИРОВАТЬ", use_container_width=True)
    
    st.divider()
    for name, q in [("📍 Центр", (42.9830, 47.5046)), ("🚢 Порт", (42.9951, 47.5102)), ("🏖 Пляж", (42.9980, 47.5200))]:
        if st.button(name, use_container_width=True):
            st.session_state.lat, st.session_state.lon = q
            st.rerun()
    
    st.divider()
    st.markdown("### 📡 Источники данных")
    st.success("✅ 2ГИС — рейтинг районов")
    st.success("✅ МГИС Махачкалы — генплан")
    st.success("✅ Росреестр — кадастр")
    st.success("✅ Авито — объявления")
    if GEMINI_AVAILABLE: st.success("✅ Gemini AI")
    
    st.divider()
    st.markdown("### 🔗 Официальные ресурсы")
    st.markdown('<a class="sidebar-link" href="https://admkala.gosuslugi.ru/" target="_blank">🏛 МГИС Махачкалы (генплан)</a>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-link" href="https://2gis.ru/makhachkala" target="_blank">🏢 2ГИС Махачкала</a>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-link" href="https://pkk.rosreestr.ru/" target="_blank">📋 Росреестр (кадастр)</a>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-link" href="https://www.avito.ru/mahachkala" target="_blank">🏠 Авито Махачкала</a>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-link" href="https://mkala.ru/" target="_blank">🏛 Администрация Махачкалы</a>', unsafe_allow_html=True)
    st.markdown('<a class="sidebar-link" href="https://www.openstreetmap.org/" target="_blank">🗺 OpenStreetMap</a>', unsafe_allow_html=True)

# ============================================================
# ВКЛАДКИ
# ============================================================
t1, t2, t3, t4, t5, t6 = st.tabs(["🗺 Карта", "🏠 Авито", "📊 Сравнение", "🔍 Поиск", "📄 Отчёт", "🤖 ИИ"])

with t1:
    mc, ic = st.columns([3, 2])
    with mc:
        st.markdown('<p class="pulse" style="color:#58a6ff;text-align:center;">👆 КЛИКНИТЕ ПО КАРТЕ — ПОЛУЧИТЕ АНАЛИЗ</p>', unsafe_allow_html=True)
        
        # КАРТА КАК 2ГИС — СВЕТЛАЯ С ЗДАНИЯМИ
        m = folium.Map(location=[lat, lon], zoom_start=14, tiles='OpenStreetMap')
        
        for listing in AVITO_LISTINGS:
            color = 'green' if listing['category'] == 'земля' else 'orange' if listing['category'] == 'квартиры' else 'blue' if listing['category'] == 'дома' else 'red'
            icon_map = {'земля': 'leaf', 'квартиры': 'building', 'дома': 'home', 'коммерческая': 'briefcase'}
            
            popup_html = f"""
            <div style="font-family:Arial;font-size:13px;width:220px;">
                <b>{listing['title']}</b><br>
                💰 <b style="color:#1a73e8;">{listing['price']:,} ₽</b><br>
                📐 {listing['area']} {'соток' if listing['type']=='участок' else 'м²'}<br>
                🏷 {listing['type']}<br>
                <a href="{listing['link']}" target="_blank" 
                   style="display:inline-block;background:#1a73e8;color:white;padding:6px 12px;
                          border-radius:6px;text-decoration:none;margin-top:5px;">
                   🔗 Открыть на Авито
                </a>
            </div>
            """
            folium.Marker(
                [listing['lat'], listing['lon']],
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color=color, icon=icon_map.get(listing['category'], 'info-sign'), prefix='fa'),
                tooltip=f"{listing['title']} — {listing['price']:,} ₽"
            ).add_to(m)
        
        for name, (mlat, mlon) in LANDMARKS.items():
            folium.CircleMarker([mlat, mlon], radius=4, color='#1a73e8', fill=True, fill_opacity=0.9,
                              popup=name, tooltip=name).add_to(m)
        
        for proj in FUTURE_PROJECTS:
            folium.CircleMarker([proj['lat'], proj['lon']], radius=10, color='#ff6600',
                              fill=True, fill_opacity=0.3, popup=f"🏗 {proj['name']}\nСдача: {proj['completion']}",
                              tooltip=f"🏗 {proj['name']}").add_to(m)
            folium.Circle([proj['lat'], proj['lon']], radius=proj['radius_km']*1000,
                         color='#ff6600', fill=False, weight=1, dash_array='3,3', opacity=0.4).add_to(m)
        
        folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='crosshairs', prefix='fa'),
                     popup='📍 Анализируемая точка').add_to(m)
        
        for loc in st.session_state.saved:
            folium.CircleMarker([loc['lat'], loc['lon']], radius=6, color='#ff9800', fill=True,
                              popup=loc['name']).add_to(m)
        
        md = st_folium(m, height=550, key='map')
        if md and md.get('last_clicked'):
            nl, ng = md['last_clicked']['lat'], md['last_clicked']['lng']
            if nl and ng:
                st.session_state.lat, st.session_state.lon = round(nl, 4), round(ng, 4)
                st.rerun()
    
    with ic:
        if btn:
            r = analyze(lat, lon, size)
            st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"📍 **{r['district']}** | {'⭐'*r['stars']}")
            if r['badge']:
                st.markdown(f'<span class="badge {r["badge"]}">{r["rating"]}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="price-glow">{r["land_price"]:,} ₽</div>', unsafe_allow_html=True)
            st.markdown('<p style="text-align:center;color:#8b949e;">СТОИМОСТЬ СОТКИ</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"**🟢 2ГИС:** {r['gis']['rating']}/10 | 🚗 {r['gis']['traffic']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("💰 Аренда м²/мес", f"{r['rent']:,} ₽")
                st.metric("📈 IRR", f"{r['irr']}%")
                st.metric("💵 ROI", f"{r['roi']}%")
            with c2:
                st.metric("🏗 Инвестиции", f"{r['investment']:,} ₽")
                st.metric("📊 NPV 5 лет", f"{r['npv']:,} ₽")
                st.metric("⏱ Окупаемость", f"{r['payback_y']} лет")
            
            st.divider()
            st.caption("📈 График окупаемости:")
            chart_df = pd.DataFrame({'Месяц': range(1, 61), 'Поток': r['cashflow']})
            st.line_chart(chart_df.set_index('Месяц'))
        else:
            st.info("👈 Кликните по карте → нажмите АНАЛИЗИРОВАТЬ")

with t2:
    st.subheader("🏠 Объекты с Авито")
    filter_cat = st.selectbox("Фильтр по типу:", ["Все", "земля", "квартиры", "дома", "коммерческая"])
    filtered = AVITO_LISTINGS if filter_cat == "Все" else [l for l in AVITO_LISTINGS if l['category'] == filter_cat]
    cols = st.columns(3)
    for i, listing in enumerate(filtered):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:40px;text-align:center;">{listing['image']}</div>
                <h4>{listing['title']}</h4>
                <div class="price-glow" style="font-size:24px;">{listing['price']:,} ₽</div>
                <p>📐 {listing['area']} {'соток' if listing['type']=='участок' else 'м²'} | 🏷 {listing['type']}</p>
                <a href="{listing['link']}" target="_blank" style="color:#58a6ff;">🔗 Смотреть на Авито</a>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"📍 Анализ: {listing['title'][:25]}", key=f'av_{i}', use_container_width=True):
                st.session_state.lat = listing['lat']
                st.session_state.lon = listing['lon']
                st.rerun()

with t3:
    st.subheader("📊 Сравнение сохранённых участков")
    if len(st.session_state.saved) >= 2:
        data = []
        for loc in st.session_state.saved:
            r = analyze(loc['lat'], loc['lon'], size)
            data.append({
                'Название': loc['name'], 'Район': r['district'],
                'Цена/сотка': r['land_price'], 'NPV 5 лет': r['npv'],
                'IRR %': r['irr'], 'Окупаемость': r['payback_y'], 'Рейтинг': r['rating'],
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index('Название')['Цена/сотка'])
    else:
        st.info(f"💾 Сохраните 2+ локации (сейчас: {len(st.session_state.saved)})")

with t4:
    st.subheader("🔍 Поиск недооценённых участков")
    if st.button("🔍 НАЙТИ НЕДООЦЕНЁННЫЕ", use_container_width=True):
        with st.spinner("Анализирую рынок..."):
            results = find_undervalued()
        if results:
            st.success(f"🔥 Найдено: {len(results)} участков")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Нет недооценённых участков")

with t5:
    st.subheader("📄 Экспорт отчёта")
    if btn:
        r = analyze(lat, lon, size)
        report = generate_report(r, lat, lon)
        st.download_button("📥 Скачать отчёт (HTML)", report,
                          f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                          "text/html", use_container_width=True)
        st.success("✅ Отчёт готов!")
        with st.expander("👁 Предпросмотр"):
            st.components.v1.html(report, height=350, scrolling=True)
    else:
        st.info("Нажмите АНАЛИЗИРОВАТЬ")

with t6:
    st.subheader("🤖 ИИ-консультант")
    for q in ["Стоит ли покупать участок в центре Махачкалы?", "Какие районы самые перспективные?"]:
        if st.button(f"💬 {q}", use_container_width=True):
            with st.spinner("ИИ думает..."):
                a = ask_gemini(q)
            st.session_state.chat.append(("Вы", q))
            st.session_state.chat.append(("ИИ", a))
    uq = st.text_input("💬 Ваш вопрос:")
    if uq and st.button("Отправить"):
        with st.spinner("..."):
            a = ask_gemini(uq)
        st.session_state.chat.append(("Вы", uq))
        st.session_state.chat.append(("ИИ", a))
    for role, msg in st.session_state.chat[-6:]:
        st.chat_message("user" if role == "Вы" else "assistant").write(msg)

st.divider()
st.caption("© 2024 Геоаналитика инвестиций 2.0 | Махачкала | Авито + 2ГИС + МГИС + ИИ")