#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Кухни Островский — сайт + админ-панель (/admin)
Контент читается из content.json на КАЖДЫЙ запрос -> правки видны сразу.
"""
import os
import re
import io
import gzip
import json
import time
import hmac
import hashlib
import secrets
import mimetypes
import html
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import date

# ----------------------------------------------------------------------------
# Конфигурация
# ----------------------------------------------------------------------------
DOMAIN = os.environ.get("DOMAIN", "https://кухниостровский.рф")
PORT = int(os.environ.get("PORT", "8080"))
ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "кухнироманост")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kuhroman")
SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_hex(32))
SESSION_TTL = 7 * 24 * 3600  # 7 дней

CONTENT_FILE = os.environ.get("CONTENT_FILE", "content.json")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
MAX_UPLOAD = 10 * 1024 * 1024
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".mp4", ".webm"}

HOST_FOR_SEO = DOMAIN.replace("https://", "").replace("http://", "")

# ----------------------------------------------------------------------------
# Утилиты
# ----------------------------------------------------------------------------
def esc(x):
    return html.escape(str(x), quote=True)

def load_content():
    """Читаем content.json на каждый запрос — сайт обновляется мгновенно."""
    if not os.path.exists(CONTENT_FILE):
        save_content(DEFAULT_CONTENT)
    try:
        with open(CONTENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = DEFAULT_CONTENT
    # до-заполняем недостающие ключи дефолтами, чтобы сайт не падал
    merged = json.loads(json.dumps(DEFAULT_CONTENT))
    deep_merge(merged, data)
    return merged

def deep_merge(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v

def save_content(content):
    tmp = CONTENT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONTENT_FILE)

def deep_get(d, path, default=""):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur if cur is not None else default

def set_path(obj, path, value):
    keys = path.split(".")
    cur = obj
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value

# --- сессии ----------------------------------------------------------------
def make_token():
    ts = str(int(time.time()))
    payload = ts + ":" + ADMIN_LOGIN
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + sig

def verify_token(token):
    try:
        payload, sig = token.rsplit(".", 1)
        expect = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expect):
            return False
        ts, login = payload.split(":", 1)
        if not hmac.compare_digest(login, ADMIN_LOGIN):
            return False
        return int(time.time()) - int(ts) < SESSION_TTL
    except Exception:
        return False

def get_cookie(req, name):
    raw = req.headers.get("Cookie") or ""
    for part in raw.split(";"):
        part = part.strip()
        if part.startswith(name + "="):
            return part[len(name) + 1:]
    return None

# --- favicon (рисуем сами, без внешних картинок) ---------------------------
def _make_icons():
    """Генерирует favicon: градиент + буква К. Возвращает dict с байтами."""
    out = {}
    try:
        from PIL import Image, ImageDraw
        size = 512
        img = Image.new("RGB", (size, size))
        px = img.load()
        top = (26, 18, 12)
        bot = (184, 134, 11)
        for y in range(size):
            t = y / (size - 1)
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            for x in range(size):
                px[x, y] = (r, g, b)
        d = ImageDraw.Draw(img)
        # рамка
        d.rectangle([24, 24, size - 24, size - 24], outline=(212, 175, 55), width=14)
        # буква К
        lw = 44
        cx, cy = size // 2, size // 2
        d.line([(cx, 110), (cx, size - 110)], fill=(255, 240, 200), width=lw)
        d.line([(cx, cy), (110, size - 110)], fill=(255, 240, 200), width=lw)
        d.line([(cx, cy), (size - 110, size - 110)], fill=(255, 240, 200), width=lw)
        def png_bytes(im):
            b = io.BytesIO()
            im.save(b, "PNG")
            return b.getvalue()
        out["512"] = png_bytes(img)
        out["180"] = png_bytes(img.resize((180, 180), Image.LANCZOS))
        out["32"] = png_bytes(img.resize((32, 32), Image.LANCZOS))
        out["16"] = png_bytes(img.resize((16, 16), Image.LANCZOS))
        ico = io.BytesIO()
        img.resize((64, 64), Image.LANCZOS).save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        out["ico"] = ico.getvalue()
        out["ok"] = True
    except Exception:
        # fallback: простой PNG-заглушка (без Pillow)
        out["ok"] = False
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#1a120c"/><stop offset="1" stop-color="#b8860b"/>'
            '</linearGradient></defs>'
            '<rect width="512" height="512" fill="url(#g)"/>'
            '<circle cx="256" cy="256" r="210" fill="none" stroke="#d4af37" stroke-width="16"/>'
            '<text x="256" y="330" font-size="260" text-anchor="middle" fill="#ffe8b0" '
            'font-family="Georgia, serif" font-weight="bold">К</text></svg>'
        ).encode()
        out["512"] = svg
        out["180"] = svg
        out["32"] = svg
        out["16"] = svg
        out["ico"] = svg
    return out

ICONS = _make_icons()

# ----------------------------------------------------------------------------
# HTTP-сервер
# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "SourceCraft/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    # ---------- helpers ----------
    def _send(self, body: bytes, ctype: str, status=200, cache="no-cache", etag=None, extra=None):
        try:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            if etag:
                self.send_header("ETag", etag)
                if self.headers.get("If-None-Match") == etag:
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
            enc = self.headers.get("Accept-Encoding") or ""
            if "gzip" in enc and len(body) > 512 and ctype.startswith(("text/", "application/json", "application/javascript")):
                body = gzip.compress(body, 6)
                self.send_header("Content-Encoding", "gzip")
                self.send_header("Vary", "Accept-Encoding")
            self.send_header("Content-Length", str(len(body)))
            if extra:
                for k, v in extra.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _send_html(self, text, status=200, cache="no-cache"):
        self._send(text.encode("utf-8"), "text/html; charset=utf-8", status=status, cache=cache)

    def _send_json(self, obj, status=200):
        self._send(json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8", status=status, cache="no-store")

    def _read_body(self, max_size=MAX_UPLOAD):
        length = int(self.headers.get("Content-Length") or 0)
        if length > max_size:
            raise ValueError("body too large")
        return self.rfile.read(length)

    def _need_admin(self):
        return not (get_cookie(self, "sc_admin") and verify_token(get_cookie(self, "sc_admin")))

    # ---------- GET ----------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/":
                self.page_index()
            elif path == "/admin":
                self.page_admin()
            elif path == "/robots.txt":
                self._send(ROBOTS.encode("utf-8"), "text/plain; charset=utf-8")
            elif path == "/sitemap.xml":
                self._send(SITEMAP.encode("utf-8"), "application/xml; charset=utf-8")
            elif path == "/manifest.webmanifest":
                self._send(MANIFEST.encode("utf-8"), "application/manifest+json; charset=utf-8")
            elif path == "/favicon.ico":
                self._send(ICONS["ico"], "image/x-icon", cache="public, max-age=86400")
            elif path == "/favicon-16x16.png":
                self._send(ICONS["16"], "image/png", cache="public, max-age=86400")
            elif path == "/favicon-32x32.png":
                self._send(ICONS["32"], "image/png", cache="public, max-age=86400")
            elif path == "/apple-touch-icon.png":
                self._send(ICONS["180"], "image/png", cache="public, max-age=86400")
            elif path == "/favicon-512x512.png":
                self._send(ICONS["512"], "image/png", cache="public, max-age=86400")
            elif path.startswith("/uploads/"):
                self.send_upload(path)
            else:
                self.page_404()
        except Exception as e:
            try:
                self._send_html("Ошибка сервера: " + esc(str(e)), status=500)
            except Exception:
                pass

    def page_index(self):
        c = load_content()
        html_page = render_page(c)
        etag = '"%s"' % hashlib.md5(html_page.encode("utf-8")).hexdigest()
        self._send(html_page.encode("utf-8"), "text/html; charset=utf-8", cache="no-cache", etag=etag)

    def page_404(self):
        self._send_html(PAGE_404, status=404)

    def send_upload(self, path):
        base = os.path.realpath(UPLOAD_DIR)
        fp = os.path.realpath(os.path.join(UPLOAD_DIR, os.path.basename(path)))
        if not fp.startswith(base) or not os.path.isfile(fp):
            return self.page_404()
        ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
        with open(fp, "rb") as f:
            data = f.read()
        self._send(data, ctype, cache="public, max-age=86400")

    # ---------- admin GET ----------
    def page_admin(self):
        if self._need_admin():
            return self._send_html(admin_login_page(""))
        self._send_html(admin_page(load_content()))

    # ---------- POST ----------
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/admin/login":
                self.admin_login()
            elif path == "/admin/logout":
                self.admin_logout()
            elif path == "/admin/save":
                self.admin_save()
            elif path == "/admin/upload":
                self.admin_upload()
            else:
                self._send_json({"ok": False, "error": "not found"}, 404)
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 400)

    def admin_login(self):
        form = parse_qs(self._read_body(64 * 1024).decode("utf-8"))
        login = form.get("login", [""])[0]
        pwd = form.get("password", [""])[0]
        ok_l = hmac.compare_digest(login.encode("utf-8"), ADMIN_LOGIN.encode("utf-8"))
        ok_p = hmac.compare_digest(pwd.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8"))
        if ok_l and ok_p:
            self.send_response(303)
            self.send_header("Location", "/admin")
            self.send_header("Set-Cookie", "sc_admin=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (make_token(), SESSION_TTL))
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._send_html(admin_login_page("Неверный логин или пароль"))

    def admin_logout(self):
        self.send_response(303)
        self.send_header("Location", "/admin")
        self.send_header("Set-Cookie", "sc_admin=; Path=/; HttpOnly; Max-Age=0")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def admin_save(self):
        if self._need_admin():
            return self._send_json({"ok": False, "error": "auth"}, 401)
        form = parse_qs(self._read_body(2 * 1024 * 1024).decode("utf-8"))
        section = form.get("section", [""])[0]
        raw = form.get("data", ["{}"])[0]
        data = json.loads(raw)
        content = load_content()
        if section == "full":
            if not isinstance(data, dict):
                raise ValueError("JSON должен быть объектом")
            content = data
        elif section == "MULTI":
            for k, v in data.items():
                content[k] = v
        else:
            content[section] = data
        save_content(content)
        self._send_json({"ok": True, "saved": section})

    def admin_upload(self):
        if self._need_admin():
            return self._send_json({"ok": False, "error": "auth"}, 401)
        body = self._read_body(MAX_UPLOAD)
        ctype = self.headers.get("Content-Type", "")
        parts = parse_multipart(body, ctype)
        if not parts or "file" not in parts:
            return self._send_json({"ok": False, "error": "файл не найден"}, 400)
        fname, data = parts["file"]
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ALLOWED_EXT:
            return self._send_json({"ok": False, "error": "недопустимый формат"}, 400)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        name = secrets.token_hex(8) + ext
        with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
            f.write(data)
        self._send_json({"ok": True, "url": "/uploads/" + name})


def parse_multipart(body, content_type):
    m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type or "")
    if not m:
        return None
    boundary = (m.group(1) or m.group(2)).strip().encode()
    result = {}
    for raw in body.split(b"--" + boundary):
        if raw in (b"", b"\r\n", b"--\r\n"):
            continue
        if raw.startswith(b"--"):
            continue
        head, sep, data = raw.partition(b"\r\n\r\n")
        if not sep:
            continue
        headers = head.decode("utf-8", "ignore")
        name_m = re.search(r'name="([^"]*)"', headers)
        fname_m = re.search(r'filename="([^"]*)"', headers)
        name = name_m.group(1) if name_m else ""
        fname = fname_m.group(1) if fname_m else ""
        data = data.rstrip(b"\r\n")
        result[name] = (fname, data)
    return result


# ----------------------------------------------------------------------------
# Рендер сайта
# ----------------------------------------------------------------------------
def render_works(items):
    if not items:
        return ""
    cards = ""
    for i, w in enumerate(items):
        img = w.get("image", "")
        title = w.get("title", "Работа")
        city = w.get("city", "")
        year = w.get("year", "")
        meta = " · ".join(x for x in [city, year] if x)
        cards += (
            '<article class="work-card reveal" data-full="%s">'
            '<div class="work-media"><img src="%s" alt="%s" loading="lazy">'
            '<span class="work-zoom">🔍</span></div>'
            '<div class="work-info"><h3>%s</h3>%s</div></article>'
            % (esc(json.dumps(w, ensure_ascii=False)), esc(img), esc(title), esc(title),
               '<p class="work-meta">' + esc(meta) + "</p>" if meta else "")
        )
    return (
        '<section class="section" id="works"><div class="container">'
        '<h2 class="sec-title reveal">Наши работы</h2>'
        '<p class="sec-sub reveal">Нажмите на фото, чтобы рассмотреть ближе</p>'
        '<div class="carousel" id="worksCarousel">' + cards + "</div>"
        '<div class="carousel-nav"><button class="cn-btn" data-dir="-1">←</button>'
        '<button class="cn-btn" data-dir="1">→</button></div>'
        "</div></section>"
    )

def render_reviews(items, video):
    cards = ""
    for i, r in enumerate(items):
        stars = "★" * int(r.get("rating", 5))
        cards += (
            '<article class="review-card reveal"><div class="review-stars">%s</div>'
            '<p class="review-text">%s</p>'
            '<div class="review-author">%s</div></article>'
            % (esc(stars), esc(r.get("text", "")), esc(r.get("name", "")))
        )
    if video.get("enabled") and video.get("youtube"):
        yt = video["youtube"]
        poster = video.get("poster", "")
        cards += (
            '<article class="review-card reveal video-card" data-video="%s">'
            '<div class="video-poster"><img src="%s" alt="Видеоотзыв" loading="lazy">'
            '<div class="video-play">▶</div></div>'
            '<p class="review-author">%s</p></article>'
            % (esc(yt), esc(poster), esc(video.get("author", "Видеоотзыв")))
        )
    if not cards:
        return ""
    return (
        '<section class="section" id="reviews"><div class="container">'
        '<h2 class="sec-title reveal">Отзывы</h2>'
        '<div class="carousel" id="reviewsCarousel">' + cards + "</div>"
        '<div class="carousel-nav"><button class="cn-btn" data-dir="-1">←</button>'
        '<button class="cn-btn" data-dir="1">→</button></div>'
        "</div></section>"
    )

def render_cards(items, cls, icon_key=True):
    out = ""
    for it in items:
        icon = it.get("icon", "✦") if icon_key else ""
        out += (
            '<div class="%s reveal"><div class="card-icon">%s</div>'
            "<h3>%s</h3><p>%s</p></div>"
            % (cls, esc(icon), esc(it.get("title", "")), esc(it.get("text", "")))
        )
    return out

def render_process(items):
    out = ""
    for i, it in enumerate(items):
        out += (
            '<div class="step reveal"><div class="step-num">%02d</div>'
            "<h3>%s</h3><p>%s</p></div>"
            % (i + 1, esc(it.get("title", "")), esc(it.get("text", "")))
        )
    return out

def render_page(c):
    s = c.get("site", {})
    seo = c.get("seo", {})
    hero = c.get("hero", {})
    about = c.get("about", {})
    cta = c.get("cta", {})
    cont = c.get("contacts", {})
    foot = c.get("footer", {})

    cities = "".join('<span class="city-chip">' + esc(x) + "</span>" for x in s.get("cities", []))
    features = "".join("<li>" + esc(x) + "</li>" for x in about.get("features", []))
    stats = "".join(
        '<div class="stat reveal"><div class="stat-ic">%s</div><h3>%s</h3><p>%s</p></div>'
        % (esc(x.get("icon", "")), esc(x.get("title", "")), esc(x.get("text", "")))
        for x in hero.get("stats", [])
    )
    menu_links = (
        '<a href="#about">Специалист</a><a href="#works">Работы</a>'
        '<a href="#reviews">Отзывы</a><a href="#services">Услуги</a>'
        '<a href="#process">Как работаем</a><a href="#cities">Города</a>'
        '<a href="#contacts">Контакты</a>'
    )
    services_html = render_cards(c.get("services", []), "service-card")
    guarantees_html = render_cards(c.get("guarantees", []), "guarantee-card")
    process_html = render_process(c.get("process", []))
    works_html = render_works(c.get("works", []))
    reviews_html = render_reviews(c.get("reviews", []), c.get("video", {}))

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "HomeAndConstructionBusiness", "@id": DOMAIN + "/#org",
             "name": s.get("logo", ""), "url": DOMAIN,
             "telephone": cont.get("phone", ""), "image": DOMAIN + "/favicon-512x512.png",
             "address": {"@type": "PostalAddress", "addressLocality": "Ростов-на-Дону", "addressCountry": "RU"},
             "areaServed": [{"@type": "City", "name": x} for x in s.get("cities", [])]},
            {"@type": "WebSite", "@id": DOMAIN + "/#website", "url": DOMAIN,
             "name": s.get("logo", ""), "inLanguage": "ru",
             "publisher": {"@id": DOMAIN + "/#org"}},
            {"@type": "WebPage", "@id": DOMAIN + "/#webpage", "url": DOMAIN,
             "name": seo.get("title", ""), "isPartOf": {"@id": DOMAIN + "/#website"}},
            {"@type": "ContactPage", "@id": DOMAIN + "/#contact", "url": DOMAIN + "/#contacts",
             "about": {"@id": DOMAIN + "/#org"}}
        ]
    }, ensure_ascii=False)

    page = PAGE_TEMPLATE
    page = page.replace("@@TITLE@@", esc(seo.get("title", "")))
    page = page.replace("@@DESCRIPTION@@", esc(seo.get("description", "")))
    page = page.replace("@@KEYWORDS@@", esc(seo.get("keywords", "")))
    page = page.replace("@@OGIMAGE@@", esc(DOMAIN + seo.get("ogImage", "/favicon-512x512.png")))
    page = page.replace("@@CANONICAL@@", DOMAIN + "/")
    page = page.replace("@@JSONLD@@", jsonld)
    page = page.replace("@@LOGO@@", esc(s.get("logo", "")))
    page = page.replace("@@MENU@@", menu_links)
    page = page.replace("@@PHONE@@", esc(s.get("phone", "")))
    page = page.replace("@@PHONE_HREF@@", esc(s.get("phoneHref", "#")))
    page = page.replace("@@HERO_TITLE@@", esc(hero.get("title", "")))
    page = page.replace("@@HERO_SUB@@", esc(hero.get("subtitle", "")))
    page = page.replace("@@HERO_BTN1@@", esc(hero.get("btn1", "")))
    page = page.replace("@@HERO_BTN1_HREF@@", esc(hero.get("btn1Href", "#works")))
    page = page.replace("@@HERO_BTN2@@", esc(hero.get("btn2", "")))
    page = page.replace("@@HERO_BTN2_HREF@@", esc(hero.get("btn2Href", "#contacts")))
    page = page.replace("@@HERO_WM@@", esc(hero.get("watermark", "")))
    page = page.replace("@@STATS@@", stats)
    page = page.replace("@@ABOUT_TITLE@@", esc(about.get("title", "")))
    page = page.replace("@@ABOUT_NAME@@", esc(about.get("name", "")))
    page = page.replace("@@ABOUT_TEXT@@", esc(about.get("text", "")))
    page = page.replace("@@ABOUT_FEATURES@@", features)
    page = page.replace("@@WORKS@@", works_html)
    page = page.replace("@@REVIEWS@@", reviews_html)
    page = page.replace("@@SERVICES@@", services_html)
    page = page.replace("@@PROCESS@@", process_html)
    page = page.replace("@@GUARANTEES@@", guarantees_html)
    page = page.replace("@@CITIES@@", cities)
    page = page.replace("@@CTA_TITLE@@", esc(cta.get("title", "")))
    page = page.replace("@@CTA_TEXT@@", esc(cta.get("text", "")))
    page = page.replace("@@CTA_BTN@@", esc(cta.get("btn", "")))
    page = page.replace("@@CTA_BTN_HREF@@", esc(cta.get("btnHref", "#")))
    page = page.replace("@@CONTACT_TITLE@@", esc(cont.get("title", "")))
    page = page.replace("@@CONTACT_TEXT@@", esc(cont.get("text", "")))
    page = page.replace("@@CONTACT_PHONE@@", esc(cont.get("phone", "")))
    page = page.replace("@@CONTACT_PHONE_HREF@@", esc(cont.get("phoneHref", "#")))
    page = page.replace("@@CONTACT_TG@@", esc(cont.get("telegram", "")))
    page = page.replace("@@CONTACT_TG_HREF@@", esc(cont.get("telegramHref", "#")))
    page = page.replace("@@CONTACT_VK@@", esc(cont.get("vk", "")))
    page = page.replace("@@CONTACT_VK_HREF@@", esc(cont.get("vkHref", "#")))
    page = page.replace("@@CONTACT_NOTE@@", esc(cont.get("note", "")))
    page = page.replace("@@FOOTER_TEXT@@", esc(foot.get("text", "")))
    page = page.replace("@@FOOTER_EXTRA@@", esc(foot.get("extra", "")))
    return page


# ----------------------------------------------------------------------------
# Шаблон сайта
# ----------------------------------------------------------------------------
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESCRIPTION@@">
<meta name="keywords" content="@@KEYWORDS@@">
<meta name="robots" content="index, follow">
<link rel="canonical" href="@@CANONICAL@@">
<link rel="alternate" hreflang="ru" href="@@CANONICAL@@">
<meta name="geo.region" content="RU-ROS">
<meta name="geo.placename" content="Ростов-на-Дону">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="@@LOGO@@">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESCRIPTION@@">
<meta property="og:url" content="@@CANONICAL@@">
<meta property="og:image" content="@@OGIMAGE@@">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="@@TITLE@@">
<meta name="twitter:description" content="@@DESCRIPTION@@">
<meta name="twitter:image" content="@@OGIMAGE@@">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<script type="application/ld+json">@@JSONLD@@</script>
<style>
:root{--gold:#d4af37;--gold2:#f0d78c;--bg:#14100c;--bg2:#1c1610;--card:#221a12;--text:#f5ede0;--muted:#b8a98e;--line:rgba(212,175,55,.22)}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:Georgia,'Times New Roman',serif;background:var(--bg);color:var(--text);overflow-x:hidden;line-height:1.6}
body::before{content:'';position:fixed;inset:0;z-index:-3;background:
 radial-gradient(1200px 700px at 80% -10%, rgba(212,175,55,.16), transparent 60%),
 radial-gradient(1000px 800px at -10% 30%, rgba(184,134,11,.12), transparent 60%),
 radial-gradient(900px 700px at 60% 110%, rgba(212,175,55,.10), transparent 60%),
 linear-gradient(160deg,#14100c,#1c1610 45%,#120e0a)}
body::after{content:'';position:fixed;inset:0;z-index:998;pointer-events:none;opacity:.05;
 background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='.7'/%3E%3C/svg%3E")}
.orb{position:fixed;border-radius:50%;filter:blur(70px);opacity:.5;z-index:-2;pointer-events:none;animation:float 16s ease-in-out infinite}
.orb1{width:420px;height:420px;left:-120px;top:10%;background:radial-gradient(circle,rgba(212,175,55,.35),transparent 70%)}
.orb2{width:360px;height:360px;right:-100px;top:45%;background:radial-gradient(circle,rgba(184,134,11,.30),transparent 70%);animation-delay:-6s}
.orb3{width:300px;height:300px;left:30%;bottom:-80px;background:radial-gradient(circle,rgba(212,175,55,.22),transparent 70%);animation-delay:-11s}
@keyframes float{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-30px) scale(1.06)}}
.container{max-width:1180px;margin:0 auto;padding:0 20px}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
h1,h2,h3{font-weight:normal;letter-spacing:.5px}
/* header */
#header{position:fixed;top:0;left:0;right:0;z-index:900;transition:background .3s,box-shadow .3s}
#header.solid{background:rgba(20,16,12,.92);backdrop-filter:blur(14px);box-shadow:0 1px 0 var(--line)}
.header-inner{display:flex;align-items:center;gap:18px;height:68px}
.logo{display:flex;align-items:center;gap:10px;font-size:19px}
.logo-mark{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;font-size:20px;color:#1c1610;font-weight:bold;
 background:linear-gradient(135deg,var(--gold2),var(--gold));box-shadow:0 0 0 1px rgba(212,175,55,.5),0 0 22px rgba(212,175,55,.35)}
.logo b{color:var(--gold2)}
.menu{display:flex;gap:20px;margin-left:auto;font-size:15px}
.menu a{color:var(--muted);transition:color .2s;white-space:nowrap}
.menu a:hover{color:var(--gold2)}
.header-phone{color:var(--gold2);font-size:15px;white-space:nowrap}
.burger{display:none;margin-left:auto;background:none;border:0;cursor:pointer;width:46px;height:46px;place-items:center;gap:5px;flex-direction:column}
.burger span{width:24px;height:2px;background:var(--gold2);transition:.3s}
.burger.open span:nth-child(1){transform:translateY(7px) rotate(45deg)}
.burger.open span:nth-child(2){opacity:0}
.burger.open span:nth-child(3){transform:translateY(-7px) rotate(-45deg)}
/* bottom sheet menu */
.sheet{position:fixed;left:0;right:0;bottom:0;z-index:950;background:rgba(24,19,13,.98);backdrop-filter:blur(16px);
 border-top:1px solid var(--line);border-radius:22px 22px 0 0;padding:22px 22px calc(22px + env(safe-area-inset-bottom));
 transform:translateY(105%);transition:transform .35s cubic-bezier(.2,.9,.3,1);display:none}
.sheet.open{transform:translateY(0)}
.sheet a{display:block;padding:14px 6px;font-size:17px;border-bottom:1px solid rgba(212,175,55,.1);color:var(--text)}
.sheet a:last-child{border-bottom:0}
.sheet-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:940;opacity:0;pointer-events:none;transition:.3s}
.sheet-overlay.open{opacity:1;pointer-events:auto}
/* hero */
.hero{min-height:100svh;display:flex;align-items:center;position:relative;overflow:hidden;padding:110px 0 60px}
.hero-bg{position:absolute;inset:-4%;z-index:-1;background:
 radial-gradient(700px 420px at 20% 30%, rgba(212,175,55,.16), transparent 60%),
 radial-gradient(600px 400px at 85% 70%, rgba(184,134,11,.14), transparent 60%),
 linear-gradient(150deg,#221a10,#151009 60%,#1e1710);
 animation:kenburns 26s ease-in-out infinite alternate}
@keyframes kenburns{from{transform:scale(1) translate(0,0)}to{transform:scale(1.08) translate(-1.5%,1.5%)}}
.watermark{position:absolute;font-size:clamp(70px,14vw,190px);font-weight:bold;color:transparent;-webkit-text-stroke:1px rgba(212,175,55,.10);white-space:nowrap;user-select:none;pointer-events:none;z-index:-1}
.wm1{top:8%;left:-2%;animation:wm 18s ease-in-out infinite alternate}
@keyframes wm{from{transform:translateX(0)}to{transform:translateX(-40px)}}
.hero-inner{max-width:820px}
.hero h1{font-size:clamp(34px,6vw,68px);line-height:1.12;margin-bottom:22px;
 background:linear-gradient(120deg,#fff7e6,var(--gold2) 45%,var(--gold));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .sub{font-size:clamp(16px,2.4vw,21px);color:var(--muted);max-width:640px;margin-bottom:34px}
.hero-actions{display:flex;gap:16px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:52px;padding:14px 30px;border-radius:40px;font-size:16px;border:1px solid transparent;transition:.25s;cursor:pointer;text-align:center}
.btn.gold{background:linear-gradient(135deg,var(--gold2),var(--gold));color:#1c1610;font-weight:bold;box-shadow:0 8px 30px rgba(212,175,55,.35)}
.btn.gold:hover{transform:translateY(-2px);box-shadow:0 14px 40px rgba(212,175,55,.5)}
.btn.ghost{border-color:var(--line);color:var(--gold2)}
.btn.ghost:hover{border-color:var(--gold);background:rgba(212,175,55,.08)}
.scroll-hint{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:6px;color:var(--muted);font-size:13px;animation:bob 2s ease-in-out infinite}
.scroll-hint i{width:1px;height:38px;background:linear-gradient(var(--gold),transparent)}
@keyframes bob{0%,100%{transform:translate(-50%,0)}50%{transform:translate(-50%,8px)}}
/* sections */
.section{padding:84px 0;position:relative}
.sec-title{font-size:clamp(28px,4.4vw,44px);text-align:center;margin-bottom:12px}
.sec-title::after{content:'';display:block;width:90px;height:2px;margin:16px auto 0;background:linear-gradient(90deg,transparent,var(--gold),transparent);position:relative}
.sec-title::before{content:'◆';position:absolute;left:50%;transform:translate(-50%,34px);color:var(--gold);font-size:12px;background:var(--bg);padding:0 8px}
.sec-sub{text-align:center;color:var(--muted);margin-bottom:44px;font-size:17px}
/* reveal */
.reveal{opacity:0;transform:translateY(26px);transition:opacity .8s ease,transform .8s ease}
.reveal.visible{opacity:1;transform:none}
/* stats */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}
.stat{background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(212,175,55,.05));border:1px solid var(--line);border-radius:18px;padding:26px 20px;text-align:center}
.stat-ic{font-size:34px;margin-bottom:10px}
.stat h3{color:var(--gold2);font-size:18px;margin-bottom:6px}
.stat p{color:var(--muted);font-size:14px}
/* about */
.about-grid{display:grid;grid-template-columns:1fr 1fr;gap:44px;align-items:center}
.about-card{background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(212,175,55,.05));border:1px solid var(--line);border-radius:22px;padding:36px}
.about-card h3{color:var(--gold2);font-size:26px;margin-bottom:14px}
.about-card ul{list-style:none;margin-top:18px}
.about-card li{padding:9px 0 9px 30px;position:relative;color:var(--muted)}
.about-card li::before{content:'◆';position:absolute;left:0;color:var(--gold);font-size:11px;top:14px}
/* carousel */
.carousel{display:flex;gap:22px;overflow-x:auto;scroll-snap-type:x mandatory;padding:6px 4px 22px;scrollbar-width:none}
.carousel::-webkit-scrollbar{display:none}
.work-card,.review-card{flex:0 0 320px;scroll-snap-align:start;background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(212,175,55,.05));border:1px solid var(--line);border-radius:20px;overflow:hidden;transition:.3s;cursor:pointer}
.work-card:hover{transform:translateY(-4px);border-color:rgba(212,175,55,.5);box-shadow:0 16px 44px rgba(0,0,0,.4)}
.work-media{position:relative;aspect-ratio:4/3;overflow:hidden}
.work-media img{width:100%;height:100%;object-fit:cover;transition:transform .6s}
.work-card:hover .work-media img{transform:scale(1.06)}
.work-zoom{position:absolute;right:14px;top:14px;background:rgba(20,16,12,.7);border:1px solid var(--line);width:40px;height:40px;border-radius:50%;display:grid;place-items:center;backdrop-filter:blur(6px)}
.work-info{padding:16px 18px}
.work-info h3{font-size:17px;color:var(--gold2)}
.work-meta{color:var(--muted);font-size:13px;margin-top:4px}
.carousel-nav{display:flex;justify-content:center;gap:12px;margin-top:8px}
.cn-btn{width:48px;height:48px;border-radius:50%;border:1px solid var(--line);background:rgba(212,175,55,.06);color:var(--gold2);font-size:20px;cursor:pointer;transition:.2s}
.cn-btn:hover{background:rgba(212,175,55,.18);border-color:var(--gold)}
.review-stars{color:var(--gold);letter-spacing:3px;padding:20px 20px 0;font-size:15px}
.review-text{padding:12px 20px;color:var(--text);font-size:15px;min-height:110px}
.review-author{padding:0 20px 22px;color:var(--gold2);font-weight:bold}
.video-card .video-poster{position:relative;aspect-ratio:16/9;cursor:pointer}
.video-poster img{width:100%;height:100%;object-fit:cover}
.video-play{position:absolute;inset:0;display:grid;place-items:center;font-size:40px;color:#fff;text-shadow:0 2px 20px rgba(0,0,0,.7)}
/* services / guarantees */
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:22px}
.service-card,.guarantee-card{background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(212,175,55,.05));border:1px solid var(--line);border-radius:18px;padding:26px;transition:.3s}
.service-card:hover,.guarantee-card:hover{border-color:rgba(212,175,55,.5);transform:translateY(-3px)}
.card-icon{font-size:32px;margin-bottom:12px}
.service-card h3,.guarantee-card h3{color:var(--gold2);font-size:18px;margin-bottom:8px}
.service-card p,.guarantee-card p{color:var(--muted);font-size:14px}
/* process */
.process{display:grid;grid-template-columns:repeat(5,1fr);gap:20px}
.step{position:relative;background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(212,175,55,.05));border:1px solid var(--line);border-radius:18px;padding:26px 18px;text-align:center}
.step-num{width:52px;height:52px;margin:0 auto 12px;border-radius:50%;display:grid;place-items:center;color:#1c1610;font-weight:bold;background:linear-gradient(135deg,var(--gold2),var(--gold));font-size:17px}
.step h3{color:var(--gold2);font-size:16px;margin-bottom:6px}
.step p{color:var(--muted);font-size:13px}
/* cities */
.cities{display:flex;flex-wrap:wrap;justify-content:center;gap:14px}
.city-chip{padding:14px 26px;border:1px solid var(--line);border-radius:40px;color:var(--gold2);background:rgba(212,175,55,.05);font-size:16px}
/* cta */
.cta{background:linear-gradient(135deg,rgba(212,175,55,.14),rgba(184,134,11,.10));border:1px solid var(--line);border-radius:26px;padding:56px 40px;text-align:center}
.cta h2{font-size:clamp(26px,4vw,40px);margin-bottom:14px;color:var(--gold2)}
.cta p{color:var(--muted);max-width:560px;margin:0 auto 26px}
/* contacts */
.contacts-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.contact-card{background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(212,175,55,.05));border:1px solid var(--line);border-radius:18px;padding:28px;text-align:center;transition:.3s}
.contact-card:hover{border-color:rgba(212,175,55,.5);transform:translateY(-3px)}
.contact-card .card-icon{font-size:30px}
.contact-card a{color:var(--gold2);font-size:17px;word-break:break-word}
/* footer */
footer{border-top:1px solid var(--line);padding:36px 0;text-align:center;color:var(--muted);font-size:14px}
footer .f-logo{color:var(--gold2);font-size:18px;margin-bottom:8px}
/* cookie */
.cookie{position:fixed;left:16px;right:16px;bottom:16px;z-index:960;max-width:420px;margin:0 auto;background:rgba(24,19,13,.96);border:1px solid var(--line);border-radius:16px;padding:18px 20px;font-size:14px;color:var(--muted);display:none}
.cookie.show{display:block}
.cookie button{margin-top:10px;background:linear-gradient(135deg,var(--gold2),var(--gold));color:#1c1610;border:0;padding:10px 22px;border-radius:30px;font-weight:bold;cursor:pointer}
/* lightbox */
.lightbox{position:fixed;inset:0;z-index:990;background:rgba(0,0,0,.94);display:none;align-items:center;justify-content:center;padding:20px}
.lightbox.open{display:flex}
.lightbox img{max-width:100%;max-height:88vh;border-radius:10px;touch-action:pan-x pan-y}
.lightbox .lb-close{position:absolute;top:18px;right:18px;width:48px;height:48px;border-radius:50%;border:1px solid var(--line);background:rgba(255,255,255,.06);color:#fff;font-size:22px;cursor:pointer}
/* responsive */
@media(max-width:960px){
 .menu{display:none}
 .header-phone{display:none}
 .burger{display:flex}
 .sheet{display:block}
 .stats{grid-template-columns:repeat(2,1fr)}
 .about-grid{grid-template-columns:1fr}
 .process{grid-template-columns:repeat(2,1fr)}
 .contacts-grid{grid-template-columns:1fr}
}
@media(max-width:520px){
 .stats{grid-template-columns:1fr 1fr;gap:12px}
 .stat{padding:18px 12px}
 .process{grid-template-columns:1fr}
 .carousel .work-card,.carousel .review-card{flex-basis:86%}
 .btn{width:100%}
 .hero-actions{gap:12px}
 .cta{padding:38px 20px}
}
@media(prefers-reduced-motion:reduce){
 *,*::before,*::after{animation:none!important;transition:none!important}
 .reveal{opacity:1;transform:none}
}
</style>
</head>
<body>
<div class="orb orb1"></div><div class="orb orb2"></div><div class="orb orb3"></div>

<header id="header"><div class="container header-inner">
  <a class="logo" href="#top"><span class="logo-mark">К</span><span class="logo-text">Кухни <b>Островский</b></span></a>
  <nav class="menu" id="menu">@@MENU@@</nav>
  <a class="header-phone" href="@@PHONE_HREF@@">@@PHONE@@</a>
  <button class="burger" id="burger" aria-label="Меню"><span></span><span></span><span></span></button>
</div></header>
<div class="sheet-overlay" id="sheetOverlay"></div>
<div class="sheet" id="sheet">
  <nav>@@MENU@@</nav>
  <a class="btn gold" href="@@PHONE_HREF@@" style="margin-top:16px">Позвонить: @@PHONE@@</a>
</div>

<section class="hero" id="top">
  <div class="hero-bg"></div>
  <div class="watermark wm1">@@HERO_WM@@</div>
  <div class="container hero-inner">
    <h1 class="reveal visible">@@HERO_TITLE@@</h1>
    <p class="sub reveal visible">@@HERO_SUB@@</p>
    <div class="hero-actions reveal visible">
      <a class="btn gold" href="@@HERO_BTN1_HREF@@">@@HERO_BTN1@@</a>
      <a class="btn ghost" href="@@HERO_BTN2_HREF@@">@@HERO_BTN2@@</a>
    </div>
  </div>
  <div class="scroll-hint"><span>Листайте</span><i></i></div>
</section>

<section class="section" style="padding-top:20px"><div class="container"><div class="stats">@@STATS@@</div></div></section>

<section class="section" id="about"><div class="container">
  <h2 class="sec-title reveal">@@ABOUT_TITLE@@</h2>
  <div class="about-grid">
    <div class="about-card reveal">
      <h3>@@ABOUT_NAME@@</h3>
      <p>@@ABOUT_TEXT@@</p>
      <ul>@@ABOUT_FEATURES@@</ul>
    </div>
    <div class="about-card reveal">
      <h3>Что вы получаете</h3>
      <p>Бесплатный замер и проект, прозрачная смета, собственное производство и монтаж под ключ. Помогаем с выбором материалов и фурнитуры, чтобы мебель служила долго и радовала каждый день.</p>
      <ul><li>Индивидуальный подход</li><li>Аккуратный монтаж</li><li>Уборка после установки</li></ul>
    </div>
  </div>
</div></section>

@@WORKS@@
@@REVIEWS@@

<section class="section" id="services"><div class="container">
  <h2 class="sec-title reveal">Услуги</h2>
  <p class="sec-sub reveal">Что мы делаем на заказ</p>
  <div class="cards-grid">@@SERVICES@@</div>
</div></section>

<section class="section" id="process"><div class="container">
  <h2 class="sec-title reveal">Как мы работаем</h2>
  <p class="sec-sub reveal">Понятный процесс — от заявки до готовой мебели</p>
  <div class="process">@@PROCESS@@</div>
</div></section>

<section class="section" id="guarantees"><div class="container">
  <h2 class="sec-title reveal">Гарантии</h2>
  <div class="cards-grid">@@GUARANTEES@@</div>
</div></section>

<section class="section" id="cities"><div class="container">
  <h2 class="sec-title reveal">Города</h2>
  <p class="sec-sub reveal">Работаем в Ростове-на-Дону и рядом</p>
  <div class="cities">@@CITIES@@</div>
</div></section>

<section class="section" id="contacts"><div class="container">
  <h2 class="sec-title reveal">@@CONTACT_TITLE@@</h2>
  <p class="sec-sub reveal">@@CONTACT_TEXT@@</p>
  <div class="contacts-grid">
    <div class="contact-card reveal"><div class="card-icon">📞</div><a href="@@CONTACT_PHONE_HREF@@">@@CONTACT_PHONE@@</a></div>
    <div class="contact-card reveal"><div class="card-icon">✈️</div><a href="@@CONTACT_TG_HREF@@" target="_blank" rel="noopener">@@CONTACT_TG@@</a></div>
    <div class="contact-card reveal"><div class="card-icon">🅥</div><a href="@@CONTACT_VK_HREF@@" target="_blank" rel="noopener">@@CONTACT_VK@@</a></div>
  </div>
  <p style="text-align:center;color:var(--muted);margin-top:22px">@@CONTACT_NOTE@@</p>
</div></section>

<section class="section" style="padding-top:0"><div class="container"><div class="cta reveal">
  <h2>@@CTA_TITLE@@</h2>
  <p>@@CTA_TEXT@@</p>
  <a class="btn gold" href="@@CTA_BTN_HREF@@">@@CTA_BTN@@</a>
</div></div></section>

<footer><div class="container">
  <div class="f-logo">Кухни <b>Островский</b></div>
  <p>@@FOOTER_TEXT@@ · @@FOOTER_EXTRA@@</p>
</div></footer>

<div class="lightbox" id="lightbox"><button class="lb-close" id="lbClose">✕</button><img id="lbImg" alt=""></div>

<div class="cookie" id="cookieBar"><div>Мы используем cookies, чтобы сайт работал лучше.</div><button onclick="document.getElementById('cookieBar').style.display='none';localStorage.setItem('cookieOk','1')">Хорошо</button></div>

<script>
(function(){
  var header=document.getElementById('header');
  function onScroll(){header.classList.toggle('solid',window.scrollY>10)}
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();

  var burger=document.getElementById('burger'),sheet=document.getElementById('sheet'),overlay=document.getElementById('sheetOverlay');
  function toggleMenu(open){
    burger.classList.toggle('open',open);sheet.classList.toggle('open',open);overlay.classList.toggle('open',open);
    document.body.style.overflow=open?'hidden':'';
  }
  burger.addEventListener('click',function(){toggleMenu(!sheet.classList.contains('open'))});
  overlay.addEventListener('click',function(){toggleMenu(false)});
  sheet.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){toggleMenu(false)})});

  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('visible');io.unobserve(e.target)}})},{threshold:.12});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el)});

  function setupCarousel(id){
    var wrap=document.getElementById(id);if(!wrap)return;
    var nav=wrap.parentElement.querySelector('.carousel-nav');
    if(!nav)return;
    nav.querySelectorAll('.cn-btn').forEach(function(b){
      b.addEventListener('click',function(){
        var dir=parseInt(b.dataset.dir,10);
        wrap.scrollBy({left:dir*(wrap.clientWidth*.85),behavior:'smooth'});
      });
    });
  }
  setupCarousel('worksCarousel');setupCarousel('reviewsCarousel');

  var lb=document.getElementById('lightbox'),lbImg=document.getElementById('lbImg');
  document.querySelectorAll('.work-card').forEach(function(card){
    card.addEventListener('click',function(){
      var data=JSON.parse(card.dataset.full||'{}');
      if(data.image){lbImg.src=data.image;lb.classList.add('open')}
    });
  });
  document.getElementById('lbClose').addEventListener('click',function(){lb.classList.remove('open')});
  lb.addEventListener('click',function(e){if(e.target===lb)lb.classList.remove('open')});

  document.querySelectorAll('.video-card').forEach(function(card){
    card.addEventListener('click',function(){
      var yt=card.dataset.video;if(!yt)return;
      var holder=card.querySelector('.video-poster');
      if(holder)holder.innerHTML='<iframe src="'+yt+'?autoplay=1" allow="autoplay; fullscreen" allowfullscreen style="width:100%;height:100%;border:0;position:absolute;inset:0"></iframe>';
    });
  });

  if(!localStorage.getItem('cookieOk')){setTimeout(function(){document.getElementById('cookieBar').classList.add('show')},1500)}
})();
</script>
</body>
</html>"""

