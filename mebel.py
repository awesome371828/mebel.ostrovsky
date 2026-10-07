# mebel.py
# Единый Flask-сервер: сайт + админка + SEO для Азова, Ростова-на-Дону, Батайска.
# Запуск: python mebel.py
# Руководитель по умолчанию: логин "кухниост", пароль "романкух".

import os
import re
import csv
import io
import json
import sqlite3
import hashlib
import secrets
import mimetypes
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote, urljoin

from flask import (
    Flask, request, session, redirect, url_for, render_template_string,
    send_from_directory, send_file, abort, jsonify, make_response, g
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# ---------- Конфигурация ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "mebel.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
SECRET_PATH = os.path.join(BASE_DIR, ".secret_key")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def _load_secret():
    if os.path.exists(SECRET_PATH):
        with open(SECRET_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(SECRET_PATH, "w", encoding="utf-8") as f:
        f.write(key)
    return key

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.secret_key = _load_secret()
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

CITIES = ["Азов", "Ростов-на-Дону", "Батайск"]
ROSTOV_DISTRICTS = [
    "Ворошиловский", "Железнодорожный", "Кировский", "Ленинский",
    "Октябрьский", "Первомайский", "Пролетарский", "Советский",
]
KEYWORDS = [
    "кухни на заказ батайск",
    "кухни на заказ ростов",
    "кухни на заказ азов",
    "шкафы на заказ батайск",
    "шкафы на заказ ростов",
    "шкафы на заказ азов",
    "гардеробные на заказ батайск",
    "гардеробные на заказ ростов",
    "гардеробные на заказ азов",
    "мебель на заказ батайск",
    "мебель на заказ ростов",
    "мебель на заказ азов",
    "прихожие на заказ батайск",
    "прихожие на заказ ростов",
    "прихожие на заказ азов",
    "кухни под заказ батайск",
    "кухни под заказ ростов",
    "кухни под заказ азов",
]

# ---------- База данных ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'менеджер',
        full_name TEXT,
        created_at TEXT NOT NULL,
        created_by INTEGER,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login TEXT,
        action TEXT,
        details TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE,
        name TEXT,
        phone TEXT,
        email TEXT,
        city TEXT,
        messenger TEXT,
        call_time TEXT,
        furniture_type TEXT,
        source TEXT DEFAULT 'сайт',
        status TEXT DEFAULT 'новая',
        priority TEXT DEFAULT 'обычный',
        responsible_id INTEGER,
        notes TEXT,
        wish TEXT,
        deadline TEXT,
        no_answer INTEGER DEFAULT 0,
        repeat_client INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS lead_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original TEXT,
        kind TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS lead_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        user_id INTEGER,
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS lead_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        user_id INTEGER,
        channel TEXT,
        result TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        code TEXT UNIQUE,
        title TEXT,
        room_type TEXT,
        layout TEXT,
        sizes TEXT,
        materials TEXT,
        fittings TEXT,
        components TEXT,
        price_materials REAL DEFAULT 0,
        price_work REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        delivery REAL DEFAULT 0,
        assembly REAL DEFAULT 0,
        total REAL DEFAULT 0,
        version INTEGER DEFAULT 1,
        status TEXT DEFAULT 'черновик',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS project_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        version INTEGER NOT NULL,
        snapshot TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        kind TEXT,
        date TEXT,
        assignee TEXT,
        note TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS warehouse (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        name TEXT,
        qty REAL DEFAULT 0,
        unit TEXT,
        min_qty REAL DEFAULT 0,
        supplier TEXT,
        price REAL DEFAULT 0,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        style TEXT,
        material TEXT,
        price REAL DEFAULT 0,
        city TEXT,
        term TEXT,
        description TEXT,
        before_photo TEXT,
        after_photo TEXT,
        published INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author TEXT,
        text TEXT,
        rating INTEGER DEFAULT 5,
        city TEXT,
        approved INTEGER DEFAULT 0,
        confirmed INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        answer TEXT,
        published INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS promotions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        code TEXT,
        city TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        title TEXT,
        meta_title TEXT,
        meta_description TEXT,
        og_image TEXT,
        jsonld TEXT,
        body TEXT,
        status TEXT DEFAULT 'черновик',
        publish_at TEXT,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS page_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER,
        snapshot TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS homepage_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        sort_order INTEGER DEFAULT 0,
        hidden INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS archive (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity TEXT,
        entity_id INTEGER,
        payload TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS seo_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT,
        district TEXT,
        keyword TEXT,
        slug TEXT UNIQUE,
        title TEXT,
        meta_title TEXT,
        meta_description TEXT,
        body TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS content_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT,
        updated_at TEXT NOT NULL
    );
    """)
    db.commit()

    # руководитель по умолчанию
    cur.execute("SELECT id FROM users WHERE login = ?", ("кухниост",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (login, password_hash, role, full_name, created_at, active) VALUES (?,?,?,?,?,1)",
            ("кухниост", generate_password_hash("романкух"), "руководитель",
             "Главный руководитель", datetime.now().isoformat(timespec="seconds"))
        )
        db.commit()

    # стартовые SEO-страницы
    cur.execute("SELECT COUNT(*) AS c FROM seo_pages")
    if cur.fetchone()["c"] == 0:
        now = datetime.now().isoformat(timespec="seconds")
        for city in CITIES:
            for kw in KEYWORDS:
                slug = re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")
                slug = f"{slug}-{re.sub(r'[^a-z0-9]+','-',city.lower()).strip('-')}"
                title = kw.capitalize()
                meta_title = f"{title} — заказать в {city} | Мастерская мебели"
                meta_desc = f"{title}. Изготовление на заказ в {city}. Замер, дизайн, монтаж. Гарантия."
                body = (
                    f"<h1>{title}</h1>"
                    f"<p>Изготовим {kw} в {city}. Собственное производство, "
                    f"замер, 3D-проект, монтаж под ключ.</p>"
                )
                cur.execute(
                    "INSERT OR IGNORE INTO seo_pages (city, district, keyword, slug, title, meta_title, meta_description, body, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (city, "", kw, slug, title, meta_title, meta_desc, body, now)
                )
        for d in ROSTOV_DISTRICTS:
            kw = f"кухни на заказ ростов {d.lower()} район"
            slug = f"kuhni-na-zakaz-rostov-{re.sub(r'[^a-z0-9]+','-',d.lower()).strip('-')}"
            cur.execute(
                "INSERT OR IGNORE INTO seo_pages (city, district, keyword, slug, title, meta_title, meta_description, body, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                ("Ростов-на-Дону", d, kw, slug, kw.capitalize(),
                 f"{kw} — заказать | Мастерская мебели",
                 f"{kw}. Собственное производство, замер, монтаж. Гарантия.",
                 f"<h1>{kw.capitalize()}</h1><p>Работаем в {d} районе Ростова-на-Дону.</p>",
                 now)
            )
        db.commit()

    db.close()

# ---------- Утилиты ----------
def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def log_action(action, details=""):
    db = get_db()
    db.execute(
        "INSERT INTO audit_log (user_id, login, action, details, created_at) VALUES (?,?,?,?,?)",
        (session.get("user_id"), session.get("login", ""), action, details, now_iso())
    )
    db.commit()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(*roles):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return deco

def save_upload(file_storage, kind="photo"):
    if not file_storage or not file_storage.filename:
        return None
    original = file_storage.filename
    safe = secure_filename(original)
    name = f"{secrets.token_hex(8)}_{safe}"
    path = os.path.join(UPLOAD_DIR, name)
    file_storage.save(path)
    return name, original

def make_lead_number():
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS c FROM leads").fetchone()
    return f"Z-{datetime.now().strftime('%Y%m')}-{row['c']+1:04d}"

def export_rows(rows, headers):
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(headers)
    for r in rows:
        w.writerow([r[h] if h in r.keys() else "" for h in headers])
    return out.getvalue()

# ---------- Главная и публичный сайт ----------
BASE_HEAD = """
<!doctype html><html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title or "Мебель на заказ — Азов, Ростов-на-Дону, Батайск" }}</title>
<meta name="description" content="{{ description or 'Кухни, шкафы, гардеробные на заказ. Азов, Ростов-на-Дону, Батайск.' }}">
<meta property="og:title" content="{{ title or 'Мебель на заказ' }}">
<meta property="og:description" content="{{ description or 'Кухни на заказ в Азове, Ростове-на-Дону, Батайске.' }}">
<meta property="og:image" content="{{ og_image or '/static/og.jpg' }}">
<meta property="og:type" content="website">
<link rel="canonical" href="{{ canonical or request.url }}">
{{ jsonld|safe if jsonld else '' }}
<script type="text/javascript">
  (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
  m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
  (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
  ym(00000000, "init", {clickmap:true, trackLinks:true, accurateTrackBounce:true});
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-XXXXXXX');</script>
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:0;color:#222;background:#fff}
header{background:#1f2937;color:#fff;padding:14px 20px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header a{color:#fff;text-decoration:none;margin-right:12px}
main{max-width:1100px;margin:0 auto;padding:20px}
.card{border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:12px 0;background:#fafafa}
button,.btn{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:10px 16px;cursor:pointer;text-decoration:none;display:inline-block}
input,textarea,select{padding:9px;border:1px solid #cbd5e1;border-radius:8px;width:100%;box-sizing:border-box;margin:4px 0}
label{font-size:13px;color:#475569}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.sticky{position:fixed;bottom:14px;right:14px;z-index:50;display:flex;gap:8px}
.sticky a{background:#111827;color:#fff;padding:12px 16px;border-radius:999px;text-decoration:none}
footer{background:#f1f5f9;padding:20px;text-align:center;color:#475569;margin-top:40px}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #e5e7eb;padding:6px;text-align:left}
</style>
</head><body>
<header>
  <b><a href="/">Мебель на заказ</a></b>
  <a href="/catalog/kitchens">Кухни</a>
  <a href="/catalog/wardrobes">Шкафы</a>
  <a href="/catalog/dressing">Гардеробные</a>
  <a href="/catalog/hallways">Прихожие</a>
  <a href="/catalog/living">Гостиные</a>
  <a href="/catalog/bath">Ванные</a>
  <a href="/catalog/kids">Детские</a>
  <a href="/catalog/office">Офис</a>
  <a href="/portfolio">Портфолио</a>
  <a href="/faq">FAQ</a>
  <a href="/client">Личный кабинет</a>
  <a href="/admin">Админка</a>
</header>
<main>
"""

BASE_FOOT = """
</main>
<div class="sticky">
  <a href="tel:+70000000000">📞 Позвонить</a>
  <a href="#lead">✉️ Заявка</a>
</div>
<footer>
  Азов · Ростов-на-Дону · Батайск · © {{ year }}
  <div><a href="/privacy">Политика конфиденциальности</a> · <a href="/consent">Согласие на обработку ПДн</a> · <a href="/terms">Пользовательское соглашение</a></div>
</footer>
<script>
  // exit-intent: показать форму заявки
  let shown=false;
  document.addEventListener('mouseleave',function(e){
    if(e.clientY<10 && !shown){shown=true;document.getElementById('lead')?.scrollIntoView({behavior:'smooth'});}
  });
  // предупреждение о несохранённых изменениях в админке
  window.__dirty=false;
  document.addEventListener('input',function(e){if(e.target.closest('form[data-dirty]'))window.__dirty=true;});
  window.addEventListener('beforeunload',function(e){if(window.__dirty){e.preventDefault();e.returnValue='';}});
</script>
</body></html>
"""

def render_page(title, description="", body="", canonical=None, og_image=None, jsonld=None):
    html = BASE_HEAD + body + BASE_FOOT
    return render_template_string(
        html, title=title, description=description, canonical=canonical,
        og_image=og_image, jsonld=jsonld, year=datetime.now().year
    )

@app.route("/")
def index():
    db = get_db()
    blocks = db.execute("SELECT * FROM homepage_blocks WHERE hidden=0 ORDER BY sort_order, id").fetchall()
    portfolio = db.execute("SELECT * FROM portfolio WHERE published=1 ORDER BY id DESC LIMIT 6").fetchall()
    reviews = db.execute("SELECT * FROM reviews WHERE approved=1 ORDER BY id DESC LIMIT 6").fetchall()
    body = []
    for b in blocks:
        body.append(f'<section class="card"><h2>{b["title"]}</h2><div>{b["body"]}</div></section>')
    if not blocks:
        body.append('<section class="card"><h1>Кухни и мебель на заказ в Азове, Ростове-на-Дону и Батайске</h1>'
                    '<p>Собственное производство, замер, дизайн, монтаж. Гарантия.</p></section>')
    body.append('<h2>Портфолио</h2><div class="grid">')
    for p in portfolio:
        body.append(f'<div class="card"><h3>{p["title"]}</h3><p>{p["category"]} · {p["city"]}</p>'
                    f'<a class="btn" href="/portfolio/{p["id"]}">Смотреть</a></div>')
    body.append('</div>')
    body.append('<h2>Отзывы</h2><div class="grid">')
    for r in reviews:
        body.append(f'<div class="card"><b>{r["author"]}</b> · {r["city"]}<p>{r["text"]}</p></div>')
    body.append('</div>')
    body.append(LEAD_FORM_HTML)
    return render_page("Мебель на заказ — Азов, Ростов-на-Дону, Батайск",
                       "Кухни, шкафы, гардеробные на заказ. Замер, дизайн, монтаж.",
                       "".join(body))

LEAD_FORM_HTML = """
<section class="card" id="lead">
<h2>Оставить заявку</h2>
<form method="post" action="/lead" enctype="multipart/form-data">
  <div class="grid">
    <div><label>Имя</label><input name="name" required></div>
    <div><label>Телефон</label><input name="phone" required placeholder="+7 (___) ___-__-__" oninput="this.value=this.value.replace(/[^0-9+()\\- ]/g,'')"></div>
    <div><label>Email</label><input name="email" type="email"></div>
    <div><label>Город</label>
      <select name="city" id="citySelect">
        <option>Азов</option><option selected>Ростов-на-Дону</option><option>Батайск</option>
      </select>
    </div>
    <div><label>Мессенджер</label>
      <select name="messenger"><option>Telegram</option><option>WhatsApp</option><option>VK</option><option>Звонок</option></select>
    </div>
    <div><label>Удобное время звонка</label><input name="call_time" placeholder="например, 10:00–13:00"></div>
    <div><label>Тип мебели</label>
      <select name="furniture_type">
        <option>Кухня</option><option>Шкаф</option><option>Гардеробная</option>
        <option>Прихожая</option><option>Гостиная</option><option>Ванная</option>
        <option>Детская</option><option>Офис</option>
      </select>
    </div>
    <div><label>Пожелания</label><textarea name="wish"></textarea></div>
    <div><label>Фото помещения</label><input type="file" name="photo" accept="image/*" multiple></div>
    <div><label>Эскиз</label><input type="file" name="sketch" accept="image/*,.pdf"></div>
  </div>
  <label><input type="checkbox" required> Согласен на обработку персональных данных</label>
  <input type="text" name="hp" style="display:none">
  <button type="submit">Отправить заявку</button>
  <a class="btn" href="/calculator">Рассчитать стоимость</a>
  <a class="btn" href="/materials">Каталог материалов</a>
  <a class="btn" href="/consult">Консультация дизайнера</a>
</form>
</section>
<script>
fetch('/api/geo').then(r=>r.json()).then(d=>{if(d.city){document.getElementById('citySelect').value=d.city;}}).catch(()=>{});
</script>
"""

@app.route("/api/geo")
def api_geo():
    # упрощённо: определяем город по заголовку или по IP-заглушке
    return jsonify({"city": "Ростов-на-Дону"})

@app.route("/lead", methods=["POST"])
def lead_create():
    if request.form.get("hp"):
        return redirect(url_for("thank_you"))
    db = get_db()
    number = make_lead_number()
    cur = db.execute(
        "INSERT INTO leads (number, name, phone, email, city, messenger, call_time, furniture_type, source, status, priority, notes, wish, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (number, request.form.get("name"), request.form.get("phone"), request.form.get("email"),
         request.form.get("city"), request.form.get("messenger"), request.form.get("call_time"),
         request.form.get("furniture_type"), "сайт", "новая", "обычный", "", request.form.get("wish"),
         now_iso(), now_iso())
    )
    lead_id = cur.lastrowid
    for f in request.files.getlist("photo"):
        saved = save_upload(f, "photo")
        if saved:
            db.execute("INSERT INTO lead_files (lead_id, filename, original, kind, created_at) VALUES (?,?,?,?,?)",
                       (lead_id, saved[0], saved[1], "photo", now_iso()))
    for f in request.files.getlist("sketch"):
        saved = save_upload(f, "sketch")
        if saved:
            db.execute("INSERT INTO lead_files (lead_id, filename, original, kind, created_at) VALUES (?,?,?,?,?)",
                       (lead_id, saved[0], saved[1], "sketch", now_iso()))
    db.commit()
    log_action("lead_create", f"{number} {request.form.get('phone')}")
    return redirect(url_for("thank_you"))

@app.route("/thank-you")
def thank_you():
    return render_page("Заявка отправлена", "Спасибо! Мы свяжемся с вами.",
                       "<div class='card'><h1>Спасибо!</h1><p>Заявка получена. Менеджер свяжется с вами.</p>"
                       "<a class='btn' href='/'>На главную</a></div>")

@app.route("/uploads/<path:filename>")
def uploaded(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ---------- Каталог и портфолио ----------
CATALOG = {
    "kitchens": "Кухни на заказ",
    "wardrobes": "Шкафы на заказ",
    "dressing": "Гардеробные на заказ",
    "hallways": "Прихожие на заказ",
    "living": "Гостиные на заказ",
    "bath": "Ванные на заказ",
    "kids": "Детские на заказ",
    "office": "Офисная мебель на заказ",
}

@app.route("/catalog/<slug>")
def catalog(slug):
    if slug not in CATALOG:
        abort(404)
    db = get_db()
    items = db.execute("SELECT * FROM portfolio WHERE published=1 AND category=? ORDER BY id DESC", (slug,)).fetchall()
    body = [f"<h1>{CATALOG[slug]}</h1>"]
    # фильтры
    body.append("""
    <form class="card" method="get">
      <div class="grid">
        <div><label>Стиль</label><input name="style" value="{{ request.args.get('style','') }}"></div>
        <div><label>Цвет фасадов</label><input name="color" value="{{ request.args.get('color','') }}"></div>
        <div><label>Материал корпуса</label><input name="material" value="{{ request.args.get('material','') }}"></div>
        <div><label>Столешница</label><input name="top" value="{{ request.args.get('top','') }}"></div>
        <div><label>Фурнитура</label><input name="fittings" value="{{ request.args.get('fittings','') }}"></div>
        <div><label>Площадь, м²</label><input name="area" value="{{ request.args.get('area','') }}"></div>
        <div><label>Цена от</label><input name="price_min" value="{{ request.args.get('price_min','') }}"></div>
        <div><label>Цена до</label><input name="price_max" value="{{ request.args.get('price_max','') }}"></div>
      </div>
      <button type="submit">Фильтровать</button>
    </form>
    """)
    body.append('<div class="grid">')
    for it in items:
        body.append(f'<div class="card"><h3>{it["title"]}</h3><p>{it["style"]} · {it["material"]} · {it["city"]}</p>'
                    f'<p>Срок: {it["term"]}</p><a class="btn" href="/portfolio/{it["id"]}">Подробнее</a></div>')
    body.append('</div>')
    body.append(LEAD_FORM_HTML)
    return render_page(CATALOG[slug], CATALOG[slug] + " в Азове, Ростове-на-Дону, Батайске", "".join(body))

@app.route("/portfolio")
def portfolio_list():
    db = get_db()
    items = db.execute("SELECT * FROM portfolio WHERE published=1 ORDER BY id DESC").fetchall()
    body = ["<h1>Портфолио</h1>", '<div class="grid">']
    for it in items:
        body.append(f'<div class="card"><h3>{it["title"]}</h3><p>{it["category"]} · {it["city"]}</p>'
                    f'<a class="btn" href="/portfolio/{it["id"]}">Смотреть</a></div>')
    body.append('</div>')
    body.append(LEAD_FORM_HTML)
    return render_page("Портфолио", "Выполненные проекты мебели на заказ", "".join(body))

@app.route("/portfolio/<int:pid>")
def portfolio_item(pid):
    db = get_db()
    it = db.execute("SELECT * FROM portfolio WHERE id=? AND published=1", (pid,)).fetchone()
    if not it:
        abort(404)
    body = f"""
    <article class="card">
      <h1>{it['title']}</h1>
      <p><b>Категория:</b> {it['category']} · <b>Стиль:</b> {it['style']} · <b>Материал:</b> {it['material']}</p>
      <p><b>Город:</b> {it['city']} · <b>Срок:</b> {it['term']}</p>
      <p>{it['description'] or ''}</p>
      <div class="grid">
        <div><h3>До</h3>{'<img src="/uploads/'+it['before_photo']+'" style="max-width:100%">' if it['before_photo'] else ''}</div>
        <div><h3>После</h3>{'<img src="/uploads/'+it['after_photo']+'" style="max-width:100%">' if it['after_photo'] else ''}</div>
      </div>
    </article>
    """
    body += LEAD_FORM_HTML
    return render_page(it["title"], it["description"] or it["title"], body)

# ---------- FAQ и статьи ----------
@app.route("/faq")
def faq_page():
    db = get_db()
    items = db.execute("SELECT * FROM faq WHERE published=1").fetchall()
    body = ["<h1>Часто задаваемые вопросы</h1>"]
    for it in items:
        body.append(f'<div class="card"><h3>{it["question"]}</h3><p>{it["answer"]}</p></div>')
    body.append(LEAD_FORM_HTML)
    return render_page("FAQ", "Ответы на частые вопросы", "".join(body))

ARTICLES = {
    "materials": "Выбор материала фасадов",
    "tabletop": "Выбор столешницы",
    "fittings": "Выбор фурнитуры",
    "measure": "Правильные замеры помещения",
    "prepare": "Подготовка помещения к монтажу",
    "height": "Высота рабочей поверхности",
    "gloss": "Матовые и глянцевые фасады",
    "mdf": "МДФ, ЛДСП и массив",
    "color": "Выбор цвета кухни",
    "ergonomics": "Эргономика кухни",
    "storage": "Организация хранения",
    "builtin": "Встроенная техника",
    "sockets": "Размещение розеток",
    "light": "Выбор освещения",
    "triangle": "Рабочий треугольник кухни",
    "check-order": "Чек-лист перед заказом кухни",
    "check-measure": "Чек-лист подготовки к замеру",
    "check-accept": "Чек-лист приёмки мебели",
    "glossary": "Словарь мебельных терминов",
}

@app.route("/article/<slug>")
def article(slug):
    if slug not in ARTICLES:
        abort(404)
    title = ARTICLES[slug]
    body = f"<article class='card'><h1>{title}</h1><p>Полезная статья для клиентов.</p></article>"
    body += LEAD_FORM_HTML
    return render_page(title, title + " — полезный контент", body)

@app.route("/materials")
def materials():
    return article("materials")

@app.route("/consult")
def consult():
    body = "<div class='card'><h1>Консультация дизайнера</h1><p>Оставьте заявку, и дизайнер свяжется с вами.</p></div>"
    body += LEAD_FORM_HTML
    return render_page("Консультация дизайнера", "Заказать консультацию дизайнера", body)

@app.route("/calculator")
def calculator():
    body = """
    <section class="card">
      <h1>Калькулятор предварительной стоимости</h1>
      <form onsubmit="event.preventDefault();calc();">
        <div class="grid">
          <div><label>Форма кухни</label>
            <select id="form"><option value="1">Прямая</option><option value="1.2">Угловая</option><option value="1.4">П-образная</option></select>
          </div>
          <div><label>Длина, м</label><input id="len" type="number" value="3" step="0.1"></div>
          <div><label>Количество шкафов</label><input id="shk" type="number" value="6"></div>
          <div><label>Тип открывания</label>
            <select id="open"><option value="1">Распашные</option><option value="1.15">Подъёмные</option></select>
          </div>
        </div>
        <button type="submit">Рассчитать</button>
      </form>
      <h3 id="result"></h3>
      <div id="preview" class="card" style="display:none">Предварительная визуализация выбранного варианта</div>
    </section>
    <section class="card">
      <h2>Конструктор цвета</h2>
      <div class="grid">
        <div><label>Цвет фасада</label><input type="color" id="facade" value="#ffffff" oninput="preview()"></div>
        <div><label>Цвет столешницы</label><input type="color" id="top" value="#888888" oninput="preview()"></div>
        <div><label>Ручки</label><select id="handle"><option>Скрытые</option><option>Рейлинговые</option><option>Кнопки</option></select></div>
        <div><label>Освещение</label><select id="light"><option>Тёплое</option><option>Холодное</option><option>Нейтральное</option></select></div>
      </div>
    </section>
    <script>
    function calc(){
      const f=parseFloat(document.getElementById('form').value);
      const l=parseFloat(document.getElementById('len').value);
      const s=parseFloat(document.getElementById('shk').value);
      const o=parseFloat(document.getElementById('open').value);
      const price=Math.round((30000*l + 8000*s) * f * o);
      document.getElementById('result').textContent='Ориентировочная стоимость: '+price.toLocaleString('ru-RU')+' ₽';
      document.getElementById('preview').style.display='block';
    }
    function preview(){document.getElementById('preview').style.display='block';}
    </script>
    """
    body += LEAD_FORM_HTML
    return render_page("Калькулятор стоимости кухни", "Предварительный расчёт стоимости кухни", body)

# ---------- Личный кабинет клиента ----------
@app.route("/client", methods=["GET", "POST"])
def client_cabinet():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        session["client_phone"] = phone
        return redirect(url_for("client_cabinet"))
    phone = session.get("client_phone")
    body = ["<h1>Личный кабинет клиента</h1>"]
    if not phone:
        body.append("""
        <div class="card"><form method="post">
          <label>Вход по номеру телефона</label>
          <input name="phone" required placeholder="+7...">
          <button type="submit">Войти</button>
        </form></div>
        """)
    else:
        db = get_db()
        leads = db.execute("SELECT * FROM leads WHERE phone=? ORDER BY id DESC", (phone,)).fetchall()
        body.append(f"<p>Телефон: {phone} · <a href='/client/logout'>Выйти</a></p>")
        for l in leads:
            body.append(f"<div class='card'><h3>Заявка {l['number']}</h3>"
                        f"<p>Статус: {l['status']} · Срок: {l['deadline'] or '—'}</p>"
                        f"<p>Проект: <a href='/status/{l['number']}'>этапы изготовления</a></p>"
                        f"<a class='btn' href='/warranty?lead={l['number']}'>Гарантийное обслуживание</a> "
                        f"<a class='btn' href='/defect?lead={l['number']}'>Сообщить о недостатке</a> "
                        f"<a class='btn' href='/adjust?lead={l['number']}'>Регулировка фасадов</a> "
                        f"<a class='btn' href='/extra-shelf?lead={l['number']}'>Доп. полка</a> "
                        f"<a class='btn' href='/extra-facade?lead={l['number']}'>Новый фасад</a> "
                        f"<a class='btn' href='/extra-fittings?lead={l['number']}'>Доп. фурнитура</a>"
                        f"</div>")
    return render_page("Личный кабинет клиента", "Статус заказа и документы", "".join(body))

@app.route("/client/logout")
def client_logout():
    session.pop("client_phone", None)
    return redirect(url_for("client_cabinet"))

@app.route("/status/<number>")
def order_status(number):
    db = get_db()
    lead = db.execute("SELECT * FROM leads WHERE number=?", (number,)).fetchone()
    if not lead:
        abort(404)
    events = db.execute("SELECT * FROM calendar_events WHERE project_id IN (SELECT id FROM projects WHERE lead_id=?) ORDER BY date", (lead["id"],)).fetchall()
    body = [f"<h1>Статус заказа {number}</h1>"]
    body.append(f"<div class='card'><p>Текущий статус: <b>{lead['status']}</b></p>")
    body.append("<h3>Этапы изготовления</h3><ul>")
    for e in events:
        body.append(f"<li>{e['date']} — {e['kind']} ({e['assignee'] or '—'})</li>")
    body.append("</ul></div>")
    return render_page(f"Статус заказа {number}", "Этапы изготовления", "".join(body))

SERVICE_FORMS = {
    "warranty": "Гарантийное обслуживание",
    "defect": "Сообщение о недостатке",
    "adjust": "Заказ регулировки фасадов",
    "extra-shelf": "Заказ дополнительной полки",
    "extra-facade": "Заказ нового фасада",
    "extra-fittings": "Заказ дополнительной фурнитуры",
}

@app.route("/<service>", methods=["GET", "POST"])
def service_form(service):
    if service not in SERVICE_FORMS:
        abort(404)
    if request.method == "POST":
        db = get_db()
        log_action("service_request", f"{service}: {request.form.get('lead','')} {request.form.get('text','')}")
        return redirect(url_for("thank_you"))
    body = f"""
    <div class="card"><h1>{SERVICE_FORMS[service]}</h1>
    <form method="post" data-dirty>
      <label>Номер заказа</label><input name="lead" value="{request.args.get('lead','')}">
      <label>Описание</label><textarea name="text"></textarea>
      <button type="submit">Отправить</button>
    </form></div>
    """
    return render_page(SERVICE_FORMS[service], SERVICE_FORMS[service], body)

# ---------- SEO-страницы ----------
@app.route("/seo/<slug>")
def seo_page(slug):
    db = get_db()
    page = db.execute("SELECT * FROM seo_pages WHERE slug=?", (slug,)).fetchone()
    if not page:
        abort(404)
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": "Мебель на заказ",
        "areaServed": page["city"],
        "description": page["meta_description"],
        "address": {"@type": "PostalAddress", "addressLocality": page["city"], "addressCountry": "RU"}
    }, ensure_ascii=False)
    body = f"<article class='card'>{page['body']}</article>"
    body += LEAD_FORM_HTML
    return render_page(page["meta_title"], page["meta_description"], body, jsonld=jsonld)

@app.route("/cities")
def cities_index():
    body = ["<h1>Города и районы</h1>"]
    for c in CITIES:
        body.append(f"<div class='card'><h2>{c}</h2>")
        rows = get_db().execute("SELECT slug, keyword FROM seo_pages WHERE city=? ORDER BY keyword", (c,)).fetchall()
        for r in rows:
            body.append(f"<a href='/seo/{r['slug']}'>{r['keyword']}</a><br>")
        body.append("</div>")
    body.append("<div class='card'><h2>Районы Ростова-на-Дону</h2>")
    for d in ROSTOV_DISTRICTS:
        rows = get_db().execute("SELECT slug, keyword FROM seo_pages WHERE district=?", (d,)).fetchall()
        for r in rows:
            body.append(f"<a href='/seo/{r['slug']}'>{r['keyword']}</a><br>")
    body.append("</div>")
    return render_page("Города и районы", "SEO-страницы по городам и районам", "".join(body))

@app.route("/sitemap.xml")
def sitemap():
    db = get_db()
    urls = []
    for row in db.execute("SELECT slug FROM seo_pages").fetchall():
        urls.append(url_for("seo_page", slug=row["slug"], _external=True))
    for row in db.execute("SELECT id FROM portfolio WHERE published=1").fetchall():
        urls.append(url_for("portfolio_item", pid=row["id"], _external=True))
    for slug in CATALOG:
        urls.append(url_for("catalog", slug=slug, _external=True))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"<url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    xml.append("</urlset>")
    return make_response("\n".join(xml), 200, {"Content-Type": "application/xml"})

@app.route("/robots.txt")
def robots():
    return make_response(
        "User-agent: *\nAllow: /\nSitemap: " + url_for("sitemap", _external=True),
        200, {"Content-Type": "text/plain"}
    )

# ---------- Админка ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE login=? AND active=1", (login,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["login"] = user["login"]
            session["role"] = user["role"]
            db.execute("INSERT INTO audit_log (user_id, login, action, details, created_at) VALUES (?,?,?,?,?)",
                       (user["id"], user["login"], "login", "", now_iso()))
            db.commit()
            return redirect(url_for("admin_index"))
        error = "Неверный логин или пароль"
    return render_page("Вход в админку", "Авторизация", f"""
    <div class="card" style="max-width:420px;margin:40px auto">
      <h1>Вход в админку</h1>
      {f'<p style="color:red">{error}</p>' if error else ''}
      <form method="post">
        <label>Логин</label><input name="login" required>
        <label>Пароль</label><input name="password" type="password" required>
        <button type="submit">Войти</button>
      </form>
    </div>""")

@app.route("/admin/logout")
def admin_logout():
    log_action("logout", "")
    session.clear()
    return redirect(url_for("admin_login"))

ADMIN_HEAD = """
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Админка</title>
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f8fafc;color:#0f172a}
header{background:#0f172a;color:#fff;padding:12px 18px;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
header a{color:#fff;text-decoration:none}
main{max-width:1200px;margin:0 auto;padding:18px}
.card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin:12px 0}
input,textarea,select{padding:8px;border:1px solid #cbd5e1;border-radius:6px;width:100%;box-sizing:border-box}
button,.btn{background:#2563eb;color:#fff;border:0;border-radius:6px;padding:8px 12px;cursor:pointer;text-decoration:none;display:inline-block}
table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #e2e8f0;padding:6px;text-align:left;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.badge{background:#e0f2fe;color:#0369a1;border-radius:999px;padding:2px 8px;font-size:12px}
</style></head><body>
<header>
  <b><a href="/admin">Админка</a></b>
  <a href="/admin/leads">Заявки</a>
  <a href="/admin/projects">Проекты</a>
  <a href="/admin/calendar">Календарь</a>
  <a href="/admin/warehouse">Склад</a>
  <a href="/admin/portfolio">Портфолио</a>
  <a href="/admin/reviews">Отзывы</a>
  <a href="/admin/faq">FAQ</a>
  <a href="/admin/pages">Страницы</a>
  <a href="/admin/blocks">Блоки главной</a>
  <a href="/admin/seo">SEO</a>
  <a href="/admin/reports">Отчёты</a>
  <a href="/admin/users">Пользователи</a>
  <a href="/admin/audit">Журнал</a>
  <a href="/" target="_blank">Сайт</a>
  <span style="margin-left:auto">{{ session.login }} ({{ session.role }})</span>
  <a href="/admin/logout">Выйти</a>
</header>
<main>
"""

ADMIN_FOOT = "</main></body></html>"

def admin_page(title, body):
    return render_template_string(ADMIN_HEAD + body + ADMIN_FOOT)

@app.route("/admin")
@login_required
def admin_index():
    db = get_db()
    leads = db.execute("SELECT COUNT(*) c FROM leads").fetchone()["c"]
    projects = db.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
    new_leads = db.execute("SELECT COUNT(*) c FROM leads WHERE status='новая'").fetchone()["c"]
    body = f"""
    <h1>Дашборд руководителя</h1>
    <div class="grid">
      <div class="card"><h3>Заявки</h3><p>{leads}</p></div>
      <div class="card"><h3>Новые</h3><p>{new_leads}</p></div>
      <div class="card"><h3>Проекты</h3><p>{projects}</p></div>
    </div>
    <div class="card">
      <h3>Ключевые показатели</h3>
      <p>Конверсия сайта, средний чек, длительность сделки, повторные клиенты, причины отказа — в разделе «Отчёты».</p>
    </div>
    """
    return admin_page("Админка", body)

# --- заявки ---
@app.route("/admin/leads")
@login_required
def admin_leads():
    db = get_db()
    q = "SELECT * FROM leads WHERE 1=1"
    args = []
    for field in ["city", "furniture_type", "status", "source"]:
        val = request.args.get(field)
        if val:
            q += f" AND {field}=?"
            args.append(val)
    if request.args.get("budget"):
        q += " AND notes LIKE ?"
        args.append(f"%{request.args['budget']}%")
    if request.args.get("date"):
        q += " AND substr(created_at,1,10)=?"
        args.append(request.args["date"])
    q += " ORDER BY id DESC"
    rows = db.execute(q, args).fetchall()
    body = ["<h1>Заявки</h1>",
            """<form class="card" method="get"><div class="grid">
            <div><label>Город</label><input name="city" value="{{request.args.get('city','')}}"></div>
            <div><label>Тип мебели</label><input name="furniture_type" value="{{request.args.get('furniture_type','')}}"></div>
            <div><label>Статус</label><input name="status" value="{{request.args.get('status','')}}"></div>
            <div><label>Источник</label><input name="source" value="{{request.args.get('source','')}}"></div>
            <div><label>Бюджет</label><input name="budget" value="{{request.args.get('budget','')}}"></div>
            <div><label>Дата</label><input name="date" value="{{request.args.get('date','')}}"></div>
            </div><button>Фильтр</button></form>""",
            "<table><tr><th>ID</th><th>Номер</th><th>Имя</th><th>Телефон</th><th>Город</th><th>Тип</th><th>Статус</th><th>Ответственный</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['number']}</td><td>{r['name']}</td><td>{r['phone']}</td>"
                    f"<td>{r['city']}</td><td>{r['furniture_type']}</td><td>{r['status']}</td>"
                    f"<td>{r['responsible_id'] or '—'}</td>"
                    f"<td><a href='/admin/leads/{r['id']}'>Открыть</a></td></tr>")
    body.append("</table>")
    body.append('<a class="btn" href="/admin/leads/export.csv">Экспорт CSV</a>')
    return admin_page("Заявки", "".join(body))

@app.route("/admin/leads/export.csv")
@login_required
def admin_leads_export():
    rows = get_db().execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    headers = ["id", "number", "name", "phone", "email", "city", "furniture_type", "status", "source", "created_at"]
    out = export_rows(rows, headers)
    return make_response(out, 200, {"Content-Type": "text/csv; charset=utf-8",
                                    "Content-Disposition": "attachment; filename=leads.csv"})

@app.route("/admin/leads/<int:lid>", methods=["GET", "POST"])
@login_required
def admin_lead(lid):
    db = get_db()
    lead = db.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone()
    if not lead:
        abort(404)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update":
            db.execute("""UPDATE leads SET status=?, priority=?, responsible_id=?, notes=?, wish=?, deadline=?,
                          no_answer=?, repeat_client=?, updated_at=? WHERE id=?""",
                       (request.form.get("status"), request.form.get("priority"),
                        request.form.get("responsible_id") or None,
                        request.form.get("notes"), request.form.get("wish"),
                        request.form.get("deadline"),
                        1 if request.form.get("no_answer") else 0,
                        1 if request.form.get("repeat_client") else 0,
                        now_iso(), lid))
            log_action("lead_update", f"{lead['number']}")
        elif action == "note":
            db.execute("INSERT INTO lead_notes (lead_id, user_id, text, created_at) VALUES (?,?,?,?)",
                       (lid, session["user_id"], request.form.get("text"), now_iso()))
        elif action == "call":
            db.execute("INSERT INTO lead_calls (lead_id, user_id, channel, result, created_at) VALUES (?,?,?,?,?)",
                       (lid, session["user_id"], request.form.get("channel"), request.form.get("result"), now_iso()))
        elif action == "mass_status":
            pass
        elif action == "delete_pd":
            db.execute("UPDATE leads SET name='', phone='', email='', notes='', wish='' WHERE id=?", (lid,))
            log_action("lead_pd_delete", f"{lead['number']}")
        db.commit()
        return redirect(url_for("admin_lead", lid=lid))
    responsible = db.execute("SELECT id, login, full_name FROM users WHERE active=1").fetchall()
    files = db.execute("SELECT * FROM lead_files WHERE lead_id=?", (lid,)).fetchall()
    notes = db.execute("SELECT * FROM lead_notes WHERE lead_id=? ORDER BY id DESC", (lid,)).fetchall()
    calls = db.execute("SELECT * FROM lead_calls WHERE lead_id=? ORDER BY id DESC", (lid,)).fetchall()
    body = [f"<h1>Заявка {lead['number']}</h1>",
            f"""<div class="card">
            <form method="post" data-dirty>
              <input type="hidden" name="action" value="update">
              <div class="grid">
                <div><label>Статус</label><select name="status">
                  {''.join(f'<option {"selected" if lead["status"]==s else ""}>{s}</option>' for s in ["новая","в работе","замер","расчёт","договор","завершена"])}
                </select></div>
                <div><label>Приоритет</label><select name="priority">
                  {''.join(f'<option {"selected" if lead["priority"]==p else ""}>{p}</option>' for p in ["низкий","обычный","высокий"])}
                </select></div>
                <div><label>Ответственный</label><select name="responsible_id">
                  <option value="">—</option>
                  {''.join(f'<option value="{u["id"]}" {"selected" if lead["responsible_id"]==u["id"] else ""}>{u["login"]}</option>' for u in responsible)}
                </select></div>
                <div><label>Срок</label><input name="deadline" value="{lead['deadline'] or ''}"></div>
              </div>
              <label>Заметки</label><textarea name="notes">{lead['notes'] or ''}</textarea>
              <label>Пожелания</label><textarea name="wish">{lead['wish'] or ''}</textarea>
              <label><input type="checkbox" name="no_answer" {"checked" if lead["no_answer"] else ""}> Клиент не отвечает</label>
              <label><input type="checkbox" name="repeat_client" {"checked" if lead["repeat_client"] else ""}> Повторный клиент</label>
              <button type="submit">Сохранить</button>
            </form></div>""",
            f"""<div class="card"><h3>Файлы и фото помещения</h3>
            {''.join(f'<div><a href="/uploads/{f["filename"]}" target="_blank">{f["original"]}</a> ({f["kind"]})</div>' for f in files)}
            <form method="post" enctype="multipart/form-data">
              <input type="file" name="photo" multiple>
              <input type="file" name="sketch" multiple>
              <button formaction="/admin/leads/{lid}/upload" formmethod="post">Загрузить</button>
            </form></div>""",
            f"""<div class="card"><h3>Внутренние заметки</h3>
            <form method="post"><input type="hidden" name="action" value="note">
            <textarea name="text"></textarea><button>Добавить</button></form>
            {''.join(f'<p>{n["created_at"]}: {n["text"]}</p>' for n in notes)}</div>""",
            f"""<div class="card"><h3>История звонков и сообщений</h3>
            <form method="post"><input type="hidden" name="action" value="call">
            <select name="channel"><option>Звонок</option><option>Telegram</option><option>WhatsApp</option><option>VK</option></select>
            <input name="result" placeholder="Результат"><button>Добавить</button></form>
            {''.join(f'<p>{c["created_at"]} {c["channel"]}: {c["result"]}</p>' for c in calls)}</div>""",
            f"""<div class="card"><h3>Действия</h3>
            <form method="post"><input type="hidden" name="action" value="delete_pd">
            <button>Удалить персональные данные</button></form>
            <a class="btn" href="/admin/projects/new?lead_id={lid}">Создать проект</a>
            <form method="post"><input type="hidden" name="action" value="mass_status">
            <input name="status" placeholder="Новый статус для массовой смены">
            <button>Сменить статус</button></form></div>""",
            f"""<div class="card"><h3>Шаблоны ответов</h3>
            <textarea>Здравствуйте! Спасибо за заявку. Когда вам удобно принять замерщика?</textarea>
            <button onclick="navigator.clipboard.writeText(this.previousElementSibling.value)">Копировать</button>
            <button onclick="navigator.clipboard.writeText('{lead['phone']}')">Копировать контакты</button></div>"""
            ]
    return admin_page("Заявка", "".join(body))

@app.route("/admin/leads/<int:lid>/upload", methods=["POST"])
@login_required
def admin_lead_upload(lid):
    db = get_db()
    for key, kind in [("photo", "photo"), ("sketch", "sketch")]:
        for f in request.files.getlist(key):
            saved = save_upload(f, kind)
            if saved:
                db.execute("INSERT INTO lead_files (lead_id, filename, original, kind, created_at) VALUES (?,?,?,?,?)",
                           (lid, saved[0], saved[1], kind, now_iso()))
    db.commit()
    return redirect(url_for("admin_lead", lid=lid))

# --- проекты ---
@app.route("/admin/projects")
@login_required
def admin_projects():
    rows = get_db().execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    body = ["<h1>Проекты</h1>", "<table><tr><th>ID</th><th>Код</th><th>Название</th><th>Статус</th><th>Версия</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['code']}</td><td>{r['title']}</td><td>{r['status']}</td>"
                    f"<td>{r['version']}</td><td><a href='/admin/projects/{r['id']}'>Открыть</a></td></tr>")
    body.append("</table>")
    return admin_page("Проекты", "".join(body))

@app.route("/admin/projects/new", methods=["GET", "POST"])
@login_required
def admin_project_new():
    if request.method == "POST":
        db = get_db()
        code = f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db.execute("""INSERT INTO projects (lead_id, code, title, room_type, layout, sizes, materials, fittings,
                      components, price_materials, price_work, discount, delivery, assembly, total, version, status,
                      created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (request.form.get("lead_id") or None, code, request.form.get("title"),
                    request.form.get("room_type"), request.form.get("layout"), request.form.get("sizes"),
                    request.form.get("materials"), request.form.get("fittings"), request.form.get("components"),
                    float(request.form.get("price_materials") or 0), float(request.form.get("price_work") or 0),
                    float(request.form.get("discount") or 0), float(request.form.get("delivery") or 0),
                    float(request.form.get("assembly") or 0), 0, 1, "черновик", now_iso(), now_iso()))
        pid = db.execute("SELECT id FROM projects WHERE code=?", (code,)).fetchone()["id"]
        db.commit()
        return redirect(url_for("admin_project", pid=pid))
    body = """<div class="card"><h1>Новый проект</h1>
    <form method="post" data-dirty>
      <div class="grid">
        <div><label>Заявка ID</label><input name="lead_id" value="{{request.args.get('lead_id','')}}"></div>
        <div><label>Название</label><input name="title"></div>
        <div><label>Тип помещения</label><input name="room_type"></div>
        <div><label>Планировка</label><input name="layout"></div>
        <div><label>Размеры</label><input name="sizes"></div>
        <div><label>Материалы</label><input name="materials"></div>
        <div><label>Фурнитура</label><input name="fittings"></div>
        <div><label>Комплектующие</label><input name="components"></div>
        <div><label>Стоимость материалов</label><input name="price_materials" type="number"></div>
        <div><label>Стоимость работы</label><input name="price_work" type="number"></div>
        <div><label>Скидка</label><input name="discount" type="number"></div>
        <div><label>Доставка</label><input name="delivery" type="number"></div>
        <div><label>Сборка</label><input name="assembly" type="number"></div>
      </div>
      <button type="submit">Создать</button>
    </form></div>"""
    return admin_page("Новый проект", body)

@app.route("/admin/projects/<int:pid>", methods=["GET", "POST"])
@login_required
def admin_project(pid):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not p:
        abort(404)
    if request.method == "POST":
        if request.form.get("action") == "update":
            total = (float(request.form.get("price_materials") or 0) + float(request.form.get("price_work") or 0)
                     - float(request.form.get("discount") or 0) + float(request.form.get("delivery") or 0)
                     + float(request.form.get("assembly") or 0))
            db.execute("""UPDATE projects SET title=?, room_type=?, layout=?, sizes=?, materials=?, fittings=?,
                          components=?, price_materials=?, price_work=?, discount=?, delivery=?, assembly=?,
                          total=?, status=?, updated_at=? WHERE id=?""",
                       (request.form.get("title"), request.form.get("room_type"), request.form.get("layout"),
                        request.form.get("sizes"), request.form.get("materials"), request.form.get("fittings"),
                        request.form.get("components"), float(request.form.get("price_materials") or 0),
                        float(request.form.get("price_work") or 0), float(request.form.get("discount") or 0),
                        float(request.form.get("delivery") or 0), float(request.form.get("assembly") or 0),
                        total, request.form.get("status"), now_iso(), pid))
            snapshot = json.dumps(dict(p), ensure_ascii=False, default=str)
            db.execute("INSERT INTO project_versions (project_id, version, snapshot, created_at) VALUES (?,?,?,?)",
                       (pid, p["version"], snapshot, now_iso()))
            db.execute("UPDATE projects SET version=version+1 WHERE id=?", (pid,))
            log_action("project_update", f"{p['code']}")
        db.commit()
        return redirect(url_for("admin_project", pid=pid))
    versions = db.execute("SELECT * FROM project_versions WHERE project_id=? ORDER BY version DESC", (pid,)).fetchall()
    body = [f"<h1>Проект {p['code']}</h1>",
            f"""<div class="card"><form method="post" data-dirty>
            <input type="hidden" name="action" value="update">
            <div class="grid">
              <div><label>Название</label><input name="title" value="{p['title'] or ''}"></div>
              <div><label>Помещение</label><input name="room_type" value="{p['room_type'] or ''}"></div>
              <div><label>Планировка</label><input name="layout" value="{p['layout'] or ''}"></div>
              <div><label>Размеры</label><input name="sizes" value="{p['sizes'] or ''}"></div>
              <div><label>Материалы</label><input name="materials" value="{p['materials'] or ''}"></div>
              <div><label>Фурнитура</label><input name="fittings" value="{p['fittings'] or ''}"></div>
              <div><label>Комплектующие</label><input name="components" value="{p['components'] or ''}"></div>
              <div><label>Материалы, ₽</label><input name="price_materials" type="number" value="{p['price_materials']}"></div>
              <div><label>Работа, ₽</label><input name="price_work" type="number" value="{p['price_work']}"></div>
              <div><label>Скидка, ₽</label><input name="discount" type="number" value="{p['discount']}"></div>
              <div><label>Доставка, ₽</label><input name="delivery" type="number" value="{p['delivery']}"></div>
              <div><label>Сборка, ₽</label><input name="assembly" type="number" value="{p['assembly']}"></div>
              <div><label>Статус</label><input name="status" value="{p['status']}"></div>
            </div>
            <p>Итого: <b>{p['total']} ₽</b></p>
            <button type="submit">Сохранить</button>
            <a class="btn" href="/admin/projects/{pid}/pdf">PDF-смета</a>
            <a class="btn" href="/admin/projects/{pid}/contract">Договор</a>
            </form></div>""",
            f"<div class='card'><h3>Версии</h3>" +
            "".join(f"<div>v{v['version']} от {v['created_at']} <a href='/admin/projects/{pid}/version/{v['id']}'>Сравнить</a></div>" for v in versions) +
            "</div>",
            f"""<div class="card"><h3>Календарь</h3>
            <form method="post" action="/admin/calendar/add">
              <input type="hidden" name="project_id" value="{pid}">
              <select name="kind"><option>замер</option><option>доставка</option><option>монтаж</option></select>
              <input type="date" name="date">
              <input name="assignee" placeholder="Исполнитель">
              <button>Добавить</button>
            </form></div>"""]
    return admin_page("Проект", "".join(body))

@app.route("/admin/projects/<int:pid>/pdf")
@login_required
def project_pdf(pid):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not p:
        abort(404)
    text = (f"Смета {p['code']}\n\nНазвание: {p['title']}\nМатериалы: {p['price_materials']} ₽\n"
            f"Работа: {p['price_work']} ₽\nСкидка: {p['discount']} ₽\nДоставка: {p['delivery']} ₽\n"
            f"Сборка: {p['assembly']} ₽\nИтого: {p['total']} ₽\n")
    return make_response(text, 200, {"Content-Type": "text/plain; charset=utf-8",
                                    "Content-Disposition": f"attachment; filename=project-{p['code']}.txt"})

@app.route("/admin/projects/<int:pid>/contract")
@login_required
def project_contract(pid):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not p:
        abort(404)
    text = f"Договор по проекту {p['code']}\n\nЗаказчик: ____________________\nИсполнитель: ____________________\nСумма: {p['total']} ₽\n"
    return make_response(text, 200, {"Content-Type": "text/plain; charset=utf-8",
                                    "Content-Disposition": f"attachment; filename=contract-{p['code']}.txt"})

@app.route("/admin/projects/<int:pid>/version/<int:vid>")
@login_required
def project_version(pid, vid):
    db = get_db()
    v = db.execute("SELECT * FROM project_versions WHERE id=? AND project_id=?", (vid, pid)).fetchone()
    if not v:
        abort(404)
    cur = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    body = f"<div class='card'><h1>Сравнение версий</h1><h2>Текущая</h2><pre>{json.dumps(dict(cur), ensure_ascii=False, default=str, indent=2)}</pre>"
    body += f"<h2>Версия {v['version']}</h2><pre>{v['snapshot']}</pre></div>"
    return admin_page("Сравнение версий", body)

# --- календарь ---
@app.route("/admin/calendar")
@login_required
def admin_calendar():
    rows = get_db().execute("SELECT * FROM calendar_events ORDER BY date").fetchall()
    body = ["<h1>Календарь замеров, доставки и монтажа</h1>",
            "<table><tr><th>Дата</th><th>Тип</th><th>Проект</th><th>Исполнитель</th><th>Примечание</th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['date']}</td><td>{r['kind']}</td><td>{r['project_id']}</td><td>{r['assignee']}</td><td>{r['note']}</td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить событие</h3>
    <form method="post" action="/admin/calendar/add">
      <div class="grid">
        <div><label>Проект ID</label><input name="project_id"></div>
        <div><label>Тип</label><select name="kind"><option>замер</option><option>доставка</option><option>монтаж</option></select></div>
        <div><label>Дата</label><input type="date" name="date"></div>
        <div><label>Исполнитель</label><input name="assignee"></div>
        <div><label>Примечание</label><input name="note"></div>
      </div><button>Добавить</button></form></div>""")
    return admin_page("Календарь", "".join(body))

@app.route("/admin/calendar/add", methods=["POST"])
@login_required
def admin_calendar_add():
    db = get_db()
    db.execute("INSERT INTO calendar_events (project_id, kind, date, assignee, note, created_at) VALUES (?,?,?,?,?,?)",
               (request.form.get("project_id") or None, request.form.get("kind"), request.form.get("date"),
                request.form.get("assignee"), request.form.get("note"), now_iso()))
    db.commit()
    return redirect(url_for("admin_calendar"))

# --- склад ---
@app.route("/admin/warehouse", methods=["GET", "POST"])
@login_required
def admin_warehouse():
    db = get_db()
    if request.method == "POST":
        db.execute("""INSERT INTO warehouse (category, name, qty, unit, min_qty, supplier, price, updated_at)
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (request.form.get("category"), request.form.get("name"), float(request.form.get("qty") or 0),
                    request.form.get("unit"), float(request.form.get("min_qty") or 0),
                    request.form.get("supplier"), float(request.form.get("price") or 0), now_iso()))
        db.commit()
    rows = db.execute("SELECT * FROM warehouse ORDER BY category, name").fetchall()
    body = ["<h1>Склад</h1>",
            "<table><tr><th>Категория</th><th>Название</th><th>Остаток</th><th>Мин.</th><th>Поставщик</th><th>Цена</th><th></th></tr>"]
    for r in rows:
        warn = "⚠️" if r["qty"] <= r["min_qty"] else ""
        body.append(f"<tr><td>{r['category']}</td><td>{r['name']}</td><td>{r['qty']} {warn}</td>"
                    f"<td>{r['min_qty']}</td><td>{r['supplier']}</td><td>{r['price']}</td>"
                    f"<td><a href='/admin/warehouse/{r['id']}/supplier'>Заявка поставщику</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить материал</h3>
    <form method="post"><div class="grid">
      <div><label>Категория</label><select name="category"><option>Фасады</option><option>Столешницы</option><option>Плиты</option><option>Фурнитура</option></select></div>
      <div><label>Название</label><input name="name"></div>
      <div><label>Количество</label><input name="qty" type="number" step="0.01"></div>
      <div><label>Ед.</label><input name="unit"></div>
      <div><label>Мин. остаток</label><input name="min_qty" type="number" step="0.01"></div>
      <div><label>Поставщик</label><input name="supplier"></div>
      <div><label>Цена</label><input name="price" type="number" step="0.01"></div>
    </div><button>Добавить</button></form></div>""")
    return admin_page("Склад", "".join(body))

@app.route("/admin/warehouse/<int:wid>/supplier")
@login_required
def warehouse_supplier(wid):
    db = get_db()
    w = db.execute("SELECT * FROM warehouse WHERE id=?", (wid,)).fetchone()
    if not w:
        abort(404)
    text = f"Заявка поставщику\n\nМатериал: {w['name']}\nКатегория: {w['category']}\nКоличество: {w['qty']} {w['unit']}\nПоставщик: {w['supplier']}\n"
    return make_response(text, 200, {"Content-Type": "text/plain; charset=utf-8",
                                    "Content-Disposition": f"attachment; filename=supplier-{wid}.txt"})

# --- портфолио ---
@app.route("/admin/portfolio", methods=["GET", "POST"])
@login_required
def admin_portfolio():
    db = get_db()
    if request.method == "POST":
        db.execute("""INSERT INTO portfolio (title, category, style, material, price, city, term, description,
                      before_photo, after_photo, published, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                   (request.form.get("title"), request.form.get("category"), request.form.get("style"),
                    request.form.get("material"), float(request.form.get("price") or 0),
                    request.form.get("city"), request.form.get("term"), request.form.get("description"),
                    None, None, 1 if request.form.get("published") else 0, now_iso()))
        db.commit()
    rows = db.execute("SELECT * FROM portfolio ORDER BY id DESC").fetchall()
    body = ["<h1>Портфолио</h1>",
            "<table><tr><th>ID</th><th>Название</th><th>Категория</th><th>Город</th><th>Опубликовано</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['title']}</td><td>{r['category']}</td><td>{r['city']}</td>"
                    f"<td>{'да' if r['published'] else 'нет'}</td>"
                    f"<td><a href='/admin/portfolio/{r['id']}'>Открыть</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить проект</h3>
    <form method="post" enctype="multipart/form-data">
      <div class="grid">
        <div><label>Название</label><input name="title"></div>
        <div><label>Категория</label><select name="category">
          <option value="kitchens">Кухни</option><option value="wardrobes">Шкафы</option>
          <option value="dressing">Гардеробные</option><option value="hallways">Прихожие</option>
          <option value="living">Гостиные</option><option value="bath">Ванные</option>
          <option value="kids">Детские</option><option value="office">Офис</option>
        </select></div>
        <div><label>Стиль</label><input name="style"></div>
        <div><label>Материал</label><input name="material"></div>
        <div><label>Цена</label><input name="price" type="number"></div>
        <div><label>Город</label><select name="city"><option>Азов</option><option>Ростов-на-Дону</option><option>Батайск</option></select></div>
        <div><label>Срок</label><input name="term"></div>
        <div><label>Описание</label><textarea name="description"></textarea></div>
        <div><label>Фото «до»</label><input type="file" name="before_photo"></div>
        <div><label>Фото «после»</label><input type="file" name="after_photo"></div>
        <div><label><input type="checkbox" name="published" checked> Опубликовать</label></div>
      </div><button>Добавить</button></form></div>""")
    return admin_page("Портфолио", "".join(body))

@app.route("/admin/portfolio/<int:pid>", methods=["GET", "POST"])
@login_required
def admin_portfolio_item(pid):
    db = get_db()
    p = db.execute("SELECT * FROM portfolio WHERE id=?", (pid,)).fetchone()
    if not p:
        abort(404)
    if request.method == "POST":
        fields = []
        if request.files.get("before_photo"):
            saved = save_upload(request.files["before_photo"], "before")
            if saved:
                db.execute("UPDATE portfolio SET before_photo=? WHERE id=?", (saved[0], pid))
        if request.files.get("after_photo"):
            saved = save_upload(request.files["after_photo"], "after")
            if saved:
                db.execute("UPDATE portfolio SET after_photo=? WHERE id=?", (saved[0], pid))
        db.execute("""UPDATE portfolio SET title=?, category=?, style=?, material=?, price=?, city=?, term=?,
                      description=?, published=? WHERE id=?""",
                   (request.form.get("title"), request.form.get("category"), request.form.get("style"),
                    request.form.get("material"), float(request.form.get("price") or 0),
                    request.form.get("city"), request.form.get("term"), request.form.get("description"),
                    1 if request.form.get("published") else 0, pid))
        db.commit()
        return redirect(url_for("admin_portfolio_item", pid=pid))
    body = f"""<div class="card"><h1>{p['title']}</h1>
    <form method="post" enctype="multipart/form-data" data-dirty>
      <div class="grid">
        <div><label>Название</label><input name="title" value="{p['title']}"></div>
        <div><label>Категория</label><input name="category" value="{p['category']}"></div>
        <div><label>Стиль</label><input name="style" value="{p['style'] or ''}"></div>
        <div><label>Материал</label><input name="material" value="{p['material'] or ''}"></div>
        <div><label>Цена</label><input name="price" type="number" value="{p['price']}"></div>
        <div><label>Город</label><input name="city" value="{p['city']}"></div>
        <div><label>Срок</label><input name="term" value="{p['term'] or ''}"></div>
        <div><label>Описание</label><textarea name="description">{p['description'] or ''}</textarea></div>
        <div><label>Фото «до»</label><input type="file" name="before_photo"></div>
        <div><label>Фото «после»</label><input type="file" name="after_photo"></div>
        <div><label><input type="checkbox" name="published" {"checked" if p["published"] else ""}> Опубликовать</label></div>
      </div><button>Сохранить</button>
    </form></div>"""
    return admin_page("Проект портфолио", body)

# --- отзывы ---
@app.route("/admin/reviews", methods=["GET", "POST"])
@login_required
def admin_reviews():
    db = get_db()
    if request.method == "POST":
        db.execute("INSERT INTO reviews (author, text, rating, city, approved, confirmed, created_at) VALUES (?,?,?,?,?,?,?)",
                   (request.form.get("author"), request.form.get("text"), int(request.form.get("rating") or 5),
                    request.form.get("city"), 1 if request.form.get("approved") else 0,
                    1 if request.form.get("confirmed") else 0, now_iso()))
        db.commit()
    rows = db.execute("SELECT * FROM reviews ORDER BY id DESC").fetchall()
    body = ["<h1>Отзывы</h1>",
            "<table><tr><th>ID</th><th>Автор</th><th>Город</th><th>Оценка</th><th>Опубликован</th><th>Подтверждён</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['author']}</td><td>{r['city']}</td><td>{r['rating']}</td>"
                    f"<td>{'да' if r['approved'] else 'нет'}</td><td>{'да' if r['confirmed'] else 'нет'}</td>"
                    f"<td><a href='/admin/reviews/{r['id']}/approve'>Опубликовать</a> "
                    f"<a href='/admin/reviews/{r['id']}/confirm'>Подтвердить</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить отзыв</h3>
    <form method="post"><div class="grid">
      <div><label>Автор</label><input name="author"></div>
      <div><label>Город</label><input name="city"></div>
      <div><label>Оценка</label><input name="rating" type="number" value="5"></div>
      <div><label>Текст</label><textarea name="text"></textarea></div>
      <div><label><input type="checkbox" name="approved"> Опубликовать</label></div>
      <div><label><input type="checkbox" name="confirmed"> Подтверждён</label></div>
    </div><button>Добавить</button></form></div>""")
    return admin_page("Отзывы", "".join(body))

@app.route("/admin/reviews/<int:rid>/approve")
@login_required
def review_approve(rid):
    db = get_db()
    db.execute("UPDATE reviews SET approved=1 WHERE id=?", (rid,))
    db.commit()
    return redirect(url_for("admin_reviews"))

@app.route("/admin/reviews/<int:rid>/confirm")
@login_required
def review_confirm(rid):
    db = get_db()
    db.execute("UPDATE reviews SET confirmed=1 WHERE id=?", (rid,))
    db.commit()
    return redirect(url_for("admin_reviews"))

# --- FAQ ---
@app.route("/admin/faq", methods=["GET", "POST"])
@login_required
def admin_faq():
    db = get_db()
    if request.method == "POST":
        db.execute("INSERT INTO faq (question, answer, published) VALUES (?,?,?)",
                   (request.form.get("question"), request.form.get("answer"), 1 if request.form.get("published") else 0))
        db.commit()
    rows = db.execute("SELECT * FROM faq ORDER BY id DESC").fetchall()
    body = ["<h1>FAQ</h1>", "<table><tr><th>ID</th><th>Вопрос</th><th>Ответ</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['question']}</td><td>{r['answer']}</td>"
                    f"<td><a href='/admin/faq/{r['id']}/toggle'>Вкл/выкл</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить вопрос</h3>
    <form method="post"><input name="question" placeholder="Вопрос">
    <textarea name="answer" placeholder="Ответ"></textarea>
    <label><input type="checkbox" name="published" checked> Опубликовать</label>
    <button>Добавить</button></form></div>""")
    return admin_page("FAQ", "".join(body))

@app.route("/admin/faq/<int:fid>/toggle")
@login_required
def faq_toggle(fid):
    db = get_db()
    db.execute("UPDATE faq SET published = 1 - published WHERE id=?", (fid,))
    db.commit()
    return redirect(url_for("admin_faq"))

# --- страницы ---
@app.route("/admin/pages", methods=["GET", "POST"])
@login_required
def admin_pages():
    db = get_db()
    if request.method == "POST":
        slug = request.form.get("slug")
        db.execute("""INSERT INTO pages (slug, title, meta_title, meta_description, og_image, jsonld, body, status, publish_at, updated_at)
                      VALUES (?,?,?,?,?,?,?,?,?,?)""",
                   (slug, request.form.get("title"), request.form.get("meta_title"),
                    request.form.get("meta_description"), request.form.get("og_image"),
                    request.form.get("jsonld"), request.form.get("body"),
                    request.form.get("status") or "черновик", request.form.get("publish_at") or None, now_iso()))
        db.commit()
    rows = db.execute("SELECT * FROM pages ORDER BY id DESC").fetchall()
    body = ["<h1>Страницы</h1>", "<table><tr><th>ID</th><th>Slug</th><th>Заголовок</th><th>Статус</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['slug']}</td><td>{r['title']}</td><td>{r['status']}</td>"
                    f"<td><a href='/admin/pages/{r['id']}'>Открыть</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить страницу</h3>
    <form method="post" data-dirty>
      <div class="grid">
        <div><label>Slug</label><input name="slug"></div>
        <div><label>Заголовок</label><input name="title"></div>
        <div><label>Meta Title</label><input name="meta_title"></div>
        <div><label>Meta Description</label><input name="meta_description"></div>
        <div><label>OG Image</label><input name="og_image"></div>
        <div><label>JSON-LD</label><textarea name="jsonld"></textarea></div>
        <div><label>Статус</label><select name="status"><option>черновик</option><option>опубликовано</option></select></div>
        <div><label>Публикация</label><input type="datetime-local" name="publish_at"></div>
      </div>
      <label>Содержимое</label><textarea name="body" rows="10"></textarea>
      <button>Сохранить</button></form></div>""")
    return admin_page("Страницы", "".join(body))

@app.route("/admin/pages/<int:pid>", methods=["GET", "POST"])
@login_required
def admin_page_edit(pid):
    db = get_db()
    p = db.execute("SELECT * FROM pages WHERE id=?", (pid,)).fetchone()
    if not p:
        abort(404)
    if request.method == "POST":
        db.execute("INSERT INTO page_history (page_id, snapshot, created_at) VALUES (?,?,?)",
                   (pid, json.dumps(dict(p), ensure_ascii=False, default=str), now_iso()))
        db.execute("""UPDATE pages SET slug=?, title=?, meta_title=?, meta_description=?, og_image=?, jsonld=?,
                      body=?, status=?, publish_at=?, updated_at=? WHERE id=?""",
                   (request.form.get("slug"), request.form.get("title"), request.form.get("meta_title"),
                    request.form.get("meta_description"), request.form.get("og_image"), request.form.get("jsonld"),
                    request.form.get("body"), request.form.get("status"), request.form.get("publish_at") or None,
                    now_iso(), pid))
        db.commit()
        log_action("page_update", f"{p['slug']}")
        return redirect(url_for("admin_page_edit", pid=pid))
    history = db.execute("SELECT * FROM page_history WHERE page_id=? ORDER BY id DESC LIMIT 10", (pid,)).fetchall()
    body = f"""<div class="card"><h1>Страница {p['slug']}</h1>
    <form method="post" data-dirty>
      <div class="grid">
        <div><label>Slug</label><input name="slug" value="{p['slug']}"></div>
        <div><label>Заголовок</label><input name="title" value="{p['title'] or ''}"></div>
        <div><label>Meta Title</label><input name="meta_title" value="{p['meta_title'] or ''}" maxlength="60">
          <small>Длина: <span id="tl">{len(p['meta_title'] or '')}</span>/60</small></div>
        <div><label>Meta Description</label><input name="meta_description" value="{p['meta_description'] or ''}" maxlength="160">
          <small>Длина: <span id="dl">{len(p['meta_description'] or '')}</span>/160</small></div>
        <div><label>OG Image</label><input name="og_image" value="{p['og_image'] or ''}"></div>
        <div><label>JSON-LD</label><textarea name="jsonld">{p['jsonld'] or ''}</textarea></div>
        <div><label>Статус</label><select name="status">
          <option {"selected" if p["status"]=="черновик" else ""}>черновик</option>
          <option {"selected" if p["status"]=="опубликовано" else ""}>опубликовано</option>
        </select></div>
        <div><label>Публикация</label><input type="datetime-local" name="publish_at" value="{p['publish_at'] or ''}"></div>
      </div>
      <label>Содержимое</label><textarea name="body" rows="12">{p['body'] or ''}</textarea>
      <button>Сохранить</button>
      <a class="btn" href="/page/{p['slug']}">Предпросмотр</a>
    </form></div>
    <div class="card"><h3>История изменений</h3>
    {''.join(f"<div>{h['created_at']} <a href='/admin/pages/{pid}/rollback/{h['id']}'>Откатить</a></div>" for h in history)}
    </div>"""
    return admin_page("Редактирование страницы", body)

@app.route("/admin/pages/<int:pid>/rollback/<int:hid>")
@login_required
def page_rollback(pid, hid):
    db = get_db()
    h = db.execute("SELECT * FROM page_history WHERE id=? AND page_id=?", (hid, pid)).fetchone()
    if not h:
        abort(404)
    snap = json.loads(h["snapshot"])
    db.execute("""UPDATE pages SET slug=?, title=?, meta_title=?, meta_description=?, og_image=?, jsonld=?,
                  body=?, status=?, publish_at=?, updated_at=? WHERE id=?""",
               (snap.get("slug"), snap.get("title"), snap.get("meta_title"), snap.get("meta_description"),
                snap.get("og_image"), snap.get("jsonld"), snap.get("body"), snap.get("status"),
                snap.get("publish_at"), now_iso(), pid))
    db.commit()
    log_action("page_rollback", f"{pid}->{hid}")
    return redirect(url_for("admin_page_edit", pid=pid))

@app.route("/page/<slug>")
def public_page(slug):
    db = get_db()
    p = db.execute("SELECT * FROM pages WHERE slug=? AND status='опубликовано'", (slug,)).fetchone()
    if not p:
        abort(404)
    if p["publish_at"] and p["publish_at"] > datetime.now().isoformat(timespec="minutes"):
        abort(404)
    return render_page(p["title"], p["meta_description"] or "", p["body"] or "",
                       og_image=p["og_image"], jsonld=p["jsonld"])

# --- блоки главной ---
@app.route("/admin/blocks", methods=["GET", "POST"])
@login_required
def admin_blocks():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            db.execute("INSERT INTO homepage_blocks (title, body, sort_order, hidden, created_at) VALUES (?,?,?,?,?)",
                       (request.form.get("title"), request.form.get("body"),
                        int(request.form.get("sort_order") or 0), 0, now_iso()))
        elif action == "order":
            for i, bid in enumerate(request.form.getlist("block_id")):
                db.execute("UPDATE homepage_blocks SET sort_order=? WHERE id=?", (i, bid))
        db.commit()
    rows = db.execute("SELECT * FROM homepage_blocks ORDER BY sort_order, id").fetchall()
    body = ["<h1>Блоки главной</h1>",
            "<form method='post'><input type='hidden' name='action' value='order'>",
            "<div id='sortable'>"]
    for r in rows:
        body.append(f"""<div class="card" draggable="true" data-id="{r['id']}">
          <input type="hidden" name="block_id" value="{r['id']}">
          <b>{r['title']}</b> {'<span class="badge">скрыт</span>' if r['hidden'] else ''}
          <p>{r['body']}</p>
          <a href="/admin/blocks/{r['id']}">Ред.</a> |
          <a href="/admin/blocks/{r['id']}/hide">Скрыть/показать</a> |
          <a href="/admin/blocks/{r['id']}/duplicate">Дублировать</a> |
          <a href="/admin/blocks/{r['id']}/delete">Удалить</a>
        </div>""")
    body.append("</div><button>Сохранить порядок</button></form>")
    body.append("""<div class="card"><h3>Добавить блок</h3>
    <form method="post"><input type="hidden" name="action" value="add">
    <input name="title" placeholder="Заголовок">
    <textarea name="body" placeholder="Содержимое"></textarea>
    <input name="sort_order" type="number" value="0">
    <button>Добавить</button></form></div>
    <script>
    let drag=null;
    document.querySelectorAll('#sortable .card').forEach(el=>{
      el.addEventListener('dragstart',e=>{drag=el;});
      el.addEventListener('dragover',e=>{e.preventDefault();});
      el.addEventListener('drop',e=>{e.preventDefault();if(drag&&drag!==el){el.parentNode.insertBefore(drag,el);}});
    });
    </script>""")
    return admin_page("Блоки главной", "".join(body))

@app.route("/admin/blocks/<int:bid>", methods=["GET", "POST"])
@login_required
def admin_block_edit(bid):
    db = get_db()
    b = db.execute("SELECT * FROM homepage_blocks WHERE id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    if request.method == "POST":
        db.execute("UPDATE homepage_blocks SET title=?, body=?, sort_order=? WHERE id=?",
                   (request.form.get("title"), request.form.get("body"),
                    int(request.form.get("sort_order") or 0), bid))
        db.commit()
        return redirect(url_for("admin_blocks"))
    body = f"""<div class="card"><h1>Редактирование блока</h1>
    <form method="post" data-dirty>
      <label>Заголовок</label><input name="title" value="{b['title']}">
      <label>Содержимое</label><textarea name="body" rows="8">{b['body']}</textarea>
      <label>Порядок</label><input name="sort_order" type="number" value="{b['sort_order']}">
      <button>Сохранить</button>
    </form></div>"""
    return admin_page("Блок", body)

@app.route("/admin/blocks/<int:bid>/hide")
@login_required
def block_hide(bid):
    db = get_db()
    db.execute("UPDATE homepage_blocks SET hidden = 1 - hidden WHERE id=?", (bid,))
    db.commit()
    return redirect(url_for("admin_blocks"))

@app.route("/admin/blocks/<int:bid>/duplicate")
@login_required
def block_duplicate(bid):
    db = get_db()
    b = db.execute("SELECT * FROM homepage_blocks WHERE id=?", (bid,)).fetchone()
    if b:
        db.execute("INSERT INTO homepage_blocks (title, body, sort_order, hidden, created_at) VALUES (?,?,?,?,?)",
                   (b["title"] + " (копия)", b["body"], b["sort_order"] + 1, b["hidden"], now_iso()))
        db.commit()
    return redirect(url_for("admin_blocks"))

@app.route("/admin/blocks/<int:bid>/delete")
@login_required
def block_delete(bid):
    db = get_db()
    b = db.execute("SELECT * FROM homepage_blocks WHERE id=?", (bid,)).fetchone()
    if b:
        db.execute("INSERT INTO archive (entity, entity_id, payload, created_at) VALUES (?,?,?,?)",
                   ("homepage_block", bid, json.dumps(dict(b), ensure_ascii=False), now_iso()))
        db.execute("DELETE FROM homepage_blocks WHERE id=?", (bid,))
        db.commit()
    return redirect(url_for("admin_blocks"))

# --- SEO ---
@app.route("/admin/seo", methods=["GET", "POST"])
@login_required
def admin_seo():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            slug = request.form.get("slug")
            db.execute("""INSERT INTO seo_pages (city, district, keyword, slug, title, meta_title, meta_description, body, created_at)
                          VALUES (?,?,?,?,?,?,?,?,?)""",
                       (request.form.get("city"), request.form.get("district"), request.form.get("keyword"),
                        slug, request.form.get("title"), request.form.get("meta_title"),
                        request.form.get("meta_description"), request.form.get("body"), now_iso()))
        elif action == "generate":
            now = now_iso()
            for city in CITIES:
                for kw in KEYWORDS:
                    slug = f"{re.sub(r'[^a-z0-9]+','-',kw.lower()).strip('-')}-{re.sub(r'[^a-z0-9]+','-',city.lower()).strip('-')}"
                    title = kw.capitalize()
                    db.execute("""INSERT OR IGNORE INTO seo_pages (city, district, keyword, slug, title, meta_title, meta_description, body, created_at)
                                  VALUES (?,?,?,?,?,?,?,?,?)""",
                               (city, "", kw, slug, title, f"{title} — заказать в {city} | Мастерская мебели",
                                f"{title}. Изготовление на заказ в {city}. Замер, дизайн, монтаж. Гарантия.",
                                f"<h1>{title}</h1><p>Изготовим {kw} в {city}.</p>", now))
            db.commit()
        db.commit()
    rows = db.execute("SELECT * FROM seo_pages ORDER BY city, keyword").fetchall()
    body = ["<h1>SEO-страницы</h1>",
            "<p><a class='btn' href='/sitemap.xml' target='_blank'>sitemap.xml</a> "
            "<a class='btn' href='/robots.txt' target='_blank'>robots.txt</a></p>",
            "<form method='post'><input type='hidden' name='action' value='generate'><button>Сгенерировать все города и ключи</button></form>",
            "<table><tr><th>ID</th><th>Город</th><th>Район</th><th>Ключ</th><th>Slug</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['city']}</td><td>{r['district']}</td><td>{r['keyword']}</td>"
                    f"<td>{r['slug']}</td><td><a href='/seo/{r['slug']}' target='_blank'>Открыть</a> "
                    f"<a href='/admin/seo/{r['id']}'>Ред.</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Добавить SEO-страницу</h3>
    <form method="post"><input type="hidden" name="action" value="add">
    <div class="grid">
      <div><label>Город</label><select name="city"><option>Азов</option><option>Ростов-на-Дону</option><option>Батайск</option></select></div>
      <div><label>Район</label><input name="district"></div>
      <div><label>Ключ</label><input name="keyword"></div>
      <div><label>Slug</label><input name="slug"></div>
      <div><label>Title</label><input name="title"></div>
      <div><label>Meta Title</label><input name="meta_title" maxlength="60"></div>
      <div><label>Meta Description</label><input name="meta_description" maxlength="160"></div>
    </div>
    <label>Содержимое</label><textarea name="body" rows="6"></textarea>
    <button>Добавить</button></form></div>""")
    return admin_page("SEO", "".join(body))

@app.route("/admin/seo/<int:sid>", methods=["GET", "POST"])
@login_required
def admin_seo_edit(sid):
    db = get_db()
    s = db.execute("SELECT * FROM seo_pages WHERE id=?", (sid,)).fetchone()
    if not s:
        abort(404)
    if request.method == "POST":
        db.execute("""UPDATE seo_pages SET city=?, district=?, keyword=?, slug=?, title=?, meta_title=?,
                      meta_description=?, body=? WHERE id=?""",
                   (request.form.get("city"), request.form.get("district"), request.form.get("keyword"),
                    request.form.get("slug"), request.form.get("title"), request.form.get("meta_title"),
                    request.form.get("meta_description"), request.form.get("body"), sid))
        db.commit()
        return redirect(url_for("admin_seo"))
    body = f"""<div class="card"><h1>SEO-страница</h1>
    <form method="post" data-dirty>
      <div class="grid">
        <div><label>Город</label><input name="city" value="{s['city']}"></div>
        <div><label>Район</label><input name="district" value="{s['district'] or ''}"></div>
        <div><label>Ключ</label><input name="keyword" value="{s['keyword']}"></div>
        <div><label>Slug</label><input name="slug" value="{s['slug']}"></div>
        <div><label>Title</label><input name="title" value="{s['title']}"></div>
        <div><label>Meta Title</label><input name="meta_title" value="{s['meta_title']}" maxlength="60"></div>
        <div><label>Meta Description</label><input name="meta_description" value="{s['meta_description']}" maxlength="160"></div>
      </div>
      <label>Содержимое</label><textarea name="body" rows="10">{s['body']}</textarea>
      <button>Сохранить</button>
      <a class="btn" href="/seo/{s['slug']}" target="_blank">Открыть на сайте</a>
    </form></div>"""
    return admin_page("SEO-страница", body)

# --- отчёты ---
@app.route("/admin/reports")
@login_required
def admin_reports():
    db = get_db()
    total = db.execute("SELECT COUNT(*) c FROM leads").fetchone()["c"]
    by_source = db.execute("SELECT source, COUNT(*) c FROM leads GROUP BY source").fetchall()
    by_city = db.execute("SELECT city, COUNT(*) c FROM leads GROUP BY city").fetchall()
    by_manager = db.execute("""SELECT u.login, COUNT(l.id) c FROM users u LEFT JOIN leads l ON l.responsible_id=u.id
                               GROUP BY u.login ORDER BY c DESC""").fetchall()
    avg = db.execute("SELECT AVG(total) a FROM projects").fetchone()["a"] or 0
    body = [f"<h1>Отчёты</h1><div class='grid'>",
            f"<div class='card'><h3>Всего заявок</h3><p>{total}</p></div>",
            f"<div class='card'><h3>Средний чек</h3><p>{round(avg,2)} ₽</p></div>",
            "</div>",
            "<div class='card'><h3>Источники заявок</h3><ul>"]
    for r in by_source:
        body.append(f"<li>{r['source']}: {r['c']}</li>")
    body.append("</ul></div><div class='card'><h3>Города</h3><ul>")
    for r in by_city:
        body.append(f"<li>{r['city']}: {r['c']}</li>")
    body.append("</ul></div><div class='card'><h3>Эффективность менеджеров</h3><ul>")
    for r in by_manager:
        body.append(f"<li>{r['login']}: {r['c']}</li>")
    body.append("</ul></div>")
    body.append("""<div class="card"><h3>Дополнительные отчёты</h3>
    <p>Конверсия сайта, популярные страницы, клики по телефону и мессенджерам, конверсия каждого города,
    рекламные кампании, длительность сделки, повторные клиенты, причины отказа — данные собираются
    через Яндекс.Метрику и Google Analytics, а также из полей заявок.</p></div>""")
    return admin_page("Отчёты", "".join(body))

# --- пользователи ---
@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("руководитель")
def admin_users():
    db = get_db()
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "менеджер")
        if login and password:
            db.execute("INSERT INTO users (login, password_hash, role, full_name, created_at, created_by, active) VALUES (?,?,?,?,?,?,1)",
                       (login, generate_password_hash(password), role, request.form.get("full_name"),
                        now_iso(), session["user_id"]))
            db.commit()
            log_action("user_create", f"{login} {role}")
    rows = db.execute("SELECT * FROM users ORDER BY id").fetchall()
    body = ["<h1>Пользователи и права</h1>",
            "<table><tr><th>ID</th><th>Логин</th><th>Роль</th><th>ФИО</th><th>Активен</th><th></th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['login']}</td><td>{r['role']}</td><td>{r['full_name'] or ''}</td>"
                    f"<td>{'да' if r['active'] else 'нет'}</td>"
                    f"<td><a href='/admin/users/{r['id']}/toggle'>Вкл/выкл</a></td></tr>")
    body.append("</table>")
    body.append("""<div class="card"><h3>Создать сотрудника</h3>
    <form method="post">
      <div class="grid">
        <div><label>Логин</label><input name="login" required></div>
        <div><label>Пароль</label><input name="password" required></div>
        <div><label>Роль</label><select name="role">
          <option>менеджер</option><option>дизайнер</option><option>руководитель</option>
        </select></div>
        <div><label>ФИО</label><input name="full_name"></div>
      </div>
      <button>Создать и выдать права</button>
    </form>
    <p>Руководитель создаёт логин и пароль, назначает роль. Сотрудник входит по этим данным.</p></div>""")
    return admin_page("Пользователи", "".join(body))

@app.route("/admin/users/<int:uid>/toggle")
@login_required
@role_required("руководитель")
def user_toggle(uid):
    db = get_db()
    db.execute("UPDATE users SET active = 1 - active WHERE id=?", (uid,))
    db.commit()
    return redirect(url_for("admin_users"))

# --- журнал ---
@app.route("/admin/audit")
@login_required
def admin_audit():
    rows = get_db().execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 500").fetchall()
    body = ["<h1>Журнал действий</h1>", "<table><tr><th>Время</th><th>Логин</th><th>Действие</th><th>Детали</th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['created_at']}</td><td>{r['login']}</td><td>{r['action']}</td><td>{r['details']}</td></tr>")
    body.append("</table>")
    return admin_page("Журнал", "".join(body))

# --- поиск по админке ---
@app.route("/admin/search")
@login_required
def admin_search():
    q = request.args.get("q", "").strip()
    db = get_db()
    body = [f"<h1>Поиск: {q}</h1>"]
    if q:
        like = f"%{q}%"
        leads = db.execute("SELECT id, number, name, phone FROM leads WHERE number LIKE ? OR name LIKE ? OR phone LIKE ?", (like, like, like)).fetchall()
        projects = db.execute("SELECT id, code, title FROM projects WHERE code LIKE ? OR title LIKE ?", (like, like)).fetchall()
        pages = db.execute("SELECT id, slug, title FROM pages WHERE slug LIKE ? OR title LIKE ?", (like, like)).fetchall()
        body.append("<div class='card'><h3>Заявки</h3>" + "".join(f"<div><a href='/admin/leads/{r['id']}'>{r['number']} {r['name']}</a></div>" for r in leads) + "</div>")
        body.append("<div class='card'><h3>Проекты</h3>" + "".join(f"<div><a href='/admin/projects/{r['id']}'>{r['code']} {r['title']}</a></div>" for r in projects) + "</div>")
        body.append("<div class='card'><h3>Страницы</h3>" + "".join(f"<div><a href='/admin/pages/{r['id']}'>{r['slug']} {r['title']}</a></div>" for r in pages) + "</div>")
    return admin_page("Поиск", "".join(body))

# --- массовое редактирование и импорт/экспорт ---
@app.route("/admin/leads/mass", methods=["POST"])
@login_required
def admin_leads_mass():
    ids = request.form.getlist("lead_id")
    status = request.form.get("status")
    db = get_db()
    for lid in ids:
        db.execute("UPDATE leads SET status=?, updated_at=? WHERE id=?", (status, now_iso(), lid))
    db.commit()
    log_action("lead_mass", f"{len(ids)} -> {status}")
    return redirect(url_for("admin_leads"))

@app.route("/admin/import", methods=["GET", "POST"])
@login_required
def admin_import():
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            content = file.read().decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(content), delimiter=";")
            db = get_db()
            for row in reader:
                db.execute("""INSERT INTO leads (number, name, phone, city, furniture_type, status, source, created_at, updated_at)
                              VALUES (?,?,?,?,?,?,?,?,?)""",
                           (row.get("number") or make_lead_number(), row.get("name"), row.get("phone"),
                            row.get("city"), row.get("furniture_type"), row.get("status") or "новая",
                            row.get("source") or "импорт", now_iso(), now_iso()))
            db.commit()
            log_action("import", file.filename)
        return redirect(url_for("admin_leads"))
    body = """<div class="card"><h1>Импорт из CSV</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".csv">
      <button>Импортировать</button>
    </form></div>"""
    return admin_page("Импорт", body)

@app.route("/admin/export")
@login_required
def admin_export():
    rows = get_db().execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    out = export_rows(rows, ["id", "number", "name", "phone", "city", "status", "created_at"])
    return make_response(out, 200, {"Content-Type": "text/csv; charset=utf-8",
                                    "Content-Disposition": "attachment; filename=export.csv"})

# --- архив ---
@app.route("/admin/archive")
@login_required
def admin_archive():
    rows = get_db().execute("SELECT * FROM archive ORDER BY id DESC").fetchall()
    body = ["<h1>Архив удалённых элементов</h1>",
            "<table><tr><th>ID</th><th>Сущность</th><th>ID сущности</th><th>Время</th></tr>"]
    for r in rows:
        body.append(f"<tr><td>{r['id']}</td><td>{r['entity']}</td><td>{r['entity_id']}</td><td>{r['created_at']}</td></tr>")
    body.append("</table>")
    return admin_page("Архив", "".join(body))

# --- ошибки ---
@app.errorhandler(404)
def not_found(e):
    body = """<div class="card"><h1>404</h1><p>Страница не найдена.</p>
    <form action="/admin/search"><input name="q" placeholder="Поиск"><button>Найти</button></form>
    <a class="btn" href="/">На главную</a></div>"""
    return render_page("404", "Страница не найдена", body), 404

@app.errorhandler(403)
def forbidden(e):
    return render_page("403", "Доступ запрещён", "<div class='card'><h1>403</h1><p>Нет прав.</p></div>"), 403

# --- запуск ---
if __name__ == "__main__":
    init_db()
    print("Сервер запущен: http://127.0.0.1:5000")
    print("Админка: http://127.0.0.1:5000/admin")
    print("Руководитель: логин 'кухниост', пароль 'романкух'")
    app.run(host="0.0.0.0", port=5000, debug=True)
