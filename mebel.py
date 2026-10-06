# -*- coding: utf-8 -*-
"""mebel.py — Кухни Островский: сайт + админка."""
import base64
import gzip
import hashlib
import hmac
import html as _html
import io
import json
import os
import re
import secrets
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

PORT = int(os.environ.get("PORT", "8080"))
DOMAIN = os.environ.get("DOMAIN", "https://кухниостровский.рф").rstrip("/")
ROOT = os.path.dirname(os.path.abspath(__file__))

SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "https://hliafkrpvmntpctmqwfu.supabase.co").rstrip("/")
SUPABASE_ANON = os.environ.get("SUPABASE_ANON_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEyMDQ1NzYsImV4cCI6MjEwNjc4MDU3Nn0.yi57-Ty1iIfhnEh80_zvifhX1W_JX2qCl7QrARuJ2ns"
SUPABASE_SERVICE = os.environ.get("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTIwNDU3NiwiZXhwIjoyMTA2NzgwNTc2fQ.Yr4z9vx6kF9ZINNNUjUn43GYi-A2BmBfg8uyrOtmDWo"
BUCKET = os.environ.get("SUPABASE_BUCKET", "site-images")

ADMIN_LOGIN_ENV = os.environ.get("ADMIN_LOGIN", "кухниост")
ADMIN_PASSWORD_ENV = os.environ.get("ADMIN_PASSWORD", "романкух")

YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY", "")
FOLDER_ID = os.environ.get("FOLDER_ID", "")
GIGACHAT_AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY", "")
AI_PROVIDER = (os.environ.get("AI_PROVIDER", "auto") or "auto").lower()

DATA_TABLE = os.environ.get("SUPABASE_TABLE", "site_content")
SESSION_TTL = 604800
MAX_UPLOAD = 8 * 1024 * 1024
DATA_ROW_ID = 1
CACHE_TTL = 15
HTTP_TIMEOUT = 12

FAVICON_URL = "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0"
VIDEO_POSTER = "https://sun9-44.vkuserphoto.ru/s/v1/ig2/z3K7MYc56nf_4Ek_wkhJ-j-VZt7iv_VEt9wUN0gJSY0VORuRVxQCX1S5baisBgJyoYuCcrENJNxLajL1WKwdFS91.jpg?quality=95&cs=1280x0"

ROBOTS = "User-agent: *\nAllow: /\nHost: кухниостровский.рф\nSitemap: https://кухниостровский.рф/sitemap.xml\n"
MANIFEST = '{"name":"Кухни Островский","short_name":"Кухни Островский","start_url":"/","display":"standalone","background_color":"#0e0c09","theme_color":"#0e0c09","lang":"ru-RU","icons":[{"src":"/favicon.ico","sizes":"16x16 32x32 48x48 64x64","type":"image/x-icon"},{"src":"/apple-touch-icon.png","sizes":"180x180","type":"image/png"}]}'

PAGE_404 = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>404</title></head><body style="margin:0;background:#0e0c09;color:#f5efe3;font-family:system-ui;display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center"><div><h1 style="font-size:72px;color:#eccfa0">404</h1><p>Страница не найдена</p><a href="/" style="display:inline-block;margin-top:22px;padding:14px 26px;border-radius:12px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;text-decoration:none">На главную</a></div></body></html>"""

ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:linear-gradient(135deg,#0e0c09,#1a1611);color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.2);border-radius:20px;padding:42px 38px;width:100%;max-width:420px}
h1{font-family:Georgia,serif;font-size:28px;color:#fff;margin-bottom:8px;text-align:center}
p.sub{color:#b9ad9a;font-size:13.5px;text-align:center;margin-bottom:28px}
label{display:block;color:#eccfa0;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:600}
input{width:100%;padding:14px 16px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;font-size:15px;margin-bottom:18px}
input:focus{outline:none;border-color:#d4af6a}
button{width:100%;padding:15px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;border:none;border-radius:12px;cursor:pointer;text-transform:uppercase;letter-spacing:1px;font-family:inherit}
.err{background:rgba(220,60,60,.14);border:1px solid rgba(220,60,60,.4);color:#ff9a9a;padding:12px;border-radius:10px;font-size:13px;margin-bottom:18px;text-align:center}
</style></head><body>
<form class="card" method="POST" action="/admin/login">
<h1>Кухни Островский</h1><p class="sub">Панель управления</p>__ERROR__
<label>Логин</label><input type="text" name="login" required autofocus>
<label>Пароль</label><input type="password" name="password" required>
<button>Войти</button></form></body></html>"""

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
            req = urllib.request.Request(FAVICON_URL, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://vk.com/"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                _favicon_cache["data"] = data
                _favicon_cache["ts"] = now
                _make_icons(data)
        except Exception:
            return None
    return _favicon_cache["data"]


DATA_CACHE = {"data": None, "ts": 0.0}
SESSIONS = {}
SESSION_LOCK = threading.Lock()


def _sb_headers():
    key = SUPABASE_SERVICE or SUPABASE_ANON
    return {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": "application/json"}


def _sb_read():
    now = time.time()
    if DATA_CACHE["data"] is not None and now - DATA_CACHE["ts"] < CACHE_TTL:
        return DATA_CACHE["data"]
    url = SUPABASE_URL + "/rest/v1/" + DATA_TABLE + "?id=eq." + str(DATA_ROW_ID) + "&select=data"
    try:
        req = urllib.request.Request(url, headers=_sb_headers())
        with urllib.request.urlopen(req, timeout=10) as r:
            js = json.loads(r.read().decode("utf-8"))
        data = js[0]["data"] if js and js[0].get("data") else {}
    except Exception as e:
        print("[sb_read]", e, flush=True)
        data = DATA_CACHE["data"] or {}
    DATA_CACHE["data"] = data
    DATA_CACHE["ts"] = now
    return data


def _sb_save(data):
    url = SUPABASE_URL + "/rest/v1/" + DATA_TABLE
    headers = _sb_headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
    payload = json.dumps([{"id": DATA_ROW_ID, "data": data}], ensure_ascii=False).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            ok = r.status in (200, 201, 204)
        if ok:
            DATA_CACHE["data"] = data
            DATA_CACHE["ts"] = time.time()
        return ok
    except Exception as e:
        print("[sb_save]", e, flush=True)
        return False


def _new_session():
    t = secrets.token_urlsafe(32)
    with SESSION_LOCK:
        SESSIONS[t] = time.time() + SESSION_TTL
    return t


def _check_session(token):
    if not token:
        return False
    with SESSION_LOCK:
        exp = SESSIONS.get(token)
        if not exp:
            return False
        if exp < time.time():
            SESSIONS.pop(token, None)
            return False
    return True


def _drop_session(token):
    if token:
        with SESSION_LOCK:
            SESSIONS.pop(token, None)PAGE = """<!DOCTYPE html>
<html lang="ru" class="js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ</title>
<meta name="description" content="Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и 3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97">
<meta name="keywords" content="кухни остров, кухни островский, кухни островского, кухни островский ростов, кухни ростов островский, кухни батайск островский, кухни азов островский, кухни на заказ ростов, кухни на заказ батайск, кухни на заказ азов, мебель островского, мебель на заказ ростов, корпусная мебель, шкафы купе, гардеробные, прихожие, кухни под ключ, мебель островский">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="geo.region" content="RU-ROS">
<meta name="geo.placename" content="Ростов-на-Дону">
<meta name="theme-color" content="#0e0c09">
<link rel="canonical" href="https://кухниостровский.рф/">
<meta name="yandex-verification" content="f7e96d07aee79bf3">
<meta name="google-site-verification" content="dNSAELu64Y7aK5sjz_zpmhoz6YKn2PIZ03UKPwrgnCI">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Кухни Островский">
<meta property="og:url" content="https://кухниостровский.рф/">
<meta property="og:title" content="Кухни Островский — кухни на заказ в Ростове, Батайске и Азове">
<meta property="og:description" content="Кухни и корпусная мебель под ключ. Бесплатный замер и 3D-проект. ☎ +7 (950) 846-53-97">
<meta property="og:image" content="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,500&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0e0c09;--gold:#d4af6a;--gold-soft:#eccfa0;--gold-deep:#a37c3f;--text:#f5efe3;--muted:#b9ad9a;--r-lg:24px;--r-md:16px;--r-sm:12px;--shadow-lg:0 34px 80px rgba(0,0,0,.5);--shadow-md:0 18px 46px rgba(0,0,0,.36);--shadow-gold:0 16px 42px rgba(212,175,106,.26);--serif:'Cormorant Garamond',Georgia,serif;--sans:'Manrope',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;overflow-x:hidden}
section{scroll-margin-top:92px}
body{font-family:var(--sans);color:var(--text);line-height:1.72;-webkit-font-smoothing:antialiased;overflow-x:hidden;position:relative;min-height:100vh}
body::before{content:"";position:fixed;inset:0;z-index:-2;background:radial-gradient(1200px 700px at 85% -10%,rgba(212,175,106,.16),transparent 60%),radial-gradient(1000px 640px at -10% 30%,rgba(212,175,106,.09),transparent 55%),linear-gradient(180deg,#12100b,#0c0a07 45%,#100d09)}
.orb{position:fixed;border-radius:50%;pointer-events:none;z-index:-1}
.orb-1{width:560px;height:560px;left:-180px;top:10%;background:radial-gradient(circle,rgba(212,175,106,.13),transparent 65%);animation:orbFloat 18s ease-in-out infinite alternate}
.orb-2{width:480px;height:480px;right:-160px;top:40%;background:radial-gradient(circle,rgba(163,124,63,.12),transparent 65%);animation:orbFloat 24s ease-in-out infinite alternate-reverse}
.orb-3{width:640px;height:640px;left:28%;bottom:-240px;background:radial-gradient(circle,rgba(212,175,106,.08),transparent 65%);animation:orbFloat 30s ease-in-out infinite alternate}
@keyframes orbFloat{from{transform:translateY(-36px)}to{transform:translateY(44px)}}
::selection{background:rgba(212,175,106,.32);color:#fff}
h1,h2,h3{font-family:var(--serif);overflow-wrap:break-word;word-break:break-word;letter-spacing:.3px}
img{max-width:100%;display:block}
a{text-decoration:none;color:inherit}
ul{list-style:none}
button{font-family:inherit;cursor:pointer}
.wrap{width:100%;max-width:1180px;margin:0 auto;padding:0 20px}
.progress{position:fixed;top:0;left:0;height:3px;z-index:300;background:linear-gradient(90deg,var(--gold-deep),var(--gold-soft),var(--gold));width:0%;box-shadow:0 0 14px rgba(236,207,160,.7)}
#cursorGlow{position:fixed;left:0;top:0;width:340px;height:340px;border-radius:50%;pointer-events:none;z-index:55;background:radial-gradient(circle,rgba(212,175,106,.09),transparent 66%);mix-blend-mode:screen;display:none}
@media(hover:hover) and (pointer:fine){#cursorGlow{display:block}}
header{position:fixed;top:0;left:0;right:0;z-index:200;background:rgba(14,12,9,.55);backdrop-filter:blur(18px);transition:background .45s,box-shadow .45s}
header.solid{background:rgba(14,12,9,.92);box-shadow:0 12px 44px rgba(0,0,0,.45)}
.nav{display:flex;align-items:center;justify-content:space-between;height:78px;gap:12px}
.logo{display:flex;align-items:center;gap:13px;min-width:0;max-width:100%;cursor:pointer}
.brand-ava-w{position:relative;flex-shrink:0;display:inline-flex}
.brand-ava-w::before{content:"";position:absolute;inset:-5px;border-radius:50%;border:1px solid rgba(236,207,160,.5);opacity:.7;animation:ringPulse 3.6s ease-in-out infinite}
@keyframes ringPulse{0%,100%{transform:scale(.94);opacity:.35}50%{transform:scale(1.08);opacity:.75}}
.brand-ava{width:46px;height:46px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 5px rgba(212,175,106,.1),0 0 24px rgba(212,175,106,.4);position:relative;z-index:1}
.logo .brand-txt{display:flex;flex-direction:column;min-width:0;line-height:1.15}
.logo .brand-txt .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:var(--serif);font-size:26px;font-weight:600;color:#fff;background:linear-gradient(120deg,#fff,var(--gold-soft));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.logo .brand-txt .sub{color:var(--gold-soft);font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:62vw;margin-top:3px;opacity:.85}
.menu{position:fixed;top:0;height:78px;right:max(20px,calc((100vw - 1220px)/2));display:flex;gap:24px;align-items:center;z-index:201}
.menu a{position:relative;color:rgba(255,255,255,.8);font-size:13px;font-weight:600;letter-spacing:.5px;transition:.3s;padding:6px 0;white-space:nowrap}
.menu a::after{content:"";position:absolute;left:0;bottom:0;width:100%;height:1.5px;background:linear-gradient(90deg,var(--gold-soft),var(--gold));transform:scaleX(0);transform-origin:left;transition:transform .4s cubic-bezier(.22,.61,.36,1);border-radius:2px}
.menu a:hover{color:#fff}.menu a:hover::after{transform:scaleX(1)}
.menu a.active{color:var(--gold-soft)}.menu a.active::after{transform:scaleX(1)}
.sheet-handle{display:none}.menu-call{display:none}
.burger{display:none;background:none;border:none;cursor:pointer;width:44px;height:44px;position:relative;z-index:210;flex-shrink:0}
.burger span{position:absolute;left:7px;right:7px;height:2px;background:#fff;transition:.3s;border-radius:2px}
.burger span:nth-child(1){top:13px}.burger span:nth-child(2){top:21px}.burger span:nth-child(3){top:29px}
.burger.open span:nth-child(1){top:21px;transform:rotate(45deg)}
.burger.open span:nth-child(2){opacity:0}
.burger.open span:nth-child(3){top:21px;transform:rotate(-45deg)}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.5);opacity:0;visibility:hidden;transition:.35s;z-index:195;backdrop-filter:blur(3px)}
.scrim.show{opacity:1;visibility:visible}
[data-watermark]{position:relative}
[data-watermark]::before{content:attr(data-watermark);position:absolute;top:4%;right:2%;font-family:var(--serif);font-size:clamp(110px,16vw,230px);line-height:1;font-weight:600;color:transparent;-webkit-text-stroke:1px rgba(212,175,106,.07);white-space:nowrap;pointer-events:none;user-select:none;z-index:0}
[data-watermark] .wrap{position:relative;z-index:1}
.panel{position:relative;min-height:100vh;display:flex;align-items:center;padding:150px 0;overflow:hidden}
.panel .bg{position:absolute;inset:-14% 0;z-index:0;background-size:cover;background-position:center;will-change:transform;transform:translateZ(0)}
.panel .bg::after{content:"";position:absolute;inset:0;background:linear-gradient(to right,rgba(10,8,6,.94) 22%,rgba(10,8,6,.6) 58%,rgba(10,8,6,.75))}
.panel--hero .bg::before{content:"";position:absolute;inset:-8%;background-image:inherit;background-size:cover;background-position:center;animation:kenburns 22s ease-in-out infinite alternate;will-change:transform}
@keyframes kenburns{from{transform:scale(1)}to{transform:scale(1.1)}}
.panel--hero .bg::after{z-index:1}
.panel .content{position:relative;z-index:2;width:100%;will-change:transform;transform:translateZ(0)}
.panel--center .content{text-align:center}
.panel--center .bg::after{background:linear-gradient(180deg,rgba(10,8,6,.86),rgba(10,8,6,.62))}
.panel--dark .bg::after{background:linear-gradient(180deg,rgba(10,8,6,.9),rgba(10,8,6,.7))}
.panel + .panel{margin-top:16px}
.gold-divider{display:flex;align-items:center;justify-content:center;gap:14px;padding:6px 0}
.gold-divider i{display:inline-block;width:64px;height:1px;background:linear-gradient(90deg,transparent,var(--gold));opacity:.6}
.gold-divider i:last-child{background:linear-gradient(90deg,var(--gold),transparent)}
.gold-divider b{width:7px;height:7px;transform:rotate(45deg);background:var(--gold);box-shadow:0 0 12px rgba(212,175,106,.55)}
.eyebrow{display:inline-flex;align-items:center;gap:12px;color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:12px;font-weight:600;margin-bottom:20px}
.eyebrow::before{content:"";width:42px;height:1px;background:linear-gradient(90deg,transparent,var(--gold))}
.eyebrow::after{content:"";width:42px;height:1px;background:linear-gradient(90deg,var(--gold),transparent)}
h1{font-size:clamp(34px,6vw,76px);font-weight:500;line-height:1.08;color:#fff;letter-spacing:.4px;text-shadow:0 5px 30px rgba(0,0,0,.5);max-width:100%}
h1 em{font-style:italic}
.sub{color:rgba(245,239,227,.9);font-size:clamp(16px,1.8vw,19.5px);font-weight:300;margin:24px 0 34px;max-width:580px;text-shadow:0 2px 16px rgba(0,0,0,.55)}
.btn-row{display:flex;gap:16px;flex-wrap:wrap}
.btn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:15px 30px;font-size:13px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;transition:transform .4s cubic-bezier(.22,.61,.36,1),box-shadow .4s;cursor:pointer;border-radius:13px;border:none}
.btn-solid{background:linear-gradient(135deg,var(--gold-soft),var(--gold) 55%,var(--gold-deep));color:#17120b;box-shadow:var(--shadow-gold);animation:btnGlow 3.6s ease-in-out infinite}
@keyframes btnGlow{0%,100%{box-shadow:0 16px 42px rgba(212,175,106,.26)}50%{box-shadow:0 24px 62px rgba(236,207,160,.5)}}
.btn-solid:hover{transform:translateY(-4px);box-shadow:0 26px 60px rgba(212,175,106,.45)}
.btn-line{border:1px solid rgba(255,255,255,.4);color:#fff;background:rgba(255,255,255,.04)}
.btn-line:hover{background:rgba(255,255,255,.12);transform:translateY(-4px)}
.btn::after{content:"";position:absolute;top:0;left:-130%;width:55%;height:100%;background:linear-gradient(120deg,transparent,rgba(255,255,255,.4),transparent);transform:skewX(-20deg);transition:left .7s ease}
.btn:hover::after{left:145%}
.shimmer{background:linear-gradient(90deg,var(--gold-soft),#fff 35%,var(--gold-soft) 70%);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerMove 3.4s linear infinite}
@keyframes shimmerMove{0%{background-position:0% center}100%{background-position:-220% center}}
h1 em.shimmer{-webkit-text-fill-color:transparent}
.cta h2.shimmer{-webkit-text-fill-color:transparent}
.scroll-cue{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);z-index:5;color:rgba(255,255,255,.75);font-size:11px;letter-spacing:4px;text-transform:uppercase;text-align:center;animation:fadeInUp 1s ease .8s both}
.scroll-cue .line{width:1px;height:46px;background:linear-gradient(180deg,var(--gold-soft),transparent);margin:10px auto 0;animation:drip 2.4s infinite}
@keyframes drip{0%{transform:scaleY(0);transform-origin:top}50%{transform:scaleY(1);transform-origin:top}51%{transform-origin:bottom}100%{transform:scaleY(0);transform-origin:bottom}}
@keyframes fadeInUp{from{opacity:0;transform:translate(-50%,10px)}to{opacity:1;transform:translate(-50%,0)}}
.sec-head{max-width:740px;margin:0 auto 52px;text-align:center}
.sec-head .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.sec-head h2{position:relative;font-size:clamp(30px,4.4vw,48px);font-weight:500;margin:16px 0 14px;line-height:1.14;color:#faf3e6;text-shadow:0 4px 22px rgba(0,0,0,.45),0 0 40px rgba(212,175,106,.14)}
.sec-head h2::before,.sec-head h2::after{content:"";position:absolute;top:50%;width:56px;height:1px;background:linear-gradient(90deg,transparent,var(--gold));transform:translateY(-50%);opacity:.7}
.sec-head h2::before{right:calc(100% + 26px)}
.sec-head h2::after{left:calc(100% + 26px)}
.sec-head p{color:var(--muted);font-size:15.5px;max-width:620px;margin:0 auto}
h2.k{position:relative;font-size:clamp(32px,4.6vw,48px);color:#faf3e6;font-weight:500;margin:16px 0 14px;text-align:center;text-shadow:0 4px 22px rgba(0,0,0,.45),0 0 40px rgba(212,175,106,.14)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;text-align:center}
.stat{padding:32px 16px;border-radius:var(--r-md);background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);transition:transform .45s,border-color .45s,box-shadow .45s}
.stat:hover{transform:translateY(-6px);border-color:rgba(236,207,160,.3);box-shadow:0 22px 54px rgba(0,0,0,.42)}
.stat .num{font-family:var(--serif);font-size:58px;font-weight:500;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold) 60%,var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.stat .lbl{color:var(--muted);font-size:13.5px;margin-top:12px}
.about{display:grid;grid-template-columns:1fr 1.1fr;gap:64px;align-items:center}
.about-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:48px 40px;text-align:center;border-radius:var(--r-lg);box-shadow:var(--shadow-md);position:relative;overflow:hidden}
.about-card::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.6}
.avatar{width:130px;height:130px;border-radius:50%;margin:0 auto 22px;overflow:hidden;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 7px rgba(212,175,106,.12),0 16px 40px rgba(0,0,0,.5);position:relative}
.avatar img{width:100%;height:100%;object-fit:cover}
.about-card h3{font-size:29px;color:#fff}
.about-card .role{color:var(--gold-soft);font-size:13px;margin-top:5px}
.about-card .sep{width:52px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:22px auto}
.about-card p{color:var(--muted);font-size:14.5px;line-height:1.76}
.about-body .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.about-body h2{font-size:clamp(30px,3.6vw,44px);font-weight:500;margin:16px 0 22px;line-height:1.14;color:#faf3e6}
.about-body p{color:var(--muted);font-size:15.5px;margin-bottom:26px}
.features{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.features li{position:relative;padding-left:36px;color:var(--text);font-size:14.5px;transition:transform .3s}
.features li:hover{transform:translateX(5px)}
.features li::before{content:"";position:absolute;left:0;top:4px;width:18px;height:18px;border:1.5px solid rgba(212,175,106,.6);border-radius:50%;background:rgba(212,175,106,.08)}
.features li::after{content:"+";position:absolute;left:4px;top:4px;font-size:14px;color:var(--gold-soft);font-weight:800;line-height:1}
.consult .phone{display:inline-block;font-weight:800;font-size:clamp(30px,4.4vw,52px);letter-spacing:1px;margin-top:12px;white-space:nowrap;background:linear-gradient(120deg,var(--gold-soft),var(--gold));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.consult p{color:var(--muted);font-size:15.5px;margin:30px auto 0;max-width:630px;line-height:1.82}
.carousel{position:relative;max-width:1120px;margin:0 auto}
.car-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;padding:12px 8px 24px;scrollbar-width:none}
.car-track::-webkit-scrollbar{display:none}
.car-nav{position:absolute;top:38%;transform:translateY(-50%);width:48px;height:48px;border-radius:50%;background:rgba(14,12,9,.68);border:1px solid rgba(236,207,160,.35);color:var(--gold-soft);font-size:21px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform .4s;z-index:5}
.car-nav:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-50%) scale(1.08)}
.car-prev{left:-16px}.car-next{right:-16px}
.car-dots{display:flex;justify-content:center;gap:10px;margin-top:12px;flex-wrap:wrap}
.car-dot{width:8px;height:8px;min-width:8px;border-radius:99px;background:rgba(255,255,255,.2);cursor:pointer;transition:width .35s,background .35s;border:none;padding:0}
.car-dot:hover{background:rgba(236,207,160,.55)}
.car-dot.active{width:26px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));box-shadow:0 0 12px rgba(236,207,160,.6)}
.swipe-hint{display:flex;align-items:center;justify-content:center;gap:8px;color:var(--muted);font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-top:10px;animation:hintPulse 1.8s ease-in-out infinite}
.swipe-hint::after{content:"->";display:inline-block}
.car-slide{flex:0 0 auto;width:min(78vw,440px);scroll-snap-align:center;border-radius:var(--r-lg);overflow:hidden;border:1px solid rgba(255,255,255,.08);background:linear-gradient(135deg,#16120c,#0b0906);cursor:zoom-in;transition:transform .5s cubic-bezier(.22,.61,.36,1),box-shadow .5s,border-color .5s;box-shadow:var(--shadow-md);position:relative}
.car-slide:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.3);box-shadow:var(--shadow-lg)}
.car-slide img{width:100%;height:300px;object-fit:cover;display:block}
.rev-track{align-items:flex-start}
.rev-card{scroll-snap-align:center;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);padding:24px 26px;width:min(82vw,520px);flex:0 0 auto;display:flex;flex-direction:column;box-shadow:var(--shadow-md);position:relative;overflow:hidden;transition:transform .5s,box-shadow .5s}
.rev-card:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.28);box-shadow:var(--shadow-lg)}
.rev-head{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.rev-ava{width:50px;height:50px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.6);flex-shrink:0}
.rev-name{color:#fff;font-weight:700;font-size:14.5px}
.rev-sub{color:var(--muted);font-size:11px;margin-top:2px}
.rev-stars{color:var(--gold-soft);letter-spacing:3px;font-size:14px;margin-left:auto;white-space:nowrap}
.rev-text{color:#ece2cd;font-size:13.5px;line-height:1.66;font-weight:300;text-align:left;word-break:break-word}
.rev-video{margin-top:14px;border-radius:var(--r-md);overflow:hidden;border:1px solid rgba(255,255,255,.08)}
.video-box{position:relative;width:100%;height:260px;background-size:cover;background-position:center;cursor:pointer;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#16120c,#0b0906)}
.vb-play{position:relative;z-index:2;width:64px;height:64px;border-radius:50%;border:1px solid rgba(236,207,160,.7);background:rgba(14,12,9,.55);color:var(--gold-soft);display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 0 0 8px rgba(212,175,106,.14),0 0 30px rgba(212,175,106,.4)}
.vb-play svg{width:22px;height:22px;fill:currentColor;margin-left:3px}
.video-box iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.svc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.svc{position:relative;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 30px;transition:transform .5s cubic-bezier(.22,.61,.36,1),box-shadow .5s,border-color .5s;border-radius:var(--r-lg);overflow:hidden}
.svc:hover{transform:translateY(-8px);background:rgba(255,255,255,.05);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.svc svg{width:34px;height:34px;stroke:var(--gold-soft);fill:none;stroke-width:1.4;margin-bottom:20px}
.svc h3{font-size:23px;color:#fff;margin-bottom:9px}
.svc p{color:var(--muted);font-size:14px;line-height:1.7}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.step{position:relative;padding:34px 26px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);transition:transform .45s,box-shadow .45s,border-color .45s;overflow:hidden}
.step:hover{transform:translateY(-7px);border-color:rgba(236,207,160,.28);box-shadow:var(--shadow-md)}
.step .n{font-family:var(--serif);font-size:54px;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.step h3{font-size:22px;color:#fff;margin:14px 0 8px}
.step p{color:var(--muted);font-size:14px;line-height:1.7}
.guar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.guar{position:relative;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 26px;text-align:center;transition:transform .45s,box-shadow .45s,border-color .45s;border-radius:var(--r-lg);overflow:hidden}
.guar:hover{transform:translateY(-8px);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.guar .ico{width:54px;height:54px;margin:0 auto 18px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);background:radial-gradient(circle at 30% 30%,rgba(236,207,160,.16),rgba(212,175,106,.03));transition:transform .45s}
.guar .ico svg{width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:1.5}
.guar h3{font-size:18px;color:#fff;margin-bottom:8px}
.guar p{color:var(--muted);font-size:13px;line-height:1.7}
.city-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.city{position:relative;padding:38px 28px;border-radius:var(--r-lg);background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);text-align:center;transition:transform .45s,box-shadow .45s,border-color .45s;overflow:hidden}
.city:hover{transform:translateY(-7px);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.city .city-name{font-family:var(--serif);font-size:28px;color:#fff;font-weight:500}
.city .city-line{width:42px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:14px auto}
.city p{color:var(--muted);font-size:14px;line-height:1.68}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}
.contact-info h2{font-size:clamp(30px,4.1vw,46px);color:#faf3e6;margin:16px 0 14px;line-height:1.12}
.contact-info .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.contact-info>p{color:var(--muted);font-size:15.5px;margin-bottom:32px}
.c-line{display:flex;align-items:flex-start;gap:20px;margin-bottom:24px;transition:transform .4s}
.c-line:hover{transform:translateX(6px)}
.c-ico{width:44px;height:44px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);background:radial-gradient(circle at 30% 30%,rgba(236,207,160,.15),rgba(212,175,106,.02));flex-shrink:0;transition:transform .45s}
.c-ico svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.5}
.c-line .lab{font-size:10.5px;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.c-line .val{font-size:18px;font-weight:600;color:var(--text);word-break:break-word}
.c-line a.val:hover{color:var(--gold-soft)}
.call-block{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:46px 36px;text-align:center;border-radius:var(--r-lg);box-shadow:var(--shadow-md);position:relative;overflow:hidden}
.call-block .cb-lab{font-size:12px;letter-spacing:4px;text-transform:uppercase;color:var(--gold-soft)}
.call-block .cb-num{display:block;font-weight:800;font-size:clamp(27px,3.6vw,44px);color:#fff;margin:14px 0 18px;white-space:nowrap;transition:color .3s;text-shadow:0 5px 22px rgba(0,0,0,.42)}
.call-block .cb-num:hover{color:var(--gold-soft)}
.call-block .cb-hint{color:var(--muted);font-size:14px;line-height:1.82}
.contact-actions{display:flex;flex-direction:column;gap:12px;margin-top:24px}
.c-action{display:flex;align-items:center;justify-content:center;gap:11px;width:100%;min-height:52px;padding:15px 18px;border-radius:var(--r-sm);font-weight:700;font-size:14.5px;transition:transform .4s,background .4s,filter .4s,box-shadow .4s;color:#fff}
.c-action svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8}
.c-action.c-call{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;box-shadow:var(--shadow-gold)}
.c-action.c-call:hover{filter:brightness(1.08);transform:translateY(-4px)}
.c-action.c-tg{background:rgba(64,169,242,.12);border:1px solid rgba(64,169,242,.38);color:#8fd0ff}
.c-action.c-tg:hover{background:rgba(64,169,242,.24);transform:translateY(-4px)}
.c-action.c-max{background:rgba(177,88,252,.12);border:1px solid rgba(177,88,252,.38);color:#e0b8ff}
.c-action.c-max:hover{background:rgba(177,88,252,.24);transform:translateY(-4px)}
.cta{text-align:center;padding:110px 0;position:relative}
.cta h2{font-size:clamp(32px,4.6vw,52px);color:#faf3e6;font-weight:500;margin-bottom:16px;text-shadow:0 5px 26px rgba(0,0,0,.45)}
.cta p{color:var(--muted);font-size:16.5px;max-width:630px;margin:0 auto 34px}
footer{position:relative;background:linear-gradient(180deg,rgba(14,12,9,.4),rgba(10,8,6,.97));color:var(--muted);padding:52px 20px 60px;text-align:center;font-size:13px;border-top:1px solid rgba(255,255,255,.06)}
footer::before{content:"";position:absolute;top:-1px;left:50%;transform:translateX(-50%);width:min(420px,72%);height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
footer .flogo{font-family:var(--serif);font-size:28px;color:#fff;margin-bottom:8px;line-height:1.3}
footer .flogo span{color:var(--gold-soft);font-size:13px;font-weight:500;letter-spacing:1px}
.social-row{display:flex;justify-content:center;gap:14px;margin:22px 0 18px;flex-wrap:wrap}
.soc{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:50%;border:1px solid rgba(236,207,160,.32);color:var(--gold-soft);background:rgba(212,175,106,.06);transition:transform .35s,background .35s,box-shadow .35s}
.soc svg{width:19px;height:19px;stroke:currentColor;fill:none;stroke-width:1.6}
.soc:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-4px);box-shadow:var(--shadow-gold)}
.cookie-bar{position:fixed;bottom:16px;left:50%;transform:translate(-50%,140%);z-index:400;background:rgba(14,12,9,.93);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.08);border-radius:var(--r-md);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;box-shadow:var(--shadow-lg);width:min(680px,calc(100vw - 32px));transition:transform .6s cubic-bezier(.22,.61,.36,1)}
.cookie-bar.show{transform:translate(-50%,0)}
.cookie-bar p{color:var(--muted);font-size:13px;max-width:720px;line-height:1.5}
.cookie-bar .btn{flex-shrink:0;padding:12px 26px}
.lightbox{position:fixed;inset:0;z-index:3000;background:rgba(8,6,4,.96);backdrop-filter:blur(10px);display:none;align-items:center;justify-content:center;flex-direction:column;gap:14px}
.lightbox.open{display:flex;animation:lbFade .3s ease}
@keyframes lbFade{from{opacity:0}to{opacity:1}}
.lb-stage{position:relative;width:100%;max-width:1180px;height:calc(100vh - 130px);display:flex;align-items:center;justify-content:center;overflow:hidden;touch-action:none}
.lb-stage img{max-width:94%;max-height:100%;border-radius:var(--r-lg);border:1px solid rgba(236,207,160,.55);box-shadow:0 26px 90px rgba(0,0,0,.8);cursor:grab;transition:transform .18s ease-out;user-select:none}
.lb-bar{display:flex;align-items:center;justify-content:center;gap:20px}
.lb-count{color:var(--muted);font-size:13px;min-width:70px;text-align:center}
.lb-close{position:absolute;top:18px;right:24px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#fff;font-size:28px;cursor:pointer;z-index:5;line-height:1;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:transform .3s,background .3s}
.lb-close:hover{transform:rotate(90deg);background:rgba(236,207,160,.18)}
.lb-nav{width:50px;height:50px;border-radius:50%;background:rgba(14,12,9,.6);border:1px solid rgba(236,207,160,.5);color:var(--gold-soft);font-size:24px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .3s,transform .3s}
.lb-nav:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:scale(1.06)}
.js .reveal{opacity:0;transform:translateY(26px);transition:opacity .8s ease,transform .8s cubic-bezier(.22,.61,.36,1)}
.js .reveal.in{opacity:1;transform:none}
@media(max-width:1024px){.stats{grid-template-columns:repeat(2,1fr);gap:30px}.svc-grid{grid-template-columns:repeat(2,1fr)}.guar-grid{grid-template-columns:repeat(2,1fr)}.panel{padding:132px 0}}
@media(max-width:860px){.menu{position:fixed;top:auto;left:0;right:0;bottom:0;width:100%;max-height:82vh;background:linear-gradient(180deg,#16130e,#0b0907);flex-direction:column;gap:4px;padding:12px 24px 22px;transform:translateY(105%);transition:transform .45s;z-index:205;border-radius:26px 26px 0 0;overflow-y:auto;height:auto}.menu.open{transform:none}.sheet-handle{display:flex;justify-content:center;padding:4px 0 8px}.sheet-handle span{width:42px;height:4px;border-radius:99px;background:rgba(236,207,160,.35)}.menu a{font-size:19px;font-family:var(--serif);color:#fff;border-bottom:1px solid rgba(236,207,160,.12);padding:13px 6px;display:flex;align-items:center;min-height:48px}.menu a::after{display:none}.menu-call{display:block;margin-top:10px;padding-top:10px;border-top:1px solid rgba(236,207,160,.14)}.menu-call a{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:52px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;font-size:14.5px;font-weight:700;border:none;border-radius:var(--r-sm);padding:15px 18px}.burger{display:block}.scrim{display:block}.about{grid-template-columns:1fr;gap:36px}.features{grid-template-columns:1fr}.steps{grid-template-columns:1fr;gap:20px}.contact-grid{grid-template-columns:1fr;gap:36px}.city-grid{grid-template-columns:1fr}.panel{padding:116px 0}.car-nav{display:none}.rev-card{width:86vw}.video-box{height:230px}}
@media(max-width:520px){.logo .brand-ava{width:40px;height:40px}.logo .brand-txt .name{font-size:20px}.nav{height:64px}.panel{min-height:auto;padding:96px 0 56px}h1{font-size:31px}.sub{font-size:15px;margin:18px 0 26px}.btn-row{width:100%}.btn{width:100%;text-align:center}.car-slide{width:84vw}.car-slide img{height:240px}.rev-card{width:92vw;padding:17px}.rev-text{font-size:12.5px}.video-box{height:190px}.consult .phone{font-size:25px}.call-block .cb-num{font-size:22px}}
</style>
</head>
<body>
<div class="progress" id="progress"></div>
<div id="cursorGlow" aria-hidden="true"></div>
<div class="orb orb-1" aria-hidden="true"></div>
<div class="orb orb-2" aria-hidden="true"></div>
<div class="orb orb-3" aria-hidden="true"></div>
<header id="header">
  <div class="wrap nav">
    <a href="#top" class="logo" id="logo">
      <span class="brand-ava-w"><img class="brand-ava" src="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=512x0" width="46" height="46" alt="Кухни Островский"></span>
      <span class="brand-txt"><span class="name">Кухни Островский</span><span class="sub">Ростов · Батайск · Азов</span></span>
    </a>
    <button class="burger" id="burger" aria-label="Меню"><span></span><span></span><span></span></button>
  </div>
</header>
<ul class="menu" id="menu">
  <li class="sheet-handle"><span></span></li>
  <li><a href="#about">Специалист</a></li>
  <li><a href="#works">Работы</a></li>
  <li><a href="#reviews">Отзывы</a></li>
  <li><a href="#services">Услуги</a></li>
  <li><a href="#process">Как работаем</a></li>
  <li><a href="#cities">Города</a></li>
  <li><a href="#contacts">Контакты</a></li>
</ul>
<div class="scrim" id="scrim"></div>
<section class="panel panel--hero" id="top" data-watermark="Мебель">
  <div class="bg" style="background-image:url('https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <span class="eyebrow">Мебель и кухни на заказ</span>
    <h1 id="heroTitle">Мебель, которая <em class="shimmer">создаёт настроение</em></h1>
    <p class="sub">Проектируем и изготавливаем кухни, шкафы, гардеробные и другую корпусную мебель в Ростове, Батайске и Азове — по вашему проекту, от замера до монтажа.</p>
    <div class="btn-row">
      <a href="#consult" class="btn btn-solid">Получить консультацию</a>
      <a href="#works" class="btn btn-line">Смотреть работы</a>
    </div>
  </div></div>
  <div class="scroll-cue">Листайте<div class="line"></div></div>
</section>
<section class="panel panel--dark">
  <div class="bg" style="background-image:url('https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="stats">
      <div class="stat reveal"><div class="num" data-count="10" data-suffix="+">0</div><div class="lbl">лет опыта</div></div>
      <div class="stat reveal"><div class="num" data-count="5" data-decimal="1">0</div><div class="lbl">средняя оценка клиентов</div></div>
      <div class="stat reveal"><div class="num" data-count="8" data-suffix="/10">0</div><div class="lbl">клиентов по рекомендации</div></div>
      <div class="stat reveal"><div class="num" data-count="100" data-suffix="%">0</div><div class="lbl">полный цикл под ключ</div></div>
    </div>
  </div></div>
</section>
<section class="panel" id="about">
  <div class="bg" style="background-image:url('https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="about">
      <div class="about-card reveal">
        <div class="avatar"><img src="https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg" width="130" height="130" loading="lazy" alt="Роман Островский"></div>
        <h3>Роман Островский</h3>
        <div class="role">Руководитель мебельной мастерской Островского</div>
        <div class="sep"></div>
        <p>С командой изготавливаем кухни и корпусную мебель по индивидуальным проектам — с учётом ваших идей, размеров и задач.</p>
      </div>
      <div class="about-body reveal">
        <div class="kicker">О руководителе</div>
        <h2>Кухни и мебель под ключ — с заботой о деталях</h2>
        <p>Мы помогаем с планировкой и подбором материалов, предлагаем решения даже для сложных задач — когда другие разводят руками. Ведём вас от консультации и замера до сборки и установки.</p>
        <ul class="features">
          <li>Кухни, шкафы, гардеробные и прихожие</li>
          <li>Честный расчёт — без навязывания лишнего</li>
          <li>Аккуратность, пунктуальность, сопровождение</li>
          <li>Гарантия качества</li>
        </ul>
      </div>
    </div>
  </div></div>
</section>
<div class="gold-divider"><i></i><b></b><i></i></div>
<section class="panel panel--center panel--dark" id="consult">
  <div class="bg" style="background-image:url('https://sun9-8.vkuserphoto.ru/s/v1/ig2/AoDEQQq8KCsEBOBqdk9RRlULuWjVVgCUagW7IM8b_22MwfOkqLPub-TPecVvAY3Ke9SQAv0kJ2TNClg7D6J-A8exIN_BuA.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content consult">
    <span class="kicker reveal" style="color:var(--gold-soft);letter-spacing:6px;text-transform:uppercase;font-size:12px;font-weight:600">Бесплатно</span>
    <h2 class="k reveal">Консультация</h2>
    <a href="tel:+79508465397" class="phone reveal">+7 (950) 846-53-97</a>
    <p class="reveal">Позвоните или напишите нам в <b style="color:#fff">Telegram</b> или <b style="color:#fff">MAX</b> — расскажем про кухни и мебель, всё обсудим и договоримся о бесплатном замере.</p>
  </div></div>
</section>
<section class="panel panel--center panel--dark" id="works" data-watermark="Работы">
  <div class="bg" style="background-image:url('https://sun9-16.vkuserphoto.ru/s/v1/ig2/ixSL4F3j2Ap0i5_nVXsAKJNZZNAI7zoUPBfzKGHoj3gghnjX-hMD-JRLJaSlCoWevjw84ikJrGOfVeMqWyZ7ftzM.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Наши работы</div>
      <h2>Кухни и мебель, которые мы сделали</h2>
      <p>Нажмите на фото, чтобы рассмотреть в большом размере.</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="carPrev">&#10094;</button>
      <div class="car-track" id="carTrack">
        <div class="car-slide"><img loading="lazy" src="https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&cs=2560x0" alt="Кухня на заказ в Ростове"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-8.vkuserphoto.ru/s/v1/ig2/AoDEQQq8KCsEBOBqdk9RRlULuWjVVgCUagW7IM8b_22MwfOkqLPub-TPecVvAY3Ke9SQAv0kJ2TNClg7D6J-A8exIN_BuA.jpg?quality=95&cs=2560x0" alt="Кухня на заказ в Батайске"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-16.vkuserphoto.ru/s/v1/ig2/ixSL4F3j2Ap0i5_nVXsAKJNZZNAI7zoUPBfzKGHoj3gghnjX-hMD-JRLJaSlCoWevjw84ikJrGOfVeMqWyZ7ftzM.jpg?quality=95&cs=2560x0" alt="Кухня на заказ в Азове"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-6.vkuserphoto.ru/s/v1/ig2/JKHhwxCxe9S8QiEr0nEM-BhAyX2i0e3uIKGPBdi__ZkSecHlRyd93LMhVldSePb2ePDSA6kgE41mw1rNGCHoKdAnBE3sGg.jpg?quality=95&cs=2560x0" alt="Мебель на заказ в Ростове"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-4.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=2560x0" alt="Кухня на заказ"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-71.vkuserphoto.ru/s/v1/ig2/4XeUobSuuxA-pHVDGYziNB5aAnUsbLzt1Bgi8TtDa5yKbWt2yRxo8Egt_2a_Sz_jAYg1f2sxfOOy-ngKWvlDbjuqyHjSaQ.jpg?quality=95&cs=2560x0" alt="Шкаф-купе на заказ"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&cs=2560x0" alt="Мебель на заказ в Батайске"></div>
        <div class="car-slide"><img loading="lazy" src="https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&cs=2560x0" alt="Кухня на заказ"></div>
      </div>
      <button class="car-nav car-next" id="carNext">&#10095;</button>
      <div class="car-dots" id="carDots"></div>
      <div class="swipe-hint">Листайте</div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше работ — в сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>
<div class="lightbox" id="lightbox">
  <button class="lb-close" id="lbClose">x</button>
  <div class="lb-stage" id="lbStage"><img id="lbImg" alt="Работа"></div>
  <div class="lb-bar">
    <button class="lb-nav lb-prev" id="lbPrev">&#10094;</button>
    <div class="lb-count" id="lbCount"></div>
    <button class="lb-nav lb-next" id="lbNext">&#10095;</button>
  </div>
</div>
<section class="panel panel--center" id="reviews" data-watermark="Отзывы">
  <div class="bg" style="background-image:url('https://sun9-4.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Отзывы</div>
      <h2>Что говорят наши клиенты</h2>
      <p>Реальные отзывы о нашей работе. Листайте влево-вправо.</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="revPrev">&#10094;</button>
      <div class="car-track rev-track" id="revTrack">
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" width="50" height="50" src="https://sun9-3.vkuserphoto.ru/s/v1/ig2/-cVZEipS5I4ROZUZ2fxoIaGJBZXpUs76_WKoUZpPw_r2-gnqqUvgTqjLjYoTZ0R21nsCSvjUPyw_vSn1jxAYJC8K.jpg?quality=95&cs=256x0" alt="Виктория Брандикова">
            <div><div class="rev-name">Виктория Брандикова</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа кухню, всё прошло на высшем уровне, начиная от замеров, до установки! Мы очень рады, что обратились именно к нему. Роман супер профессионал своего дела! Кухня у нас маленькая, нестандартная, но Роман всё разрешил, практично разместил технику, переставил мойку, установил подсветку. Кухня была готова в короткие сроки, установкой очень довольны, всё под ключ. Однозначно всем буду рекомендовать!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" width="50" height="50" src="https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&cs=256x0" alt="Виктория Маренко">
            <div><div class="rev-name">Виктория Маренко</div><div class="rev-sub">Кухня и гардеробная</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">И вновь мы обратились к Роману! Понадобилась кухня. Кухня на самом деле очень удобная! Как и хотелось — светлая, но не маркая. Учтены все пожелания и воплощены в жизнь! Гардеробную так же заказывали у Романа, и она идеальна! Ответственный подход, качество, внимательность и чистота исполнения — качества, которые для нас важны.</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" width="50" height="50" src="https://sun9-53.vkuserphoto.ru/s/v1/ig2/gZheSpaWhz7StIdwlzSoCIfA01e-x8jVUMESDK2u9ONRR1s3txB-b6F7lqLLj-Y6QFqFU5x463yoWmnTxf5T88g2.jpg?quality=95&cs=256x0" alt="Любовь Петелько">
            <div><div class="rev-name">Любовь Петелько</div><div class="rev-sub">Шкаф, тумбы, прихожая</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Всем здравствуйте. Я заказала у Романа шкаф-купе в спальню. Пообщавшись с ним, получила много советов и рекомендаций по составу и цвету шкафа. В итоге решила в комплект заказать сразу тумбы, гарнитур под телевизор, и прихожую. Установили все раньше обещанного срока. Я очень довольна и всем рекомендую. Роман специалист своего дела.</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" width="50" height="50" src="https://sun9-83.vkuserphoto.ru/s/v1/ig2/zYO0FQ_fFsgxDWhaTE85lNpixn2ikScuD58qVoXtqda8vFxoS-LGsT54k9pk9tDVEpzGpJfCw5eg5TNtYgE2Q8_y.jpg?quality=95&cs=256x0" alt="Дмитрий Юшенко">
            <div><div class="rev-name">Дмитрий Юшенко</div><div class="rev-sub">Шкаф и стенка</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа шкаф и стенку в спальню. Работа вышла отличной, подсказал несколько удачных решений наших хотелок. Все супер! Спасибо!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" width="50" height="50" src="https://sun9-46.vkuserphoto.ru/s/v1/ig2/bVm2vnJWOD92dzHJ3_21NbqhcwF7DW7a05XzjaTWteG9Dviu9nt8LlA5bgzdbsBhGtYbrs7rvOMTylQQIV43cl4T.jpg?quality=95&cs=256x0" alt="Екатерина Умнягина">
            <div><div class="rev-name">Екатерина Умнягина</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа кухню, всё очень понравилось! Подбирали всё до мелочей, и Рома всё исполнил, как мы хотели, за это мы ему очень благодарны. Всё сделано идеально, спрятали то, что не должно быть видно, и получилось очень красиво. Спасибо, Рома!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" width="50" height="50" src="https://sun9-48.vkuserphoto.ru/s/v1/ig2/OdS0JaUmpkj7vzQLNz1oyY6PBksnYylZuY54LZ2vnibrqxNc0IimIjE6d6NWySeMm6N2MLIUHG6WLKtAFJ82ICwE.jpg?quality=95&cs=256x0" alt="Анастасия Зайцева">
            <div><div class="rev-name">Анастасия Зайцева</div><div class="rev-sub">Два шкафа, гардеробная</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа два шкафа. Во время замеров у нас не было определённой идеи, как сделать вместительный шкаф в небольшую спальню, ещё и с несущей колонной. Роман подкинул прекрасную идею — получилась целая угловая гардеробная! Большое спасибо за эстетичное воплощение нашей мечты!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <div><div class="rev-name">Александр Карташев</div><div class="rev-sub">Видеоотзыв · Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <div class="rev-video">
            <div class="video-box" data-src="https://vk.ru/video_ext.php?oid=-212015374&id=456239019&hash=6abf300a7c2518d4" style="background-image:url('__VIDEO_POSTER__')" role="button">
              <span class="vb-play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>
            </div>
          </div>
          <p class="rev-text">«Прям гордость квартиры! За приемлемую цену получили отличную кухню: выступ стояка закрыли пеналом, а в ножку барного стола встроили розетки».</p>
        </div>
      </div>
      <button class="car-nav car-next" id="revNext">&#10095;</button>
      <div class="car-dots" id="revDots"></div>
      <div class="swipe-hint">Листайте</div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше отзывов — в сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>
<div class="gold-divider"><i></i><b></b><i></i></div>
<section class="panel panel--dark" id="services" data-watermark="Услуги">
  <div class="bg" style="background-image:url('https://sun9-4.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Что мы делаем</div>
      <h2>Услуги</h2>
      <p>Индивидуальный подход к каждому проекту и полный цикл производства.</p>
    </div>
    <div class="svc-grid">
      <div class="svc reveal"><svg viewBox="0 0 24 24"><path d="M3 9h18M3 9v10a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V9M3 9l2-4h14l2 4M8 9v2M12 9v2M16 9v2"/></svg><h3>Кухни на заказ</h3><p>Проектируем кухню точно под ваш размер, стиль и привычки — от классики до минимализма.</p></div>
      <div class="svc reveal"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="1"/><path d="M3 8h18M8 8v13M16 8v13"/></svg><h3>Шкафы и гардеробные</h3><p>Шкафы-купе, гардеробные, тумбы и комоды — встроенные и отдельно стоящие.</p></div>
      <div class="svc reveal"><svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18M5 5l14 14M19 5L5 19"/></svg><h3>Прихожие и стенки</h3><p>Прихожие, стенки, гарнитуры под ТВ — аккуратно впишем в ваш интерьер.</p></div>
      <div class="svc reveal"><svg viewBox="0 0 24 24"><path d="M14 6l4 4M5 19l7-7M17 3l4 4-4 4-1-1-1 1-4-4 1-1-1-1 4-4z"/></svg><h3>Сборка и монтаж</h3><p>Профессиональная установка, аккуратная сборка и подключение техники.</p></div>
      <div class="svc reveal"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg><h3>Замер и проект</h3><p>Выезжаем на замер, делаем планировку и 3D-проект — бесплатно.</p></div>
      <div class="svc reveal"><svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9M3 12h6M3 12l4-4M3 12l4 4"/></svg><h3>Обновление мебели</h3><p>Освежим фасады и фурнитуру существующей кухни — дешевле, чем новая.</p></div>
    </div>
  </div></div>
</section>
<section class="panel" id="process">
  <div class="bg" style="background-image:url('https://sun9-16.vkuserphoto.ru/s/v1/ig2/_AK_Czw9ThnFAWSmhSfPYvg9RvHW0QYDGS9DhqW75-oe2hQSjQob1DbdypL9Hx3wBn09V3pUvlfCN6Efcbojr7T81tfxQQ.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Как мы работаем</div>
      <h2>Путь от идеи до готовой мебели</h2>
    </div>
    <div class="steps">
      <div class="step reveal"><div class="n">01</div><h3>Обращение</h3><p>Вы звоните или пишете — обговариваем задачу и пожелания.</p></div>
      <div class="step reveal"><div class="n">02</div><h3>Замер</h3><p>Выезжаем, снимаем размеры и обсуждаем планировку. Бесплатно.</p></div>
      <div class="step reveal"><div class="n">03</div><h3>Проект</h3><p>Готовим 3D-проект и подбираем материалы с фурнитурой.</p></div>
      <div class="step reveal"><div class="n">04</div><h3>Договор</h3><p>Фиксируем стоимость и условия, подписываем договор.</p></div>
      <div class="step reveal"><div class="n">05</div><h3>Производство</h3><p>Изготавливаем мебель на собственном производстве.</p></div>
      <div class="step reveal"><div class="n">06</div><h3>Доставка и монтаж</h3><p>Привозим, собираем и устанавливаем. Сдаём с гарантией.</p></div>
    </div>
  </div></div>
</section>
<section class="panel panel--dark">
  <div class="bg" style="background-image:url('https://sun9-65.vkuserphoto.ru/s/v1/ig2/X4rCpkIxEZW50prB2rGftYiyGQpOQ3E_QQl-211zjBdRmXjKBx5Si91JffsT0LxA1oPbjqueZA0oI1diMrJIRBFMkYuglw.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Почему мы</div>
      <h2>Гарантии и преимущества</h2>
    </div>
    <div class="guar-grid">
      <div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24"><path d="M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg></div><h3>Гарантия качества</h3><p>Отвечаем за свою работу и сопровождаем после установки.</p></div>
      <div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24"><path d="M4 20h16M6 20V8l6-4 6 4v12M9 11h6M9 15h6M10 11v8M14 11v8"/></svg></div><h3>Честный расчёт</h3><p>Без навязывания лишнего и скрытых доплат.</p></div>
      <div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24"><path d="M3 21V9l9-5 9 5v12M3 21h18M9 21v-6h6v6M12 9v2"/></svg></div><h3>Собственное производство</h3><p>Без посредников — контролируем качество на каждом этапе.</p></div>
      <div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/></svg></div><h3>Личное сопровождение</h3><p>Вы всегда на связи со специалистом — от замера до монтажа.</p></div>
    </div>
  </div></div>
</section>
<section class="panel panel--center panel--dark" id="cities">
  <div class="bg" style="background-image:url('https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Где работаем</div>
      <h2>Три города — один стандарт качества</h2>
      <p>Бесплатный замер и проект в каждом из городов.</p>
    </div>
    <div class="city-grid">
      <div class="city reveal"><div class="city-name">Ростов-на-Дону</div><div class="city-line"></div><p>Выезд на замер, проектирование, производство и монтаж мебели под ключ.</p></div>
      <div class="city reveal"><div class="city-name">Батайск</div><div class="city-line"></div><p>Кухни и корпусная мебель с бесплатным замером и 3D-проектом.</p></div>
      <div class="city reveal"><div class="city-name">Азов</div><div class="city-line"></div><p>Индивидуальные проекты, доставка, сборка и установка с гарантией.</p></div>
    </div>
  </div></div>
</section>
<section class="panel panel--center panel--dark">
  <div class="bg" style="background-image:url('https://sun9-40.vkuserphoto.ru/s/v1/ig2/6mMk6psQJqaVgakjpP8A0DWbiwzLbWcoj3Gxz_Om-TUclffQ0Ic3VfIW1-fA1hDVhIHu6cqb3QifLlY7mNhIvynD.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content cta">
    <h2 class="reveal shimmer">Готовы обсудить вашу мебель?</h2>
    <p class="reveal">Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.</p>
    <a href="tel:+79508465397" class="btn btn-solid reveal">Позвонить специалисту</a>
  </div></div>
</section>
<section class="panel panel--dark" id="contacts">
  <div class="bg" style="background-image:url('https://sun9-72.vkuserphoto.ru/s/v1/ig2/NEuGxEzenp7yiZvM8YDHtxZdKGuEE4RvCN46VZcwJR0oWlxofxoJAu0QLcnyALApDuTlQ_exYkbXwlk4iu00Z5UBO0cfeQ.jpg?quality=95&cs=2560x0')"></div>
  <div class="wrap"><div class="content">
    <div class="contact-grid">
      <div class="contact-info reveal">
        <div class="kicker">Контакты</div>
        <h2>Создадим мебель, о которой вы мечтали</h2>
        <p>Позвоните или напишите — ответим быстро и подскажем по всем вопросам.</p>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/></svg></div><div><div class="lab">Регион работы</div><div class="val">Ростов-на-Дону, Батайск, Азов</div></div></div>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><path d="M4 20h16M6 20V8l6-4 6 4v12"/></svg></div><div><div class="lab">Сайт в VK</div><a class="val" href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener">mebel.ostrovsky</a></div></div>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/></svg></div><div><div class="lab">Telegram / MAX</div><div class="val">по номеру +7 (950) 846-53-97</div></div></div>
      </div>
      <div class="reveal">
        <div class="call-block">
          <div class="cb-lab">Свяжитесь с нами удобным способом</div>
          <a class="cb-num" href="tel:+79508465397">+7 (950) 846-53-97</a>
          <div class="cb-hint">Бесплатная консультация и запись на замер.<br>Звоните или пишите в любой мессенджер.</div>
          <div class="contact-actions">
            <a class="c-action c-call" href="tel:+79508465397">Позвонить</a>
            <a class="c-action c-tg" href="https://t.me/fanny161" target="_blank" rel="noopener">Написать в Telegram</a>
            <a class="c-action c-max" href="tel:+79508465397">Написать в MAX</a>
          </div>
        </div>
      </div>
    </div>
  </div></div>
</section>
<footer>
  <div class="flogo">Кухни Островский<span> · Ростов · Батайск · Азов</span></div>
  <div class="social-row">
    <a class="soc" href="tel:+79508465397" title="Позвонить"><svg viewBox="0 0 24 24"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 2z"/></svg></a>
    <a class="soc" href="https://t.me/fanny161" target="_blank" rel="noopener" title="Telegram"><svg viewBox="0 0 24 24"><path d="M21.9 4.6L18.8 19c-.2 1-.8 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.8L18 6.4c.4-.3-.1-.5-.6-.2L6.7 13.4l-4.6-1.4c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.6 1z"/></svg></a>
    <a class="soc" href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" title="ВКонтакте"><svg viewBox="0 0 24 24"><path d="M14 19c-6 0-9.5-4.5-9.7-12h3c.1 5 2.5 8 4.3 8.8V7h3v5c1.8-.2 3.6-2.6 4.2-5h3c-.6 3.4-2.8 5.8-4.6 6.6 1.8.9 4.6 3.6 5.4 8.4h-3.4c-.6-2.5-2.4-4.4-4.3-4.9V19H14z"/></svg></a>
  </div>
  <p>Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов</p>
  <p style="margin-top:8px">© <span id="year"></span> Кухни Островский. Все права защищены.</p>
</footer>
<div class="cookie-bar" id="cookieBar">
  <p>Мы используем файлы cookie для корректной работы сайта.</p>
  <button class="btn btn-solid" id="cookieOk">Принять</button>
</div>
<script>
(function(){
const progress=document.getElementById('progress');
const header=document.getElementById('header');
const burger=document.getElementById('burger'),menu=document.getElementById('menu'),scrim=document.getElementById('scrim');
let ticking=false,menuOpen=false;
function onScroll(){if(ticking)return;ticking=true;requestAnimationFrame(function(){
  const h=document.documentElement;
  const sc=h.scrollHeight>h.clientHeight?h.scrollTop/(h.scrollHeight-h.clientHeight):0;
  progress.style.width=(sc*100)+'%';
  header.classList.toggle('solid',h.scrollTop>40);
  let current='';
  ['about','works','reviews','services','process','cities','contacts'].forEach(function(id){var el=document.getElementById(id);if(el&&el.getBoundingClientRect().top<=120)current=id;});
  menu.querySelectorAll('a[href^="#"]').forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+current);});
  ticking=false;
});}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
document.getElementById('logo').addEventListener('click',function(e){e.preventDefault();window.scrollTo({top:0,behavior:'smooth'});});
function closeMenu(){burger.classList.remove('open');menu.classList.remove('open');scrim.classList.remove('show');menuOpen=false;}
function openMenu(){burger.classList.add('open');menu.classList.add('open');scrim.classList.add('show');menuOpen=true;}
burger.addEventListener('click',function(){if(menuOpen)closeMenu();else openMenu();});
scrim.addEventListener('click',closeMenu);
menu.querySelectorAll('a').forEach(function(a){a.addEventListener('click',closeMenu);});
function animateCount(el){var target=parseFloat(el.dataset.count);var dec=parseInt(el.dataset.decimal||'0');var suffix=el.dataset.suffix||'';var dur=1200,start=performance.now();function tick(t){var p=Math.min((t-start)/dur,1);p=1-Math.pow(1-p,3);var val=(target*p).toFixed(dec);el.textContent=(dec?val:Math.round(val))+suffix;if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}
var statIO=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){animateCount(e.target);statIO.unobserve(e.target);}});},{threshold:.5});
document.querySelectorAll('.stat .num').forEach(function(el){statIO.observe(el);});
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
function initCarousel(trackId,prevId,nextId,dotsId){var track=document.getElementById(trackId),prev=document.getElementById(prevId),next=document.getElementById(nextId),dotsBox=document.getElementById(dotsId),items=[].slice.call(track.children);dotsBox.innerHTML='';items.forEach(function(_,i){var d=document.createElement('button');d.className='car-dot'+(i===0?' active':'');d.addEventListener('click',function(){items[i].scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'});});dotsBox.appendChild(d);});var dots=[].slice.call(dotsBox.children);var step=function(){return items[0].offsetWidth+20;};var sT=false;track.addEventListener('scroll',function(){if(sT)return;sT=true;requestAnimationFrame(function(){var idx=Math.round(track.scrollLeft/step());dots.forEach(function(d,i){d.classList.toggle('active',i===idx);});sT=false;});},{passive:true});prev.addEventListener('click',function(){track.scrollBy({left:-step(),behavior:'smooth'});});next.addEventListener('click',function(){track.scrollBy({left:step(),behavior:'smooth'});});}
initCarousel('carTrack','carPrev','carNext','carDots');
initCarousel('revTrack','revPrev','revNext','revDots');
document.querySelectorAll('.video-box').forEach(function(box){box.addEventListener('click',function(){if(box.querySelector('iframe'))return;var iframe=document.createElement('iframe');iframe.src=box.dataset.src;iframe.setAttribute('allow','autoplay; encrypted-media; fullscreen');iframe.setAttribute('allowfullscreen','1');box.innerHTML='';box.appendChild(iframe);});});
var cookieBar=document.getElementById('cookieBar'),cookieOk=document.getElementById('cookieOk');
if(!localStorage.getItem('cookiesAccepted')){setTimeout(function(){cookieBar.classList.add('show');},900);}
cookieOk.addEventListener('click',function(){localStorage.setItem('cookiesAccepted','1');cookieBar.classList.remove('show');});
document.getElementById('year').textContent=new Date().getFullYear();
})();
</script>
</body>
</html>""".replace("__VIDEO_POSTER__", VIDEO_POSTER)


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
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", cache)
            self.send_header("ETag", etag)
            if isinstance(body, str):
                self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            self.wfile.write(data)

    def _redirect(self, location, cache="public, max-age=86400"):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Cache-Control", cache)
        self.end_headers()

    def _token(self):
        raw = self.headers.get("Cookie", "")
        if not raw:
            return None
        try:
            c = SimpleCookie()
            c.load(raw)
            m = c.get("admin_session")
            return m.value if m else None
        except Exception:
            return None

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/admin/login":
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", ""), "text/html; charset=utf-8")
        elif path == "/admin/logout":
            _drop_session(self._token())
            self.send_response(302)
            self.send_header("Location", "/admin/login")
            self.send_header("Set-Cookie", "admin_session=; Path=/; Max-Age=0; HttpOnly")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path == "/admin/api/data":
            if not _check_session(self._token()):
                self._send(401, '{"error":"no auth"}', "application/json")
                return
            self._send(200, json.dumps(_sb_read(), ensure_ascii=False), "application/json; charset=utf-8")
        elif path == "/admin":
            if not _check_session(self._token()):
                self.send_response(302)
                self.send_header("Location", "/admin/login")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8")
        elif path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://кухниостровский.рф/</loc><priority>1.0</priority></url></urlset>', "application/xml; charset=utf-8", "public, max-age=3600")
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
        if path == "/admin/login":
            n = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(n).decode("utf-8", "ignore") if n else ""
            p = parse_qs(body)
            login = (p.get("login") or [""])[0].strip()
            pw = (p.get("password") or [""])[0]
            if login == ADMIN_LOGIN_ENV and pw == ADMIN_PASSWORD_ENV:
                tok = _new_session()
                self.send_response(302)
                self.send_header("Location", "/admin")
                self.send_header("Set-Cookie", "admin_session=" + tok + "; Path=/; Max-Age=" + str(SESSION_TTL) + "; HttpOnly; SameSite=Lax")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", '<div class="err">Неверный логин или пароль</div>'), "text/html; charset=utf-8")
            return
        if path == "/admin/api/save":
            if not _check_session(self._token()):
                self._send(401, '{"error":"no auth"}', "application/json")
                return
            n = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(n).decode("utf-8") if n else "{}"
            try:
                obj = json.loads(body)
            except Exception:
                self._send(400, '{"error":"bad json"}', "application/json")
                return
            ok = _sb_save(obj)
            self._send(200, json.dumps({"ok": ok}), "application/json; charset=utf-8")
            return
        self._send(404, "not found", "text/plain")

    def log_message(self, *args):
        pass


ADMIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Админка</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0e0c09;color:#f5efe3;line-height:1.5}
header{background:rgba(14,12,9,.96);border-bottom:1px solid rgba(236,207,160,.16);padding:12px 18px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:20}
.brand{font-family:Georgia,serif;font-size:19px;color:#eccfa0}.brand span{font-size:11px;opacity:.65;letter-spacing:1px}
.actions{display:flex;gap:8px;flex-wrap:wrap}
.btn{padding:9px 15px;border-radius:9px;border:1px solid rgba(236,207,160,.16);background:rgba(255,255,255,.04);color:#f5efe3;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;font-family:inherit}
.btn:hover{border-color:#d4af6a}
.btn-gold{background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;border:none}
main{max-width:900px;margin:0 auto;padding:24px 18px 100px}
h2{font-family:Georgia,serif;font-size:22px;color:#fff;margin:24px 0 12px;padding-bottom:8px;border-bottom:1px solid rgba(236,207,160,.16)}
label{display:block;color:#eccfa0;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;margin:14px 0 6px;font-weight:600}
input,textarea{width:100%;padding:10px 13px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.12);border-radius:9px;color:#fff;font-size:14px;font-family:inherit;resize:vertical}
input:focus,textarea:focus{outline:none;border-color:#d4af6a}
.toast{position:fixed;bottom:20px;left:50%;transform:translate(-50%,150%);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;padding:12px 22px;border-radius:11px;font-weight:700;font-size:13.5px;z-index:9999;transition:transform .35s;max-width:92vw}
.toast.show{transform:translate(-50%,0)}.toast.err{background:linear-gradient(135deg,#ff8a8a,#e04a4a);color:#fff}
.intro{background:rgba(212,175,106,.07);border:1px solid rgba(212,175,106,.22);border-radius:11px;padding:14px 16px;font-size:13px;margin-bottom:18px}
.intro b{color:#eccfa0}
</style></head><body>
<header>
<div class="brand">Кухни Островский <span>CMS</span></div>
<div class="actions"><a class="btn" href="/" target="_blank">Открыть сайт</a><button class="btn btn-gold" id="saveBtn">Сохранить</button><a class="btn" href="/admin/logout">Выйти</a></div>
</header>
<main>
<div class="intro">Редактор контента. Пишите свои тексты и ссылки на картинки — они попадут в Supabase и останутся после деплоя. <b>Ссылки на картинки:</b> можно оставлять VK-ссылки из шаблона или любые другие (например, из Supabase Storage).</div>
<div id="fields"></div>
</main>
<div class="toast" id="toast"></div>
<script>
var DATA={};
function q(s){return document.querySelector(s)}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function toast(m,bad){var t=q('#toast');t.textContent=m;t.classList.toggle('err',!!bad);t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove('show')},3000)}
function getPath(o,p){return p.split('.').reduce(function(a,k){return a==null?undefined:a[k]},o)}
function setPath(o,p,v){var a=p.split('.'),c=o;for(var i=0;i<a.length-1;i++){var k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k]}c[a[a.length-1]]=v}
var SCHEMA=[
 {t:'SEO',f:[['seo.title','Title',1],['seo.description','Description',2],['seo.keywords','Keywords',2],['seo.og_title','OG title',0],['seo.og_description','OG description',1],['seo.og_image','OG картинка',0]]},
 {t:'Бренд',f:[['brand.name','Название',0],['brand.sub','Подпись',0],['brand.logo_url','Логотип (URL)',0],['brand.phone','Телефон',0],['brand.phone_raw','Телефон для tel:',0],['brand.telegram','Telegram',0],['brand.vk','VK',0]]},
 {t:'Главный экран',f:[['hero.eyebrow','Надзаголовок',0],['hero.title_before','Заголовок 1',0],['hero.title_em','Заголовок золото',0],['hero.sub','Подзаголовок',2],['hero.btn1','Кнопка 1',0],['hero.btn2','Кнопка 2',0],['hero.bg','Фон (URL)',0]]},
 {t:'О специалисте',f:[['about.kicker','Надзаголовок',0],['about.title','Заголовок',0],['about.name','Имя',0],['about.role','Должность',0],['about.photo','Фото (URL)',0],['about.card_text','Карточка',2],['about.text','Основной текст',2],['about.bg','Фон (URL)',0]]},
 {t:'Консультация',f:[['consult.kicker','Надзаголовок',0],['consult.title','Заголовок',0],['consult.phone','Телефон',0],['consult.text','Текст',2],['consult.bg','Фон (URL)',0]]},
 {t:'Работы',f:[['works.kicker','Надзаголовок',0],['works.title','Заголовок',0],['works.subtitle','Подзаголовок',2],['works.bg','Фон (URL)',0]]},
 {t:'Отзывы',f:[['reviews.kicker','Надзаголовок',0],['reviews.title','Заголовок',0],['reviews.subtitle','Подзаголовок',2],['reviews.bg','Фон (URL)',0],['reviews.video_poster','Превью видео (URL)',0]]},
 {t:'Услуги',f:[['services.kicker','Надзаголовок',0],['services.title','Заголовок',0],['services.subtitle','Подзаголовок',2],['services.bg','Фон (URL)',0]]},
 {t:'Этапы',f:[['process.kicker','Надзаголовок',0],['process.title','Заголовок',0],['process.bg','Фон (URL)',0]]},
 {t:'Гарантии',f:[['guarantees.kicker','Надзаголовок',0],['guarantees.title','Заголовок',0],['guarantees.bg','Фон (URL)',0]]},
 {t:'Города',f:[['cities.kicker','Надзаголовок',0],['cities.title','Заголовок',0],['cities.subtitle','Подзаголовок',2],['cities.bg','Фон (URL)',0]]},
 {t:'CTA',f:[['cta.title','Заголовок',0],['cta.text','Текст',2],['cta.button','Кнопка',0],['cta.bg','Фон (URL)',0]]},
 {t:'Контакты',f:[['contacts.kicker','Надзаголовок',0],['contacts.title','Заголовок',0],['contacts.subtitle','Подзаголовок',2],['contacts.call_label','Подпись звонка',0],['contacts.call_number','Телефон',0],['contacts.call_hint','Под телефоном',2],['contacts.bg','Фон (URL)',0]]},
 {t:'Подвал',f:[['footer.line','Строка',0],['footer.copyright','Копирайт',0]]},
 {t:'Cookie',f:[['cookie.text','Текст',2],['cookie.button','Кнопка',0]]},
 {t:'Страница 404',f:[['page404.title','Заголовок',0],['page404.text','Текст',2],['page404.button','Кнопка',0]]}
];
function render(){
  var h='';
  SCHEMA.forEach(function(sec){
    h+='<h2>'+esc(sec.t)+'</h2>';
    sec.f.forEach(function(f){
      var p=f[0],lab=f[1],rows=f[2];
      var v=getPath(DATA,p);
      h+='<label>'+esc(lab)+'</label>';
      if(rows>0){h+='<textarea data-path="'+p+'" rows="'+rows+'">'+esc(v)+'</textarea>';}
      else{h+='<input type="text" data-path="'+p+'" value="'+esc(v)+'">';}
    });
  });
  q('#fields').innerHTML=h;
  document.querySelectorAll('[data-path]').forEach(function(el){
    el.addEventListener('input',function(){
      setPath(DATA,el.dataset.path,el.value);
    });
  });
}
function load(){
  fetch('/admin/api/data',{credentials:'same-origin'}).then(function(r){if(r.status===401){location.href='/admin/login';return null}return r.json()}).then(function(j){if(!j)return;DATA=j;render()}).catch(function(e){toast('Ошибка загрузки: '+e.message,true)});
}
q('#saveBtn').addEventListener('click',function(){
  fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)}).then(function(r){return r.json()}).then(function(j){
    if(j&&j.ok){toast('Сохранено')}else{toast('Ошибка!',true)}
  }).catch(function(e){toast('Ошибка: '+e.message,true)});
});
load();
</script></body></html>"""


if __name__ == "__main__":
    print("Кухни Островский сервер запущен на http://0.0.0.0:" + str(PORT), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
