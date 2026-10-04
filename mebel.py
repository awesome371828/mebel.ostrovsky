# -*- coding: utf-8 -*-
"""
mebel.py — сайт «Кухни Островский» + админка.

Эндпоинты:
  GET /                       — страница сайта
  GET /robots.txt             — правила для поисковиков
  GET /sitemap.xml            — карта сайта (с изображениями)
  GET /favicon.ico            — ICO-фавикон
  GET /favicon-16x16.png      — PNG 16px
  GET /favicon-32x32.png      — PNG 32px
  GET /apple-touch-icon.png   — иконка для iOS
  GET /manifest.webmanifest   — манифест
  GET /admin                  — админка
  GET /uploads/*              — загруженные файлы
  (любой другой путь)         — страница 404
"""
import gzip
import hashlib
import hmac
import html as _html
import io
import json
import mimetypes
import os
import re
import secrets
import time
import traceback
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

PORT = int(os.environ.get("PORT", "8080"))
DOMAIN = "https://кухниостровский.рф"

# --- Админка ---------------------------------------------------------------
ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "кухнироманост")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "kuhroman")
SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_hex(32))
SESSION_TTL = 7 * 24 * 3600  # 7 дней
CONTENT_FILE = os.environ.get("CONTENT_FILE", "content.json")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
MAX_UPLOAD = 10 * 1024 * 1024
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".mp4", ".webm"}

FAVICON_URL = "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0"
VIDEO_POSTER = "https://sun9-44.vkuserphoto.ru/s/v1/ig2/z3K7MYc56nf_4Ek_wkhJ-j-VZt7iv_VEt9wUN0gJSY0VORuRVxQCX1S5baisBgJyoYuCcrENJNxLajL1WKwdFS91.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x541,1080x811,1280x961,1440x1081,2560x1922&from=bu&u=Fj3HDKPJXUOEmCWl6MePYyPYB6lNmsGien6u_9mlUi8&cs=1280x0"

ROBOTS = """User-agent: *
Allow: /
Disallow: /admin

Host: кухниостровский.рф

Sitemap: {domain}/sitemap.xml
""".format(domain=DOMAIN)

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{domain}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <image:image><image:loc>{img1}</image:loc><image:title>Кухня на заказ в Ростове — Кухни Островский</image:title></image:image>
    <image:image><image:loc>{img2}</image:loc><image:title>Кухня на заказ в Батайске — Кухни Островский</image:title></image:image>
    <image:image><image:loc>{img3}</image:loc><image:title>Кухня на заказ в Азове — Кухни Островский</image:title></image:image>
    <image:image><image:loc>{img4}</image:loc><image:title>Мебель на заказ — Кухни Островский</image:title></image:image>
  </url>
