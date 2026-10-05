# -*- coding: utf-8 -*-
"""
mebel.py — Кухни Островский: сайт + админка /admin на Supabase
"""
import base64
import gzip
import hashlib
import hmac
import io
import json
import mimetypes
import os
import re
import secrets
import threading
import time
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qs

try:
    from supabase import create_client
    _SUPABASE_LIB = True
except Exception:
    _SUPABASE_LIB = False

# ---------- Config ----------
PORT = int(os.environ.get("PORT", "8080"))
DOMAIN = "https://кухниостровский.рф"
ROOT = os.path.dirname(os.path.abspath(__file__))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE = os.environ.get("SUPABASE_SERVICE_KEY", "")

ADMIN_LOGIN_ENV = os.environ.get("ADMIN_LOGIN", "кухниост")
ADMIN_PASSWORD_ENV = os.environ.get("ADMIN_PASSWORD", "романкух")

SESSION_TTL = 86400 * 7
MAX_UPLOAD = 8 * 1024 * 1024
DATA_ROW_ID = 1
CACHE_TTL = 60

# ---------- Supabase клиенты ----------
_sb_read = None
_sb_write = None


def _sb_read_client():
    global _sb_read
    if _sb_read is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_ANON:
        try:
            _sb_read = create_client(SUPABASE_URL, SUPABASE_ANON)
        except Exception as e:
            print(f"[supabase read init] {e}")
    return _sb_read


def _sb_write_client():
    global _sb_write
    if _sb_write is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_SERVICE:
        try:
            _sb_write = create_client(SUPABASE_URL, SUPABASE_SERVICE)
        except Exception as e:
            print(f"[supabase write init] {e}")
    return _sb_write


# ---------- Пароль / сессии ----------
_auth_lock = threading.Lock()
_sessions = {}


def _pbkdf2(password, salt, iterations=200_000):
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return base64.b64encode(dk).decode("ascii")


def _hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)
    iters = 200_000
    return {
        "algo": "pbkdf2_sha256",
        "iterations": iters,
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": _pbkdf2(password, salt, iters),
    }


def _verify_password(password, rec):
    try:
        salt = base64.b64decode(rec["salt"])
        expected = rec["hash"]
        got = _pbkdf2(password, salt, int(rec.get("iterations", 200_000)))
        return hmac.compare_digest(got, expected)
    except Exception:
        return False


def _new_session():
    token = secrets.token_urlsafe(32)
    with _auth_lock:
        _sessions[token] = time.time() + SESSION_TTL
    return token


def _check_session(token):
    if not token:
        return False
    with _auth_lock:
        exp = _sessions.get(token)
        if not exp:
            return False
        if exp < time.time():
            _sessions.pop(token, None)
            return False
    return True


def _drop_session(token):
    if token:
        with _auth_lock:
            _sessions.pop(token, None)