ROBOTS = """User-agent: *
Allow: /
Disallow: /admin
Host: %s
Sitemap: %s/sitemap.xml
""" % (HOST_FOR_SEO, DOMAIN)

def _sitemap():
    c = load_content()
    items = ""
    for w in c.get("works", []):
        img = w.get("image", "")
        items += "<url><loc>%s/#works</loc>%s</url>" % (
            DOMAIN, "<image:image><image:loc>%s</image:loc></image:image>" % esc(img) if img else "")
    return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
<url><loc>%s/</loc><lastmod>%s</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>
<url><loc>%s/#works</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>
<url><loc>%s/#reviews</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>
<url><loc>%s/#services</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>
<url><loc>%s/#contacts</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>
%s</urlset>""" % (DOMAIN, date.today().isoformat(), DOMAIN, DOMAIN, DOMAIN, DOMAIN, items)

SITEMAP = _sitemap()

MANIFEST = """{
  "name": "Кухни Островский",
  "short_name": "Кухни Островский",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#14100c",
  "theme_color": "#14100c",
  "icons": [
    {"src": "/favicon-16x16.png", "sizes": "16x16", "type": "image/png"},
    {"src": "/favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
    {"src": "/favicon-512x512.png", "sizes": "512x512", "type": "image/png"}
  ]
}"""

PAGE_404 = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>404 — страница не найдена</title>
<style>
body{margin:0;min-height:100vh;display:grid;place-items:center;background:#14100c;color:#f5ede0;font-family:Georgia,serif;text-align:center}
.wrap{padding:20px}h1{font-size:90px;margin:0;background:linear-gradient(135deg,#f0d78c,#d4af37);-webkit-background-clip:text;background-clip:text;color:transparent}
p{color:#b8a98e}a{display:inline-block;margin-top:20px;padding:14px 30px;border-radius:40px;color:#1c1610;font-weight:bold;text-decoration:none;background:linear-gradient(135deg,#f0d78c,#d4af37)}
</style></head><body><div class="wrap"><h1>404</h1><p>Такой страницы нет, но мебель никуда не делась :)</p><a href="/">На главную</a></div></body></html>"""


# ----------------------------------------------------------------------------
# Админка
# ----------------------------------------------------------------------------
def admin_login_page(error):
    return """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход — админка</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{min-height:100vh;display:grid;place-items:center;font-family:Georgia,serif;background:#14100c;color:#f5ede0;
 background:radial-gradient(800px 500px at 70% -10%,rgba(212,175,55,.18),transparent 60%),radial-gradient(700px 500px at -10% 80%,rgba(184,134,11,.14),transparent 60%),#14100c}
.card{width:min(420px,92vw);background:rgba(28,22,16,.9);border:1px solid rgba(212,175,55,.25);border-radius:22px;padding:40px 34px;box-shadow:0 24px 70px rgba(0,0,0,.5)}
.logo{width:56px;height:56px;border-radius:50%;display:grid;place-items:center;margin:0 auto 16px;font-size:28px;color:#1c1610;font-weight:bold;background:linear-gradient(135deg,#f0d78c,#d4af37)}
h1{text-align:center;font-size:24px;margin-bottom:6px;color:#f0d78c}
p.sub{text-align:center;color:#b8a98e;font-size:14px;margin-bottom:26px}
label{display:block;font-size:13px;color:#b8a98e;margin:14px 0 6px}
input{width:100%;padding:14px 16px;border-radius:12px;border:1px solid rgba(212,175,55,.25);background:#14100c;color:#f5ede0;font-size:16px;font-family:inherit;outline:none}
input:focus{border-color:#d4af37}
button{width:100%;margin-top:24px;padding:15px;border:0;border-radius:40px;font-size:16px;font-weight:bold;cursor:pointer;color:#1c1610;background:linear-gradient(135deg,#f0d78c,#d4af37)}
.err{background:rgba(180,50,40,.15);border:1px solid rgba(200,70,60,.4);color:#ffb4a8;padding:12px 14px;border-radius:12px;font-size:14px;margin-top:16px;text-align:center}
a.back{display:block;text-align:center;margin-top:18px;color:#b8a98e;font-size:13px;text-decoration:none}
</style></head><body>
<div class="card">
  <div class="logo">К</div>
  <h1>Кухни Островский</h1>
  <p class="sub">Вход в админ-панель</p>
  <form method="post" action="/admin/login">
    <label>Логин</label><input type="text" name="login" autocomplete="username" required>
    <label>Пароль</label><input type="password" name="password" autocomplete="current-password" required>
    <button type="submit">Войти</button>
    %s
  </form>
  <a class="back" href="/">← На сайт</a>
</div>
</body></html>""" % ('<div class="err">' + esc(error) + "</div>" if error else "")


def admin_page(c):
    j = json.dumps(c, ensure_ascii=False, indent=2)
    return ADMIN_TEMPLATE \
        .replace("@@JSON@@", esc(j)) \
        .replace("@@SITE_LOGO@@", esc(deep_get(c, "site.logo"))) \
        .replace("@@SITE_PHONE@@", esc(deep_get(c, "site.phone"))) \
        .replace("@@SITE_PHONE_HREF@@", esc(deep_get(c, "site.phoneHref"))) \
        .replace("@@SITE_TG@@", esc(deep_get(c, "site.telegram"))) \
        .replace("@@SITE_TG_HREF@@", esc(deep_get(c, "site.telegramHref"))) \
        .replace("@@SITE_VK@@", esc(deep_get(c, "site.vk"))) \
        .replace("@@SITE_VK_HREF@@", esc(deep_get(c, "site.vkHref"))) \
        .replace("@@CITIES_TA@@", esc("\n".join(c.get("site", {}).get("cities", [])))) \
        .replace("@@HERO_TITLE@@", esc(deep_get(c, "hero.title"))) \
        .replace("@@HERO_SUB@@", esc(deep_get(c, "hero.subtitle"))) \
        .replace("@@HERO_BTN1@@", esc(deep_get(c, "hero.btn1"))) \
        .replace("@@HERO_BTN1_HREF@@", esc(deep_get(c, "hero.btn1Href"))) \
        .replace("@@HERO_BTN2@@", esc(deep_get(c, "hero.btn2"))) \
        .replace("@@HERO_BTN2_HREF@@", esc(deep_get(c, "hero.btn2Href"))) \
        .replace("@@HERO_WM@@", esc(deep_get(c, "hero.watermark"))) \
        .replace("@@ABOUT_TITLE@@", esc(deep_get(c, "about.title"))) \
        .replace("@@ABOUT_NAME@@", esc(deep_get(c, "about.name"))) \
        .replace("@@ABOUT_TEXT@@", esc(deep_get(c, "about.text"))) \
        .replace("@@ABOUT_FEATURES@@", esc("\n".join(c.get("about", {}).get("features", [])))) \
        .replace("@@SEO_TITLE@@", esc(deep_get(c, "seo.title"))) \
        .replace("@@SEO_DESC@@", esc(deep_get(c, "seo.description"))) \
        .replace("@@SEO_KEYWORDS@@", esc(deep_get(c, "seo.keywords"))) \
        .replace("@@SEO_OG@@", esc(deep_get(c, "seo.ogImage"))) \
        .replace("@@SEO_ROBOTS@@", esc(deep_get(c, "seo.robots"))) \
        .replace("@@CONTACT_TITLE@@", esc(deep_get(c, "contacts.title"))) \
        .replace("@@CONTACT_TEXT@@", esc(deep_get(c, "contacts.text"))) \
        .replace("@@CONTACT_NOTE@@", esc(deep_get(c, "contacts.note"))) \
        .replace("@@CTA_TITLE@@", esc(deep_get(c, "cta.title"))) \
        .replace("@@CTA_TEXT@@", esc(deep_get(c, "cta.text"))) \
        .replace("@@CTA_BTN@@", esc(deep_get(c, "cta.btn"))) \
        .replace("@@CTA_BTN_HREF@@", esc(deep_get(c, "cta.btnHref"))) \
        .replace("@@FOOTER_TEXT@@", esc(deep_get(c, "footer.text"))) \
        .replace("@@FOOTER_EXTRA@@", esc(deep_get(c, "footer.extra"))) \
        .replace("@@WORKS_JSON@@", esc(json.dumps(c.get("works", []), ensure_ascii=False))) \
        .replace("@@REVIEWS_JSON@@", esc(json.dumps(c.get("reviews", []), ensure_ascii=False))) \
        .replace("@@VIDEO_ENABLED@@", 'checked' if c.get("video", {}).get("enabled") else '') \
        .replace("@@VIDEO_YOUTUBE@@", esc(deep_get(c, "video.youtube"))) \
        .replace("@@VIDEO_POSTER@@", esc(deep_get(c, "video.poster"))) \
        .replace("@@VIDEO_AUTHOR@@", esc(deep_get(c, "video.author"))) \
        .replace("@@SERVICES_JSON@@", esc(json.dumps(c.get("services", []), ensure_ascii=False))) \
        .replace("@@PROCESS_JSON@@", esc(json.dumps(c.get("process", []), ensure_ascii=False))) \
        .replace("@@GUARANTEES_JSON@@", esc(json.dumps(c.get("guarantees", []), ensure_ascii=False)))


ADMIN_TEMPLATE = """<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Админка — Кухни Островский</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#12100d;color:#efe6d8;min-height:100vh}
.top{position:sticky;top:0;z-index:50;background:rgba(18,16,13,.95);backdrop-filter:blur(12px);border-bottom:1px solid rgba(212,175,55,.22);padding:0 18px;display:flex;align-items:center;gap:14px;height:60px}
.top .t-logo{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#f0d78c,#d4af37);color:#1c1610;font-weight:bold}
.top h1{font-size:17px;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.top a{color:#d4af37;text-decoration:none;font-size:14px;white-space:nowrap}
.top form{display:inline}
.top .btn-out{padding:8px 14px;border:1px solid rgba(212,175,55,.4);border-radius:30px}
.tabs{display:flex;gap:6px;overflow-x:auto;padding:14px 18px 0;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab-btn{white-space:nowrap;padding:10px 16px;border-radius:12px 12px 0 0;border:1px solid transparent;background:none;color:#b8a98e;font-size:14px;cursor:pointer;font-family:inherit}
.tab-btn.active{color:#f0d78c;background:rgba(212,175,55,.1);border-color:rgba(212,175,55,.25) rgba(212,175,55,.25) transparent}
main{padding:22px 18px 80px;max-width:1000px;margin:0 auto}
.tab{display:none}
.tab.active{display:block}
.card{background:rgba(28,22,16,.75);border:1px solid rgba(212,175,55,.18);border-radius:16px;padding:22px;margin-bottom:18px}
.card h2{font-size:18px;color:#f0d78c;margin-bottom:14px;font-weight:600}
label{display:block;font-size:13px;color:#b8a98e;margin:12px 0 5px}
input[type=text],input[type=url],input[type=password],textarea{width:100%;padding:11px 13px;border-radius:10px;border:1px solid rgba(212,175,55,.22);background:#12100d;color:#efe6d8;font-size:15px;font-family:inherit;outline:none}
input:focus,textarea:focus{border-color:#d4af37}
textarea{min-height:90px;resize:vertical;line-height:1.5}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}
.check-row{display:flex;align-items:center;gap:10px;margin:14px 0}
.check-row input{width:20px;height:20px}
.save{display:inline-flex;align-items:center;gap:8px;margin-top:18px;padding:13px 28px;border:0;border-radius:40px;background:linear-gradient(135deg,#f0d78c,#d4af37);color:#1c1610;font-weight:bold;font-size:15px;cursor:pointer;font-family:inherit}
.save:hover{filter:brightness(1.08)}
.hint{font-size:12px;color:#8a7d68;margin-top:6px}
table.tbl{width:100%;border-collapse:collapse;margin-top:10px}
table.tbl th{text-align:left;color:#b8a98e;font-size:12px;font-weight:500;padding:6px 8px;border-bottom:1px solid rgba(212,175,55,.2)}
table.tbl td{padding:6px 8px;border-bottom:1px solid rgba(212,175,55,.1)}
table.tbl input{font-size:14px}
.row-add{margin-top:10px;padding:9px 16px;border-radius:30px;border:1px dashed rgba(212,175,55,.5);background:none;color:#d4af37;cursor:pointer;font-family:inherit}
.row-del{background:none;border:1px solid rgba(200,80,60,.5);color:#ff9d8f;border-radius:8px;width:32px;height:32px;cursor:pointer}
.uploads{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.up-item{border:1px solid rgba(212,175,55,.2);border-radius:10px;padding:8px;display:flex;flex-direction:column;gap:6px;align-items:center;max-width:140px}
.up-item img{width:100px;height:75px;object-fit:cover;border-radius:6px}
.up-item code{font-size:11px;color:#b8a98e;word-break:break-all}
.toast{position:fixed;bottom:20px;left:50%;transform:translate(-50%,80px);background:linear-gradient(135deg,#f0d78c,#d4af37);color:#1c1610;font-weight:bold;padding:13px 26px;border-radius:40px;z-index:999;transition:.3s;opacity:0;box-shadow:0 10px 30px rgba(0,0,0,.4)}
.toast.show{transform:translate(-50%,0);opacity:1}
@media(max-width:640px){.grid2{grid-template-columns:1fr}.top a.hide-m{display:none}}
</style></head><body>
<div class="top">
  <div class="t-logo">К</div>
  <h1>Админка — Кухни Островский</h1>
  <a href="/" target="_blank" class="hide-m">Открыть сайт ↗</a>
  <form method="post" action="/admin/logout"><button class="btn-out" style="background:none;color:#d4af37;font-family:inherit;font-size:14px;cursor:pointer">Выйти</button></form>
</div>

<div class="tabs">
  <button class="tab-btn active" data-tab="hero">Главная</button>
  <button class="tab-btn" data-tab="works">Работы</button>
  <button class="tab-btn" data-tab="reviews">Отзывы</button>
  <button class="tab-btn" data-tab="services">Услуги</button>
  <button class="tab-btn" data-tab="process">Как работаем</button>
  <button class="tab-btn" data-tab="guarantees">Гарантии</button>
  <button class="tab-btn" data-tab="site">Города и контакты</button>
  <button class="tab-btn" data-tab="seo">SEO</button>
  <button class="tab-btn" data-tab="files">Фото</button>
  <button class="tab-btn" data-tab="json">JSON</button>
</div>

<main>
<!-- ГЛАВНАЯ -->
<form class="tab active" id="tab-hero" data-section="hero">
  <div class="card"><h2>Первый экран</h2>
    <label>Заголовок (H1)</label><input type="text" name="title" value="@@HERO_TITLE@@">
    <label>Подзаголовок</label><textarea name="subtitle">@@HERO_SUB@@</textarea>
    <div class="grid2">
      <div><label>Кнопка 1 — текст</label><input type="text" name="btn1" value="@@HERO_BTN1@@">
      <label>Кнопка 1 — ссылка</label><input type="text" name="btn1Href" value="@@HERO_BTN1_HREF@@"></div>
      <div><label>Кнопка 2 — текст</label><input type="text" name="btn2" value="@@HERO_BTN2@@">
      <label>Кнопка 2 — ссылка</label><input type="text" name="btn2Href" value="@@HERO_BTN2_HREF@@"></div>
    </div>
    <label>Водяной знак на фоне</label><input type="text" name="watermark" value="@@HERO_WM@@">
    <div class="hint">Сохранение происходит нажатием кнопки внизу карточки</div>
  </div>
  <div class="card"><h2>Статистика (карточки под шапкой)</h2>
    <table class="tbl" data-array="stats">
      <thead><tr><th>Иконка</th><th>Заголовок</th><th>Текст</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button type="button" class="row-add" data-array="stats" data-fields='["icon","title","text"]'>+ Добавить карточку</button>
  </div>
  <div class="card"><h2>Специалист (блок «О себе»)</h2>
    <label>Заголовок секции</label><input type="text" name="about.title" value="@@ABOUT_TITLE@@">
    <label>Имя</label><input type="text" name="about.name" value="@@ABOUT_NAME@@">
    <label>Текст</label><textarea name="about.text">@@ABOUT_TEXT@@</textarea>
    <label>Преимущества (каждое с новой строки)</label><textarea name="about.features">@@ABOUT_FEATURES@@</textarea>
  </div>
  <button class="save" type="submit">💾 Сохранить раздел</button>
</form>

<!-- РАБОТЫ -->
<form class="tab" id="tab-works" data-section="works">
  <div class="card"><h2>Работы (карусель)</h2>
    <div class="hint" style="margin-bottom:10px">Поля: <b>title</b> — название, <b>city</b> — город, <b>year</b> — год, <b>image</b> — ссылка на фото (можно загрузить во вкладке «Фото» и вставить /uploads/...).</div>
    <table class="tbl" data-array="works">
      <thead><tr><th>Название</th><th>Город</th><th>Год</th><th>Фото (URL)</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button type="button" class="row-add" data-array="works" data-fields='["title","city","year","image"]'>+ Добавить работу</button>
  </div>
  <button class="save" type="submit">💾 Сохранить работы</button>
</form>

<!-- ОТЗЫВЫ -->
<form class="tab" id="tab-reviews" data-section="MULTI">
  <div class="card"><h2>Отзывы</h2>
    <div class="hint" style="margin-bottom:10px">Поля: <b>name</b> — имя, <b>text</b> — текст отзыва, <b>rating</b> — оценка (1–5).</div>
    <table class="tbl" data-array="reviews">
      <thead><tr><th>Имя</th><th>Текст</th><th>Оценка</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button type="button" class="row-add" data-array="reviews" data-fields='["name","text","rating"]'>+ Добавить отзыв</button>
  </div>
  <div class="card"><h2>Видеоотзыв (последняя карточка в карусели)</h2>
    <div class="check-row"><input type="checkbox" id="videoEnabled" @@VIDEO_ENABLED@@><label for="videoEnabled" style="margin:0">Показывать видеоотзыв</label></div>
    <label>Ссылка на YouTube (embed-ссылка, например https://www.youtube.com/embed/XXXX)</label>
    <input type="text" id="videoYoutube" value="@@VIDEO_YOUTUBE@@">
    <label>Постер (картинка до нажатия «Play») — URL</label>
    <input type="text" id="videoPoster" value="@@VIDEO_POSTER@@">
    <label>Автор отзыва</label>
    <input type="text" id="videoAuthor" value="@@VIDEO_AUTHOR@@">
  </div>
  <button class="save" type="submit">💾 Сохранить отзывы</button>
</form>

<!-- УСЛУГИ -->
<form class="tab" id="tab-services" data-section="services">
  <div class="card"><h2>Услуги</h2>
    <table class="tbl" data-array="services">
      <thead><tr><th>Иконка</th><th>Название</th><th>Описание</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button type="button" class="row-add" data-array="services" data-fields='["icon","title","text"]'>+ Добавить услугу</button>
  </div>
  <button class="save" type="submit">💾 Сохранить услуги</button>
</form>

<!-- ПРОЦЕСС -->
<form class="tab" id="tab-process" data-section="process">
  <div class="card"><h2>Этапы «Как мы работаем»</h2>
    <table class="tbl" data-array="process">
      <thead><tr><th>Название</th><th>Описание</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button type="button" class="row-add" data-array="process" data-fields='["title","text"]'>+ Добавить этап</button>
  </div>
  <button class="save" type="submit">💾 Сохранить этапы</button>
</form>

<!-- ГАРАНТИИ -->
<form class="tab" id="tab-guarantees" data-section="guarantees">
  <div class="card"><h2>Гарантии</h2>
    <table class="tbl" data-array="guarantees">
      <thead><tr><th>Название</th><th>Описание</th><th></th></tr></thead>
      <tbody></tbody>
    </table>
    <button type="button" class="row-add" data-array="guarantees" data-fields='["title","text"]'>+ Добавить пункт</button>
  </div>
  <button class="save" type="submit">💾 Сохранить гарантии</button>
</form>

<!-- ГОРОДА И КОНТАКТЫ -->
<form class="tab" id="tab-site" data-section="MULTI">
  <div class="card"><h2>Сайт / Города</h2>
    <div class="grid2">
      <div><label>Название (логотип)</label><input type="text" name="site.logo" value="@@SITE_LOGO@@"></div>
      <div><label>Телефон (текст)</label><input type="text" name="site.phone" value="@@SITE_PHONE@@"></div>
    </div>
    <div class="grid2">
      <div><label>Телефон (ссылка tel:)</label><input type="text" name="site.phoneHref" value="@@SITE_PHONE_HREF@@"></div>
      <div><label>Telegram (ссылка)</label><input type="text" name="site.telegramHref" value="@@SITE_TG_HREF@@"></div>
    </div>
    <div class="grid2">
      <div><label>Telegram (текст)</label><input type="text" name="site.telegram" value="@@SITE_TG@@"></div>
      <div><label>VK (ссылка)</label><input type="text" name="site.vkHref" value="@@SITE_VK_HREF@@"></div>
    </div>
    <label>VK (текст)</label><input type="text" name="site.vk" value="@@SITE_VK@@">
    <label>Города (каждый с новой строки)</label><textarea name="site.cities">@@CITIES_TA@@</textarea>
  </div>
  <div class="card"><h2>Контакты (секция на сайте)</h2>
    <div class="grid2">
      <div><label>Заголовок</label><input type="text" name="contacts.title" value="@@CONTACT_TITLE@@"></div>
      <div><label>Подпись</label><input type="text" name="contacts.text" value="@@CONTACT_TEXT@@"></div>
    </div>
    <label>Примечание (города)</label><input type="text" name="contacts.note" value="@@CONTACT_NOTE@@">
  </div>
  <div class="card"><h2>Блок «Бесплатный замер» (CTA)</h2>
    <label>Заголовок</label><input type="text" name="cta.title" value="@@CTA_TITLE@@">
    <label>Текст</label><textarea name="cta.text">@@CTA_TEXT@@</textarea>
    <div class="grid2">
      <div><label>Кнопка</label><input type="text" name="cta.btn" value="@@CTA_BTN@@"></div>
      <div><label>Ссылка кнопки</label><input type="text" name="cta.btnHref" value="@@CTA_BTN_HREF@@"></div>
    </div>
  </div>
  <div class="card"><h2>Подвал</h2>
    <div class="grid2">
      <div><label>Текст</label><input type="text" name="footer.text" value="@@FOOTER_TEXT@@"></div>
      <div><label>Дополнительно</label><input type="text" name="footer.extra" value="@@FOOTER_EXTRA@@"></div>
    </div>
  </div>
  <button class="save" type="submit">💾 Сохранить</button>
</form>

<!-- SEO -->
<form class="tab" id="tab-seo" data-section="seo">
  <div class="card"><h2>SEO — поисковая оптимизация</h2>
    <label>Title (заголовок вкладки в браузере и в поиске)</label>
    <input type="text" name="title" value="@@SEO_TITLE@@">
    <label>Description (описание в поиске)</label>
    <textarea name="description">@@SEO_DESC@@</textarea>
    <label>Keywords</label>
    <textarea name="keywords">@@SEO_KEYWORDS@@</textarea>
    <div class="grid2">
      <div><label>og:image (URL картинки для соцсетей)</label><input type="text" name="ogImage" value="@@SEO_OG@@"></div>
      <div><label>robots</label><input type="text" name="robots" value="@@SEO_ROBOTS@@"></div>
    </div>
  </div>
  <button class="save" type="submit">💾 Сохранить SEO</button>
</form>

<!-- ФОТО -->
<div class="tab" id="tab-files">
  <div class="card"><h2>Загрузка фото</h2>
    <input type="file" id="fileInput" accept=".png,.jpg,.jpeg,.webp,.gif,.svg">
    <button class="save" type="button" id="uploadBtn" style="margin-top:12px">⬆ Загрузить</button>
    <div id="uploadMsg" class="hint"></div>
    <div class="uploads" id="uploadsList"></div>
  </div>
</div>

<!-- JSON -->
<form class="tab" id="tab-json" data-section="full">
  <div class="card"><h2>Полный JSON (максимальный контроль)</h2>
    <div class="hint" style="margin-bottom:10px">Здесь можно менять вообще всё — любые поля сайта. Формат: валидный JSON.</div>
    <textarea id="fullJson" style="min-height:480px;font-family:ui-monospace,monospace;font-size:13px">@@JSON@@</textarea>
  </div>
  <button class="save" type="submit">💾 Сохранить JSON</button>
</form>
</main>

<div class="toast" id="toast">Сохранено ✅</div>

<script>
(function(){
  // ---- вкладки ----
  var tabs=document.querySelectorAll('.tab-btn'),tabPanes={};
  document.querySelectorAll('.tab').forEach(function(t){tabPanes[t.id]=t});
  tabs.forEach(function(b){
    b.addEventListener('click',function(){
      tabs.forEach(function(x){x.classList.remove('active')});
      Object.keys(tabPanes).forEach(function(k){tabPanes[k].classList.remove('active')});
      b.classList.add('active');
      var pane=document.getElementById('tab-'+b.dataset.tab);if(pane)pane.classList.add('active');
    });
  });

  function toast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2200)}

  // ---- таблицы-редакторы ----
  function collectArrays(form){
    var res={};
    form.querySelectorAll('table[data-array]').forEach(function(tbl){
      var arr=tbl.dataset.array,rows=[];
      tbl.querySelectorAll('tbody tr').forEach(function(tr){
        var obj={};
        tr.querySelectorAll('input[data-field]').forEach(function(inp){obj[inp.dataset.field]=inp.value});
        rows.push(obj);
      });
      res[arr]=rows;
    });
    return res;
  }

  function addRow(tbl,fields){
    var tr=document.createElement('tr');
    fields.forEach(function(f){
      var td=document.createElement('td');
      var inp=document.createElement('input');
      inp.type='text';inp.dataset.field=f;inp.placeholder=f;
      td.appendChild(inp);tr.appendChild(td);
    });
    var td=document.createElement('td');
    var del=document.createElement('button');
    del.type='button';del.className='row-del';del.textContent='✕';
    del.addEventListener('click',function(){tr.remove()});
    td.appendChild(del);tr.appendChild(td);
    tbl.querySelector('tbody').appendChild(tr);
  }

  function initTables(){
    document.querySelectorAll('table[data-array]').forEach(function(tbl){
      var fields=JSON.parse(tbl.dataset.fields||'[]');
      var data=window.__ADMIN_ARR__&&window.__ADMIN_ARR__[tbl.dataset.array];
      (data||[]).forEach(function(item){addRow(tbl,fields);var tr=tbl.querySelector('tbody tr:last-child');tr.querySelectorAll('input[data-field]').forEach(function(inp){inp.value=item[inp.dataset.field]||''})});
    });
    document.querySelectorAll('.row-add').forEach(function(btn){
      btn.addEventListener('click',function(){
        var tbl=document.querySelector('table[data-array="'+btn.dataset.array+'"]');
        addRow(tbl,JSON.parse(btn.dataset.fields||'[]'));
      });
    });
  }

  // ---- сохранение форм ----
  document.querySelectorAll('form[data-section]').forEach(function(form){
    form.addEventListener('submit',function(e){
      e.preventDefault();
      var section=form.dataset.section,obj={};
      form.querySelectorAll('input[name],textarea[name]').forEach(function(el){
        var name=el.name;
        if(name.indexOf('.')>-1){setPath(obj,name,el.value)}
        else{obj[name]=el.value}
      });
      var arrays=collectArrays(form);
      Object.keys(arrays).forEach(function(k){obj[k]=arrays[k]});
      // особенности
      if(section==='MULTI'){
        if(obj['site.cities']!==undefined){
          if(!obj.site)obj.site={};
          obj.site.cities=obj['site.cities'].split('\\n').map(function(s){return s.trim()}).filter(Boolean);
          delete obj['site.cities'];
        }
      }
      if(form.id==='tab-reviews'){
        obj.video={enabled:document.getElementById('videoEnabled').checked,
          youtube:document.getElementById('videoYoutube').value.trim(),
          poster:document.getElementById('videoPoster').value.trim(),
          author:document.getElementById('videoAuthor').value.trim()};
        delete obj['video.enabled'];
      }
      send(section,obj);
    });
  });

  function setPath(o,p,v){var ks=p.split('.'),c=o;for(var i=0;i<ks.length-1;i++){c=c[ks[i]]=c[ks[i]]||{}}c[ks[ks.length-1]]=v}
  function collectSimple(form){
    var o={};
    form.querySelectorAll('input[name],textarea[name]').forEach(function(el){setPath(o,el.name,el.value)});
    return o;
  }

  function send(section,data){
    var fd=new FormData();fd.append('section',section);fd.append('data',JSON.stringify(data));
    fetch('/admin/save',{method:'POST',body:fd})
      .then(function(r){return r.json()})
      .then(function(res){toast(res.ok?'Сохранено ✅':'Ошибка: '+res.error)})
      .catch(function(err){toast('Ошибка сети: '+err)});
  }

  document.getElementById('tab-json').addEventListener('submit',function(e){
    e.preventDefault();
    try{var data=JSON.parse(document.getElementById('fullJson').value);send('full',data)}
    catch(err){toast('Невалидный JSON: '+err.message)}
  });

  // ---- загрузка фото ----
  var fileInput=document.getElementById('fileInput');
  document.getElementById('uploadBtn').addEventListener('click',function(){
    if(!fileInput.files.length){toast('Выберите файл');return}
    var fd=new FormData();fd.append('file',fileInput.files[0]);
    fetch('/admin/upload',{method:'POST',body:fd})
      .then(function(r){return r.json()})
      .then(function(res){
        if(res.ok){toast('Загружено! URL: '+res.url);document.getElementById('uploadMsg').textContent='URL: '+res.url;loadUploads()}
        else{toast('Ошибка: '+res.error)}
      })
      .catch(function(err){toast('Ошибка: '+err)});
  });

  function loadUploads(){
    fetch('/uploads/list.json').then(function(r){return r.json()}).then(function(list){
      var box=document.getElementById('uploadsList');box.innerHTML='';
      (list||[]).forEach(function(u){
        var d=document.createElement('div');d.className='up-item';
        d.innerHTML='<img src="'+u+'" alt=""><code>'+u+'</code>';
        d.addEventListener('click',function(){navigator.clipboard&&navigator.clipboard.writeText(u);toast('URL скопирован')});
        box.appendChild(d);
      });
    }).catch(function(){});
  }

  // данные массивов для таблиц
  window.__ADMIN_ARR__={
    stats:%STATS_JSON%,
    works:%WORKS_JSON%,
    reviews:%REVIEWS_JSON%,
    services:%SERVICES_JSON%,
    process:%PROCESS_JSON%,
    guarantees:%GUARANTEES_JSON%
  };
  initTables();
  if(document.getElementById('tab-files'))loadUploads();
})();
</script>
</body></html>"""


# ----------------------------------------------------------------------------
# Дефолтный контент
# ----------------------------------------------------------------------------
DEFAULT_CONTENT = {
  "site": {
    "logo": "Кухни Островский",
    "domain": "https://кухниостровский.рф",
    "phone": "+7 (950) 846-53-97",
    "phoneHref": "tel:+79508465397",
    "telegram": "t.me/fanny161",
    "telegramHref": "https://t.me/fanny161",
    "vk": "vk.com/mebel.ostrovsky",
    "vkHref": "https://vk.com/mebel.ostrovsky",
    "cities": ["Ростов-на-Дону", "Батайск", "Азов"]
  },
  "seo": {
    "title": "Кухни Островский — кухни и мебель на заказ в Ростове-на-Дону, Батайске и Азове",
    "description": "Кухни и корпусная мебель на заказ. Бесплатный замер и проект. Ростов-на-Дону, Батайск, Азов. Звоните: +7 (950) 846-53-97",
    "keywords": "кухни на заказ, мебель на заказ, кухни ростов-на-дону, корпусная мебель, шкафы, батайск, азов, кухни островский",
    "ogImage": "/favicon-512x512.png",
    "robots": "index, follow"
  },
  "hero": {
    "title": "Мебель, которая создаёт настроение",
    "subtitle": "Кухни и корпусная мебель на заказ. Бесплатный замер и проект в Ростове-на-Дону, Батайске и Азове.",
    "btn1": "Смотреть работы",
    "btn1Href": "#works",
    "btn2": "Бесплатный замер",
    "btn2Href": "#contacts",
    "watermark": "Кухни Островский",
    "stats": [
      {"icon": "🛠", "title": "Собственное производство", "text": "Изготавливаем мебель под ключ"},
      {"icon": "📐", "title": "Бесплатный замер", "text": "Выезжаем в Ростов-на-Дону, Батайск и Азов"},
      {"icon": "✏️", "title": "Индивидуальный проект", "text": "Проект под ваши размеры и задачи"},
      {"icon": "🔑", "title": "Под ключ", "text": "От замера до установки и уборки"}
    ]
  },
  "about": {
    "title": "Специалист",
    "name": "Роман Островский",
    "text": "Занимаюсь изготовлением кухонь и корпусной мебели на заказ. Помогаю на каждом этапе: от замера и проекта до производства и монтажа. Работаю в Ростове-на-Дону, Батайске и Азове.",
    "features": ["Бесплатный замер и проект", "Собственное производство", "Фиксируем цену в договоре"]
  },
  "works": [],
  "reviews": [],
  "video": {
    "enabled": False,
    "title": "Видеоотзыв",
    "author": "Александр Карташев",
    "youtube": "",
    "poster": ""
  },
  "services": [
    {"icon": "🍳", "title": "Кухни на заказ", "text": "Кухни любой планировки и стиля под ваши размеры."},
    {"icon": "🪑", "title": "Корпусная мебель", "text": "Шкафы, гардеробные, тумбы, стенки — по индивидуальным размерам."},
    {"icon": "🏠", "title": "Мебель для дома", "text": "Прихожие, спальни, детские, гостиные."},
    {"icon": "📐", "title": "Замер и проект", "text": "Бесплатный выезд, замер и дизайн-проект."}
  ],
  "process": [
    {"title": "Заявка", "text": "Оставляете заявку или звоните — обсуждаем задачу."},
    {"title": "Замер", "text": "Бесплатно приезжаем, делаем точный замер."},
    {"title": "Проект", "text": "Готовим проект и смету, фиксируем цену."},
    {"title": "Производство", "text": "Изготавливаем мебель на собственном производстве."},
    {"title": "Монтаж", "text": "Доставляем, устанавливаем и убираем за собой."}
  ],
  "guarantees": [
    {"title": "Договор", "text": "Работаем по договору, цена фиксируется."},
    {"title": "Гарантия", "text": "Даём гарантию на мебель и монтаж."},
    {"title": "Сроки", "text": "Соблюдаем оговорённые сроки изготовления."},
    {"title": "Чистота", "text": "После монтажа убираем и вывозим упаковку."}
  ],
  "cta": {
    "title": "Бесплатный замер и проект",
    "text": "Оставьте заявку — перезвоним, ответим на вопросы и договоримся о замере.",
    "btn": "Позвонить",
    "btnHref": "tel:+79508465397"
  },
  "contacts": {
    "title": "Контакты",
    "text": "Звоните или пишите — ответим на все вопросы.",
    "phone": "+7 (950) 846-53-97",
    "phoneHref": "tel:+79508465397",
    "telegram": "t.me/fanny161",
    "telegramHref": "https://t.me/fanny161",
    "vk": "vk.com/mebel.ostrovsky",
    "vkHref": "https://vk.com/mebel.ostrovsky",
    "note": "Ростов-на-Дону, Батайск, Азов"
  },
  "footer": {
    "text": "© Кухни Островский",
    "extra": "Кухни и мебель на заказ. Ростов-на-Дону, Батайск, Азов."
  }
}


# ----------------------------------------------------------------------------
# Запуск
# ----------------------------------------------------------------------------
def main():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if not os.path.exists(CONTENT_FILE):
        save_content(DEFAULT_CONTENT)
        print("[init] создан %s" % CONTENT_FILE)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("[ok] Сайт: %s  |  Админка: %s/admin" % (DOMAIN, DOMAIN))
    print("[ok] Логин: %s  |  Пароль: %s" % (ADMIN_LOGIN, "*" * len(ADMIN_PASSWORD)))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[stop] сервер остановлен")


if __name__ == "__main__":
    main()