</urlset>
""".format(
    domain=DOMAIN,
    today=date.today().isoformat(),
    img1="https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&amp;from=bu&amp;u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&amp;cs=1280x0",
    img2="https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&amp;as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&amp;from=bu&amp;u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&amp;cs=1280x0",
    img3="https://sun9-11.vkuserphoto.ru/s/v1/ig2/Xh5Xw9Yb1reqhfFznlGk8NjvSQAxCbysuiL5IWRt_f3ELVb8fvoYPg00eFIHV-xiS9I4nhYBj4ttU_FHVkPpX8Z3.jpg?quality=95&amp;as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,1600x1200&amp;from=bu&amp;u=pY-bjOidU1jjNjiF66Dn4Ycgmb6utH_d0Ti7oSJr0qA&amp;cs=1080x0",
    img4="https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&amp;as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&amp;from=bu&amp;u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&amp;cs=1080x0",
)

MANIFEST = """{
  "name": "Кухни Островский — кухни на заказ в Ростове, Батайске и Азове",
  "short_name": "Кухни Островский",
  "description": "Кухни и корпусная мебель на заказ. Бесплатный замер и 3D-проект.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0e0c09",
  "theme_color": "#0e0c09",
  "lang": "ru-RU",
  "icons": [
    {"src": "/favicon.ico", "sizes": "16x16 32x32 48x48 64x64", "type": "image/x-icon", "purpose": "any"},
    {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png", "purpose": "any"},
    {"src": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0", "sizes": "any", "type": "image/jpeg", "purpose": "any"}
  ]
}
"""

PAGE_404 = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, follow">
<title>404 — страница не найдена | Кухни Островский</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Manrope',system-ui,sans-serif;background:#0e0c09;color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center}
.card{max-width:560px;width:100%}
.code{font-family:Georgia,serif;font-size:clamp(80px,18vw,160px);line-height:1;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 8px 26px rgba(212,175,106,.35))}
h1{font-family:Georgia,serif;font-size:clamp(24px,5vw,34px);color:#fff;margin:14px 0 10px;letter-spacing:.4px}
p{color:#b9ad9a;font-size:15px;line-height:1.7;margin-bottom:28px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:15px 30px;border-radius:14px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;font-size:13px;letter-spacing:1.2px;text-transform:uppercase;text-decoration:none;box-shadow:0 18px 44px rgba(212,175,106,.28);transition:.3s}
.btn:hover{transform:translateY(-3px);box-shadow:0 26px 60px rgba(212,175,106,.45)}
.contacts{margin-top:30px;color:#b9ad9a;font-size:13.5px;line-height:1.9}
.contacts a{color:#eccfa0;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <div class="code">404</div>
  <h1>Такой страницы нет</h1>
  <p>Возможно, ссылка устарела или адрес введён с ошибкой. Вернитесь на главную — там вас ждут наши работы, отзывы и контакты.</p>
  <a class="btn" href="/">На главную</a>
  <div class="contacts">
    ☎ <a href="tel:+79508465397">+7 (950) 846-53-97</a><br>
    ✈ <a href="https://t.me/fanny161" target="_blank" rel="noopener">Telegram</a> ·
    <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener">ВКонтакте</a>
  </div>
</div>
</body>
</html>
"""

# ============================================================================
# PAGE — СЮДА ВСТАВЬ СВОЙ БЛОК КАК ЕСТЬ
# Начиная со строки:   PAGE = """<!DOCTYPE html>
# и заканчивая строкой: """.replace("__VIDEO_POSTER__", VIDEO_POSTER)
# НИЧЕГО В НЁМ НЕ МЕНЯЙ — там все URL картинок VK.
# ============================================================================
PAGE = """<!DOCTYPE html>
ВСТАВЬ СЮДА СВОЙ БЛОК PAGE (HTML/CSS/JS) ЦЕЛИКОМ
""".replace("__VIDEO_POSTER__", VIDEO_POSTER)

_favicon_cache = {"data": None, "ts": 0.0}
_icons_cache = {"ico": None, "png16": None, "png32": None, "png180": None}
FAVICON_TTL = 3600


def _make_icons(data):
    """Если установлен Pillow — собираем настоящие ICO и PNG из аватарки."""
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
    """Скачивает аватарку с CDN один раз в час и держит её локально."""
    now = time.time()
    if _favicon_cache["data"] is None or now - _favicon_cache["ts"] > FAVICON_TTL:
        try:
            req = urllib.request.Request(FAVICON_URL, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://vk.com/",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                _favicon_cache["data"] = data
                _favicon_cache["ts"] = now
                _make_icons(data)
        except Exception:
            return None
    return _favicon_cache["data"]


def esc(x):
    return _html.escape(str(x), quote=True)


def load_content():
    if not os.path.exists(CONTENT_FILE):
        save_content({"replacements": [], "page": ""})
    try:
        with open(CONTENT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"replacements": [], "page": ""}


def save_content(content):
    tmp = CONTENT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONTENT_FILE)


# --- Дополнительные анимации на ВЕСЬ сайт (добавляются сами, PAGE не трогаем)
EXTRA_CSS = """/*SC-EXTRA-CSS*/
.btn,.c-action{overflow:hidden;position:relative}
.btn-solid::after,.c-action.c-call::after{content:"";position:absolute;top:0;left:-130%;width:55%;height:100%;background:linear-gradient(120deg,transparent,rgba(255,255,255,.55),transparent);transform:skewX(-20deg);animation:btnShine 2.8s ease-in-out infinite}
@keyframes btnShine{0%,55%{left:-130%}85%,100%{left:145%}}
.btn-solid::before,.c-action.c-call::before{content:"";position:absolute;inset:-4px;border-radius:18px;border:2px solid rgba(236,207,160,.6);animation:btnRing 2.2s ease-out infinite;opacity:0}
@keyframes btnRing{0%{transform:scale(.95);opacity:.7}75%{transform:scale(1.06);opacity:0}100%{opacity:0}}
.btn:hover,.c-action:hover{filter:brightness(1.12);text-shadow:0 0 16px rgba(236,207,160,.45)}
.svc,.step,.guar,.city,.stat,.rev-card,.car-slide{transition:transform .5s cubic-bezier(.22,.61,.36,1),box-shadow .5s,border-color .5s}
.svc:hover,.step:hover,.guar:hover,.city:hover,.stat:hover,.rev-card:hover,.car-slide:hover{transform:translateY(-10px) scale(1.02);box-shadow:0 30px 70px rgba(0,0,0,.55),0 0 44px rgba(212,175,106,.18)}
.svc h3,.step h3,.guar h3{transition:color .4s,text-shadow .4s}
.svc:hover h3,.step:hover h3,.guar:hover h3{color:#fff;text-shadow:0 0 22px rgba(236,207,160,.75)}
.svc svg,.guar .ico,.c-ico,.soc svg{transition:transform .5s cubic-bezier(.22,.61,.36,1)}
.svc:hover svg{transform:scale(1.16) rotate(-6deg)}
.guar:hover .ico{transform:scale(1.14) rotate(8deg)}
.soc{transition:transform .4s,background .4s,box-shadow .4s,color .4s}
.soc:hover{transform:translateY(-5px) rotate(6deg) scale(1.08)}
.car-nav{transition:transform .4s,background .4s,border-color .4s,box-shadow .4s}
.car-nav:hover{transform:translateY(-50%) scale(1.12);box-shadow:0 0 30px rgba(236,207,160,.45)}
.lb-nav:hover{transform:scale(1.1)}
.menu a{transition:color .3s,text-shadow .3s}
.menu a:hover{text-shadow:0 0 14px rgba(236,207,160,.6)}
.logo .brand-ava{animation:avaGlow 3.2s ease-in-out infinite}
@keyframes avaGlow{0%,100%{box-shadow:0 0 0 5px rgba(212,175,106,.12),0 0 22px rgba(212,175,106,.35)}50%{box-shadow:0 0 0 8px rgba(212,175,106,.22),0 0 40px rgba(236,207,160,.7)}}
.consult .phone,.call-block .cb-num{animation:numBreath 3s ease-in-out infinite}
@keyframes numBreath{0%,100%{filter:drop-shadow(0 7px 22px rgba(212,175,106,.3))}50%{filter:drop-shadow(0 7px 36px rgba(236,207,160,.7))}}
.sec-head h2::before,.sec-head h2::after{animation:lineBreath 3.2s ease-in-out infinite}
@keyframes lineBreath{0%,100%{opacity:.45}50%{opacity:1}}
.cookie-bar .btn{animation:cookiePulse 2s ease-in-out infinite}
@keyframes cookiePulse{0%,100%{box-shadow:0 16px 42px rgba(212,175,106,.26)}50%{box-shadow:0 22px 58px rgba(236,207,160,.55)}}
.vb-play{animation:playPulse2 2.2s ease-in-out infinite}
@keyframes playPulse2{0%,100%{box-shadow:0 0 0 8px rgba(212,175,106,.14),0 0 30px rgba(212,175,106,.4)}50%{box-shadow:0 0 0 15px rgba(212,175,106,.07),0 0 48px rgba(236,207,160,.65)}}
.rev-stars{animation:starTwinkle 2.6s ease-in-out infinite}
@keyframes starTwinkle{0%,100%{opacity:.75;text-shadow:0 0 12px rgba(236,207,160,.4)}50%{opacity:1;text-shadow:0 0 26px rgba(236,207,160,.85)}}
@media(prefers-reduced-motion:reduce){.btn-solid::before,.btn-solid::after,.c-action.c-call::before,.c-action.c-call::after{animation:none}}
/*SC-EXTRA-CSS-END*/"""

EXTRA_JS = """/*SC-EXTRA-JS*/
(function(){
  function ripple(b){
    b.addEventListener('click',function(e){
      var r=b.getBoundingClientRect();
      var x=e.clientX-r.left,y=e.clientY-r.top;
      var s=document.createElement('span');
      s.style.cssText='position:absolute;left:'+x+'px;top:'+y+'px;width:0;height:0;border-radius:50%;background:rgba(255,255,255,.55);transform:translate(-50%,-50%);pointer-events:none;transition:width .55s ease-out,height .55s ease-out,opacity .55s ease-out;';
      b.appendChild(s);
      requestAnimationFrame(function(){s.style.width='280px';s.style.height='280px';s.style.opacity='0';});
      setTimeout(function(){s.remove()},600);
    });
  }
  document.querySelectorAll('.btn,.c-action').forEach(ripple);
  if(matchMedia('(hover:hover) and (pointer:fine)').matches && !matchMedia('(prefers-reduced-motion: reduce)').matches){
    document.querySelectorAll('.car-slide,.rev-card,.svc,.step,.guar,.city,.stat').forEach(function(c){
      c.addEventListener('mousemove',function(e){
        var r=c.getBoundingClientRect();
        var rx=(e.clientX-r.left)/r.width-.5, ry=(e.clientY-r.top)/r.height-.5;
        c.style.transform='translateY(-10px) perspective(800px) rotateX('+(-ry*3).toFixed(2)+'deg) rotateY('+(rx*3).toFixed(2)+'deg) scale(1.02)';
      });
      c.addEventListener('mouseleave',function(){c.style.transform='';});
    });
  }
})();
/*SC-EXTRA-JS-END*/"""


def apply_overrides(html_text, content):
    # 1) Пользовательские замены текста
    for r in content.get("replacements", []):
        if not isinstance(r, dict):
            continue
        find = (r.get("find") or "").strip()
        repl = r.get("replace") or ""
        if find and find in html_text:
            html_text = html_text.replace(find, repl)
    # 2) Фикс Google: alternateName именно в блоке WebSite (якорь #website)
    anchor = '"@id": "https://кухниостровский.рф/#website",'
    if anchor in html_text and '"alternateName": "кухниостровский.рф"' not in html_text:
        html_text = html_text.replace(
            anchor,
            anchor + '\n  "alternateName": "кухниостровский.рф",', 1)
    # 3) Анимации на весь сайт (безопасно, не задваиваются)
    if "/*SC-EXTRA-CSS*/" not in html_text and "</style>" in html_text:
        html_text = html_text.replace("</style>", EXTRA_CSS + "\n</style>", 1)
    if "/*SC-EXTRA-JS*/" not in html_text and "</body>" in html_text:
        html_text = html_text.replace("</body>", "<script>" + EXTRA_JS + "</script>\n</body>", 1)
    return html_text


def uploads_list():
    if not os.path.isdir(UPLOAD_DIR):
        return []
    return ["/uploads/" + f for f in sorted(os.listdir(UPLOAD_DIR)) if not f.startswith(".")]


def make_token():
    # Токен только ASCII (timestamp.hex) — кириллица в cookie вызывает 500
    ts = str(int(time.time()))
    msg = ts + ":" + ADMIN_LOGIN
    sig = hmac.new(SESSION_SECRET.encode(), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return ts + "." + sig


def verify_token(token):
    try:
        payload, sig = token.rsplit(".", 1)
        msg = payload + ":" + ADMIN_LOGIN
        expect = hmac.new(SESSION_SECRET.encode(), msg.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expect):
            return False
        return int(time.time()) - int(payload) < SESSION_TTL
    except Exception:
        return False


def get_cookie(req, name):
    raw = req.headers.get("Cookie") or ""
    for part in raw.split(";"):
        part = part.strip()
        if part.startswith(name + "="):
            return part[len(name) + 1:]
    return None


ADMIN_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Вход — Кухни Островский</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Manrope',system-ui,sans-serif;background:#0e0c09;color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
.card{max-width:420px;width:100%;background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.25);border-radius:20px;padding:40px 34px;text-align:center;box-shadow:0 30px 80px rgba(0,0,0,.5)}
.logo{width:60px;height:60px;border-radius:50%;margin:0 auto 18px;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:28px;font-weight:700;color:#17120b;background:linear-gradient(135deg,#eccfa0,#d4af6a);box-shadow:0 10px 30px rgba(212,175,106,.4)}
h1{font-family:Georgia,serif;font-size:26px;margin-bottom:6px}
p.sub{color:#b9ad9a;font-size:14px;margin-bottom:26px}
label{display:block;text-align:left;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:#b9ad9a;margin:14px 0 6px}
input{width:100%;padding:14px 16px;border-radius:12px;border:1px solid rgba(236,207,160,.25);background:#0e0c09;color:#f5efe3;font-size:15px;outline:none;font-family:inherit}
input:focus{border-color:#d4af6a}
button{width:100%;margin-top:22px;padding:15px;border:0;border-radius:12px;font-size:14px;font-weight:700;letter-spacing:1px;text-transform:uppercase;cursor:pointer;color:#17120b;background:linear-gradient(135deg,#eccfa0,#d4af6a);font-family:inherit}
.err{margin-top:16px;padding:12px;border-radius:10px;background:rgba(200,60,50,.15);border:1px solid rgba(200,60,50,.4);color:#ffb4a8;font-size:13px}
a.back{display:block;margin-top:16px;color:#b9ad9a;font-size:13px;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <div class="logo">К</div>
  <h1>Кухни Островский</h1>
  <p class="sub">Вход в админ-панель</p>
  <form method="post" action="/admin/login">
    <label>Логин</label><input type="text" name="login" autocomplete="username" required>
    <label>Пароль</label><input type="password" name="password" autocomplete="current-password" required>
    <button type="submit">Войти</button>
    <!--ERR-->
  </form>
  <a class="back" href="/">← На сайт</a>
</div>
</body>
</html>"""


def admin_page():
    content = load_content()
    reps = content.get("replacements", [])
    rows = ""
    for r in reps:
        if not isinstance(r, dict):
            continue
        rows += ("<tr><td><input type='text' class='f' value='%s' placeholder='Что заменить'></td>"
                 "<td><input type='text' class='r' value='%s' placeholder='На что заменить'></td>"
                 "<td><button type='button' class='del' onclick=\"this.parentNode.parentNode.remove()\">✕</button></td></tr>"
                 ) % (esc(r.get("find", "")), esc(r.get("replace", "")))
    page_val = content.get("page") or PAGE
    return ADMIN_TEMPLATE.replace("__ROWS__", rows).replace("__PAGE__", esc(page_val))


ADMIN_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Админка — Кухни Островский</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Manrope',system-ui,sans-serif;background:#0e0c09;color:#f5efe3;min-height:100vh}
.top{position:sticky;top:0;z-index:50;background:rgba(14,12,9,.95);backdrop-filter:blur(14px);border-bottom:1px solid rgba(236,207,160,.2);padding:0 20px;display:flex;align-items:center;gap:14px;height:62px}
.top .logo{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-weight:700;color:#17120b;background:linear-gradient(135deg,#eccfa0,#d4af6a)}
.top h1{font-size:16px;flex:1}
.top a{color:#eccfa0;text-decoration:none;font-size:14px}
.top form{display:inline}
.top button{background:none;border:1px solid rgba(236,207,160,.4);color:#eccfa0;padding:8px 14px;border-radius:30px;cursor:pointer;font-family:inherit;font-size:13px}
.tabs{display:flex;gap:6px;padding:16px 20px 0;overflow-x:auto}
.tab-btn{white-space:nowrap;padding:10px 18px;border-radius:12px 12px 0 0;border:1px solid transparent;background:none;color:#b9ad9a;font-size:14px;cursor:pointer;font-family:inherit}
.tab-btn.active{color:#eccfa0;background:rgba(236,207,160,.08);border-color:rgba(236,207,160,.25) rgba(236,207,160,.25) transparent}
main{padding:22px 20px 80px;max-width:1100px;margin:0 auto}
.tab{display:none}
.tab.active{display:block}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.18);border-radius:16px;padding:22px;margin-bottom:18px}
.card h2{font-size:17px;color:#eccfa0;margin-bottom:12px}
.hint{font-size:12.5px;color:#b9ad9a;line-height:1.6;margin-bottom:14px}
table{width:100%;border-collapse:collapse;margin-top:10px}
th{text-align:left;color:#b9ad9a;font-size:12px;font-weight:500;padding:8px;border-bottom:1px solid rgba(236,207,160,.2)}
td{padding:6px 8px;border-bottom:1px solid rgba(236,207,160,.1)}
input[type=text],textarea{width:100%;padding:11px 13px;border-radius:10px;border:1px solid rgba(236,207,160,.22);background:#0e0c09;color:#f5efe3;font-size:14px;outline:none;font-family:inherit}
input:focus,textarea:focus{border-color:#d4af6a}
textarea{min-height:420px;font-family:ui-monospace,Consolas,monospace;font-size:12.5px;line-height:1.5;resize:vertical}
.btn{display:inline-flex;align-items:center;gap:8px;margin-top:14px;padding:13px 26px;border:0;border-radius:30px;background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit}
.btn.ghost{background:none;border:1px solid rgba(236,207,160,.4);color:#eccfa0}
.del{background:none;border:1px solid rgba(200,60,50,.5);color:#ff9d8f;width:32px;height:32px;border-radius:8px;cursor:pointer}
.add{padding:9px 16px;border-radius:30px;border:1px dashed rgba(236,207,160,.5);background:none;color:#eccfa0;cursor:pointer;font-family:inherit;margin-top:10px}
.uploads{display:flex;flex-wrap:wrap;gap:12px;margin-top:14px}
.up-item{border:1px solid rgba(236,207,160,.2);border-radius:10px;padding:8px;display:flex;flex-direction:column;gap:6px;align-items:center;max-width:140px;cursor:pointer}
.up-item img{width:100px;height:75px;object-fit:cover;border-radius:6px}
.up-item code{font-size:10px;color:#b9ad9a;word-break:break-all}
.toast{position:fixed;bottom:20px;left:50%;transform:translate(-50%,90px);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;font-weight:700;padding:13px 26px;border-radius:30px;z-index:999;opacity:0;transition:.3s;box-shadow:0 10px 30px rgba(0,0,0,.4)}
.toast.show{transform:translate(-50%,0);opacity:1}
@media(max-width:640px){main{padding:18px 14px 80px}.top h1{font-size:14px}}
</style>
</head>
<body>
<div class="top">
  <div class="logo">К</div>
  <h1>Админка — Кухни Островский</h1>
  <a href="/" target="_blank">Открыть сайт ↗</a>
  <form method="post" action="/admin/logout"><button>Выйти</button></form>
</div>

<div class="tabs">
  <button class="tab-btn active" data-tab="reps">Замены текста</button>
  <button class="tab-btn" data-tab="page">Вся страница</button>
  <button class="tab-btn" data-tab="files">Фото</button>
</div>

<main>
<div class="tab active" id="tab-reps">
  <div class="card">
    <h2>Замены текста на сайте</h2>
    <div class="hint">Меняй ЛЮБОЙ текст: телефон, заголовки, отзывы, цены, ссылки, URL картинок. Найди точную фразу, которая сейчас на сайте, и укажи, на что её заменить. Сохрани — и сайт сразу обновится.</div>
    <table>
      <thead><tr><th style="width:42%">Что найти (текст с сайта)</th><th style="width:48%">На что заменить</th><th></th></tr></thead>
      <tbody id="repRows">__ROWS__</tbody>
    </table>
    <button type="button" class="add" onclick="addRow()">+ Добавить замену</button>
    <br><button class="btn" onclick="saveReps()">💾 Сохранить замены</button>
  </div>
</div>

<div class="tab" id="tab-page">
  <div class="card">
    <h2>Вся страница (HTML/CSS/JS)</h2>
    <div class="hint">Максимальный контроль: здесь лежит весь HTML сайта. Меняй что угодно — вплоть до дизайна и анимаций. Чтобы вернуть как было — нажми «Вернуть оригинал».</div>
    <textarea id="pageEditor">__PAGE__</textarea>
    <br>
    <button class="btn" onclick="savePage()">💾 Сохранить страницу</button>
    <button class="btn ghost" onclick="resetPage()">↺ Вернуть оригинал</button>
  </div>
</div>

<div class="tab" id="tab-files">
  <div class="card">
    <h2>Загрузка фото</h2>
    <div class="hint">Загрузи картинку — получишь ссылку вида /uploads/xxx.jpg. Потом вставь её в замену (например, поменяй URL фото работы). Клик по картинке в списке — скопировать ссылку.</div>
    <input type="file" id="fileInput" accept=".png,.jpg,.jpeg,.webp,.gif,.svg">
    <br>
    <button class="btn" onclick="uploadFile()">⬆ Загрузить</button>
    <div class="uploads" id="uploadsList"></div>
  </div>
</div>
</main>

<div class="toast" id="toast"></div>

<script>
function toast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2200)}
document.querySelectorAll('.tab-btn').forEach(function(b){
  b.addEventListener('click',function(){
    document.querySelectorAll('.tab-btn').forEach(function(x){x.classList.remove('active')});
    document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('active')});
    b.classList.add('active');
    document.getElementById('tab-'+b.dataset.tab).classList.add('active');
  });
});
function addRow(){
  var tr=document.createElement('tr');
  tr.innerHTML="<td><input type='text' class='f' placeholder='Например: +7 (950) 846-53-97'></td>"+
               "<td><input type='text' class='r' placeholder='Новый текст'></td>"+
               "<td><button type='button' class='del' onclick=\"this.parentNode.parentNode.remove()\">✕</button></td>";
  document.getElementById('repRows').appendChild(tr);
}
function saveReps(){
  var reps=[];
  document.querySelectorAll('#repRows tr').forEach(function(tr){
    var f=tr.querySelector('.f'),r=tr.querySelector('.r');
    if(f&&f.value.trim())reps.push({find:f.value,replace:r?r.value:''});
  });
  fetch('/admin/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({replacements:reps})})
    .then(function(res){return res.json()}).then(function(d){toast(d.ok?'Сохранено ✅':'Ошибка: '+d.error)})
    .catch(function(e){toast('Ошибка: '+e)});
}
function savePage(){
  var v=document.getElementById('pageEditor').value;
  fetch('/admin/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page:v})})
    .then(function(res){return res.json()}).then(function(d){toast(d.ok?'Страница сохранена ✅':'Ошибка: '+d.error)})
    .catch(function(e){toast('Ошибка: '+e)});
}
function resetPage(){
  if(!confirm('Вернуть страницу к оригиналу? Все правки HTML пропадут.'))return;
  fetch('/admin/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page:''})})
    .then(function(res){return res.json()}).then(function(d){if(d.ok){toast('Оригинал восстановлен ✅');document.getElementById('pageEditor').value=document.getElementById('pageEditor').dataset.orig||'';}else{toast('Ошибка: '+d.error)}})
    .catch(function(e){toast('Ошибка: '+e)});
}
function uploadFile(){
  var inp=document.getElementById('fileInput');
  if(!inp.files.length){toast('Выберите файл');return}
  var fd=new FormData();fd.append('file',inp.files[0]);
  fetch('/admin/upload',{method:'POST',body:fd})
    .then(function(res){return res.json()})
    .then(function(d){if(d.ok){toast('Загружено! URL: '+d.url);loadUploads()}else{toast('Ошибка: '+d.error)}})
    .catch(function(e){toast('Ошибка: '+e)});
}
function loadUploads(){
  fetch('/uploads/list.json').then(function(r){return r.json()}).then(function(list){
    var box=document.getElementById('uploadsList');box.innerHTML='';
    (list||[]).forEach(function(u){
      var d=document.createElement('div');d.className='up-item';
      d.innerHTML='<img src="'+u+'" alt=""><code>'+u+'</code>';
      d.onclick=function(){if(navigator.clipboard)navigator.clipboard.writeText(u);toast('URL скопирован')};
      box.appendChild(d);
    });
  }).catch(function(){});
}
(function(){
  var ed=document.getElementById('pageEditor');if(ed)ed.dataset.orig=ed.value;
  loadUploads();
})();
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype="text/plain; charset=utf-8", cache="no-cache", gzip_ok=True):
        data = body.encode("utf-8") if isinstance(body, str) else body
        etag = '"' + hashlib.sha256(data).hexdigest()[:20] + '"'
        if code == 200 and self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache)
            self.end_headers()
            return
        accept_encoding = self.headers.get("Accept-Encoding", "")
        if gzip_ok and isinstance(body, str) and "gzip" in accept_encoding and len(data) > 700:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz:
                gz.write(data)
            data = buf.getvalue()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", cache)
            self.send_header("ETag", etag)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", cache)
            self.send_header("ETag", etag)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            if isinstance(body, str):
                self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            self.wfile.write(data)

    def _redirect(self, location, cache="public, max-age=86400"):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", cache)
        self.end_headers()

    def do_GET(self):
        try:
            self._do_get()
        except Exception as e:
            traceback.print_exc()
            self._send(500, "<h1>500 — ошибка сервера</h1><pre>" + esc(repr(e)) + "</pre>", "text/html; charset=utf-8", "no-cache")

    def _do_get(self):
        path = self.path.split("?")[0]

        if path == "/admin":
            if get_cookie(self, "sc_admin") and verify_token(get_cookie(self, "sc_admin")):
                self._send(200, admin_page(), "text/html; charset=utf-8", "no-cache")
            else:
                self._send(200, ADMIN_LOGIN_PAGE, "text/html; charset=utf-8", "no-cache")
            return

        if path in ("/", "/index.html"):
            content = load_content()
            base = content.get("page") or PAGE
            self._send(200, apply_overrides(base, content), "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, SITEMAP, "application/xml; charset=utf-8", "public, max-age=3600")
        elif path == "/uploads/list.json":
            self._send(200, json.dumps(uploads_list(), ensure_ascii=False), "application/json; charset=utf-8", "no-cache")
        elif path.startswith("/uploads/"):
            base_dir = os.path.realpath(UPLOAD_DIR)
            fp = os.path.realpath(os.path.join(UPLOAD_DIR, os.path.basename(path)))
            if not fp.startswith(base_dir) or not os.path.isfile(fp):
                self._send(404, PAGE_404, "text/html; charset=utf-8", "no-cache")
                return
            ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
            with open(fp, "rb") as f:
                self._send(200, f.read(), ctype, "public, max-age=86400", gzip_ok=False)
        elif path == "/favicon.ico":
            data = get_favicon()
            if not data:
                self._redirect(FAVICON_URL)
            elif _icons_cache["ico"]:
                self._send(200, _icons_cache["ico"], "image/x-icon", "public, max-age=86400", gzip_ok=False)
            else:
                self._send(200, data, "image/x-icon", "public, max-age=86400", gzip_ok=False)
        elif path == "/favicon-16x16.png":
            if _icons_cache["png16"]:
                self._send(200, _icons_cache["png16"], "image/png", "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/favicon-32x32.png":
            if _icons_cache["png32"]:
                self._send(200, _icons_cache["png32"], "image/png", "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/apple-touch-icon.png":
            if _icons_cache["png180"]:
                self._send(200, _icons_cache["png180"], "image/png", "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/manifest.webmanifest":
            self._send(200, MANIFEST, "application/manifest+json; charset=utf-8", "public, max-age=3600")
        else:
            self._send(404, PAGE_404, "text/html; charset=utf-8", "no-cache")

    def do_POST(self):
        path = self.path.split("?")[0]
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
                self._send(404, '{"ok":false,"error":"not found"}', "application/json; charset=utf-8", "no-cache")
        except Exception as e:
            traceback.print_exc()
            self._send(400, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), "application/json; charset=utf-8", "no-cache")

    def _read_body(self, max_size=MAX_UPLOAD):
        length = int(self.headers.get("Content-Length") or 0)
        if length > max_size:
            raise ValueError("body too large")
        return self.rfile.read(length)

    def _is_admin(self):
        return get_cookie(self, "sc_admin") and verify_token(get_cookie(self, "sc_admin"))

    def admin_login(self):
        body = self._read_body(64 * 1024).decode("utf-8")
        form = parse_qs(body)
        login = form.get("login", [""])[0]
        pwd = form.get("password", [""])[0]
        ok_l = hmac.compare_digest(login.encode("utf-8"), ADMIN_LOGIN.encode("utf-8"))
        ok_p = hmac.compare_digest(pwd.encode("utf-8"), ADMIN_PASSWORD.encode("utf-8"))
        if ok_l and ok_p:
            self.send_response(303)
            self.send_header("Location", "/admin")
            self.send_header("Set-Cookie", "sc_admin=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (make_token(), SESSION_TTL))
            self.end_headers()
        else:
            page = ADMIN_LOGIN_PAGE.replace("<!--ERR-->", '<div class="err">Неверный логин или пароль</div>')
            self._send(200, page, "text/html; charset=utf-8", "no-cache")

    def admin_logout(self):
        self.send_response(303)
        self.send_header("Location", "/admin")
        self.send_header("Set-Cookie", "sc_admin=; Path=/; HttpOnly; Max-Age=0")
        self.end_headers()

    def admin_save(self):
        if not self._is_admin():
            self._send(401, '{"ok":false,"error":"auth"}', "application/json; charset=utf-8", "no-cache")
            return
        body = self._read_body(2 * 1024 * 1024).decode("utf-8")
        data = json.loads(body)
        current = load_content()
        if "page" in data:
            current["page"] = data["page"]
        if "replacements" in data:
            current["replacements"] = data["replacements"]
        save_content(current)
        self._send(200, '{"ok":true}', "application/json; charset=utf-8", "no-cache")

    def admin_upload(self):
        if not self._is_admin():
            self._send(401, '{"ok":false,"error":"auth"}', "application/json; charset=utf-8", "no-cache")
            return
        ctype = self.headers.get("Content-Type", "")
        body = self._read_body()
        m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', ctype or "")
        if not m:
            self._send(400, '{"ok":false,"error":"no boundary"}', "application/json; charset=utf-8", "no-cache")
            return
        boundary = (m.group(1) or m.group(2)).strip().encode()
        fname, fdata = "", b""
        for raw in body.split(b"--" + boundary):
            if raw in (b"", b"\r\n", b"--\r\n") or raw.startswith(b"--"):
                continue
            head, sep, payload = raw.partition(b"\r\n\r\n")
            if not sep:
                continue
            fm = re.search(r'filename="([^"]*)"', head.decode("utf-8", "ignore"))
            if not fm:
                continue
            fname = fm.group(1)
            fdata = payload.rstrip(b"\r\n")
            break
        if not fname:
            self._send(400, '{"ok":false,"error":"file not found"}', "application/json; charset=utf-8", "no-cache")
            return
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ALLOWED_EXT:
            self._send(400, '{"ok":false,"error":"bad format"}', "application/json; charset=utf-8", "no-cache")
            return
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        name = secrets.token_hex(8) + ext
        with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
            f.write(fdata)
        self._send(200, json.dumps({"ok": True, "url": "/uploads/" + name}, ensure_ascii=False), "application/json; charset=utf-8", "no-cache")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if not os.path.exists(CONTENT_FILE):
        save_content({"replacements": [], "page": ""})
    print("Кухни Островский сервер запущен на http://0.0.0.0:{}".format(PORT))
    print("Админка: /admin  (логин: {}, пароль: {})".format(ADMIN_LOGIN, "*" * len(ADMIN_PASSWORD)))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