# ---------- DEFAULT_DATA ----------
# Полный набор дефолтов — он же служит "сидом" при первом запуске
DEFAULT_DATA = {
    "brand": {
        "name": "Кухни Островский",
        "sub": "Ростов · Батайск · Азов",
        "logo_url": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0",
        "phone": "+7 (950) 846-53-97",
        "phone_raw": "+79508465397",
        "telegram": "https://t.me/fanny161",
        "vk": "https://vk.com/mebel.ostrovsky",
        "max": "tel:+79508465397",
    },
    "seo": {
        "title": "Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ",
        "description": "Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и 3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97",
        "keywords": "кухни остров, кухни островский, кухни на заказ ростов, кухни батайск, кухни азов, мебель на заказ",
        "og_image": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0",
        "yandex_verification": "f7e96d07aee79bf3",
        "google_verification": "dNSAELu64Y7aK5sjz_zpmhoz6YKn2PIZ03UKPwrgnCI",
    },
    "hero": {
        "eyebrow": "Мебель и кухни на заказ",
        "title_before": "Мебель, которая ",
        "title_em": "создаёт настроение",
        "sub": "Проектируем и изготавливаем кухни, шкафы, гардеробные и другую корпусную мебель в Ростове, Батайске и Азове — по вашему проекту, от замера до монтажа.",
        "bg": "https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&cs=1280x0",
        "btn1": "Получить консультацию",
        "btn2": "Смотреть работы",
    },
    "stats": {
        "bg": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&cs=1280x0",
        "items": [
            {"num": "10", "suffix": "+", "decimal": "0", "label": "лет опыта"},
            {"num": "5", "suffix": "", "decimal": "1", "label": "средняя оценка клиентов"},
            {"num": "8", "suffix": "/10", "decimal": "0", "label": "клиентов по рекомендации"},
            {"num": "100", "suffix": "%", "decimal": "0", "label": "полный цикл под ключ"},
        ],
    },
    "about": {
        "bg": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg?quality=95&cs=1280x0",
        "photo": "https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg",
        "name": "Роман Островский",
        "role": "Руководитель мебельной мастерской Островского",
        "text": "С командой изготавливаем кухни и корпусную мебель по индивидуальным проектам — с учётом ваших идей, размеров и задач.",
        "kicker": "О руководителе",
        "title": "Кухни и мебель под ключ — с заботой о деталях",
        "body": "Мы помогаем с планировкой и подбором материалов, предлагаем решения даже для сложных задач — когда другие разводят руками. Ведём вас от консультации и замера до сборки и установки.",
        "features": [
            "Кухни, шкафы, гардеробные и прихожие",
            "Честный расчёт — без навязывания лишнего",
            "Аккуратность, пунктуальность, сопровождение",
            "Гарантия качества",
        ],
    },
    "consult": {
        "bg": "https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&cs=1280x0",
        "kicker": "Бесплатно",
        "title": "Консультация",
        "text": "Позвоните или напишите нам в <b style=\"color:#fff\">Telegram</b> или <b style=\"color:#fff\">MAX</b> — расскажем про кухни и мебель, всё обсудим и договоримся о бесплатном замере.",
    },
    "works": {
        "bg": "https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&cs=1280x0",
        "kicker": "Наши работы",
        "title": "Кухни и мебель, которые мы сделали",
        "subtitle": "Нажмите на фото, чтобы рассмотреть в большом размере.",
        "items": [
            {"url": "https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&cs=1080x0", "alt": "Кухня на заказ в Ростове"},
            {"url": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&cs=1080x0", "alt": "Кухня на заказ в Батайске"},
        ],
    },
    "reviews": {
        "bg": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=1280x0",
        "kicker": "Отзывы",
        "title": "Что говорят наши клиенты",
        "subtitle": "Реальные отзывы о нашей работе. Листайте влево-вправо.",
        "items": [
            {"name": "Виктория Брандикова", "sub": "Кухня на заказ", "stars": 5,
             "avatar": "", "text": "Заказывали у Романа кухню — всё прошло на высшем уровне!", "video": ""},
        ],
    },
    "services": {
        "bg": "https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&cs=1280x0",
        "kicker": "Что мы делаем",
        "title": "Услуги",
        "subtitle": "Индивидуальный подход к каждому проекту и полный цикл производства.",
        "items": [
            {"title": "Кухни на заказ", "text": "Проектируем кухню точно под ваш размер, стиль и привычки — от классики до минимализма.", "icon": "M3 9h18M3 9v10a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V9M3 9l2-4h14l2 4M8 9v2M12 9v2M16 9v2"},
            {"title": "Шкафы и гардеробные", "text": "Шкафы-купе, гардеробные, тумбы и комоды — встроенные и отдельно стоящие.", "icon": "M3 3h18v18H3zM3 8h18M8 8v13M16 8v13"},
            {"title": "Прихожие и стенки", "text": "Прихожие, стенки, гарнитуры под ТВ — аккуратно впишем в ваш интерьер.", "icon": "M12 3v18M3 12h18M5 5l14 14M19 5L5 19"},
            {"title": "Сборка и монтаж", "text": "Профессиональная установка, аккуратная сборка и подключение техники.", "icon": "M14 6l4 4M5 19l7-7M17 3l4 4-4 4-1-1-1 1-4-4 1-1-1-1 4-4z"},
            {"title": "Замер и проект", "text": "Выезжаем на замер, делаем планировку и 3D-проект — бесплатно.", "icon": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 3v18M3 12h18"},
            {"title": "Обновление мебели", "text": "Освежим фасады и фурнитуру существующей кухни — дешевле, чем новая.", "icon": "M3 12a9 9 0 1 0 9-9M3 12h6M3 12l4-4M3 12l4 4"},
        ],
    },
    "process": {
        "bg": "https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&cs=1280x0",
        "kicker": "Как мы работаем",
        "title": "Путь от идеи до готовой мебели",
        "items": [
            {"n": "01", "title": "Обращение", "text": "Вы звоните или пишете — обговариваем задачу и пожелания."},
            {"n": "02", "title": "Замер", "text": "Выезжаем, снимаем размеры и обсуждаем планировку. Бесплатно."},
            {"n": "03", "title": "Проект", "text": "Готовим 3D-проект и подбираем материалы с фурнитурой."},
            {"n": "04", "title": "Договор", "text": "Фиксируем стоимость и условия, подписываем договор."},
            {"n": "05", "title": "Производство", "text": "Изготавливаем мебель на собственном производстве."},
            {"n": "06", "title": "Доставка и монтаж", "text": "Привозим, собираем и устанавливаем. Сдаём с гарантией."},
        ],
    },
    "guarantees": {
        "bg": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&cs=1280x0",
        "kicker": "Почему мы",
        "title": "Гарантии и преимущества",
        "items": [
            {"title": "Гарантия качества", "text": "Отвечаем за свою работу и сопровождаем после установки.", "icon": "M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3zM9 12l2 2 4-4"},
            {"title": "Честный расчёт", "text": "Без навязывания лишнего и скрытых доплат.", "icon": "M4 20h16M6 20V8l6-4 6 4v12M9 11h6M9 15h6"},
            {"title": "Собственное производство", "text": "Без посредников — контролируем качество на каждом этапе.", "icon": "M3 21V9l9-5 9 5v12M3 21h18M9 21v-6h6v6M12 9v2"},
            {"title": "Личное сопровождение", "text": "Вы всегда на связи со специалистом — от замера до монтажа.", "icon": "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM4 21c0-4 3.6-6 8-6s8 2 8 6"},
        ],
    },
    "cities": {
        "bg": "https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&cs=1280x0",
        "kicker": "Где работаем",
        "title": "Три города — один стандарт качества",
        "subtitle": "Бесплатный замер и проект в каждом из городов.",
        "items": [
            {"name": "Ростов-на-Дону", "text": "Выезд на замер, проектирование, производство и монтаж мебели под ключ."},
            {"name": "Батайск", "text": "Кухни и корпусная мебель с бесплатным замером и 3D-проектом."},
            {"name": "Азов", "text": "Индивидуальные проекты, доставка, сборка и установка с гарантией."},
        ],
    },
    "cta": {
        "bg": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=1280x0",
        "title": "Готовы обсудить вашу мебель?",
        "text": "Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.",
        "button": "📞 Позвонить специалисту",
    },
    "contacts": {
        "bg": "https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&cs=1080x0",
        "kicker": "Контакты",
        "title": "Создадим мебель, о которой вы мечтали",
        "subtitle": "Позвоните или напишите — ответим быстро и подскажем по всем вопросам.",
        "regions": "Ростов-на-Дону, Батайск, Азов",
    },
    "footer": {
        "line": "Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов",
        "copyright": "Кухни Островский. Все права защищены.",
    },
    "auth": {
        "login": ADMIN_LOGIN_ENV,
        "password_hash": _hash_password(ADMIN_PASSWORD_ENV),
    },
}


# ---------- Загрузка/сохранение ----------
_data_cache = None
_cache_ts = 0.0
_data_lock = threading.Lock()


def _deep_fill(target, source):
    """Дополняет target недостающими полями из source (dict → dict merge)."""
    for k, v in source.items():
        if k not in target:
            target[k] = json.loads(json.dumps(v))
        elif isinstance(v, dict) and isinstance(target[k], dict):
            _deep_fill(target[k], v)


def load_data(force=False):
    global _data_cache, _cache_ts
    now = time.time()
    with _data_lock:
        if not force and _data_cache is not None and now - _cache_ts < CACHE_TTL:
            return _data_cache

        data = None
        sb = _sb_read_client()
        if sb is not None:
            try:
                res = sb.table("site_content").select("data").eq("id", DATA_ROW_ID).execute()
                if res.data:
                    raw = res.data[0].get("data") or {}
                    data = json.loads(json.dumps(DEFAULT_DATA))
                    _deep_fill(data, raw)
                    # Применяем env-креды админки
                    data.setdefault("auth", {})
                    data["auth"]["login"] = ADMIN_LOGIN_ENV
                    if not data["auth"].get("password_hash"):
                        data["auth"]["password_hash"] = _hash_password(ADMIN_PASSWORD_ENV)
            except Exception as e:
                print(f"[load_data] {e}")
        if data is None:
            data = json.loads(json.dumps(DEFAULT_DATA))
        _data_cache = data
        _cache_ts = now
        return data


def save_data(data):
    global _data_cache, _cache_ts
    with _data_lock:
        # auth не пишем в БД — он из env
        payload = json.loads(json.dumps(data))
        payload.pop("auth", None)

        sb = _sb_write_client()
        if sb is None:
            print("[save_data] service_role недоступен, данные только в памяти")
            _data_cache = data
            _cache_ts = time.time()
            return False
        try:
            sb.table("site_content").upsert({
                "id": DATA_ROW_ID,
                "data": payload,
            }).execute()
            _data_cache = data
            _cache_ts = time.time()
            return True
        except Exception as e:
            print(f"[save_data] {e}")
            return False


# ---------- Favicon ----------
FAVICON_URL = "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0"
_favicon_cache = {"data": None, "ts": 0.0}
_icons_cache = {"ico": None, "png16": None, "png32": None, "png180": None}
FAVICON_TTL = 3600


def _make_icons(data):
    try:
        from PIL import Image
    except Exception:
        return
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        b = io.BytesIO()
        img.save(b, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        _icons_cache["ico"] = b.getvalue()

        def _png(size):
            c = img.copy()
            c.thumbnail((size, size))
            buf = io.BytesIO()
            c.save(buf, format="PNG")
            return buf.getvalue()
        _icons_cache["png16"] = _png(16)
        _icons_cache["png32"] = _png(32)
        _icons_cache["png180"] = _png(180)
    except Exception:
        pass


def get_favicon():
    now = time.time()
    if _favicon_cache["data"] is None or now - _favicon_cache["ts"] > FAVICON_TTL:
        try:
            req = urllib.request.Request(FAVICON_URL, headers={
                "User-Agent": "Mozilla/5.0", "Referer": "https://vk.com/"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                _favicon_cache["data"] = data
                _favicon_cache["ts"] = now
                _make_icons(data)
        except Exception:
            return None
    return _favicon_cache["data"]


# ---------- Генерация страниц ----------
def _esc(s):
    return (str(s or "")
            .replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _attr(s):
    return _esc(s)


def build_robots(d):
    return (
        "User-agent: *\n"
        "Allow: /\n"
        f"Host: {urlparse(DOMAIN).netloc}\n"
        f"Sitemap: {DOMAIN}/sitemap.xml\n"
    )


def build_sitemap(d):
    today = date.today().isoformat()
    imgs = d.get("works", {}).get("items", [])[:6]
    img_tags = "\n".join(
        f'    <image:image><image:loc>{_esc(i.get("url",""))}</image:loc>'
        f'<image:title>{_esc(i.get("alt",""))}</image:title></image:image>'
        for i in imgs
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{DOMAIN}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
{img_tags}
  </url>
</urlset>
"""


def build_manifest(d):
    b = d.get("brand", {})
    seo = d.get("seo", {})
    return json.dumps({
        "name": seo.get("title", b.get("name", "Кухни Островский")),
        "short_name": b.get("name", "Кухни Островский"),
        "description": seo.get("description", ""),
        "start_url": "/", "display": "standalone",
        "background_color": "#0e0c09", "theme_color": "#0e0c09",
        "lang": "ru-RU",
        "icons": [
            {"src": "/favicon.ico", "sizes": "16x16 32x32 48x48 64x64", "type": "image/x-icon", "purpose": "any"},
            {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png", "purpose": "any"},
        ],
    }, ensure_ascii=False, indent=2)


def build_page_404(d):
    b = d.get("brand", {})
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, follow">
<title>404 — страница не найдена | {_esc(b.get("name","Кухни Островский"))}</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,sans-serif;background:#0e0c09;color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center}}
.card{{max-width:560px}}
.code{{font-family:Georgia,serif;font-size:clamp(80px,18vw,160px);line-height:1;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
h1{{font-family:Georgia,serif;font-size:clamp(24px,5vw,34px);color:#fff;margin:14px 0 10px}}
p{{color:#b9ad9a;font-size:15px;line-height:1.7;margin-bottom:28px}}
.btn{{display:inline-block;padding:15px 30px;border-radius:14px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;font-size:13px;letter-spacing:1.2px;text-transform:uppercase;text-decoration:none}}</style></head><body>
<div class="card"><div class="code">404</div><h1>Такой страницы нет</h1>
<p>Возможно, ссылка устарела или адрес введён с ошибкой. Вернитесь на главную.</p>
<a class="btn" href="/">На главную</a></div></body></html>"""


def build_page(d):
    b = d["brand"]; seo = d["seo"]; hero = d["hero"]
    stats = d["stats"]; about = d["about"]; consult = d["consult"]
    works = d["works"]; reviews = d["reviews"]; services = d["services"]
    process = d["process"]; guarantees = d["guarantees"]; cities = d["cities"]
    cta = d["cta"]; contacts = d["contacts"]; footer = d["footer"]

    def stat_html():
        return "\n".join(
            f'<div class="stat reveal"><div class="num" data-count="{_attr(it.get("num","0"))}" '
            f'data-suffix="{_attr(it.get("suffix",""))}" data-decimal="{_attr(it.get("decimal","0"))}">0</div>'
            f'<div class="lbl">{_esc(it.get("label",""))}</div></div>'
            for it in stats["items"]
        )

    def features_html():
        return "\n".join(f"<li>{_esc(x)}</li>" for x in about.get("features", []))

    def works_html():
        return "\n".join(
            f'<div class="car-slide"><img loading="lazy" src="{_attr(it.get("url",""))}" '
            f'alt="{_attr(it.get("alt",""))}"></div>'
            for it in works["items"]
        )

    def reviews_html():
        out = []
        for r in reviews["items"]:
            ava = (f'<img class="rev-ava" loading="lazy" width="50" height="50" '
                   f'src="{_attr(r["avatar"])}" alt="{_attr(r.get("name",""))}">') if r.get("avatar") else ""
            stars = "★" * int(r.get("stars", 5))
            video = ""
            if r.get("video"):
                video = (f'<div class="rev-video"><div class="video-box" data-src="{_attr(r["video"])}" '
                         f'style="background-image:url(\'{_attr(r.get("video_poster",""))}\')"></div></div>')
            out.append(
                f'<div class="rev-card"><div class="rev-head">{ava}'
                f'<div><div class="rev-name">{_esc(r.get("name",""))}</div>'
                f'<div class="rev-sub">{_esc(r.get("sub",""))}</div></div>'
                f'<div class="rev-stars">{stars}</div></div>{video}'
                f'<p class="rev-text">{_esc(r.get("text",""))}</p></div>'
            )
        return "\n".join(out)

    def services_html():
        return "\n".join(
            f'<div class="svc reveal"><svg viewBox="0 0 24 24"><path d="{_attr(s.get("icon",""))}"/></svg>'
            f'<h3>{_esc(s.get("title",""))}</h3><p>{_esc(s.get("text",""))}</p></div>'
            for s in services["items"]
        )

    def process_html():
        return "\n".join(
            f'<div class="step reveal"><div class="n">{_esc(s.get("n",""))}</div>'
            f'<h3>{_esc(s.get("title",""))}</h3><p>{_esc(s.get("text",""))}</p></div>'
            for s in process["items"]
        )

    def guarantees_html():
        return "\n".join(
            f'<div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24">'
            f'<path d="{_attr(g.get("icon",""))}"/></svg></div>'
            f'<h3>{_esc(g.get("title",""))}</h3><p>{_esc(g.get("text",""))}</p></div>'
            for g in guarantees["items"]
        )

    def cities_html():
        return "\n".join(
            f'<div class="city reveal"><div class="city-name">{_esc(c.get("name",""))}</div>'
            f'<div class="city-line"></div><p>{_esc(c.get("text",""))}</p></div>'
            for c in cities["items"]
        )

    jsonld = [{
        "@context": "https://schema.org",
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": f"{DOMAIN}/#business",
        "name": b.get("name", ""), "url": f"{DOMAIN}/",
        "logo": b.get("logo_url", ""), "image": seo.get("og_image", ""),
        "description": seo.get("description", ""),
        "telephone": b.get("phone_raw", ""),
        "sameAs": [b.get("vk", ""), b.get("telegram", "")],
    }]

    return f"""<!DOCTYPE html>
<html lang="ru" class="js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(seo.get("title",""))}</title>
<meta name="description" content="{_attr(seo.get("description",""))}">
<meta name="keywords" content="{_attr(seo.get("keywords",""))}">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#0e0c09">
<link rel="canonical" href="{DOMAIN}/">
<meta name="yandex-verification" content="{_attr(seo.get("yandex_verification",""))}">
<meta name="google-site-verification" content="{_attr(seo.get("google_verification",""))}">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="{_attr(b.get("name",""))}">
<meta property="og:url" content="{DOMAIN}/">
<meta property="og:title" content="{_attr(seo.get("title",""))}">
<meta property="og:description" content="{_attr(seo.get("description",""))}">
<meta property="og:image" content="{_attr(seo.get("og_image",""))}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0e0c09;--gold:#d4af6a;--gold-soft:#eccfa0;--gold-deep:#a37c3f;--text:#f5efe3;--muted:#b9ad9a;--serif:'Cormorant Garamond',Georgia,serif;--sans:'Manrope',system-ui,sans-serif}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth;overflow-x:hidden}}section{{scroll-margin-top:92px}}
body{{font-family:var(--sans);color:var(--text);line-height:1.72;overflow-x:hidden;background:linear-gradient(180deg,#12100b,#0c0a07 45%,#100d09);min-height:100vh}}
h1,h2,h3{{font-family:var(--serif);letter-spacing:.3px}}
img{{max-width:100%;display:block}}a{{text-decoration:none;color:inherit}}ul{{list-style:none}}button{{font-family:inherit;cursor:pointer}}
.wrap{{width:100%;max-width:1180px;margin:0 auto;padding:0 20px}}
header{{position:fixed;top:0;left:0;right:0;z-index:200;background:rgba(14,12,9,.55);backdrop-filter:blur(18px);transition:.45s}}
header.solid{{background:rgba(14,12,9,.92)}}
.nav{{display:flex;align-items:center;justify-content:space-between;height:78px;gap:12px}}
.logo{{display:flex;align-items:center;gap:13px;min-width:0}}
.brand-ava{{width:46px;height:46px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.65)}}
.brand-txt .name{{font-family:var(--serif);font-size:26px;color:#fff;display:block;line-height:1.05}}
.brand-txt .sub{{color:var(--gold-soft);font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;display:block;margin-top:3px}}
.menu{{position:fixed;top:0;height:78px;right:max(20px,calc((100vw - 1220px)/2));display:flex;gap:24px;align-items:center;z-index:201}}
.menu a{{color:rgba(255,255,255,.8);font-size:13px;font-weight:600;padding:6px 0;white-space:nowrap;transition:.3s}}
.menu a:hover,.menu a.active{{color:var(--gold-soft)}}
.burger{{display:none;background:none;border:none;width:44px;height:44px;position:relative;z-index:210}}
.burger span{{position:absolute;left:7px;right:7px;height:2px;background:#fff;transition:.3s;border-radius:2px}}
.burger span:nth-child(1){{top:13px}}.burger span:nth-child(2){{top:21px}}.burger span:nth-child(3){{top:29px}}
.burger.open span:nth-child(1){{top:21px;transform:rotate(45deg)}}
.burger.open span:nth-child(2){{opacity:0}}
.burger.open span:nth-child(3){{top:21px;transform:rotate(-45deg)}}
.scrim{{position:fixed;inset:0;background:rgba(0,0,0,.5);opacity:0;visibility:hidden;transition:.35s;z-index:195}}
.scrim.show{{opacity:1;visibility:visible}}
.panel{{position:relative;min-height:100vh;display:flex;align-items:center;padding:150px 0;overflow:hidden}}
.panel .bg{{position:absolute;inset:-14% 0;z-index:0;background-size:cover;background-position:center}}
.panel .bg::after{{content:"";position:absolute;inset:0;background:linear-gradient(to right,rgba(10,8,6,.94) 22%,rgba(10,8,6,.6) 58%,rgba(10,8,6,.75))}}
.panel--center .bg::after{{background:linear-gradient(180deg,rgba(10,8,6,.86),rgba(10,8,6,.62))}}
.panel--dark .bg::after{{background:linear-gradient(180deg,rgba(10,8,6,.9),rgba(10,8,6,.7))}}
.panel .content{{position:relative;z-index:2;width:100%}}
.panel + .panel{{margin-top:16px}}
.eyebrow{{display:inline-flex;align-items:center;gap:12px;color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:12px;font-weight:600;margin-bottom:20px}}
.eyebrow::before,.eyebrow::after{{content:"";width:42px;height:1px;background:var(--gold)}}
h1{{font-size:clamp(34px,6vw,76px);font-weight:500;line-height:1.08;color:#fff}}
h1 em{{font-style:italic}}
.sub{{color:rgba(245,239,227,.9);font-size:clamp(16px,1.8vw,19.5px);font-weight:300;margin:24px 0 34px;max-width:580px}}
.btn-row{{display:flex;gap:16px;flex-wrap:wrap}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:15px 30px;font-size:13px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;border-radius:13px;border:none;transition:.4s;cursor:pointer}}
.btn-solid{{background:linear-gradient(135deg,var(--gold-soft),var(--gold) 55%,var(--gold-deep));color:#17120b}}
.btn-solid:hover{{transform:translateY(-4px);box-shadow:0 26px 60px rgba(212,175,106,.45)}}
.btn-line{{border:1px solid rgba(255,255,255,.4);color:#fff;background:rgba(255,255,255,.04)}}
.btn-line:hover{{background:rgba(255,255,255,.12);transform:translateY(-4px)}}
.shimmer{{background:linear-gradient(90deg,var(--gold-soft),#fff 35%,var(--gold-soft) 70%);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:sh 3.4s linear infinite}}
@keyframes sh{{0%{{background-position:0% center}}100%{{background-position:-220% center}}}}
.sec-head{{max-width:740px;margin:0 auto 52px;text-align:center}}
.sec-head .kicker{{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}}
.sec-head h2{{font-size:clamp(30px,4.4vw,48px);font-weight:500;margin:16px 0 14px;color:#faf3e6}}
.sec-head p{{color:var(--muted);font-size:15.5px}}
h2.k{{font-size:clamp(32px,4.6vw,48px);color:#faf3e6;font-weight:500;margin:16px 0 14px;text-align:center}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;text-align:center}}
.stat{{padding:32px 16px;border-radius:16px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);transition:.4s}}
.stat:hover{{transform:translateY(-6px);border-color:rgba(236,207,160,.3)}}
.stat .num{{font-family:var(--serif);font-size:58px;font-weight:500;background:linear-gradient(160deg,var(--gold-soft),var(--gold) 60%,var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.stat .lbl{{color:var(--muted);font-size:13.5px;margin-top:12px}}
.about{{display:grid;grid-template-columns:1fr 1.1fr;gap:64px;align-items:center}}
.about-card{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:48px 40px;text-align:center;border-radius:24px}}
.avatar{{width:130px;height:130px;border-radius:50%;margin:0 auto 22px;overflow:hidden;border:1.5px solid rgba(236,207,160,.65)}}
.avatar img{{width:100%;height:100%;object-fit:cover}}
.about-card h3{{font-size:29px;color:#fff}}
.about-card .role{{color:var(--gold-soft);font-size:13px;margin-top:5px}}
.about-card .sep{{width:52px;height:1px;background:var(--gold);margin:22px auto}}
.about-card p{{color:var(--muted);font-size:14.5px}}
.about-body .kicker{{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}}
.about-body h2{{font-size:clamp(30px,3.6vw,44px);font-weight:500;margin:16px 0 22px;color:#faf3e6}}
.about-body p{{color:var(--muted);font-size:15.5px;margin-bottom:26px}}
.features{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.features li{{position:relative;padding-left:36px;font-size:14.5px}}
.features li::before{{content:"";position:absolute;left:0;top:4px;width:18px;height:18px;border:1.5px solid rgba(212,175,106,.6);border-radius:50%}}
.features li::after{{content:"✓";position:absolute;left:4px;top:4px;font-size:11px;color:var(--gold-soft);font-weight:800}}
.consult .phone{{display:inline-block;font-weight:800;font-size:clamp(30px,4.4vw,52px);letter-spacing:1px;margin-top:12px;background:linear-gradient(120deg,var(--gold-soft),var(--gold));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap}}
.consult p{{color:var(--muted);font-size:15.5px;margin:30px auto 0;max-width:630px}}
.carousel{{position:relative;max-width:1120px;margin:0 auto}}
.car-track{{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;padding:12px 8px 24px;scrollbar-width:none}}
.car-track::-webkit-scrollbar{{display:none}}
.car-nav{{position:absolute;top:38%;transform:translateY(-50%);width:48px;height:48px;border-radius:50%;background:rgba(14,12,9,.68);border:1px solid rgba(236,207,160,.35);color:var(--gold-soft);font-size:21px;cursor:pointer;z-index:5;display:flex;align-items:center;justify-content:center}}
.car-prev{{left:-16px}}.car-next{{right:-16px}}
.car-dots{{display:flex;justify-content:center;gap:10px;margin-top:12px;flex-wrap:wrap}}
.car-dot{{width:8px;height:8px;min-width:8px;border-radius:99px;background:rgba(255,255,255,.2);cursor:pointer;transition:.35s;border:none;padding:0}}
.car-dot.active{{width:26px;background:linear-gradient(135deg,var(--gold-soft),var(--gold))}}
.swipe-hint{{text-align:center;color:var(--muted);font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-top:10px}}
.car-slide{{flex:0 0 auto;width:min(78vw,440px);scroll-snap-align:center;border-radius:24px;overflow:hidden;border:1px solid rgba(255,255,255,.08);cursor:zoom-in;transition:.5s}}
.car-slide:hover{{transform:translateY(-8px);border-color:rgba(236,207,160,.3)}}
.car-slide img{{width:100%;height:300px;object-fit:cover}}
.rev-card{{scroll-snap-align:center;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:24px;padding:24px 26px;width:min(82vw,520px);flex:0 0 auto}}
.rev-head{{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}}
.rev-ava{{width:50px;height:50px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.6)}}
.rev-name{{color:#fff;font-weight:700;font-size:14.5px}}
.rev-sub{{color:var(--muted);font-size:11px;margin-top:2px}}
.rev-stars{{color:var(--gold-soft);letter-spacing:3px;font-size:14px;margin-left:auto}}
.rev-text{{color:#ece2cd;font-size:13.5px;line-height:1.66;font-weight:300}}
.rev-video{{margin-top:14px;border-radius:16px;overflow:hidden}}
.video-box{{position:relative;width:100%;height:260px;background-size:cover;background-position:center;cursor:pointer}}
.video-box iframe{{position:absolute;inset:0;width:100%;height:100%;border:0}}
.svc-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
.svc{{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 30px;transition:.5s;border-radius:24px}}
.svc:hover{{transform:translateY(-8px);border-color:rgba(236,207,160,.26)}}
.svc svg{{width:34px;height:34px;stroke:var(--gold-soft);fill:none;stroke-width:1.4;margin-bottom:20px}}
.svc h3{{font-size:23px;color:#fff;margin-bottom:9px}}
.svc p{{color:var(--muted);font-size:14px}}
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
.step{{padding:34px 26px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:24px;transition:.45s}}
.step:hover{{transform:translateY(-7px);border-color:rgba(236,207,160,.28)}}
.step .n{{font-family:var(--serif);font-size:54px;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}}
.step h3{{font-size:22px;color:#fff;margin:14px 0 8px}}
.step p{{color:var(--muted);font-size:14px}}
.guar-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}}
.guar{{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 26px;text-align:center;transition:.45s;border-radius:24px}}
.guar:hover{{transform:translateY(-8px);border-color:rgba(236,207,160,.26)}}
.guar .ico{{width:54px;height:54px;margin:0 auto 18px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft)}}
.guar .ico svg{{width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:1.5}}
.guar h3{{font-size:18px;color:#fff;margin-bottom:8px}}
.guar p{{color:var(--muted);font-size:13px}}
.city-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}}
.city{{padding:38px 28px;border-radius:24px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);text-align:center;transition:.45s}}
.city:hover{{transform:translateY(-7px);border-color:rgba(236,207,160,.26)}}
.city .city-name{{font-family:var(--serif);font-size:28px;color:#fff;font-weight:500}}
.city .city-line{{width:42px;height:1px;background:var(--gold);margin:14px auto}}
.city p{{color:var(--muted);font-size:14px}}
.contact-grid{{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}}
.contact-info h2{{font-size:clamp(30px,4.1vw,46px);color:#faf3e6;margin:16px 0 14px}}
.contact-info .kicker{{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}}
.contact-info>p{{color:var(--muted);font-size:15.5px;margin-bottom:32px}}
.c-line{{display:flex;align-items:flex-start;gap:20px;margin-bottom:24px}}
.c-ico{{width:44px;height:44px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);flex-shrink:0}}
.c-line .lab{{font-size:10.5px;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}}
.c-line .val{{font-size:18px;font-weight:600;color:var(--text)}}
.call-block{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:46px 36px;text-align:center;border-radius:24px}}
.call-block .cb-lab{{font-size:12px;letter-spacing:4px;text-transform:uppercase;color:var(--gold-soft)}}
.call-block .cb-num{{display:block;font-weight:800;font-size:clamp(27px,3.6vw,44px);color:#fff;margin:14px 0 18px;white-space:nowrap}}
.call-block .cb-hint{{color:var(--muted);font-size:14px}}
.contact-actions{{display:flex;flex-direction:column;gap:12px;margin-top:24px}}
.c-action{{display:flex;align-items:center;justify-content:center;gap:11px;min-height:52px;padding:15px 18px;border-radius:12px;font-weight:700;font-size:14.5px;transition:.4s;color:#fff;text-decoration:none}}
.c-call{{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b}}
.c-tg{{background:rgba(64,169,242,.12);border:1px solid rgba(64,169,242,.38);color:#8fd0ff}}
.c-max{{background:rgba(177,88,252,.12);border:1px solid rgba(177,88,252,.38);color:#e0b8ff}}
.cta{{text-align:center;padding:110px 0}}
.cta h2{{font-size:clamp(32px,4.6vw,52px);color:#faf3e6;font-weight:500;margin-bottom:16px}}
.cta p{{color:var(--muted);font-size:16.5px;max-width:630px;margin:0 auto 34px}}
footer{{background:linear-gradient(180deg,rgba(14,12,9,.4),rgba(10,8,6,.97));color:var(--muted);padding:52px 20px 60px;text-align:center;font-size:13px;border-top:1px solid rgba(255,255,255,.06)}}
footer .flogo{{font-family:var(--serif);font-size:28px;color:#fff;margin-bottom:8px}}
footer .flogo span{{color:var(--gold-soft);font-size:13px;font-family:var(--sans)}}
.social-row{{display:flex;justify-content:center;gap:14px;margin:22px 0 18px;flex-wrap:wrap}}
.soc{{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:50%;border:1px solid rgba(236,207,160,.32);color:var(--gold-soft);background:rgba(212,175,106,.06);transition:.35s;font-size:18px}}
.soc:hover{{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-4px)}}
.cookie-bar{{position:fixed;bottom:16px;left:50%;transform:translate(-50%,140%);z-index:400;background:rgba(14,12,9,.93);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;width:min(680px,calc(100vw - 32px));transition:transform .6s}}
.cookie-bar.show{{transform:translate(-50%,0)}}
.cookie-bar p{{color:var(--muted);font-size:13px}}
.lightbox{{position:fixed;inset:0;z-index:3000;background:rgba(8,6,4,.96);display:none;align-items:center;justify-content:center;flex-direction:column;gap:14px}}
.lightbox.open{{display:flex}}
.lb-stage{{width:100%;max-width:1180px;height:calc(100vh - 130px);display:flex;align-items:center;justify-content:center}}
.lb-stage img{{max-width:94%;max-height:100%;border-radius:24px;border:1px solid rgba(236,207,160,.55)}}
.lb-close{{position:absolute;top:18px;right:24px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#fff;font-size:28px;cursor:pointer;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center}}
.lb-nav{{width:50px;height:50px;border-radius:50%;background:rgba(14,12,9,.6);border:1px solid rgba(236,207,160,.5);color:var(--gold-soft);font-size:24px;cursor:pointer;display:flex;align-items:center;justify-content:center}}
.lb-bar{{display:flex;align-items:center;gap:20px}}
.lb-count{{color:var(--muted);font-size:13px}}
.js .reveal{{opacity:0;transform:translateY(26px);transition:.8s}}
.js .reveal.in{{opacity:1;transform:none}}
@media(max-width:1024px){{.stats,.svc-grid,.guar-grid{{grid-template-columns:repeat(2,1fr)}}.panel{{padding:132px 0}}}}
@media(max-width:860px){{
  .menu{{position:fixed;top:auto;left:0;right:0;bottom:0;width:100%;max-height:82vh;background:linear-gradient(180deg,#16130e,#0b0907);flex-direction:column;gap:4px;padding:12px 24px calc(22px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .45s;z-index:205;border-radius:26px 26px 0 0;overflow-y:auto;height:auto;border-top:1px solid rgba(236,207,160,.2)}}
  .menu.open{{transform:none}}
  .menu a{{font-size:19px;font-family:var(--serif);color:#fff;border-bottom:1px solid rgba(236,207,160,.12);padding:13px 6px;display:flex;align-items:center;min-height:48px}}
  .burger{{display:block}}
  .about,.contact-grid,.features,.steps,.city-grid{{grid-template-columns:1fr}}
  .car-nav{{display:none}}
}}
@media(max-width:768px){{.stats,.guar-grid{{grid-template-columns:1fr 1fr}}.svc-grid,.steps{{grid-template-columns:1fr}}.panel{{padding:104px 0 60px}}}}
@media(max-width:520px){{
  .brand-ava{{width:40px;height:40px}}.brand-txt .name{{font-size:20px}}.nav{{height:64px}}
  .panel{{min-height:auto;padding:96px 0 56px}}
  h1{{font-size:31px}}.btn-row{{width:100%}}.btn{{width:100%;text-align:center}}
  .car-slide{{width:84vw}}.car-slide img{{height:205px}}.rev-card{{width:92vw;padding:17px}}
}}
</style>
</head>
<body>
<header id="header">
  <div class="wrap nav">
    <a href="#top" class="logo" id="logo">
      <img class="brand-ava" src="{_attr(b.get("logo_url",""))}" width="46" height="46" alt="{_attr(b.get("name",""))}">
      <span class="brand-txt"><span class="name">{_esc(b.get("name",""))}</span><span class="sub">{_esc(b.get("sub",""))}</span></span>
    </a>
    <button class="burger" id="burger" aria-label="Меню"><span></span><span></span><span></span></button>
  </div>
</header>
<ul class="menu" id="menu">
  <li><a href="#about">Специалист</a></li>
  <li><a href="#works">Работы</a></li>
  <li><a href="#reviews">Отзывы</a></li>
  <li><a href="#services">Услуги</a></li>
  <li><a href="#process">Как работаем</a></li>
  <li><a href="#cities">Города</a></li>
  <li><a href="#contacts">Контакты</a></li>
</ul>
<div class="scrim" id="scrim"></div>

<section class="panel" id="top">
  <div class="bg" style="background-image:url('{_attr(hero.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <span class="eyebrow">{_esc(hero.get("eyebrow",""))}</span>
    <h1>{_esc(hero.get("title_before",""))}<em class="shimmer">{_esc(hero.get("title_em",""))}</em></h1>
    <p class="sub">{_esc(hero.get("sub",""))}</p>
    <div class="btn-row">
      <a href="#consult" class="btn btn-solid">{_esc(hero.get("btn1",""))}</a>
      <a href="#works" class="btn btn-line">{_esc(hero.get("btn2",""))}</a>
    </div>
  </div></div>
</section>

<section class="panel panel--dark">
  <div class="bg" style="background-image:url('{_attr(stats.get("bg",""))}')"></div>
  <div class="wrap"><div class="content"><div class="stats">{stat_html()}</div></div></div>
</section>

<section class="panel" id="about">
  <div class="bg" style="background-image:url('{_attr(about.get("bg",""))}')"></div>
  <div class="wrap"><div class="content"><div class="about">
    <div class="about-card reveal">
      <div class="avatar"><img src="{_attr(about.get("photo",""))}" width="130" height="130" alt="{_attr(about.get("name",""))}"></div>
      <h3>{_esc(about.get("name",""))}</h3>
      <div class="role">{_esc(about.get("role",""))}</div>
      <div class="sep"></div>
      <p>{_esc(about.get("text",""))}</p>
    </div>
    <div class="about-body reveal">
      <div class="kicker">{_esc(about.get("kicker",""))}</div>
      <h2>{_esc(about.get("title",""))}</h2>
      <p>{_esc(about.get("body",""))}</p>
      <ul class="features">{features_html()}</ul>
    </div>
  </div></div></div>
</section>

<section class="panel panel--center panel--dark" id="consult">
  <div class="bg" style="background-image:url('{_attr(consult.get("bg",""))}')"></div>
  <div class="wrap"><div class="content consult">
    <span style="color:var(--gold-soft);letter-spacing:6px;text-transform:uppercase;font-size:12px;font-weight:600">{_esc(consult.get("kicker",""))}</span>
    <h2 class="k">{_esc(consult.get("title",""))}</h2>
    <a href="tel:{_attr(b.get('phone_raw',''))}" class="phone">{_esc(b.get("phone",""))}</a>
    <p>{consult.get("text","")}</p>
  </div></div>
</section>

<section class="panel panel--center panel--dark" id="works">
  <div class="bg" style="background-image:url('{_attr(works.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{_esc(works.get("kicker",""))}</div>
      <h2>{_esc(works.get("title",""))}</h2>
      <p>{_esc(works.get("subtitle",""))}</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="carPrev">❮</button>
      <div class="car-track" id="carTrack">{works_html()}</div>
      <button class="car-nav car-next" id="carNext">❯</button>
      <div class="car-dots" id="carDots"></div>
      <div class="swipe-hint">Листайте</div>
    </div>
  </div></div>
</section>

<div class="lightbox" id="lightbox">
  <button class="lb-close" id="lbClose">×</button>
  <div class="lb-stage"><img id="lbImg" alt="Работа"></div>
  <div class="lb-bar">
    <button class="lb-nav" id="lbPrev">❮</button>
    <div class="lb-count" id="lbCount"></div>
    <button class="lb-nav" id="lbNext">❯</button>
  </div>
</div>

<section class="panel panel--center" id="reviews">
  <div class="bg" style="background-image:url('{_attr(reviews.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{_esc(reviews.get("kicker",""))}</div>
      <h2>{_esc(reviews.get("title",""))}</h2>
      <p>{_esc(reviews.get("subtitle",""))}</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="revPrev">❮</button>
      <div class="car-track rev-track" id="revTrack">{reviews_html()}</div>
      <button class="car-nav car-next" id="revNext">❯</button>
      <div class="car-dots" id="revDots"></div>
      <div class="swipe-hint">Листайте</div>
    </div>
  </div></div>
</section>

<section class="panel panel--dark" id="services">
  <div class="bg" style="background-image:url('{_attr(services.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{_esc(services.get("kicker",""))}</div>
      <h2>{_esc(services.get("title",""))}</h2>
      <p>{_esc(services.get("subtitle",""))}</p>
    </div>
    <div class="svc-grid">{services_html()}</div>
  </div></div>
</section>

<section class="panel" id="process">
  <div class="bg" style="background-image:url('{_attr(process.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{_esc(process.get("kicker",""))}</div>
      <h2>{_esc(process.get("title",""))}</h2>
    </div>
    <div class="steps">{process_html()}</div>
  </div></div>
</section>

<section class="panel panel--dark">
  <div class="bg" style="background-image:url('{_attr(guarantees.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{_esc(guarantees.get("kicker",""))}</div>
      <h2>{_esc(guarantees.get("title",""))}</h2>
    </div>
    <div class="guar-grid">{guarantees_html()}</div>
  </div></div>
</section>

<section class="panel panel--center panel--dark" id="cities">
  <div class="bg" style="background-image:url('{_attr(cities.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{_esc(cities.get("kicker",""))}</div>
      <h2>{_esc(cities.get("title",""))}</h2>
      <p>{_esc(cities.get("subtitle",""))}</p>
    </div>
    <div class="city-grid">{cities_html()}</div>
  </div></div>
</section>

<section class="panel panel--center panel--dark">
  <div class="bg" style="background-image:url('{_attr(cta.get("bg",""))}')"></div>
  <div class="wrap"><div class="content cta">
    <h2 class="reveal shimmer">{_esc(cta.get("title",""))}</h2>
    <p class="reveal">{_esc(cta.get("text",""))}</p>
    <a href="tel:{_attr(b.get('phone_raw',''))}" class="btn btn-solid reveal">{_esc(cta.get("button",""))}</a>
  </div></div>
</section>

<section class="panel panel--dark" id="contacts">
  <div class="bg" style="background-image:url('{_attr(contacts.get("bg",""))}')"></div>
  <div class="wrap"><div class="content">
    <div class="contact-grid">
      <div class="contact-info reveal">
        <div class="kicker">{_esc(contacts.get("kicker",""))}</div>
        <h2>{_esc(contacts.get("title",""))}</h2>
        <p>{_esc(contacts.get("subtitle",""))}</p>
        <div class="c-line"><div class="c-ico">📍</div><div><div class="lab">Регион работы</div><div class="val">{_esc(contacts.get("regions",""))}</div></div></div>
        <div class="c-line"><div class="c-ico">VK</div><div><div class="lab">Сайт в VK</div><a class="val" href="{_attr(b.get('vk',''))}" target="_blank" rel="noopener">mebel.ostrovsky</a></div></div>
        <div class="c-line"><div class="c-ico">✈</div><div><div class="lab">Telegram / MAX</div><div class="val">по номеру {_esc(b.get("phone",""))}</div></div></div>
      </div>
      <div class="reveal">
        <div class="call-block">
          <div class="cb-lab">Свяжитесь с нами удобным способом</div>
          <a class="cb-num" href="tel:{_attr(b.get('phone_raw',''))}">{_esc(b.get("phone",""))}</a>
          <div class="cb-hint">Бесплатная консультация и запись на замер.<br>Звоните или пишите в любой мессенджер.</div>
          <div class="contact-actions">
            <a class="c-action c-call" href="tel:{_attr(b.get('phone_raw',''))}">📞 Позвонить</a>
            <a class="c-action c-tg" href="{_attr(b.get('telegram',''))}" target="_blank" rel="noopener">✈ Написать в Telegram</a>
            <a class="c-action c-max" href="{_attr(b.get('max',''))}">🛡 Написать в MAX</a>
          </div>
        </div>
      </div>
    </div>
  </div></div>
</section>

<footer>
  <div class="flogo">{_esc(b.get("name",""))}<span> · {_esc(b.get("sub",""))}</span></div>
  <div class="social-row">
    <a class="soc" href="tel:{_attr(b.get('phone_raw',''))}" title="Позвонить">📞</a>
    <a class="soc" href="{_attr(b.get('telegram',''))}" target="_blank" rel="noopener" title="Telegram">✈</a>
    <a class="soc" href="{_attr(b.get('vk',''))}" target="_blank" rel="noopener" title="ВКонтакте">VK</a>
  </div>
  <p>{_esc(footer.get("line",""))}</p>
  <p style="margin-top:8px">© <span id="year"></span> {_esc(footer.get("copyright",""))}</p>
</footer>

<div class="cookie-bar" id="cookieBar">
  <p>Мы используем cookie для корректной работы сайта.</p>
  <button class="btn btn-solid" id="cookieOk">Принять</button>
</div>

<script>
(function(){{
const header=document.getElementById('header');
const burger=document.getElementById('burger'),menu=document.getElementById('menu'),scrim=document.getElementById('scrim');
let menuOpen=false;
window.addEventListener('scroll',()=>{{header.classList.toggle('solid',window.scrollY>40);}},{{passive:true}});
function closeMenu(){{burger.classList.remove('open');menu.classList.remove('open');scrim.classList.remove('show');menuOpen=false;}}
function openMenu(){{burger.classList.add('open');menu.classList.add('open');scrim.classList.add('show');menuOpen=true;}}
burger.addEventListener('click',()=>{{menuOpen?closeMenu():openMenu();}});
scrim.addEventListener('click',closeMenu);
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));

function animateCount(el){{const target=parseFloat(el.dataset.count);const dec=parseInt(el.dataset.decimal||'0');const suffix=el.dataset.suffix||'';const dur=1200,start=performance.now();function tick(t){{let p=Math.min((t-start)/dur,1);p=1-Math.pow(1-p,3);let val=(target*p).toFixed(dec);el.textContent=(dec?val:Math.round(val))+suffix;if(p<1)requestAnimationFrame(tick);}}requestAnimationFrame(tick);}}
const statIO=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{animateCount(e.target);statIO.unobserve(e.target);}}}});}},{{threshold:.5}});
document.querySelectorAll('.stat .num').forEach(el=>statIO.observe(el));
const io=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('in');io.unobserve(e.target);}}}});}},{{threshold:.12}});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

function initCarousel(trackId,prevId,nextId,dotsId){{const track=document.getElementById(trackId),prev=document.getElementById(prevId),next=document.getElementById(nextId),dotsBox=document.getElementById(dotsId),items=[...track.children];if(!items.length)return;dotsBox.innerHTML='';items.forEach((_,i)=>{{const d=document.createElement('button');d.className='car-dot'+(i===0?' active':'');d.setAttribute('aria-label','Слайд '+(i+1));d.addEventListener('click',()=>items[i].scrollIntoView({{behavior:'smooth',inline:'center',block:'nearest'}}));dotsBox.appendChild(d);}});const dots=[...dotsBox.children];const step=()=>items[0].offsetWidth+20;let sTick=false;track.addEventListener('scroll',()=>{{if(sTick)return;sTick=true;requestAnimationFrame(()=>{{const idx=Math.round(track.scrollLeft/step());dots.forEach((d,i)=>d.classList.toggle('active',i===idx));sTick=false;}});}},{{passive:true}});prev.addEventListener('click',()=>track.scrollBy({{left:-step(),behavior:'smooth'}}));next.addEventListener('click',()=>track.scrollBy({{left:step(),behavior:'smooth'}}));}}
initCarousel('carTrack','carPrev','carNext','carDots');
initCarousel('revTrack','revPrev','revNext','revDots');

const lightbox=document.getElementById('lightbox'),lbImg=document.getElementById('lbImg'),lbCount=document.getElementById('lbCount');
const lbItems=[...document.querySelectorAll('#carTrack .car-slide img')];let lbIdx=0;
function openLb(i){{lbIdx=i;lbImg.src=lbItems[i].src;lbImg.alt=lbItems[i].alt;lbCount.textContent=(i+1)+' / '+lbItems.length;lightbox.classList.add('open');document.body.style.overflow='hidden';}}
function closeLb(){{lightbox.classList.remove('open');document.body.style.overflow='';}}
function lbStep(d){{openLb((lbIdx+d+lbItems.length)%lbItems.length);}}
lbItems.forEach((img,i)=>img.addEventListener('click',()=>openLb(i)));
document.getElementById('lbClose').addEventListener('click',closeLb);
document.getElementById('lbPrev').addEventListener('click',e=>{{e.stopPropagation();lbStep(-1);}});
document.getElementById('lbNext').addEventListener('click',e=>{{e.stopPropagation();lbStep(1);}});
lightbox.addEventListener('click',e=>{{if(e.target===lightbox)closeLb();}});
document.addEventListener('keydown',e=>{{if(lightbox.classList.contains('open')){{if(e.key==='Escape')closeLb();if(e.key==='ArrowLeft')lbStep(-1);if(e.key==='ArrowRight')lbStep(1);}}}});

document.querySelectorAll('.video-box').forEach(box=>{{box.addEventListener('click',()=>{{if(box.querySelector('iframe'))return;const iframe=document.createElement('iframe');iframe.src=box.dataset.src;iframe.setAttribute('allow','autoplay; encrypted-media; fullscreen');iframe.setAttribute('allowfullscreen','1');box.innerHTML='';box.appendChild(iframe);}});}});

const cookieBar=document.getElementById('cookieBar'),cookieOk=document.getElementById('cookieOk');
if(!localStorage.getItem('cookiesAccepted')){{setTimeout(()=>cookieBar.classList.add('show'),900);}}
cookieOk.addEventListener('click',()=>{{localStorage.setItem('cookiesAccepted','1');cookieBar.classList.remove('show');}});
document.getElementById('year').textContent=new Date().getFullYear();
}})();
</script>
</body></html>"""


# ---------- Админка ----------
ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Вход в админку</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:linear-gradient(135deg,#0e0c09,#1a1611);color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.2);border-radius:20px;padding:42px 38px;width:100%;max-width:420px}
h1{font-family:Georgia,serif;font-size:28px;color:#fff;margin-bottom:8px;text-align:center}
p.sub{color:#b9ad9a;font-size:13.5px;text-align:center;margin-bottom:28px}
label{display:block;color:#eccfa0;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:600}
input{width:100%;padding:14px 16px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;font-size:15px;font-family:inherit;margin-bottom:18px}
input:focus{outline:none;border-color:#d4af6a}
button{width:100%;padding:15px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;font-size:14px;letter-spacing:1.2px;text-transform:uppercase;border:none;border-radius:12px;cursor:pointer}
button:hover{transform:translateY(-3px)}
.err{background:rgba(220,60,60,.14);border:1px solid rgba(220,60,60,.4);color:#ff9a9a;padding:12px 14px;border-radius:10px;font-size:13px;margin-bottom:18px;text-align:center}
</style></head><body>
<form class="card" method="POST" action="/admin/login">
  <h1>Кухни Островский</h1>
  <p class="sub">Вход в панель управления</p>
  __ERROR__
  <label>Логин</label>
  <input type="text" name="login" required autofocus>
  <label>Пароль</label>
  <input type="password" name="password" required>
  <button type="submit">Войти</button>
</form></body></html>"""


ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Админка — Кухни Островский</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--gold:#d4af6a;--gold-soft:#eccfa0;--bg:#0e0c09;--line:rgba(236,207,160,.16)}
body{font-family:system-ui,sans-serif;background:var(--bg);color:#f5efe3;min-height:100vh;line-height:1.55}
header{background:rgba(14,12,9,.95);border-bottom:1px solid var(--line);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;flex-wrap:wrap;gap:12px}
.brand{font-family:Georgia,serif;font-size:20px;color:#fff}
.brand span{color:var(--gold-soft);font-size:13px;font-family:system-ui;margin-left:8px}
.actions{display:flex;gap:10px;flex-wrap:wrap}
.btn{padding:10px 18px;border-radius:10px;border:1px solid var(--line);background:rgba(255,255,255,.04);color:#f5efe3;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px;font-family:inherit}
.btn:hover{border-color:var(--gold);color:var(--gold-soft)}
.btn-gold{background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;border:none}
.btn-gold:hover{transform:translateY(-2px)}
.btn-red{background:rgba(220,60,60,.14);border-color:rgba(220,60,60,.35);color:#ff9a9a}
.layout{display:flex;min-height:calc(100vh - 65px)}
nav.side{width:230px;background:rgba(0,0,0,.25);border-right:1px solid var(--line);padding:16px 0;flex-shrink:0;overflow-y:auto;position:sticky;top:65px;height:calc(100vh - 65px)}
nav.side a{display:block;padding:12px 22px;color:#b9ad9a;text-decoration:none;font-size:14px;border-left:3px solid transparent;cursor:pointer}
nav.side a:hover{color:#fff;background:rgba(255,255,255,.03)}
nav.side a.active{color:var(--gold-soft);border-left-color:var(--gold);background:rgba(212,175,106,.06)}
main{flex:1;padding:28px 34px;max-width:1100px;overflow-x:hidden}
h2{font-family:Georgia,serif;font-size:26px;color:#fff;margin-bottom:6px}
p.hint{color:#b9ad9a;font-size:13px;margin-bottom:22px}
.section{display:none}.section.active{display:block}
.field{margin-bottom:16px}
.field label{display:block;color:var(--gold-soft);font-size:11.5px;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:7px;font-weight:600}
.field input,.field textarea{width:100%;padding:11px 14px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.12);border-radius:9px;color:#fff;font-size:14px;font-family:inherit}
.field textarea{resize:vertical;min-height:80px}
.field input:focus,.field textarea:focus{outline:none;border-color:var(--gold)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.item{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:18px;margin-bottom:14px}
.item-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:10px;flex-wrap:wrap}
.item-head strong{color:var(--gold-soft);font-size:13.5px}
.mini{padding:6px 12px;font-size:12px;border-radius:8px}
.img-preview{width:100%;max-width:220px;height:auto;border-radius:10px;border:1px solid var(--line);margin-top:8px;display:block}
.toast{position:fixed;bottom:24px;left:50%;transform:translate(-50%,140%);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;padding:14px 26px;border-radius:12px;font-weight:700;font-size:14px;z-index:9999;transition:transform .4s}
.toast.show{transform:translate(-50%,0)}
.toast.err{background:linear-gradient(135deg,#ff8a8a,#e04a4a);color:#fff}
.burger-admin{display:none;background:none;border:1px solid var(--line);color:#fff;width:42px;height:42px;border-radius:10px;cursor:pointer;font-size:20px}
.drop{display:block;border:2px dashed var(--line);border-radius:12px;padding:22px;text-align:center;color:#b9ad9a;font-size:13px;cursor:pointer;margin-top:8px}
.drop:hover{border-color:var(--gold);color:var(--gold-soft)}
.status{font-size:12px;padding:6px 12px;border-radius:8px;display:inline-block}
.status.ok{background:rgba(80,200,120,.15);color:#7ee0a0;border:1px solid rgba(80,200,120,.4)}
.status.bad{background:rgba(220,60,60,.15);color:#ff9a9a;border:1px solid rgba(220,60,60,.4)}
@media(max-width:800px){
  nav.side{position:fixed;left:0;top:65px;bottom:0;transform:translateX(-100%);transition:.3s;z-index:99;width:240px}
  nav.side.open{transform:none}
  .row,.row-3{grid-template-columns:1fr}
  main{padding:20px 18px}
  .burger-admin{display:block}
}
</style></head><body>
<header>
  <div style="display:flex;align-items:center;gap:14px">
    <button class="burger-admin" onclick="document.querySelector('nav.side').classList.toggle('open')">☰</button>
    <div class="brand">Кухни Островский<span>CMS</span></div>
    <span class="status" id="status"></span>
  </div>
  <div class="actions">
    <a class="btn" href="/" target="_blank">👁 Сайт</a>
    <a class="btn" href="/admin/export">⬇ Экспорт</a>
    <label class="btn" style="cursor:pointer">⬆ Импорт<input type="file" accept="application/json" style="display:none" onchange="importJson(this)"></label>
    <button class="btn btn-gold" onclick="saveAll()">💾 Сохранить</button>
    <a class="btn btn-red" href="/admin/logout">Выйти</a>
  </div>
</header>
<div class="layout">
  <nav class="side">
    <a data-tab="seo">🔍 SEO</a>
    <a data-tab="brand">🏷 Бренд</a>
    <a data-tab="hero">🏠 Главный</a>
    <a data-tab="stats">📊 Цифры</a>
    <a data-tab="about">👤 О специалисте</a>
    <a data-tab="consult">💬 Консультация</a>
    <a data-tab="works" class="active">🖼 Работы</a>
    <a data-tab="reviews">⭐ Отзывы</a>
    <a data-tab="services">🛠 Услуги</a>
    <a data-tab="process">📋 Этапы</a>
    <a data-tab="guarantees">🛡 Гарантии</a>
    <a data-tab="cities">🏙 Города</a>
    <a data-tab="cta">📣 CTA</a>
    <a data-tab="contacts">📞 Контакты</a>
    <a data-tab="footer">🦶 Подвал</a>
  </nav>
  <main id="main"></main>
</div>
<div class="toast" id="toast"></div>
<script>
let DATA=null;
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function toast(m,e){const t=document.getElementById('toast');t.textContent=m;t.classList.toggle('err',!!e);t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200);}
async function loadData(){const r=await fetch('/admin/api/data',{credentials:'same-origin'});if(r.status===401){location.href='/admin/login';return;}DATA=await r.json();render();}
async function saveAll(){const r=await fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)});if(r.ok){toast('✅ Сохранено в Supabase');}else{toast('❌ Ошибка',1);}}
function getPath(o,p){return p.split('.').reduce((a,k)=>a==null?undefined:a[k],o);}
function setPath(o,p,v){const a=p.split('.');let c=o;for(let i=0;i<a.length-1;i++){const k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k];}c[a[a.length-1]]=v;}
function field(l,p,o){o=o||{};const v=getPath(DATA,p);const i=o.rows?`<textarea data-path="${p}" rows="${o.rows}">${esc(v)}</textarea>`:`<input type="text" data-path="${p}" value="${esc(v)}">`;return `<div class="field"><label>${l}</label>${i}</div>`;}
function imgField(l,p){const v=getPath(DATA,p);return `<div class="field"><label>${l}</label><input type="text" data-path="${p}" value="${esc(v)}"><label class="drop">📁 загрузить файл<input type="file" accept="image/*" style="display:none" onchange="uploadImg(this,'${p}')"></label>${v?`<img class="img-preview" src="${esc(v)}" onerror="this.style.display='none'">`:''}</div>`;}
function bindInputs(){document.querySelectorAll('[data-path]').forEach(el=>{el.addEventListener('input',()=>{setPath(DATA,el.dataset.path,el.value);});});}
async function uploadImg(inp,p){const f=inp.files[0];if(!f)return;if(f.size>8*1024*1024){toast('>8МБ',1);return;}const fd=new FormData();fd.append('file',f);toast('Загрузка...');const r=await fetch('/admin/api/upload',{method:'POST',body:fd,credentials:'same-origin'});if(!r.ok){toast('Ошибка',1);return;}const j=await r.json();setPath(DATA,p,j.url);toast('✅');render();}
function importJson(inp){const f=inp.files[0];if(!f)return;const fr=new FileReader();fr.onload=async()=>{try{const o=JSON.parse(fr.result);const r=await fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(o)});if(r.ok){toast('✅ Импорт');loadData();}else toast('❌',1);}catch(e){toast('❌ JSON',1);}};fr.readAsText(f);}
function addItem(p,v){getPath(DATA,p).push(v);render();}
function delItem(p,i){if(!confirm('Удалить?'))return;getPath(DATA,p).splice(i,1);render();}
function moveItem(p,i,d){const a=getPath(DATA,p),j=i+d;if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]];render();}

const TABS={};
TABS.seo=()=>`<h2>SEO</h2><p class="hint">Title, description, OG, верификации.</p>${field('Title','seo.title',{rows:2})}${field('Description','seo.description',{rows:3})}${field('Keywords','seo.keywords',{rows:3})}${imgField('OG-картинка','seo.og_image')}${field('Yandex verification','seo.yandex_verification')}${field('Google verification','seo.google_verification')}`;
TABS.brand=()=>`<h2>Бренд</h2><div class="row">${field('Название','brand.name')}${field('Подзаголовок','brand.sub')}</div>${imgField('Логотип','brand.logo_url')}<div class="row">${field('Телефон (визуал)','brand.phone')}${field('Телефон (tel:)','brand.phone_raw')}</div><div class="row">${field('Telegram','brand.telegram')}${field('VK','brand.vk')}</div>${field('MAX','brand.max')}`;
TABS.hero=()=>`<h2>Главный экран</h2>${field('Надзаголовок','hero.eyebrow')}${field('Заголовок до','hero.title_before')}${field('Заголовок выделенный','hero.title_em')}${field('Подзаголовок','hero.sub',{rows:3})}<div class="row">${field('Кнопка 1','hero.btn1')}${field('Кнопка 2','hero.btn2')}</div>${imgField('Фон','hero.bg')}`;
TABS.stats=()=>`<h2>Цифры</h2>${imgField('Фон','stats.bg')}${DATA.stats.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>#${i+1}</strong><button class="btn btn-red mini" onclick="delItem('stats.items',${i})">Удалить</button></div><div class="row-3">${field('Значение',`stats.items.${i}.num`)}${field('Суффикс',`stats.items.${i}.suffix`)}${field('Знаков после точки',`stats.items.${i}.decimal`)}</div>${field('Подпись',`stats.items.${i}.label`)}</div>`).join('')}<button class="btn" onclick="addItem('stats.items',{num:'0',suffix:'',decimal:'0',label:'Новое'})">+ Добавить</button>`;
TABS.about=()=>`<h2>О специалисте</h2>${imgField('Фото','about.photo')}<div class="row">${field('Имя','about.name')}${field('Должность','about.role')}</div>${field('Описание','about.text',{rows:3})}${field('Надзаголовок','about.kicker')}${field('Заголовок','about.title')}${field('Текст','about.body',{rows:4})}<div class="field"><label>Преимущества</label>${DATA.about.features.map((f,i)=>`<div style="display:flex;gap:8px;margin-bottom:8px"><input type="text" data-path="about.features.${i}" value="${esc(f)}"><button class="btn btn-red mini" onclick="delItem('about.features',${i})">×</button></div>`).join('')}<button class="btn mini" onclick="addItem('about.features','Новый пункт')">+ Добавить</button></div>${imgField('Фон','about.bg')}`;
TABS.consult=()=>`<h2>Консультация</h2>${field('Надзаголовок','consult.kicker')}${field('Заголовок','consult.title')}${field('Текст (HTML)','consult.text',{rows:4})}${imgField('Фон','consult.bg')}`;
TABS.works=()=>`<h2>Работы</h2>${field('Надзаголовок','works.kicker')}${field('Заголовок','works.title')}${field('Подзаголовок','works.subtitle')}${imgField('Фон','works.bg')}<div class="item-head" style="margin-top:20px"><strong>Фото (${DATA.works.items.length})</strong></div>${DATA.works.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>#${i+1}</strong><div><button class="btn mini" onclick="moveItem('works.items',${i},-1)">↑</button> <button class="btn mini" onclick="moveItem('works.items',${i},1)">↓</button> <button class="btn btn-red mini" onclick="delItem('works.items',${i})">Удалить</button></div></div>${imgField('Картинка',`works.items.${i}.url`)}${field('Alt',`works.items.${i}.alt`)}</div>`).join('')}<button class="btn" onclick="addItem('works.items',{url:'',alt:'Новая работа'})">+ Добавить</button>`;
TABS.reviews=()=>`<h2>Отзывы</h2>${field('Надзаголовок','reviews.kicker')}${field('Заголовок','reviews.title')}${field('Подзаголовок','reviews.subtitle')}${imgField('Фон','reviews.bg')}<div class="item-head" style="margin-top:20px"><strong>Отзывы (${DATA.reviews.items.length})</strong></div>${DATA.reviews.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.name||'')}</strong><div><button class="btn mini" onclick="moveItem('reviews.items',${i},-1)">↑</button> <button class="btn mini" onclick="moveItem('reviews.items',${i},1)">↓</button> <button class="btn btn-red mini" onclick="delItem('reviews.items',${i})">Удалить</button></div></div><div class="row">${field('Имя',`reviews.items.${i}.name`)}${field('Подпись',`reviews.items.${i}.sub`)}</div>${field('Звёзд (1-5)',`reviews.items.${i}.stars`)}${imgField('Аватар',`reviews.items.${i}.avatar`)}${field('Текст',`reviews.items.${i}.text`,{rows:5})}<div class="row">${field('Видео (URL)',`reviews.items.${i}.video`)}${field('Постер видео',`reviews.items.${i}.video_poster`)}</div></div>`).join('')}<button class="btn" onclick="addItem('reviews.items',{name:'Клиент',sub:'Кухня',stars:5,avatar:'',text:'',video:'',video_poster:''})">+ Добавить</button>`;
TABS.services=()=>`<h2>Услуги</h2>${field('Надзаголовок','services.kicker')}${field('Заголовок','services.title')}${field('Подзаголовок','services.subtitle')}${imgField('Фон','services.bg')}${DATA.services.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.title||'')}</strong><button class="btn btn-red mini" onclick="delItem('services.items',${i})">Удалить</button></div>${field('Название',`services.items.${i}.title`)}${field('Описание',`services.items.${i}.text`,{rows:2})}${field('SVG-иконка (path)',`services.items.${i}.icon`)}</div>`).join('')}<button class="btn" onclick="addItem('services.items',{title:'Новая',text:'',icon:'M12 3v18M3 12h18'})">+ Добавить</button>`;
TABS.process=()=>`<h2>Этапы</h2>${field('Надзаголовок','process.kicker')}${field('Заголовок','process.title')}${imgField('Фон','process.bg')}${DATA.process.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.n||'')} ${esc(it.title||'')}</strong><button class="btn btn-red mini" onclick="delItem('process.items',${i})">Удалить</button></div><div class="row">${field('Номер',`process.items.${i}.n`)}${field('Заголовок',`process.items.${i}.title`)}</div>${field('Текст',`process.items.${i}.text`,{rows:2})}</div>`).join('')}<button class="btn" onclick="addItem('process.items',{n:'07',title:'Шаг',text:''})">+ Добавить</button>`;
TABS.guarantees=()=>`<h2>Гарантии</h2>${field('Надзаголовок','guarantees.kicker')}${field('Заголовок','guarantees.title')}${imgField('Фон','guarantees.bg')}${DATA.guarantees.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.title||'')}</strong><button class="btn btn-red mini" onclick="delItem('guarantees.items',${i})">Удалить</button></div>${field('Заголовок',`guarantees.items.${i}.title`)}${field('Текст',`guarantees.items.${i}.text`,{rows:2})}${field('SVG path',`guarantees.items.${i}.icon`)}</div>`).join('')}<button class="btn" onclick="addItem('guarantees.items',{title:'Новое',text:'',icon:'M12 3v18'})">+ Добавить</button>`;
TABS.cities=()=>`<h2>Города</h2>${field('Надзаголовок','cities.kicker')}${field('Заголовок','cities.title')}${field('Подзаголовок','cities.subtitle')}${imgField('Фон','cities.bg')}${DATA.cities.items.map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.name||'')}</strong><button class="btn btn-red mini" onclick="delItem('cities.items',${i})">Удалить</button></div>${field('Название',`cities.items.${i}.name`)}${field('Описание',`cities.items.${i}.text`,{rows:2})}</div>`).join('')}<button class="btn" onclick="addItem('cities.items',{name:'Город',text:''})">+ Добавить</button>`;
TABS.cta=()=>`<h2>CTA</h2>${field('Заголовок','cta.title')}${field('Текст','cta.text',{rows:3})}${field('Кнопка','cta.button')}${imgField('Фон','cta.bg')}`;
TABS.contacts=()=>`<h2>Контакты</h2>${field('Надзаголовок','contacts.kicker')}${field('Заголовок','contacts.title')}${field('Подзаголовок','contacts.subtitle',{rows:2})}${field('Регионы','contacts.regions')}${imgField('Фон','contacts.bg')}`;
TABS.footer=()=>`<h2>Подвал</h2>${field('Строка','footer.line')}${field('Копирайт','footer.copyright')}`;

function render(){const a=document.querySelector('nav.side a.active')?.dataset.tab||'works';document.getElementById('main').innerHTML=(TABS[a]||(()=>'<h2>?</h2>'))();bindInputs();}
document.querySelectorAll('nav.side a').forEach(x=>x.addEventListener('click',()=>{document.querySelectorAll('nav.side a').forEach(y=>y.classList.remove('active'));x.classList.add('active');render();document.querySelector('nav.side').classList.remove('open');}));

async function checkStatus(){
  try{
    const r = await fetch('/admin/api/data', {credentials:'same-origin'});
    const el = document.getElementById('status');
    if(r.ok){ el.className='status ok'; el.textContent='🟢 Supabase'; }
    else { el.className='status bad'; el.textContent='🔴 Нет связи'; }
  }catch(e){
    const el = document.getElementById('status');
    el.className='status bad'; el.textContent='🔴 Ошибка';
  }
}
loadData();
checkStatus();
</script></body></html>"""


# ---------- HTTP-сервер ----------
def parse_multipart(body, boundary):
    parts = body.split(b"--" + boundary)
    for p in parts:
        if b"Content-Disposition" not in p:
            continue
        head, _, data = p.partition(b"\r\n\r\n")
        if not data:
            continue
        data = data.rstrip(b"\r\n--")
        if b'name="file"' in head:
            m = re.search(rb'filename="([^"]*)"', head)
            ctype = b"application/octet-stream"
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-type:"):
                    ctype = line.split(b":", 1)[1].strip()
            return data, ctype, (m.group(1).decode("utf-8", "ignore") if m else "file")
    return None, None, None


STATIC_EXT = {".html", ".txt", ".svg", ".png", ".jpg", ".jpeg", ".ico",
              ".xml", ".webmanifest", ".json", ".css", ".js", ".webp", ".gif"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cookie_token(self):
        raw = self.headers.get("Cookie", "")
        if not raw:
            return None
        try:
            c = SimpleCookie(); c.load(raw)
            m = c.get("admin_session")
            return m.value if m else None
        except Exception:
            return None

    def _is_admin(self):
        return _check_session(self._cookie_token())

    def _send(self, code, body, ctype="text/plain; charset=utf-8",
              cache="no-cache", gzip_ok=True, extra=None):
        data = body.encode("utf-8") if isinstance(body, str) else body
        etag = '"' + hashlib.sha256(data).hexdigest()[:20] + '"'

        if code == 200 and self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache)
            self.end_headers()
            return

        ae = self.headers.get("Accept-Encoding", "")
        if gzip_ok and isinstance(body, str) and "gzip" in ae and len(data) > 700:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz:
                gz.write(data)
            data = buf.getvalue()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        else:
            self.send_response(code)
            self.send_header("Content-Type", ctype)

        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location, set_cookie=None):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-cache")
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except Exception:
            n = 0
        if n <= 0 or n > MAX_UPLOAD * 3:
            return b""
        return self.rfile.read(n)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False),
                   "application/json; charset=utf-8")

    def _serve_static(self, path):
        """Отдаёт файлы из корня проекта (robots.txt, favicon.svg, google*.html и т.д.)."""
        safe = path.lstrip("/")
        if not safe or ".." in safe or safe.startswith("."):
            return False
        ext = os.path.splitext(safe)[1].lower()
        if ext not in STATIC_EXT:
            return False
        full = os.path.join(ROOT, safe)
        if not os.path.isfile(full):
            return False
        mime, _ = mimetypes.guess_type(full)
        mime = mime or "application/octet-stream"
        try:
            with open(full, "rb") as f:
                data = f.read()
        except Exception:
            return False
        self._send(200, data, mime, "public, max-age=3600", gzip_ok=False)
        return True

    # ---------- GET ----------
    def do_GET(self):
        path = self.path.split("?")[0]

        # --- Админка ---
        if path == "/admin/login":
            html = ADMIN_LOGIN_HTML.replace("__ERROR__", "")
            self._send(200, html, "text/html; charset=utf-8")
            return
        if path == "/admin/logout":
            _drop_session(self._cookie_token())
            self._redirect("/admin/login",
                           "admin_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            return
        if path == "/admin/api/data":
            if not self._is_admin():
                self._json({"error": "unauthorized"}, 401)
                return
            self._json(load_data(force=True))
            return
        if path == "/admin/export":
            if not self._is_admin():
                self._redirect("/admin/login")
                return
            body = json.dumps(load_data(force=True), ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="site_data.json"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/admin":
            if not self._is_admin():
                self._redirect("/admin/login")
                return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8")
            return

        # --- Статика из репозитория (кроме index.html) ---
        if path != "/" and path != "/index.html":
            if self._serve_static(path):
                return

        # --- Публичные страницы ---
        d = load_data()
        if path in ("/", "/index.html"):
            self._send(200, build_page(d), "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, build_robots(d), "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, build_sitemap(d), "application/xml; charset=utf-8", "public, max-age=3600")
        elif path == "/favicon.ico":
            data = get_favicon()
            if not data:
                self._redirect(FAVICON_URL)
            elif _icons_cache["ico"]:
                self._send(200, _icons_cache["ico"], "image/x-icon",
                           "public, max-age=86400", gzip_ok=False)
            else:
                self._send(200, data, "image/x-icon",
                           "public, max-age=86400", gzip_ok=False)
        elif path == "/favicon-16x16.png":
            if _icons_cache["png16"]:
                self._send(200, _icons_cache["png16"], "image/png",
                           "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/favicon-32x32.png":
            if _icons_cache["png32"]:
                self._send(200, _icons_cache["png32"], "image/png",
                           "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/apple-touch-icon.png":
            if _icons_cache["png180"]:
                self._send(200, _icons_cache["png180"], "image/png",
                           "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/manifest.webmanifest":
            self._send(200, build_manifest(d),
                       "application/manifest+json; charset=utf-8",
                       "public, max-age=3600")
        else:
            self._send(404, build_page_404(d), "text/html; charset=utf-8", "no-cache")

    # ---------- POST ----------
    def do_POST(self):
        path = self.path.split("?")[0]

        if path == "/admin/login":
            body = self._read_body().decode("utf-8", "ignore")
            p = parse_qs(body)
            login = (p.get("login") or [""])[0]
            password = (p.get("password") or [""])[0]
            if login == ADMIN_LOGIN_ENV and password == ADMIN_PASSWORD_ENV:
                token = _new_session()
                self._redirect("/admin",
                               f"admin_session={token}; Path=/; Max-Age={SESSION_TTL}; HttpOnly; SameSite=Lax")
            else:
                html = ADMIN_LOGIN_HTML.replace(
                    "__ERROR__", '<div class="err">Неверный логин или пароль</div>')
                self._send(200, html, "text/html; charset=utf-8")
            return

        if path == "/admin/api/save":
            if not self._is_admin():
                self._json({"error": "unauthorized"}, 401); return
            try:
                obj = json.loads(self._read_body().decode("utf-8"))
            except Exception:
                self._json({"error": "bad json"}, 400); return
            ok = save_data(obj)
            self._json({"ok": ok})
            return

        if path == "/admin/api/upload":
            if not self._is_admin():
                self._json({"error": "unauthorized"}, 401); return
            body = self._read_body()
            ctype = self.headers.get("Content-Type", "")
            fb = None
            if "multipart/form-data" in ctype:
                m = re.search(r'boundary=([^;]+)', ctype)
                if m:
                    fb, _, _ = parse_multipart(body, m.group(1).strip().strip('"').encode())
            if not fb:
                self._json({"error": "no file"}, 400); return
            if len(fb) > MAX_UPLOAD:
                self._json({"error": "too big"}, 413); return
            mime = "image/jpeg"
            if fb[:8] == b"\x89PNG\r\n\x1a\n": mime = "image/png"
            elif fb[:6] in (b"GIF87a", b"GIF89a"): mime = "image/gif"
            elif fb[:4] == b"RIFF" and fb[8:12] == b"WEBP": mime = "image/webp"
            elif fb[:4] == b"<svg" or fb[:5] == b"<?xml": mime = "image/svg+xml"
            data_url = f"data:{mime};base64," + base64.b64encode(fb).decode("ascii")
            self._json({"url": data_url})
            return

        self._json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    if not _SUPABASE_LIB:
        print("⚠️  Модуль supabase не установлен: pip install supabase")
    if not SUPABASE_URL:
        print("⚠️  SUPABASE_URL не задан — работаем на дефолтах")
    print(f"🚀 Сервер запущен на http://0.0.0.0:{PORT}")
    print(f"🔐 Админка: http://0.0.0.0:{PORT}/admin")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
