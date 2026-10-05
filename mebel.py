# -*- coding: utf-8 -*-
"""
mebel.py — Кухни Островский + админка /admin (Supabase) + анимации.
"""
import base64
import gzip
import hashlib
import io
import json
import os
import re
import secrets
import threading
import time
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

try:
    from supabase import create_client
    _SUPABASE_LIB = True
except Exception:
    _SUPABASE_LIB = False

PORT = int(os.environ.get("PORT", "8080"))
DOMAIN = "https://кухниостровский.рф"
ROOT = os.path.dirname(os.path.abspath(__file__))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://hliafkrpvmntpctmqwfu.supabase.co")
SUPABASE_ANON = os.environ.get(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEyMDQ1NzYsImV4cCI6MjEwNjc4MDU3Nn0.yi57-Ty1iIfhnEh80_zvifhX1W_JX2qCl7QrARuJ2ns",
)
SUPABASE_SERVICE = os.environ.get(
    "SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTIwNDU3NiwiZXhwIjoyMTA2NzgwNTc2fQ.Yr4z9vx6kF9ZINNNUjUn43GYi-A2BmBfg8uyrOtmDWo",
)
ADMIN_LOGIN_ENV = os.environ.get("ADMIN_LOGIN", "кухниост")
ADMIN_PASSWORD_ENV = os.environ.get("ADMIN_PASSWORD", "романкух")

SESSION_TTL = 86400 * 7
MAX_UPLOAD = 8 * 1024 * 1024
DATA_ROW_ID = 1
CACHE_TTL = 20

FAVICON_URL = "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0"
VIDEO_POSTER = "https://sun9-44.vkuserphoto.ru/s/v1/ig2/z3K7MYc56nf_4Ek_wkhJ-j-VZt7iv_VEt9wUN0gJSY0VORuRVxQCX1S5baisBgJyoYuCcrENJNxLajL1WKwdFS91.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x541,1080x811,1280x961,1440x1081,2560x1922&from=bu&u=Fj3HDKPJXUOEmCWl6MePYyPYB6lNmsGien6u_9mlUi8&cs=1280x0"

ROBOTS = """User-agent: *
Allow: /

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

DEFAULT_DATA = {
    "seo": {
        "title": "Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ",
        "description": "Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и 3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97",
        "keywords": "кухни остров, кухни островский, кухни островского, кухни островский ростов, кухни ростов островский, кухни батайск островский, кухни азов островский, кухни на заказ ростов, кухни на заказ батайск, кухни на заказ азов, мебель островского, мебель на заказ ростов, корпусная мебель, шкафы купе, гардеробные, прихожие, кухни под ключ, мебель островский",
        "og_image": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0",
    },
    "brand": {
        "name": "Кухни Островский",
        "sub": "Ростов · Батайск · Азов",
        "logo_url": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0",
        "phone": "+7 (950) 846-53-97",
        "phone_raw": "+79508465397",
        "telegram": "https://t.me/fanny161",
        "vk": "https://vk.com/mebel.ostrovsky",
    },
    "hero": {
        "eyebrow": "Мебель и кухни на заказ",
        "title_before": "Мебель, которая ",
        "title_em": "создаёт настроение",
        "sub": "Проектируем и изготавливаем кухни, шкафы, гардеробные и другую корпусную мебель в Ростове, Батайске и Азове — по вашему проекту, от замера до монтажа.",
        "btn1": "Получить консультацию",
        "btn2": "Смотреть работы",
        "bg": "https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0",
    },
    "stats": {
        "bg": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1280x0",
    },
    "about": {
        "bg": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2208x1656&from=bu&u=9_d3vo4cDIif_5OxDZbDgMLFC1xuAQSKRY1zAPscIwM&cs=1280x0",
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
        "bg": "https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0",
        "kicker": "Бесплатно",
        "title": "Консультация",
        "text": "Позвоните или напишите нам в <b style=\"color:#fff\">Telegram</b> или <b style=\"color:#fff\">MAX</b> — расскажем про кухни и мебель, всё обсудим и договоримся о бесплатном замере.",
    },
    "works": {
        "bg": "https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=q3wKCscaGbBU8n3umOUNA0wOvLkQBDAVXIkzDrivHgk&cs=1280x0",
        "kicker": "Наши работы",
        "title": "Кухни и мебель, которые мы сделали",
        "subtitle": "Нажмите на фото, чтобы рассмотреть в большом размере.",
        "items": [
            {"url": "https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1080x0", "alt": "Кухня на заказ в Ростове — Кухни Островский"},
            {"url": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1080x0", "alt": "Кухня на заказ в Батайске — Кухни Островский"},
            {"url": "https://sun9-11.vkuserphoto.ru/s/v1/ig2/Xh5Xw9Yb1reqhfFznlGk8NjvSQAxCbysuiL5IWRt_f3ELVb8fvoYPg00eFIHV-xiS9I4nhYBj4ttU_FHVkPpX8Z3.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,1600x1200&from=bu&u=pY-bjOidU1jjNjiF66Dn4Ycgmb6utH_d0Ti7oSJr0qA&cs=1080x0", "alt": "Кухня на заказ в Азове — Кухни Островский"},
            {"url": "https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1080x0", "alt": "Мебель на заказ в Ростове — Кухни Островский"},
            {"url": "https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1080x0", "alt": "Шкаф-купе на заказ в Ростове — Кухни Островский"},
            {"url": "https://sun9-24.vkuserphoto.ru/s/v1/ig2/lS8MpZ4V9XUKPJ7l9GmjnkCnHW2MGfnq86jH-Gzx6bAgr4m3azL5Xd_fkdPHY_NOsJjST3Zw2iQkuGKGBwYODdgM.jpg?quality=95&as=32x42,48x63,72x95,108x142,160x211,240x316,360x474,480x632,540x711,640x843,720x949,1080x1423,1280x1686,1440x1897,1943x2560&from=bu&u=dLnirpryCPR3qvUPphwt7JaP5ljnoIl1yyGyUNiUjZI&cs=1080x0", "alt": "Мебель на заказ в Батайске — Кухни Островский"},
            {"url": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1080x0", "alt": "Кухня на заказ — Кухни Островский"},
            {"url": "https://sun9-39.vkuserphoto.ru/s/v1/ig2/5cyrhjIBSWB5GGZATB29IrmjydaNdVOx-iP_dMNKsMbePp5Ccs2rnkEpLnfft3yAZGeMEE3IfInjMQ7aU6Z6jnHc.jpg?quality=95&as=32x24,48x36,72x54,108x82,160x121,240x181,360x272,480x363,540x408,640x484,720x544,1080x817,1280x968&from=bu&u=l1uWXrXXeEAKk1VMgGM5wyIo7DtKdQGhKlCwMjoS0t8&cs=1080x0", "alt": "Мебель на заказ — Кухни Островский"},
            {"url": "https://sun9-68.vkuserphoto.ru/s/v1/ig2/6KwHlOiN9pxXNIwTImKO6QGkrSCTVqreybJu-63m8wbhdFFMIl06es9cPeurIdwuwXGtsFTkdJ6IOjMaS1qRtfxJ.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VgDjFEJKqpW6dWVO-E4y4Q6xcuyoqiL7LxhG36oLPjw&cs=1080x0", "alt": "Кухня на заказ в Батайске — Кухни Островский"},
            {"url": "https://sun9-23.vkuserphoto.ru/s/v1/ig2/wfBQoeOzjZbCRCvxmIkx_V3xC0fgMd3TTxRDSRG2CHDMok6B2ZKrG7vCAJ_G1DmrZ6JS1_RC2tr87Q64wJJ4aW9w.jpg?quality=95&as=32x25,48x37,72x56,108x84,160x124,240x186,360x279,480x372,540x419,640x496,720x558,1080x837,1280x992,1440x1117,2560x1985&from=bu&u=kZXvrlzwGUvzrHmYa8tHXbvyhU_JlNlefLxxcCYqM1A&cs=1080x0", "alt": "Мебель на заказ — Кухни Островский"},
            {"url": "https://sun9-33.vkuserphoto.ru/s/v1/ig2/TQbwf8FdMs_jwKfC_ONoxEHBIpc2L5yf_T0McNeUKRn0tK7fVbC5YbHfsB0TGLlNC_D55htM_2nREACuIw7ykLIx.jpg?quality=95&as=32x43,48x65,72x97,108x145,160x215,240x323,360x484,480x645,540x726,640x860,720x968,1080x1452,1280x1721,1440x1936,1904x2560&from=bu&u=rbH0OM9Bv0PnevamgtW5nYBm9jxFI28R6D1wxzq6fJA&cs=1080x0", "alt": "Кухня на заказ — Кухни Островский"},
            {"url": "https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0", "alt": "Кухня на заказ — Кухни Островский"},
            {"url": "https://sun9-65.vkuserphoto.ru/s/v1/ig2/z_wfZeGA9H6LHDsevjkijUHpbVyLGWFM38frX4hKrjgOnscfAloGdrVpPUwl4XoXCG_YgcKXTgeeTsDDcWEBvdi1.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YbZ1WmiK3ZCk0bKWZhf_YKp6dTUU2vbsQo7Ya4Hoi6s&cs=1080x0", "alt": "Кухня на заказ — Кухни Островский"},
        ],
    },
    "reviews": {
        "bg": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0",
        "kicker": "Отзывы",
        "title": "Что говорят наши клиенты",
        "subtitle": "Реальные отзывы о нашей работе. Листайте влево-вправо.",
        "items": [
            {"name": "Виктория Брандикова", "sub": "Кухня на заказ", "stars": 5,
             "avatar": "https://sun9-3.vkuserphoto.ru/s/v1/ig2/-cVZEipS5I4ROZUZ2fxoIaGJBZXpUs76_WKoUZpPw_r2-gnqqUvgTqjLjYoTZ0R21nsCSvjUPyw_vSn1jxAYJC8K.jpg?quality=95&as=32x30,48x45,72x68,108x101,160x150,240x225,360x338,480x450,540x507,640x601,720x676,1080x1014,1280x1201,1440x1351,2505x2351&from=bu&cs=128x0",
             "text": "Заказывали у Романа кухню, всё прошло на высшем уровне, начиная от замеров, до установки! Мы очень рады, что обратились именно к нему (нашли в объявлении и нам крупно повезло), Роман супер профессионал своего дела!!! Кухня у нас маленькая, не стандартная, сверху выступы, вся на трубах, расположение мойки и кухонной плиты не удобное и вытяжку мы хотели, но нам некуда было её устанавливать (как мы думали), но Роман всё разрешил, практично разместил технику (в том числе и вытяжку), переставил мойку, установил подсветку сделал кухню функциональной светлой, практичной и современной. Кухня была готова в короткие сроки, установкой очень довольны, всё под ключ с установкой техники и подключением, всё быстро, качественно, и чисто! Мы не ожидали такого результата 😍, просто не верится, что у нас теперь удобная, вместительная, современная кухня 🔥, о такой даже и не мечтали, даже несмотря на то, что кухня бюджетная. За мебелью теперь только к Роману!!! Однозначно всем буду рекомендовать!!!", "video": ""},
            {"name": "Виктория Маренко", "sub": "Кухня и гардеробная", "stars": 5,
             "avatar": "https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0",
             "text": "И вновь мы обратились к Роману! Понадобилась кухня😊Кухня на самом деле очень удобная! Как и хотелось она светлая, но не маркая. Как всегда учтены все пожелания и воплощены в жизнь! Очень трудно нам дался выбор цветов😂но Роман спокойно вынес все наши метания🙏 выполнил работу достойно, внимательно и аккуратно! Однозначно советую обращаться к нему👍 гардеробную так же заказывали у Романа, и она идеальна👏 ответственный подход, качество, внимательность и чистота исполнения - его качества, которые для нас важны, поэтому если нам понадобится мебель- обязательно еще раз встретимся😊", "video": ""},
            {"name": "Любовь Петелько", "sub": "Шкаф, тумбы, прихожая", "stars": 5,
             "avatar": "https://sun9-53.vkuserphoto.ru/s/v1/ig2/gZheSpaWhz7StIdwlzSoCIfA01e-x8jVUMESDK2u9ONRR1s3txB-b6F7lqLLj-Y6QFqFU5x463yoWmnTxf5T88g2.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&cs=128x0",
             "text": "Всем здравствуйте. Я заказала у Романа шкаф купе в спальню. Когда Роман приехал, я не совсем понимала что я хочу, пообщавшись с ним, получила много советов и рекомендаций по составу и цвету шкафа. В итоге решила в комплект заказать сразу тумбы, гарнитур под телевизор, и прихожую. Установили все раньше обещанного срока. Я очень довольна и всем рекомендую. Роман специалист своего дела. Скоро буду заказывать зону хранения балкона и самое главное кухню мечты). Спасибо", "video": ""},
            {"name": "Дмитрий Юшенко", "sub": "Шкаф и стенка", "stars": 5,
             "avatar": "https://sun9-83.vkuserphoto.ru/s/v1/ig2/zYO0FQ_fFsgxDWhaTE85lNpixn2ikScuD58qVoXtqda8vFxoS-LGsT54k9pk9tDVEpzGpJfCw5eg5TNtYgE2Q8_y.jpg?quality=95&as=32x47,48x71,72x106,108x159,160x236,240x353,360x530,480x707,540x795,640x943,720x1061,869x1280&from=bu&cs=1280x0",
             "text": "Заказывали у Романа шкаф и стенку в спальню. Работа вышла отличной, подсказал несколько удачных решений наших хотелок. Все супер! Спасибо!", "video": ""},
            {"name": "Екатерина Умнягина", "sub": "Кухня на заказ", "stars": 5,
             "avatar": "https://sun9-46.vkuserphoto.ru/s/v1/ig2/bVm2vnJWOD92dzHJ3_21NbqhcwF7DW7a05XzjaTWteG9Dviu9nt8LlA5bgzdbsBhGtYbrs7rvOMTylQQIV43cl4T.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&cs=128x0",
             "text": "Заказывали у Романа кухню, всё очень понравилось! Подбирали всё до мелочей, и Рома всё исполнил, как мы хотели, за это мы ему очень благодарны. Всё сделано идеально, спрятали то, что не должно быть видно, и получилось очень красиво. Спасибо, Рома, за эту крутую современную кухню!!!", "video": ""},
            {"name": "Анастасия Зайцева", "sub": "Два шкафа, гардеробная", "stars": 5,
             "avatar": "https://sun9-48.vkuserphoto.ru/s/v1/ig2/OdS0JaUmpkj7vzQLNz1oyY6PBksnYylZuY54LZ2vnibrqxNc0IimIjE6d6NWySeMm6N2MLIUHG6WLKtAFJ82ICwE.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,960x1280&from=bu&cs=128x0",
             "text": "Заказывали у Романа два шкафа. Во время замеров у нас не было определённой идеи, как сделать вместительный шкаф в нашу небольшую спальню, ещё и с несущей колонной. Роман подкинул прекрасную идею, в итоге получился не просто шкаф, а целая угловая гардеробная, я была в восторге 🤩 Большой выбор цветов и текстур. Работа выполнена в оговорённый срок и качественно. 👍🏻 Большое спасибо за эстетичное воплощение нашей мечты 🤩😊", "video": ""},
            {"name": "Александр Карташев", "sub": "Видеоотзыв · Кухня на заказ", "stars": 5,
             "avatar": "",
             "text": "«<b>Прям гордость квартиры 😀</b> За приемлемую цену получили отличную кухню: выступ стояка закрыли пеналом, а в ножку барного стола встроили розетки».",
             "video": "https://vk.ru/video_ext.php?oid=-212015374&id=456239019&hash=6abf300a7c2518d4",
             "video_poster": "https://sun9-44.vkuserphoto.ru/s/v1/ig2/z3K7MYc56nf_4Ek_wkhJ-j-VZt7iv_VEt9wUN0gJSY0VORuRVxQCX1S5baisBgJyoYuCcrENJNxLajL1WKwdFS91.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x541,1080x811,1280x961,1440x1081,2560x1922&from=bu&u=Fj3HDKPJXUOEmCWl6MePYyPYB6lNmsGien6u_9mlUi8&cs=1280x0"},
        ],
    },
    "services": {
        "bg": "https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1280x0",
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
        "bg": "https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VpmAnVyzkXcBCcJLy2DSlVkJJG2zYnSPbLzk7-TXGGk&cs=1280x0",
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
        "bg": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YCey971XM2nuNjhkwSaIOfPMTMneMAyHLaPyHT4mLyY&cs=1280x0",
        "kicker": "Почему мы",
        "title": "Гарантии и преимущества",
        "items": [
            {"title": "Гарантия качества", "text": "Отвечаем за свою работу и сопровождаем после установки.", "icon": "M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3zM9 12l2 2 4-4"},
            {"title": "Честный расчёт", "text": "Без навязывания лишнего и скрытых доплат.", "icon": "M4 20h16M6 20V8l6-4 6 4v12M9 11h6M9 15h6M10 11v8M14 11v8"},
            {"title": "Собственное производство", "text": "Без посредников — контролируем качество на каждом этапе.", "icon": "M3 21V9l9-5 9 5v12M3 21h18M9 21v-6h6v6M12 9v2"},
            {"title": "Личное сопровождение", "text": "Вы всегда на связи со специалистом — от замера до монтажа.", "icon": "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM4 21c0-4 3.6-6 8-6s8 2 8 6"},
        ],
    },
    "cities": {
        "bg": "https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1280x0",
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
        "bg": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0",
        "title": "Готовы обсудить вашу мебель?",
        "text": "Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.",
        "button": "📞 Позвонить специалисту",
    },
    "contacts": {
        "bg": "https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0",
        "kicker": "Контакты",
        "title": "Создадим мебель, о которой вы мечтали",
        "subtitle": "Позвоните или напишите — ответим быстро и подскажем по всем вопросам.",
        "regions": "Ростов-на-Дону, Батайск, Азов",
    },
    "footer": {
        "line": "Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов",
        "copyright": "Кухни Островский. Все права защищены.",
    },
}

# =====================================================================
# АНИМАЦИИ — вставляются в PAGE
# =====================================================================
ANIM_STYLE = r"""
<style id="goldAnimations">
@keyframes fadeUp{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}}
@keyframes fadeZoom{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:scale(1)}}
@keyframes shimmerX{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes pulseGold{0%,100%{box-shadow:0 0 0 0 rgba(212,175,106,.4)}50%{box-shadow:0 0 0 14px rgba(212,175,106,0)}}
@keyframes rotateSlow{from{transform:rotate(0)}to{transform:rotate(360deg)}}
@keyframes goldGradient{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}

h1,h2.k,.sec-head h2,.about-body h2,.contact-info h2,.cta h2{
  background-image:linear-gradient(90deg,#faf3e6 0%,#faf3e6 30%,#eccfa0 50%,#faf3e6 70%,#faf3e6 100%);
  background-size:220% 100%;
  -webkit-background-clip:text;
  background-clip:text;
  transition:background-position 1.6s ease;
  background-position:100% 0;
}
h1 em,.shimmer,h1 em.shimmer{
  background-image:linear-gradient(90deg,#eccfa0,#fff 35%,#eccfa0 70%,#eccfa0 100%);
  background-size:220% auto;
  -webkit-background-clip:text;
  background-clip:text;
  -webkit-text-fill-color:transparent;
  animation:shimmerX 4s linear infinite;
}
.js .anim-visible h1,.js h1.anim-visible,.js .anim-visible h2,.js h2.anim-visible{background-position:0% 0;}

.js .stat,.js .svc,.js .step,.js .guar,.js .city,.js .car-slide,.js .rev-card,.js .about-card,.js .about-body,.js .call-block,.js .contact-info,.js .sec-head{
  opacity:0;
  transform:translateY(30px);
  transition:opacity .9s cubic-bezier(.22,.61,.36,1),transform .9s cubic-bezier(.22,.61,.36,1),box-shadow .4s,border-color .4s;
}
.js .stat.anim-in,.js .svc.anim-in,.js .step.anim-in,.js .guar.anim-in,.js .city.anim-in,
.js .car-slide.anim-in,.js .rev-card.anim-in,.js .about-card.anim-in,.js .about-body.anim-in,
.js .call-block.anim-in,.js .contact-info.anim-in,.js .sec-head.anim-in{opacity:1;transform:translateY(0);}

.js .stats .stat:nth-child(2){transition-delay:.12s}
.js .stats .stat:nth-child(3){transition-delay:.24s}
.js .stats .stat:nth-child(4){transition-delay:.36s}
.js .svc-grid .svc:nth-child(2){transition-delay:.1s}
.js .svc-grid .svc:nth-child(3){transition-delay:.2s}
.js .svc-grid .svc:nth-child(4){transition-delay:.3s}
.js .svc-grid .svc:nth-child(5){transition-delay:.4s}
.js .svc-grid .svc:nth-child(6){transition-delay:.5s}
.js .steps .step:nth-child(2){transition-delay:.1s}
.js .steps .step:nth-child(3){transition-delay:.2s}
.js .steps .step:nth-child(4){transition-delay:.3s}
.js .steps .step:nth-child(5){transition-delay:.4s}
.js .steps .step:nth-child(6){transition-delay:.5s}
.js .guar-grid .guar:nth-child(2){transition-delay:.12s}
.js .guar-grid .guar:nth-child(3){transition-delay:.24s}
.js .guar-grid .guar:nth-child(4){transition-delay:.36s}
.js .city-grid .city:nth-child(2){transition-delay:.14s}
.js .city-grid .city:nth-child(3){transition-delay:.28s}

.sec-head h2,.about-body h2,.contact-info h2,.cta h2{position:relative;}
.sec-head h2::after,.about-body h2::after,.contact-info h2::after,.cta h2::after{
  content:"";position:absolute;left:50%;bottom:-12px;height:2px;width:0;
  background:linear-gradient(90deg,transparent,var(--gold),transparent);
  transform:translateX(-50%);
  transition:width 1.4s cubic-bezier(.22,.61,.36,1) .3s;border-radius:2px;
}
.about-body h2::after,.contact-info h2::after{left:0;transform:none}
.js .sec-head.anim-in h2::after{width:80px}
.js .about-body.anim-in h2::after{width:100px}
.js .contact-info.anim-in h2::after{width:100px}

.btn{position:relative;overflow:hidden;transform:translateZ(0);will-change:transform}
.btn .ripple-el{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.55),transparent 70%);transform:scale(0);animation:rippleAnim .8s ease-out forwards;pointer-events:none;}
@keyframes rippleAnim{to{transform:scale(4);opacity:0}}
.btn-solid{background-size:200% 200%;animation:btnGlow 3.6s ease-in-out infinite, goldGradient 6s ease infinite;}
.c-action{position:relative;overflow:hidden}
.c-action .ripple-el{background:radial-gradient(circle,rgba(255,255,255,.35),transparent 70%)}

#goldParticles{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden;}
#goldParticles span{position:absolute;width:6px;height:6px;border-radius:50%;background:radial-gradient(circle,rgba(236,207,160,.9),rgba(212,175,106,.4) 40%,transparent 70%);box-shadow:0 0 12px rgba(236,207,160,.55);animation:particleFloat linear infinite;will-change:transform,opacity;}
@keyframes particleFloat{0%{transform:translateY(100vh) scale(.5);opacity:0}10%{opacity:1}90%{opacity:.85}100%{transform:translateY(-100px) scale(1.1);opacity:0}}

.orb{animation:orbFloat 22s ease-in-out infinite alternate, rotateSlow 60s linear infinite;will-change:transform;}
.orb-1{animation-duration:22s,80s}
.orb-2{animation-duration:28s,100s}
.orb-3{animation-duration:34s,120s}
.panel .bg{transition:transform 1.2s cubic-bezier(.22,.61,.36,1);}

.svc svg,.guar .ico,.c-ico,.vb-play{transition:transform .55s cubic-bezier(.34,1.56,.64,1),background .35s,color .35s,box-shadow .35s;}
.svc:hover svg{transform:scale(1.18) rotate(-8deg)}
.guar:hover .ico{transform:scale(1.18) rotate(8deg)}
.c-line:hover .c-ico{transform:scale(1.16) rotate(-6deg)}

.rev-stars{background:linear-gradient(90deg,#eccfa0,#fff 50%,#eccfa0 100%);background-size:200% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 3s linear infinite;}
.stat .num{display:inline-block;transition:transform .8s cubic-bezier(.34,1.56,.64,1);}
.js .stat.anim-in .num{animation:countPop .9s cubic-bezier(.34,1.56,.64,1)}
@keyframes countPop{0%{transform:scale(.3);opacity:0}60%{transform:scale(1.15)}100%{transform:scale(1);opacity:1}}

.consult .phone,.call-block .cb-num{transition:transform .4s,filter .4s;display:inline-block;}
.consult .phone:hover,.call-block .cb-num:hover{transform:scale(1.04);filter:drop-shadow(0 10px 30px rgba(212,175,106,.6));}

.eyebrow,.kicker,.sec-head .kicker{background:linear-gradient(90deg,rgba(236,207,160,.85),#fff 50%,rgba(236,207,160,.85));background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 4.5s linear infinite;}

.brand-ava-w::before{animation:ringPulse 3.2s ease-in-out infinite, rotateSlow 24s linear infinite;}
.brand-ava{transition:transform .5s cubic-bezier(.34,1.56,.64,1),filter .4s;}
.logo:hover .brand-ava{transform:scale(1.08) rotate(-6deg);filter:brightness(1.15)}

.gold-divider b{animation:pulseGold 2.8s ease-in-out infinite;}
.gold-divider i{animation:dividerLine 3s ease-in-out infinite alternate;}
@keyframes dividerLine{0%{opacity:.35;transform:scaleX(.8)}100%{opacity:1;transform:scaleX(1.15)}}

.progress{background-size:200% 100%;animation:goldGradient 4s ease infinite;box-shadow:0 0 22px rgba(236,207,160,.85);}
.stat:hover,.svc:hover,.step:hover,.guar:hover,.city:hover,.rev-card:hover{box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 60px rgba(212,175,106,.15);}
.car-slide img{transition:transform 1.1s cubic-bezier(.22,.61,.36,1),filter .8s;}
.car-slide:hover img{transform:scale(1.12)}
html{scroll-behavior:smooth}

@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;transition-duration:.01ms !important;}
  .js .stat,.js .svc,.js .step,.js .guar,.js .city,.js .car-slide,.js .rev-card,.js .about-card,.js .about-body,.js .call-block,.js .contact-info,.js .sec-head{opacity:1 !important;transform:none !important;}
}
</style>
"""

ANIM_SCRIPT = r"""
<script id="goldAnimationScript">
(function(){
  if (!('IntersectionObserver' in window)) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head').forEach(function(el){el.classList.add('anim-in');});
    document.documentElement.classList.remove('js');
    return;
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting){ e.target.classList.add('anim-in'); io.unobserve(e.target); }
    });
  }, {threshold:0.12, rootMargin:'0px 0px -50px 0px'});
  document.querySelectorAll('.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head').forEach(function(el){ io.observe(el); });

  var headIo = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting){ e.target.classList.add('anim-visible'); headIo.unobserve(e.target); }
    });
  }, {threshold:0.5});
  document.querySelectorAll('h1,h2.k,.sec-head h2,.about-body h2,.contact-info h2,.cta h2').forEach(function(el){ headIo.observe(el); });

  (function(){
    var container = document.createElement('div'); container.id = 'goldParticles'; document.body.appendChild(container);
    var count = window.innerWidth < 700 ? 12 : 24;
    for (var i=0;i<count;i++){
      var s = document.createElement('span');
      var size = 3 + Math.random()*5;
      s.style.width = size + 'px'; s.style.height = size + 'px';
      s.style.left = (Math.random()*100) + '%';
      s.style.animationDuration = (14 + Math.random()*18) + 's';
      s.style.animationDelay = (-Math.random()*20) + 's';
      s.style.opacity = (0.35 + Math.random()*0.55);
      container.appendChild(s);
    }
  })();

  document.addEventListener('click', function(e){
    var btn = e.target.closest('.btn, .c-action, .car-dot, .soc');
    if (!btn) return;
    var rect = btn.getBoundingClientRect();
    var ripple = document.createElement('span'); ripple.className = 'ripple-el';
    var size = Math.max(rect.width, rect.height);
    ripple.style.width = size + 'px'; ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
    ripple.style.top  = (e.clientY - rect.top  - size/2) + 'px';
    btn.appendChild(ripple);
    setTimeout(function(){ ripple.remove(); }, 850);
  }, {passive:true});

  var fine = matchMedia('(hover:hover) and (pointer:fine)').matches;
  if (fine) {
    document.querySelectorAll('.btn-solid, .c-action.c-call').forEach(function(btn){
      btn.addEventListener('mousemove', function(e){
        var r = btn.getBoundingClientRect();
        var dx = (e.clientX - r.left - r.width/2) / r.width;
        var dy = (e.clientY - r.top  - r.height/2) / r.height;
        btn.style.transform = 'translate(' + (dx*6) + 'px,' + (dy*6 - 4) + 'px)';
      });
      btn.addEventListener('mouseleave', function(){ btn.style.transform = ''; });
    });
  }

  if (fine) {
    document.querySelectorAll('.car-slide').forEach(function(slide){
      var img = slide.querySelector('img'); if (!img) return;
      slide.addEventListener('mousemove', function(e){
        var r = slide.getBoundingClientRect();
        var dx = (e.clientX - r.left) / r.width - .5;
        var dy = (e.clientY - r.top ) / r.height - .5;
        img.style.transform = 'scale(1.12) translate(' + (dx*10) + 'px,' + (dy*10) + 'px)';
      });
      slide.addEventListener('mouseleave', function(){ img.style.transform = ''; });
    });
  }

  if (fine) {
    var bgs = document.querySelectorAll('.panel .bg'); var ticking = false;
    function updateBgs(){
      if (ticking) return; ticking = true;
      requestAnimationFrame(function(){
        bgs.forEach(function(bg){
          var r = bg.parentElement.getBoundingClientRect();
          var center = r.top + r.height/2;
          var offset = (center - window.innerHeight/2) / window.innerHeight;
          bg.style.transform = 'translateY(' + (-offset*30) + 'px) scale(' + (1 + Math.abs(offset)*0.06) + ')';
        });
        ticking = false;
      });
    }
    window.addEventListener('scroll', updateBgs, {passive:true}); updateBgs();
  }

  document.querySelectorAll('#top .eyebrow, #top h1, #top .sub, #top .btn-row').forEach(function(el,i){
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 1s cubic-bezier(.22,.61,.36,1), transform 1s cubic-bezier(.22,.61,.36,1)';
    setTimeout(function(){ el.style.opacity = '1'; el.style.transform = 'none'; }, 200 + i*180);
  });
})();
</script>
"""


def _inject_animations(html):
    if "</head>" in html and "goldAnimations" not in html:
        html = html.replace("</head>", ANIM_STYLE + "\n</head>", 1)
    if "</body>" in html and "goldAnimationScript" not in html:
        html = html.replace("</body>", ANIM_SCRIPT + "\n</body>", 1)
    return html


# =====================================================================
# SUPABASE
# =====================================================================
_sb_read = None
_sb_write = None
_sb_lock = threading.Lock()


def _sb_read_client():
    global _sb_read
    with _sb_lock:
        if _sb_read is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_ANON:
            try: _sb_read = create_client(SUPABASE_URL, SUPABASE_ANON)
            except Exception as e: print("[supabase read] " + str(e))
        return _sb_read


def _sb_write_client():
    global _sb_write
    with _sb_lock:
        if _sb_write is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_SERVICE:
            try: _sb_write = create_client(SUPABASE_URL, SUPABASE_SERVICE)
            except Exception as e: print("[supabase write] " + str(e))
        return _sb_write


_auth_lock = threading.Lock()
_sessions = {}


def _new_session():
    t = secrets.token_urlsafe(32)
    with _auth_lock:
        _sessions[t] = time.time() + SESSION_TTL
    return t


def _check_session(token):
    if not token: return False
    with _auth_lock:
        exp = _sessions.get(token)
        if not exp: return False
        if exp < time.time():
            _sessions.pop(token, None); return False
    return True


def _drop_session(token):
    if token:
        with _auth_lock: _sessions.pop(token, None)


_data_cache = None
_cache_ts = 0.0
_data_lock = threading.Lock()
_initialized_db = False


def _deep_fill(target, source):
    for k, v in source.items():
        if k not in target:
            target[k] = json.loads(json.dumps(v))
        elif isinstance(v, dict) and isinstance(target[k], dict):
            _deep_fill(target[k], v)


def load_data(force=False):
    global _data_cache, _cache_ts, _initialized_db
    now = time.time()
    with _data_lock:
        if not force and _data_cache is not None and now - _cache_ts < CACHE_TTL:
            return _data_cache
        raw = None
        sb = _sb_read_client()
        if sb is not None:
            try:
                res = sb.table("site_content").select("data").eq("id", DATA_ROW_ID).execute()
                if res.data: raw = res.data[0].get("data") or {}
            except Exception as e:
                print("[load_data] " + str(e))
        data = json.loads(json.dumps(DEFAULT_DATA))
        if raw:
            _deep_fill(data, raw)
        else:
            if not _initialized_db:
                _initialized_db = True
                save_data(data)
        _data_cache = data
        _cache_ts = now
        return data


def save_data(data):
    global _data_cache, _cache_ts
    with _data_lock:
        sb = _sb_write_client()
        if sb is None:
            print("[save_data] service_role недоступен")
            return False
        try:
            sb.table("site_content").upsert({"id": DATA_ROW_ID, "data": data}).execute()
            _data_cache = data; _cache_ts = time.time(); return True
        except Exception as e:
            print("[save_data] " + str(e)); return False


# =====================================================================
# PAGE — вшит
# =====================================================================
PAGE = r"""<!DOCTYPE html>
<html lang="ru" class="js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ</title>
<meta name="description" content="Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и 3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97">
<meta name="keywords" content="кухни остров, кухни островский, кухни островского, кухни островский ростов, кухни ростов островский, кухни батайск островский, кухни азов островский, кухни на заказ ростов, кухни на заказ батайск, кухни на заказ азов, мебель островского, мебель на заказ ростов, корпусная мебель, шкафы купе, гардеробные, прихожие, кухни под ключ, мебель островский">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
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
<meta property="og:description" content="Кухни и корпусная мебель под ключ. Бесплатный замер и 3D-проект, собственное производство, монтаж. ☎ +7 (950) 846-53-97">
<meta property="og:image" content="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":["LocalBusiness","HomeAndConstructionBusiness"],"name":"Кухни Островский","url":"https://кухниостровский.рф/","telephone":"+79508465397","priceRange":"₽₽","address":{"@type":"PostalAddress","addressLocality":"Ростов-на-Дону","addressRegion":"Ростовская область","addressCountry":"RU"},"areaServed":[{"@type":"City","name":"Ростов-на-Дону"},{"@type":"City","name":"Батайск"},{"@type":"City","name":"Азов"}],"sameAs":["https://vk.com/mebel.ostrovsky","https://t.me/fanny161"]}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,500&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0e0c09;--gold:#d4af6a;--gold-soft:#eccfa0;--gold-deep:#a37c3f;--text:#f5efe3;--muted:#b9ad9a;--line:rgba(212,175,106,.14);--r-lg:24px;--r-md:16px;--r-sm:12px;--shadow-lg:0 34px 80px rgba(0,0,0,.5);--shadow-md:0 18px 46px rgba(0,0,0,.36);--shadow-gold:0 16px 42px rgba(212,175,106,.26);--serif:'Cormorant Garamond',Georgia,serif;--sans:'Manrope',system-ui,sans-serif;}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;overflow-x:hidden}
section{scroll-margin-top:92px}
body{font-family:var(--sans);color:var(--text);line-height:1.72;-webkit-font-smoothing:antialiased;overflow-x:hidden;position:relative;min-height:100vh}
body::before{content:"";position:fixed;inset:0;z-index:-2;background:radial-gradient(1200px 700px at 85% -10%,rgba(212,175,106,.16),transparent 60%),radial-gradient(1000px 640px at -10% 30%,rgba(212,175,106,.09),transparent 55%),radial-gradient(1400px 900px at 50% 120%,rgba(163,124,63,.14),transparent 60%),linear-gradient(180deg,#12100b,#0c0a07 45%,#100d09)}
.orb{position:fixed;border-radius:50%;pointer-events:none;z-index:-1;will-change:transform}
.orb-1{width:560px;height:560px;left:-180px;top:10%;background:radial-gradient(circle,rgba(212,175,106,.13),transparent 65%);animation:orbFloat 18s ease-in-out infinite alternate}
.orb-2{width:480px;height:480px;right:-160px;top:40%;background:radial-gradient(circle,rgba(163,124,63,.12),transparent 65%);animation:orbFloat 24s ease-in-out infinite alternate-reverse}
.orb-3{width:640px;height:640px;left:28%;bottom:-240px;background:radial-gradient(circle,rgba(212,175,106,.08),transparent 65%);animation:orbFloat 30s ease-in-out infinite alternate}
@keyframes orbFloat{from{transform:translateY(-36px)}to{transform:translateY(44px)}}
.grain{position:fixed;inset:0;z-index:2147480000;pointer-events:none;opacity:.03;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E")}
::selection{background:rgba(212,175,106,.32);color:#fff}
h1,h2,h3{font-family:var(--serif);overflow-wrap:break-word;letter-spacing:.3px}
img{max-width:100%;display:block}
a{text-decoration:none;color:inherit}
ul{list-style:none}
button{font-family:inherit;cursor:pointer}
.wrap{width:100%;max-width:1180px;margin:0 auto;padding:0 20px}
.progress{position:fixed;top:0;left:0;height:3px;z-index:300;background:linear-gradient(90deg,var(--gold-deep),var(--gold-soft),var(--gold));width:0%;box-shadow:0 0 14px rgba(236,207,160,.7)}
header{position:fixed;top:0;left:0;right:0;z-index:200;background:rgba(14,12,9,.55);backdrop-filter:blur(18px);transition:background .45s}
header.solid{background:rgba(14,12,9,.92)}
.nav{display:flex;align-items:center;justify-content:space-between;height:78px;gap:12px}
.logo{display:flex;align-items:center;gap:13px;min-width:0;cursor:pointer}
.brand-ava-w{position:relative;flex-shrink:0;display:inline-flex}
.brand-ava-w::before{content:"";position:absolute;inset:-5px;border-radius:50%;border:1px solid rgba(236,207,160,.5);opacity:.7}
.brand-ava{width:46px;height:46px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 5px rgba(212,175,106,.1),0 0 24px rgba(212,175,106,.4);position:relative;z-index:1}
.logo .brand-txt{display:flex;flex-direction:column;line-height:1.15}
.logo .brand-txt .name{font-family:var(--serif);font-size:26px;font-weight:600;color:#fff;background:linear-gradient(120deg,#fff,var(--gold-soft));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.logo .brand-txt .sub{color:var(--gold-soft);font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;margin-top:3px;opacity:.85}
.menu{position:fixed;top:0;height:78px;right:max(20px,calc((100vw - 1220px)/2));display:flex;gap:24px;align-items:center;z-index:201}
.menu a{color:rgba(255,255,255,.8);font-size:13px;font-weight:600;padding:6px 0;white-space:nowrap;transition:.3s}
.menu a:hover,.menu a.active{color:var(--gold-soft)}
.burger{display:none;background:none;border:none;width:44px;height:44px;position:relative;z-index:210}
.burger span{position:absolute;left:7px;right:7px;height:2px;background:#fff;transition:.3s;border-radius:2px}
.burger span:nth-child(1){top:13px}.burger span:nth-child(2){top:21px}.burger span:nth-child(3){top:29px}
.burger.open span:nth-child(1){top:21px;transform:rotate(45deg)}
.burger.open span:nth-child(2){opacity:0}
.burger.open span:nth-child(3){top:21px;transform:rotate(-45deg)}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.5);opacity:0;visibility:hidden;transition:.35s;z-index:195}
.scrim.show{opacity:1;visibility:visible}
.panel{position:relative;min-height:100vh;display:flex;align-items:center;padding:150px 0;overflow:hidden}
.panel .bg{position:absolute;inset:-14% 0;z-index:0;background-size:cover;background-position:center}
.panel .bg::after{content:"";position:absolute;inset:0;background:linear-gradient(to right,rgba(10,8,6,.94) 22%,rgba(10,8,6,.6) 58%,rgba(10,8,6,.75))}
.panel--center .bg::after{background:linear-gradient(180deg,rgba(10,8,6,.86),rgba(10,8,6,.62))}
.panel--dark .bg::after{background:linear-gradient(180deg,rgba(10,8,6,.9),rgba(10,8,6,.7))}
.panel .content{position:relative;z-index:2;width:100%}
.panel + .panel{margin-top:16px}
.panel--center .content{text-align:center}
.gold-divider{display:flex;align-items:center;justify-content:center;gap:14px;padding:6px 0}
.gold-divider i{display:inline-block;width:64px;height:1px;background:linear-gradient(90deg,transparent,var(--gold))}
.gold-divider i:last-child{background:linear-gradient(90deg,var(--gold),transparent)}
.gold-divider b{width:7px;height:7px;transform:rotate(45deg);background:var(--gold);box-shadow:0 0 12px rgba(212,175,106,.55)}
.eyebrow{display:inline-flex;align-items:center;gap:12px;color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:12px;font-weight:600;margin-bottom:20px}
.eyebrow::before,.eyebrow::after{content:"";width:42px;height:1px;background:var(--gold)}
h1{font-size:clamp(34px,6vw,76px);font-weight:500;line-height:1.08;color:#fff;text-shadow:0 5px 30px rgba(0,0,0,.5)}
h1 em{font-style:italic}
.sub{color:rgba(245,239,227,.9);font-size:clamp(16px,1.8vw,19.5px);font-weight:300;margin:24px 0 34px;max-width:580px}
.btn-row{display:flex;gap:16px;flex-wrap:wrap}
.btn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:15px 30px;font-size:13px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;transition:.4s;cursor:pointer;border-radius:13px;border:none}
.btn-solid{background:linear-gradient(135deg,var(--gold-soft),var(--gold) 55%,var(--gold-deep));color:#17120b;box-shadow:var(--shadow-gold);animation:btnGlow 3.6s ease-in-out infinite}
@keyframes btnGlow{0%,100%{box-shadow:0 16px 42px rgba(212,175,106,.26)}50%{box-shadow:0 24px 62px rgba(236,207,160,.5)}}
.btn-solid:hover{transform:translateY(-4px);box-shadow:0 26px 60px rgba(212,175,106,.45)}
.btn-line{border:1px solid rgba(255,255,255,.4);color:#fff;background:rgba(255,255,255,.04)}
.btn-line:hover{background:rgba(255,255,255,.12);transform:translateY(-4px)}
.shimmer{background:linear-gradient(90deg,var(--gold-soft),#fff 35%,var(--gold-soft) 70%);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerMove 3.4s linear infinite}
@keyframes shimmerMove{0%{background-position:0% center}100%{background-position:-220% center}}
.sec-head{max-width:740px;margin:0 auto 52px;text-align:center}
.sec-head .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.sec-head h2{font-size:clamp(30px,4.4vw,48px);font-weight:500;margin:16px 0 14px;color:#faf3e6}
.sec-head p{color:var(--muted);font-size:15.5px}
h2.k{font-size:clamp(32px,4.6vw,48px);color:#faf3e6;font-weight:500;margin:16px 0 14px;text-align:center}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;text-align:center}
.stat{padding:32px 16px;border-radius:var(--r-md);background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);transition:transform .45s,border-color .45s,box-shadow .45s}
.stat:hover{transform:translateY(-6px);border-color:rgba(236,207,160,.3)}
.stat .num{font-family:var(--serif);font-size:58px;font-weight:500;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold) 60%,var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.stat .lbl{color:var(--muted);font-size:13.5px;margin-top:12px}
.about{display:grid;grid-template-columns:1fr 1.1fr;gap:64px;align-items:center}
.about-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:48px 40px;text-align:center;border-radius:var(--r-lg);position:relative;overflow:hidden}
.about-card::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.6}
.avatar{width:130px;height:130px;border-radius:50%;margin:0 auto 22px;overflow:hidden;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 7px rgba(212,175,106,.12),0 16px 40px rgba(0,0,0,.5)}
.avatar img{width:100%;height:100%;object-fit:cover}
.about-card h3{font-size:29px;color:#fff}
.about-card .role{color:var(--gold-soft);font-size:13px;margin-top:5px}
.about-card .sep{width:52px;height:1px;background:var(--gold);margin:22px auto}
.about-card p{color:var(--muted);font-size:14.5px}
.about-body .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.about-body h2{font-size:clamp(30px,3.6vw,44px);font-weight:500;margin:16px 0 22px;color:#faf3e6}
.about-body p{color:var(--muted);font-size:15.5px;margin-bottom:26px}
.features{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.features li{position:relative;padding-left:36px;font-size:14.5px;transition:transform .3s}
.features li:hover{transform:translateX(5px)}
.features li::before{content:"";position:absolute;left:0;top:4px;width:18px;height:18px;border:1.5px solid rgba(212,175,106,.6);border-radius:50%;background:rgba(212,175,106,.08)}
.features li::after{content:"✓";position:absolute;left:4px;top:4px;font-size:11px;color:var(--gold-soft);font-weight:800}
.consult .phone{display:inline-block;font-weight:800;font-size:clamp(30px,4.4vw,52px);margin-top:12px;white-space:nowrap;background:linear-gradient(120deg,var(--gold-soft),var(--gold));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.consult p{color:var(--muted);font-size:15.5px;margin:30px auto 0;max-width:630px}
.carousel{position:relative;max-width:1120px;margin:0 auto}
.car-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;padding:12px 8px 24px;scrollbar-width:none}
.car-track::-webkit-scrollbar{display:none}
.car-nav{position:absolute;top:38%;transform:translateY(-50%);width:48px;height:48px;border-radius:50%;background:rgba(14,12,9,.68);border:1px solid rgba(236,207,160,.35);color:var(--gold-soft);font-size:21px;cursor:pointer;z-index:5;display:flex;align-items:center;justify-content:center}
.car-prev{left:-16px}.car-next{right:-16px}
.car-dots{display:flex;justify-content:center;gap:10px;margin-top:12px;flex-wrap:wrap}
.car-dot{width:8px;height:8px;min-width:8px;border-radius:99px;background:rgba(255,255,255,.2);cursor:pointer;transition:.35s;border:none;padding:0}
.car-dot.active{width:26px;background:linear-gradient(135deg,var(--gold-soft),var(--gold))}
.swipe-hint{text-align:center;color:var(--muted);font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-top:10px}
.car-slide{flex:0 0 auto;width:min(78vw,440px);scroll-snap-align:center;border-radius:var(--r-lg);overflow:hidden;border:1px solid rgba(255,255,255,.08);cursor:zoom-in;transition:.5s}
.car-slide:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.3)}
.car-slide img{width:100%;height:300px;object-fit:cover}
.rev-card{scroll-snap-align:center;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);padding:24px 26px;width:min(82vw,520px);flex:0 0 auto;transition:.5s}
.rev-head{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.rev-ava{width:50px;height:50px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.6)}
.rev-name{color:#fff;font-weight:700;font-size:14.5px}
.rev-sub{color:var(--muted);font-size:11px;margin-top:2px}
.rev-stars{color:var(--gold-soft);letter-spacing:3px;font-size:14px;margin-left:auto}
.rev-text{color:#ece2cd;font-size:13.5px;line-height:1.66;font-weight:300}
.rev-video{margin-top:14px;border-radius:var(--r-md);overflow:hidden}
.video-box{position:relative;width:100%;height:260px;background-size:cover;background-position:center;cursor:pointer;display:flex;align-items:center;justify-content:center}
.video-box iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.vb-play{position:relative;z-index:2;width:64px;height:64px;border-radius:50%;border:1px solid rgba(236,207,160,.7);background:rgba(14,12,9,.55);color:var(--gold-soft);display:flex;align-items:center;justify-content:center}
.vb-play svg{width:22px;height:22px;fill:currentColor;margin-left:3px}
.svc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.svc{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 30px;transition:.5s;border-radius:var(--r-lg)}
.svc:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.26)}
.svc svg{width:34px;height:34px;stroke:var(--gold-soft);fill:none;stroke-width:1.4;margin-bottom:20px}
.svc h3{font-size:23px;color:#fff;margin-bottom:9px}
.svc p{color:var(--muted);font-size:14px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.step{padding:34px 26px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);transition:.45s}
.step:hover{transform:translateY(-7px);border-color:rgba(236,207,160,.28)}
.step .n{font-family:var(--serif);font-size:54px;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.step h3{font-size:22px;color:#fff;margin:14px 0 8px}
.step p{color:var(--muted);font-size:14px}
.guar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.guar{background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 26px;text-align:center;transition:.45s;border-radius:var(--r-lg)}
.guar:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.26)}
.guar .ico{width:54px;height:54px;margin:0 auto 18px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft)}
.guar .ico svg{width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:1.5}
.guar h3{font-size:18px;color:#fff;margin-bottom:8px}
.guar p{color:var(--muted);font-size:13px}
.city-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.city{padding:38px 28px;border-radius:var(--r-lg);background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);text-align:center;transition:.45s}
.city:hover{transform:translateY(-7px);border-color:rgba(236,207,160,.26)}
.city .city-name{font-family:var(--serif);font-size:28px;color:#fff;font-weight:500}
.city .city-line{width:42px;height:1px;background:var(--gold);margin:14px auto}
.city p{color:var(--muted);font-size:14px}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}
.contact-info h2{font-size:clamp(30px,4.1vw,46px);color:#faf3e6;margin:16px 0 14px}
.contact-info .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.contact-info>p{color:var(--muted);font-size:15.5px;margin-bottom:32px}
.c-line{display:flex;align-items:flex-start;gap:20px;margin-bottom:24px;transition:transform .4s}
.c-line:hover{transform:translateX(6px)}
.c-ico{width:44px;height:44px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);flex-shrink:0;font-size:14px;font-weight:700}
.c-line .lab{font-size:10.5px;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.c-line .val{font-size:18px;font-weight:600;color:var(--text)}
.call-block{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:46px 36px;text-align:center;border-radius:var(--r-lg)}
.call-block .cb-lab{font-size:12px;letter-spacing:4px;text-transform:uppercase;color:var(--gold-soft)}
.call-block .cb-num{display:block;font-weight:800;font-size:clamp(27px,3.6vw,44px);color:#fff;margin:14px 0 18px;white-space:nowrap}
.call-block .cb-hint{color:var(--muted);font-size:14px}
.contact-actions{display:flex;flex-direction:column;gap:12px;margin-top:24px}
.c-action{display:flex;align-items:center;justify-content:center;gap:11px;min-height:52px;padding:15px 18px;border-radius:var(--r-sm);font-weight:700;font-size:14.5px;transition:.4s;color:#fff}
.c-call{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b}
.c-tg{background:rgba(64,169,242,.12);border:1px solid rgba(64,169,242,.38);color:#8fd0ff}
.c-max{background:rgba(177,88,252,.12);border:1px solid rgba(177,88,252,.38);color:#e0b8ff}
.cta{text-align:center;padding:110px 0}
.cta h2{font-size:clamp(32px,4.6vw,52px);color:#faf3e6;font-weight:500;margin-bottom:16px}
.cta p{color:var(--muted);font-size:16.5px;max-width:630px;margin:0 auto 34px}
footer{background:linear-gradient(180deg,rgba(14,12,9,.4),rgba(10,8,6,.97));color:var(--muted);padding:52px 20px 60px;text-align:center;font-size:13px;border-top:1px solid rgba(255,255,255,.06);position:relative}
footer::before{content:"";position:absolute;top:-1px;left:50%;transform:translateX(-50%);width:min(420px,72%);height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
footer .flogo{font-family:var(--serif);font-size:28px;color:#fff;margin-bottom:8px}
footer .flogo span{color:var(--gold-soft);font-size:13px;font-family:var(--sans)}
.social-row{display:flex;justify-content:center;gap:14px;margin:22px 0 18px;flex-wrap:wrap}
.soc{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:50%;border:1px solid rgba(236,207,160,.32);color:var(--gold-soft);background:rgba(212,175,106,.06);transition:.35s;font-size:18px}
.soc:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-4px)}
.cookie-bar{position:fixed;bottom:16px;left:50%;transform:translate(-50%,140%);z-index:400;background:rgba(14,12,9,.93);border:1px solid rgba(255,255,255,.08);border-radius:var(--r-md);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;width:min(680px,calc(100vw - 32px));transition:transform .6s}
.cookie-bar.show{transform:translate(-50%,0)}
.cookie-bar p{color:var(--muted);font-size:13px}
.lightbox{position:fixed;inset:0;z-index:3000;background:rgba(8,6,4,.96);display:none;align-items:center;justify-content:center;flex-direction:column;gap:14px}
.lightbox.open{display:flex}
.lb-stage{width:100%;max-width:1180px;height:calc(100vh - 130px);display:flex;align-items:center;justify-content:center}
.lb-stage img{max-width:94%;max-height:100%;border-radius:var(--r-lg);border:1px solid rgba(236,207,160,.55)}
.lb-close{position:absolute;top:18px;right:24px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#fff;font-size:28px;cursor:pointer;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.lb-nav{width:50px;height:50px;border-radius:50%;background:rgba(14,12,9,.6);border:1px solid rgba(236,207,160,.5);color:var(--gold-soft);font-size:24px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.lb-bar{display:flex;align-items:center;gap:20px}
.lb-count{color:var(--muted);font-size:13px}
.js .reveal{opacity:0;transform:translateY(26px);transition:.8s}
.js .reveal.in{opacity:1;transform:none}
@media(max-width:1024px){.stats,.svc-grid,.guar-grid{grid-template-columns:repeat(2,1fr)}.panel{padding:132px 0}}
@media(max-width:860px){
  .menu{position:fixed;top:auto;left:0;right:0;bottom:0;width:100%;max-height:82vh;background:linear-gradient(180deg,#16130e,#0b0907);flex-direction:column;gap:4px;padding:12px 24px calc(22px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .45s;z-index:205;border-radius:26px 26px 0 0;overflow-y:auto;border-top:1px solid rgba(236,207,160,.2)}
  .menu.open{transform:none}
  .menu a{font-size:19px;font-family:var(--serif);color:#fff;border-bottom:1px solid rgba(236,207,160,.12);padding:13px 6px;display:flex;align-items:center;min-height:48px}
  .burger{display:block}.scrim{display:block}
  .about,.contact-grid,.features,.steps,.city-grid{grid-template-columns:1fr}
  .car-nav{display:none}.panel{padding:116px 0}
}
@media(max-width:768px){.stats,.guar-grid{grid-template-columns:1fr 1fr}.svc-grid,.steps{grid-template-columns:1fr}.panel{padding:104px 0 60px}}
@media(max-width:520px){
  .brand-ava{width:40px;height:40px}.brand-txt .name{font-size:20px}.nav{height:64px}
  .panel{min-height:auto;padding:96px 0 56px}
  h1{font-size:31px}.btn-row{width:100%}.btn{width:100%;text-align:center;padding:14px 20px;font-size:12px}
  .car-slide{width:84vw}.car-slide img{height:205px}.rev-card{width:92vw;padding:17px}
}
</style>
</head>
<body>
<div class="progress" id="progress"></div>
<div class="grain" aria-hidden="true"></div>
<div class="orb orb-1"></div><div class="orb orb-2"></div><div class="orb orb-3"></div>
<header id="header">
  <div class="wrap nav">
    <a href="#top" class="logo" id="logo">
      <span class="brand-ava-w"><img class="brand-ava" src="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0" width="46" height="46" alt="Кухни Островский"></span>
      <span class="brand-txt"><span class="name">Кухни Островский</span><span class="sub">Ростов · Батайск · Азов</span></span>
    </a>
    <button class="burger" id="burger"><span></span><span></span><span></span></button>
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
<section class="panel panel--hero" id="top">
  <div class="bg" style="background-image:url('https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <span class="eyebrow">Мебель и кухни на заказ</span>
    <h1 id="heroTitle">Мебель, которая <em class="shimmer">создаёт настроение</em></h1>
    <p class="sub">Проектируем и изготавливаем кухни, шкафы, гардеробные и другую корпусную мебель в Ростове, Батайске и Азове — по вашему проекту, от замера до монтажа.</p>
    <div class="btn-row">
      <a href="#consult" class="btn btn-solid">Получить консультацию</a>
      <a href="#works" class="btn btn-line">Смотреть работы</a>
    </div>
  </div></div>
</section>
<section class="panel panel--dark">
  <div class="bg" style="background-image:url('https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="stats">
      <div class="stat"><div class="num" data-count="10" data-suffix="+">0</div><div class="lbl">лет опыта</div></div>
      <div class="stat"><div class="num" data-count="5" data-decimal="1">0</div><div class="lbl">средняя оценка</div></div>
      <div class="stat"><div class="num" data-count="8" data-suffix="/10">0</div><div class="lbl">по рекомендации</div></div>
      <div class="stat"><div class="num" data-count="100" data-suffix="%">0</div><div class="lbl">под ключ</div></div>
    </div>
  </div></div>
</section>
<section class="panel" id="about">
  <div class="bg" style="background-image:url('https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="about">
      <div class="about-card">
        <div class="avatar"><img src="https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg" width="130" height="130" alt="Роман Островский"></div>
        <h3>Роман Островский</h3>
        <div class="role">Руководитель мебельной мастерской Островского</div>
        <div class="sep"></div>
        <p>С командой изготавливаем кухни и корпусную мебель по индивидуальным проектам — с учётом ваших идей, размеров и задач.</p>
      </div>
      <div class="about-body">
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
<section class="panel panel--center panel--dark" id="consult">
  <div class="bg" style="background-image:url('https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content consult">
    <span class="kicker" style="color:var(--gold-soft);letter-spacing:6px;text-transform:uppercase;font-size:12px;font-weight:600">Бесплатно</span>
    <h2 class="k">Консультация</h2>
    <a href="tel:+79508465397" class="phone">+7 (950) 846-53-97</a>
    <p>Позвоните или напишите нам в <b style="color:#fff">Telegram</b> или <b style="color:#fff">MAX</b> — расскажем про кухни и мебель, всё обсудим и договоримся о бесплатном замере.</p>
  </div></div>
</section>
<section class="panel panel--center panel--dark" id="works">
  <div class="bg" style="background-image:url('https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head">
      <div class="kicker">Наши работы</div>
      <h2>Кухни и мебель, которые мы сделали</h2>
      <p>Нажмите на фото, чтобы рассмотреть в большом размере.</p>
    </div>
    <div class="carousel">
      <button class="car-nav car-prev" id="carPrev">❮</button>
      <div class="car-track" id="carTrack"></div>
      <button class="car-nav car-next" id="carNext">❯</button>
      <div class="car-dots" id="carDots"></div>
      <div class="swipe-hint">Листайте</div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше работ — в сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>
<div class="lightbox" id="lightbox">
  <button class="lb-close" id="lbClose">×</button>
  <div class="lb-stage" id="lbStage"><img id="lbImg" alt="Работа"></div>
  <div class="lb-bar">
    <button class="lb-nav" id="lbPrev">❮</button>
    <div class="lb-count" id="lbCount"></div>
    <button class="lb-nav" id="lbNext">❯</button>
  </div>
</div>
<section class="panel panel--center" id="reviews">
  <div class="bg" style="background-image:url('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head">
      <div class="kicker">Отзывы</div>
      <h2>Что говорят наши клиенты</h2>
      <p>Реальные отзывы о нашей работе. Листайте влево-вправо.</p>
    </div>
    <div class="carousel">
      <button class="car-nav car-prev" id="revPrev">❮</button>
      <div class="car-track rev-track" id="revTrack"></div>
      <button class="car-nav car-next" id="revNext">❯</button>
      <div class="car-dots" id="revDots"></div>
      <div class="swipe-hint">Листайте</div>
    </div>
  </div></div>
</section>
<section class="panel panel--dark" id="services">
  <div class="bg" style="background-image:url('https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head">
      <div class="kicker">Что мы делаем</div>
      <h2>Услуги</h2>
      <p>Индивидуальный подход к каждому проекту и полный цикл производства.</p>
    </div>
    <div class="svc-grid" id="svcGrid"></div>
  </div></div>
</section>
<section class="panel" id="process">
  <div class="bg" style="background-image:url('https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head">
      <div class="kicker">Как мы работаем</div>
      <h2>Путь от идеи до готовой мебели</h2>
    </div>
    <div class="steps" id="stepsBox"></div>
  </div></div>
</section>
<section class="panel panel--dark">
  <div class="bg" style="background-image:url('https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head">
      <div class="kicker">Почему мы</div>
      <h2>Гарантии и преимущества</h2>
    </div>
    <div class="guar-grid" id="guarGrid"></div>
  </div></div>
</section>
<section class="panel panel--center panel--dark" id="cities">
  <div class="bg" style="background-image:url('https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head">
      <div class="kicker">Где работаем</div>
      <h2>Три города — один стандарт качества</h2>
      <p>Бесплатный замер и проект в каждом из городов.</p>
    </div>
    <div class="city-grid" id="cityGrid"></div>
  </div></div>
</section>
<section class="panel panel--center panel--dark">
  <div class="bg" style="background-image:url('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=1280x0')"></div>
  <div class="wrap"><div class="content cta">
    <h2 class="shimmer">Готовы обсудить вашу мебель?</h2>
    <p>Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.</p>
    <a href="tel:+79508465397" class="btn btn-solid">📞 Позвонить специалисту</a>
  </div></div>
</section>
<section class="panel panel--dark" id="contacts">
  <div class="bg" style="background-image:url('https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&cs=1080x0')"></div>
  <div class="wrap"><div class="content">
    <div class="contact-grid">
      <div class="contact-info">
        <div class="kicker">Контакты</div>
        <h2>Создадим мебель, о которой вы мечтали</h2>
        <p>Позвоните или напишите — ответим быстро и подскажем по всем вопросам.</p>
        <div class="c-line"><div class="c-ico">📍</div><div><div class="lab">Регион работы</div><div class="val">Ростов-на-Дону, Батайск, Азов</div></div></div>
        <div class="c-line"><div class="c-ico">VK</div><div><div class="lab">Сайт в VK</div><a class="val" href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener">mebel.ostrovsky</a></div></div>
        <div class="c-line"><div class="c-ico">✈</div><div><div class="lab">Telegram / MAX</div><div class="val">по номеру +7 (950) 846-53-97</div></div></div>
      </div>
      <div>
        <div class="call-block">
          <div class="cb-lab">Свяжитесь с нами удобным способом</div>
          <a class="cb-num" href="tel:+79508465397">+7 (950) 846-53-97</a>
          <div class="cb-hint">Бесплатная консультация и запись на замер.<br>Звоните или пишите в любой мессенджер.</div>
          <div class="contact-actions">
            <a class="c-action c-call" href="tel:+79508465397">📞 Позвонить</a>
            <a class="c-action c-tg" href="https://t.me/fanny161" target="_blank" rel="noopener">✈ Написать в Telegram</a>
            <a class="c-action c-max" href="tel:+79508465397">🛡 Написать в MAX</a>
          </div>
        </div>
      </div>
    </div>
  </div></div>
</section>
<footer>
  <div class="flogo">Кухни Островский<span> · Ростов · Батайск · Азов</span></div>
  <div class="social-row">
    <a class="soc" href="tel:+79508465397" title="Позвонить">📞</a>
    <a class="soc" href="https://t.me/fanny161" target="_blank" rel="noopener" title="Telegram">✈</a>
    <a class="soc" href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" title="ВКонтакте">VK</a>
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
const header=document.getElementById('header');
const burger=document.getElementById('burger'),menu=document.getElementById('menu'),scrim=document.getElementById('scrim');
let menuOpen=false;
window.addEventListener('scroll',function(){header.classList.toggle('solid',window.scrollY>40);},{passive:true});
function closeMenu(){burger.classList.remove('open');menu.classList.remove('open');scrim.classList.remove('show');menuOpen=false;}
function openMenu(){burger.classList.add('open');menu.classList.add('open');scrim.classList.add('show');menuOpen=true;}
burger.addEventListener('click',function(){menuOpen?closeMenu():openMenu();});
scrim.addEventListener('click',closeMenu);
menu.querySelectorAll('a').forEach(function(a){a.addEventListener('click',closeMenu);});
document.getElementById('logo').addEventListener('click',function(e){e.preventDefault();window.scrollTo({top:0,behavior:'smooth'});});

function animateCount(el){var target=parseFloat(el.dataset.count);var dec=parseInt(el.dataset.decimal||'0');var suffix=el.dataset.suffix||'';var dur=1200,start=performance.now();function tick(t){var p=Math.min((t-start)/dur,1);p=1-Math.pow(1-p,3);var val=(target*p).toFixed(dec);el.textContent=(dec?val:Math.round(val))+suffix;if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}
var statIO=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){animateCount(e.target);statIO.unobserve(e.target);}});},{threshold:.5});
document.querySelectorAll('.stat .num').forEach(function(el){statIO.observe(el);});

function initCarousel(trackId,prevId,nextId,dotsId){var track=document.getElementById(trackId);if(!track)return;var prev=document.getElementById(prevId),next=document.getElementById(nextId),dotsBox=document.getElementById(dotsId);var items=Array.prototype.slice.call(track.children);if(!items.length)return;dotsBox.innerHTML='';items.forEach(function(_,i){var d=document.createElement('button');d.className='car-dot'+(i===0?' active':'');d.setAttribute('aria-label','Слайд '+(i+1));d.addEventListener('click',function(){items[i].scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'});});dotsBox.appendChild(d);});var dots=Array.prototype.slice.call(dotsBox.children);var step=function(){return items[0].offsetWidth+20;};var sTick=false;track.addEventListener('scroll',function(){if(sTick)return;sTick=true;requestAnimationFrame(function(){var idx=Math.round(track.scrollLeft/step());dots.forEach(function(d,i){d.classList.toggle('active',i===idx);});sTick=false;});},{passive:true});prev.addEventListener('click',function(){track.scrollBy({left:-step(),behavior:'smooth'});});next.addEventListener('click',function(){track.scrollBy({left:step(),behavior:'smooth'});});}
initCarousel('carTrack','carPrev','carNext','carDots');
initCarousel('revTrack','revPrev','revNext','revDots');

var lightbox=document.getElementById('lightbox'),lbImg=document.getElementById('lbImg'),lbCount=document.getElementById('lbCount');
var lbItems=Array.prototype.slice.call(document.querySelectorAll('#carTrack .car-slide img'));var lbIdx=0;
function openLb(i){lbIdx=i;lbImg.src=lbItems[i].src;lbImg.alt=lbItems[i].alt;lbCount.textContent=(i+1)+' / '+lbItems.length;lightbox.classList.add('open');document.body.style.overflow='hidden';}
function closeLb(){lightbox.classList.remove('open');document.body.style.overflow='';}
function lbStep(d){openLb((lbIdx+d+lbItems.length)%lbItems.length);}
lbItems.forEach(function(img,i){img.addEventListener('click',function(){openLb(i);});});
document.getElementById('lbClose').addEventListener('click',closeLb);
document.getElementById('lbPrev').addEventListener('click',function(e){e.stopPropagation();lbStep(-1);});
document.getElementById('lbNext').addEventListener('click',function(e){e.stopPropagation();lbStep(1);});
lightbox.addEventListener('click',function(e){if(e.target===lightbox)closeLb();});
document.addEventListener('keydown',function(e){if(lightbox.classList.contains('open')){if(e.key==='Escape')closeLb();if(e.key==='ArrowLeft')lbStep(-1);if(e.key==='ArrowRight')lbStep(1);}});

document.querySelectorAll('.video-box').forEach(function(box){box.addEventListener('click',function(){if(box.querySelector('iframe'))return;var iframe=document.createElement('iframe');iframe.src=box.dataset.src;iframe.setAttribute('allow','autoplay; encrypted-media; fullscreen');iframe.setAttribute('allowfullscreen','1');box.innerHTML='';box.appendChild(iframe);});});

var cookieBar=document.getElementById('cookieBar'),cookieOk=document.getElementById('cookieOk');
if(!localStorage.getItem('cookiesAccepted')){setTimeout(function(){cookieBar.classList.add('show');},900);}
cookieOk.addEventListener('click',function(){localStorage.setItem('cookiesAccepted','1');cookieBar.classList.remove('show');});
document.getElementById('year').textContent=new Date().getFullYear();
})();
</script>
</body>
</html>"""


# =====================================================================
# RENDER PAGE
# =====================================================================
def _sub_exact(html, anchor, replacement):
    if anchor and anchor in html:
        return html.replace(anchor, replacement, 1)
    return html


def render_page():
    html = PAGE
    d = load_data()

    b = d.get("brand", {}) or {}
    seo = d.get("seo", {}) or {}
    hero = d.get("hero", {}) or {}
    about = d.get("about", {}) or {}
    consult = d.get("consult", {}) or {}
    works = d.get("works", {}) or {}
    reviews = d.get("reviews", {}) or {}
    services = d.get("services", {}) or {}
    process_ = d.get("process", {}) or {}
    guarantees = d.get("guarantees", {}) or {}
    cities = d.get("cities", {}) or {}
    cta = d.get("cta", {}) or {}
    contacts = d.get("contacts", {}) or {}
    footer = d.get("footer", {}) or {}

    if seo.get("title"):
        html = re.sub(r"<title>.*?</title>", "<title>" + seo["title"] + "</title>", html, count=1, flags=re.S)
    if seo.get("description"):
        html = re.sub(r'<meta name="description" content="[^"]*">',
                      '<meta name="description" content="' + seo["description"] + '">', html, count=1)
    if seo.get("keywords"):
        html = re.sub(r'<meta name="keywords" content="[^"]*">',
                      '<meta name="keywords" content="' + seo["keywords"] + '">', html, count=1)
    if seo.get("og_image"):
        html = re.sub(r'<meta property="og:image" content="[^"]*">',
                      '<meta property="og:image" content="' + seo["og_image"] + '">', html, count=1)

    if b.get("name"):
        html = _sub_exact(html, '<span class="name">Кухни Островский</span>',
                          '<span class="name">' + b["name"] + '</span>')
    if b.get("sub"):
        html = _sub_exact(html, '<span class="sub">Ростов · Батайск · Азов</span>',
                          '<span class="sub">' + b["sub"] + '</span>')
    if b.get("phone"):
        html = html.replace("+7 (950) 846-53-97", b["phone"])
    if b.get("phone_raw"):
        html = html.replace("tel:+79508465397", "tel:" + b["phone_raw"])
    if b.get("telegram"):
        html = html.replace("https://t.me/fanny161", b["telegram"])
    if b.get("vk"):
        html = html.replace("https://vk.com/mebel.ostrovsky", b["vk"])

    if hero.get("eyebrow"):
        html = _sub_exact(html, '<span class="eyebrow">Мебель и кухни на заказ</span>',
                          '<span class="eyebrow">' + hero["eyebrow"] + '</span>')
    if hero.get("title_before") or hero.get("title_em"):
        tb = hero.get("title_before", "Мебель, которая ")
        te = hero.get("title_em", "создаёт настроение")
        new_h1 = '<h1 id="heroTitle">' + tb + '<em class="shimmer">' + te + '</em></h1>'
        html = re.sub(r'<h1 id="heroTitle">.*?</h1>', new_h1, html, count=1, flags=re.S)
    if hero.get("sub"):
        html = _sub_exact(html, '<p class="sub">Проектируем и изготавливаем кухни, шкафы, гардеробные и другую корпусную мебель в Ростове, Батайске и Азове — по вашему проекту, от замера до монтажа.</p>',
                          '<p class="sub">' + hero["sub"] + '</p>')
    if hero.get("btn1"):
        html = _sub_exact(html, '>Получить консультацию<', '>' + hero["btn1"] + '<')
    if hero.get("btn2"):
        html = _sub_exact(html, '>Смотреть работы<', '>' + hero["btn2"] + '<')

    if about.get("photo"):
        html = _sub_exact(html, 'src="https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg"',
                          'src="' + about["photo"] + '"')
    if about.get("name"):
        html = _sub_exact(html, '<h3>Роман Островский</h3>', '<h3>' + about["name"] + '</h3>')
    if about.get("role"):
        html = _sub_exact(html, '<div class="role">Руководитель мебельной мастерской Островского</div>',
                          '<div class="role">' + about["role"] + '</div>')
    if about.get("text"):
        html = _sub_exact(html, '<p>С командой изготавливаем кухни и корпусную мебель по индивидуальным проектам — с учётом ваших идей, размеров и задач.</p>',
                          '<p>' + about["text"] + '</p>')
    if about.get("kicker"):
        html = _sub_exact(html, '<div class="kicker">О руководителе</div>',
                          '<div class="kicker">' + about["kicker"] + '</div>')
    if about.get("title"):
        html = _sub_exact(html, '<h2>Кухни и мебель под ключ — с заботой о деталях</h2>',
                          '<h2>' + about["title"] + '</h2>')
    if about.get("body"):
        html = _sub_exact(html, '<p>Мы помогаем с планировкой и подбором материалов, предлагаем решения даже для сложных задач — когда другие разводят руками. Ведём вас от консультации и замера до сборки и установки.</p>',
                          '<p>' + about["body"] + '</p>')
    feats = about.get("features")
    if isinstance(feats, list) and feats:
        block = '<ul class="features">' + ''.join('<li>' + str(x) + '</li>' for x in feats) + '</ul>'
        html = re.sub(r'<ul class="features">.*?</ul>', block, html, count=1, flags=re.S)

    if consult.get("kicker"):
        html = _sub_exact(html, '>Бесплатно</span>', '>' + consult["kicker"] + '</span>')
    if consult.get("title"):
        html = _sub_exact(html, '<h2 class="k">Консультация</h2>', '<h2 class="k">' + consult["title"] + '</h2>')
    if consult.get("text"):
        html = re.sub(r'(<a href="tel:[^"]+" class="phone">[^<]+</a>\s*)<p>.*?</p>',
                      lambda m: m.group(1) + '<p>' + consult["text"] + '</p>',
                      html, count=1, flags=re.S)

    bg_map = {
        "hero": hero.get("bg"),
        "stats": (d.get("stats") or {}).get("bg"),
        "about": about.get("bg"),
        "consult": consult.get("bg"),
        "works": works.get("bg"),
        "reviews": reviews.get("bg"),
        "services": services.get("bg"),
        "process": process_.get("bg"),
        "guarantees": guarantees.get("bg"),
        "cities": cities.get("bg"),
        "cta": cta.get("bg"),
        "contacts": contacts.get("bg"),
    }
    old_bgs = {
        "hero": "https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&cs=1280x0",
        "stats": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&cs=1280x0",
        "about": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg?quality=95&cs=1280x0",
        "consult": "https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&cs=1280x0",
        "works": "https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&cs=1280x0",
        "reviews": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&cs=1280x0",
        "services": "https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&cs=1280x0",
        "process": "https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&cs=1280x0",
        "guarantees": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&cs=1280x0",
        "cities": "https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&cs=1280x0",
        "contacts": "https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&cs=1080x0",
    }
    for key, new_bg in bg_map.items():
        if new_bg and key in old_bgs:
            html = html.replace(old_bgs[key], new_bg)

    items = works.get("items")
    if isinstance(items, list) and items:
        block = ""
        for it in items:
            it = it or {}
            url = it.get("url", ""); alt = it.get("alt", "")
            if not url: continue
            block += '<div class="car-slide"><img loading="lazy" src="' + url + '" alt="' + alt + '"></div>'
        if block:
            html = re.sub(r'(<div class="car-track" id="carTrack">).*?(</div>)',
                          r'\1' + block + r'\2', html, count=1, flags=re.S)

    rev_items = reviews.get("items")
    if isinstance(rev_items, list) and rev_items:
        block = ""
        for r in rev_items:
            r = r or {}
            name = r.get("name",""); sub = r.get("sub",""); stars = "★" * int(r.get("stars",5))
            avatar = r.get("avatar",""); text = r.get("text",""); video = r.get("video","")
            vp = r.get("video_poster","") or VIDEO_POSTER
            ava_html = '<img class="rev-ava" loading="lazy" width="50" height="50" src="' + avatar + '" alt="Отзыв: ' + name + '">' if avatar else ""
            video_html = ""
            if video:
                video_html = '<div class="rev-video"><div class="video-box" data-src="' + video + '" style="background-image:url(\'' + vp + '\')"><span class="vb-play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span></div></div>'
            block += '<div class="rev-card"><div class="rev-head">' + ava_html + '<div><div class="rev-name">' + name + '</div><div class="rev-sub">' + sub + '</div></div><div class="rev-stars">' + stars + '</div></div>' + video_html + '<p class="rev-text">' + text + '</p></div>'
        if block:
            html = re.sub(r'(<div class="car-track rev-track" id="revTrack">).*?(</div>)',
                          r'\1' + block + r'\2', html, count=1, flags=re.S)

    svc_items = services.get("items")
    if isinstance(svc_items, list) and svc_items:
        block = ""
        for s in svc_items:
            s = s or {}
            block += '<div class="svc reveal"><svg viewBox="0 0 24 24"><path d="' + s.get("icon","") + '"/></svg><h3>' + s.get("title","") + '</h3><p>' + s.get("text","") + '</p></div>'
        if block:
            html = _sub_exact(html, '<div class="svc-grid" id="svcGrid"></div>', '<div class="svc-grid" id="svcGrid">' + block + '</div>')

    st_items = process_.get("items")
    if isinstance(st_items, list) and st_items:
        block = ""
        for s in st_items:
            s = s or {}
            block += '<div class="step reveal"><div class="n">' + s.get("n","") + '</div><h3>' + s.get("title","") + '</h3><p>' + s.get("text","") + '</p></div>'
        if block:
            html = _sub_exact(html, '<div class="steps" id="stepsBox"></div>', '<div class="steps" id="stepsBox">' + block + '</div>')

    g_items = guarantees.get("items")
    if isinstance(g_items, list) and g_items:
        block = ""
        for g in g_items:
            g = g or {}
            block += '<div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24"><path d="' + g.get("icon","") + '"/></svg></div><h3>' + g.get("title","") + '</h3><p>' + g.get("text","") + '</p></div>'
        if block:
            html = _sub_exact(html, '<div class="guar-grid" id="guarGrid"></div>', '<div class="guar-grid" id="guarGrid">' + block + '</div>')

    c_items = cities.get("items")
    if isinstance(c_items, list) and c_items:
        block = ""
        for c in c_items:
            c = c or {}
            block += '<div class="city reveal"><div class="city-name">' + c.get("name","") + '</div><div class="city-line"></div><p>' + c.get("text","") + '</p></div>'
        if block:
            html = _sub_exact(html, '<div class="city-grid" id="cityGrid"></div>', '<div class="city-grid" id="cityGrid">' + block + '</div>')

    if cta.get("title"):
        html = _sub_exact(html, '<h2 class="shimmer">Готовы обсудить вашу мебель?</h2>', '<h2 class="shimmer">' + cta["title"] + '</h2>')
    if cta.get("text"):
        html = _sub_exact(html, '<p>Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.</p>', '<p>' + cta["text"] + '</p>')
    if cta.get("button"):
        html = _sub_exact(html, '>📞 Позвонить специалисту<', '>' + cta["button"] + '<')

    if contacts.get("regions"):
        html = _sub_exact(html, '<div class="val">Ростов-на-Дону, Батайск, Азов</div>', '<div class="val">' + contacts["regions"] + '</div>')

    if footer.get("line"):
        html = _sub_exact(html, '<p>Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов</p>', '<p>' + footer["line"] + '</p>')
    if footer.get("copyright"):
        html = re.sub(r'© <span id="year"></span>[^<]*',
                      '© <span id="year"></span> ' + footer["copyright"], html, count=1)

    html = _inject_animations(html)
    return html


# =====================================================================
# FAVICON
# =====================================================================
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
            c = img.copy(); c.thumbnail((size, size))
            buf = io.BytesIO(); c.save(buf, format="PNG"); return buf.getvalue()
        _icons_cache["png16"] = _png(16); _icons_cache["png32"] = _png(32); _icons_cache["png180"] = _png(180)
    except Exception:
        pass


def get_favicon():
    now = time.time()
    if _favicon_cache["data"] is None or now - _favicon_cache["ts"] > FAVICON_TTL:
        try:
            req = urllib.request.Request(FAVICON_URL, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://vk.com/"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                _favicon_cache["data"] = data; _favicon_cache["ts"] = now; _make_icons(data)
        except Exception:
            return None
    return _favicon_cache["data"]


# =====================================================================
# АДМИНКА HTML
# =====================================================================
ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Вход в админку</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:linear-gradient(135deg,#0e0c09,#1a1611);color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.2);border-radius:20px;padding:42px 38px;width:100%;max-width:420px}
h1{font-family:Georgia,serif;font-size:28px;color:#fff;margin-bottom:8px;text-align:center}
p.sub{color:#b9ad9a;font-size:13.5px;text-align:center;margin-bottom:28px}
label{display:block;color:#eccfa0;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:600}
input{width:100%;padding:14px 16px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;font-size:15px;font-family:inherit;margin-bottom:18px}
input:focus{outline:none;border-color:#d4af6a}
button{width:100%;padding:15px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;font-size:14px;letter-spacing:1.2px;text-transform:uppercase;border:none;border-radius:12px;cursor:pointer}
.err{background:rgba(220,60,60,.14);border:1px solid rgba(220,60,60,.4);color:#ff9a9a;padding:12px 14px;border-radius:10px;font-size:13px;margin-bottom:18px;text-align:center}
</style></head><body>
<form class="card" method="POST" action="/admin/login">
  <h1>Кухни Островский</h1>
  <p class="sub">Вход в панель управления</p>
  __ERROR__
  <label>Логин</label><input type="text" name="login" required autofocus>
  <label>Пароль</label><input type="password" name="password" required>
  <button type="submit">Войти</button>
</form></body></html>"""


ADMIN_HTML = r"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Админка</title><style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--gold:#d4af6a;--gold-soft:#eccfa0;--bg:#0e0c09;--line:rgba(236,207,160,.16)}
body{font-family:system-ui,sans-serif;background:var(--bg);color:#f5efe3;min-height:100vh;line-height:1.55}
header{background:rgba(14,12,9,.95);border-bottom:1px solid var(--line);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;flex-wrap:wrap;gap:12px}
.brand{font-family:Georgia,serif;font-size:20px;color:#fff}
.brand span{color:var(--gold-soft);font-size:13px;margin-left:8px}
.actions{display:flex;gap:10px;flex-wrap:wrap}
.btn{padding:10px 18px;border-radius:10px;border:1px solid var(--line);background:rgba(255,255,255,.04);color:#f5efe3;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px;font-family:inherit}
.btn:hover{border-color:var(--gold);color:var(--gold-soft)}
.btn-gold{background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;border:none}
.btn-red{background:rgba(220,60,60,.14);border-color:rgba(220,60,60,.35);color:#ff9a9a}
.layout{display:flex;min-height:calc(100vh - 65px)}
nav.side{width:230px;background:rgba(0,0,0,.25);border-right:1px solid var(--line);padding:16px 0;flex-shrink:0;overflow-y:auto;position:sticky;top:65px;height:calc(100vh - 65px)}
nav.side a{display:block;padding:12px 22px;color:#b9ad9a;font-size:14px;border-left:3px solid transparent;cursor:pointer}
nav.side a:hover{color:#fff;background:rgba(255,255,255,.03)}
nav.side a.active{color:var(--gold-soft);border-left-color:var(--gold);background:rgba(212,175,106,.06)}
main{flex:1;padding:28px 34px;max-width:1100px;overflow-x:hidden}
h2{font-family:Georgia,serif;font-size:26px;color:#fff;margin-bottom:6px}
p.hint{color:#b9ad9a;font-size:13px;margin-bottom:22px}
.field{margin-bottom:16px}
.field label{display:block;color:var(--gold-soft);font-size:11.5px;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:7px;font-weight:600}
.field input,.field textarea{width:100%;padding:11px 14px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.12);border-radius:9px;color:#fff;font-size:14px;font-family:inherit}
.field textarea{resize:vertical;min-height:80px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.item{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:18px;margin-bottom:14px}
.item-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:10px;flex-wrap:wrap}
.item-head strong{color:var(--gold-soft);font-size:13.5px}
.mini{padding:6px 12px;font-size:12px;border-radius:8px}
.img-preview{width:100%;max-width:220px;height:auto;border-radius:10px;border:1px solid var(--line);margin-top:8px;display:block}
.toast{position:fixed;bottom:24px;left:50%;transform:translate(-50%,140%);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;padding:14px 26px;border-radius:12px;font-weight:700;font-size:14px;z-index:9999;transition:transform .4s}
.toast.show{transform:translate(-50%,0)}
.toast.err{background:linear-gradient(135deg,#ff8a8a,#e04a4a);color:#fff}
.drop{display:block;border:2px dashed var(--line);border-radius:12px;padding:22px;text-align:center;color:#b9ad9a;font-size:13px;cursor:pointer;margin-top:8px}
.drop:hover{border-color:var(--gold)}
.status{font-size:12px;padding:6px 12px;border-radius:8px;display:inline-block}
.status.ok{background:rgba(80,200,120,.15);color:#7ee0a0;border:1px solid rgba(80,200,120,.4)}
.status.bad{background:rgba(220,60,60,.15);color:#ff9a9a;border:1px solid rgba(220,60,60,.4)}
@media(max-width:800px){nav.side{position:fixed;left:0;top:65px;bottom:0;transform:translateX(-100%);transition:.3s;z-index:99;width:240px}nav.side.open{transform:none}.row{grid-template-columns:1fr}main{padding:20px 18px}}
</style></head><body>
<header>
  <div style="display:flex;align-items:center;gap:14px">
    <div class="brand">Кухни Островский<span>CMS</span></div>
    <span class="status" id="status"></span>
  </div>
  <div class="actions">
    <a class="btn" href="/" target="_blank">👁 Сайт</a>
    <button class="btn btn-gold" onclick="saveAll()">💾 Сохранить</button>
    <a class="btn btn-red" href="/admin/logout">Выйти</a>
  </div>
</header>
<div class="layout">
  <nav class="side">
    <a data-tab="seo">SEO</a>
    <a data-tab="brand">Бренд</a>
    <a data-tab="hero" class="active">Главный</a>
    <a data-tab="about">О специалисте</a>
    <a data-tab="consult">Консультация</a>
    <a data-tab="works">Работы</a>
    <a data-tab="reviews">Отзывы</a>
    <a data-tab="services">Услуги</a>
    <a data-tab="process">Этапы</a>
    <a data-tab="guarantees">Гарантии</a>
    <a data-tab="cities">Города</a>
    <a data-tab="cta">CTA</a>
    <a data-tab="contacts">Контакты</a>
    <a data-tab="footer">Подвал</a>
  </nav>
  <main id="main"></main>
</div>
<div class="toast" id="toast"></div>
<script>
let DATA=null;
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function toast(m,e){var t=document.getElementById('toast');t.textContent=m;t.classList.toggle('err',!!e);t.classList.add('show');setTimeout(function(){t.classList.remove('show');},2200);}
async function loadData(){var r=await fetch('/admin/api/data',{credentials:'same-origin'});if(r.status===401){location.href='/admin/login';return;}DATA=await r.json();render();checkStatus();}
async function saveAll(){var r=await fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)});if(r.ok){toast('Сохранено');}else{toast('Ошибка',1);}}
function getPath(o,p){return p.split('.').reduce(function(a,k){return a==null?undefined:a[k];},o);}
function setPath(o,p,v){var a=p.split('.');var c=o;for(var i=0;i<a.length-1;i++){var k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k];}c[a[a.length-1]]=v;}
function field(l,p,o){o=o||{};var v=getPath(DATA,p);var i=o.rows?'<textarea data-path="'+p+'" rows="'+o.rows+'">'+esc(v)+'</textarea>':'<input type="text" data-path="'+p+'" value="'+esc(v)+'">';return '<div class="field"><label>'+l+'</label>'+i+'</div>';}
function imgField(l,p){var v=getPath(DATA,p);return '<div class="field"><label>'+l+'</label><input type="text" data-path="'+p+'" value="'+esc(v)+'"><label class="drop">загрузить файл<input type="file" accept="image/*" style="display:none" onchange="uploadImg(this,\''+p+'\')"></label>'+(v?'<img class="img-preview" src="'+esc(v)+'">':'')+'</div>';}
function bindInputs(){document.querySelectorAll('[data-path]').forEach(function(el){el.addEventListener('input',function(){setPath(DATA,el.dataset.path,el.value);});});}
async function uploadImg(inp,p){var f=inp.files[0];if(!f)return;if(f.size>8*1024*1024){toast('>8МБ',1);return;}var fd=new FormData();fd.append('file',f);toast('Загрузка...');var r=await fetch('/admin/api/upload',{method:'POST',body:fd,credentials:'same-origin'});if(!r.ok){toast('Ошибка',1);return;}var j=await r.json();setPath(DATA,p,j.url);toast('OK');render();}
function addItem(p,v){getPath(DATA,p).push(v);render();}
function delItem(p,i){if(!confirm('Удалить?'))return;getPath(DATA,p).splice(i,1);render();}
function moveItem(p,i,d){var a=getPath(DATA,p),j=i+d;if(j<0||j>=a.length)return;var tmp=a[i];a[i]=a[j];a[j]=tmp;render();}
var TABS={};
TABS.seo=function(){return '<h2>SEO</h2>'+field('Title','seo.title',{rows:2})+field('Description','seo.description',{rows:3})+field('Keywords','seo.keywords',{rows:3})+field('OG-картинка','seo.og_image');};
TABS.brand=function(){return '<h2>Бренд</h2><div class="row">'+field('Название','brand.name')+field('Подзаголовок','brand.sub')+'</div>'+imgField('Логотип','brand.logo_url')+'<div class="row">'+field('Телефон','brand.phone')+field('Телефон (tel:)','brand.phone_raw')+'</div><div class="row">'+field('Telegram','brand.telegram')+field('VK','brand.vk')+'</div>';};
TABS.hero=function(){return '<h2>Главный экран</h2>'+field('Надзаголовок','hero.eyebrow')+field('Заголовок до','hero.title_before')+field('Заголовок выделенный','hero.title_em')+field('Подзаголовок','hero.sub',{rows:3})+'<div class="row">'+field('Кнопка 1','hero.btn1')+field('Кнопка 2','hero.btn2')+'</div>'+imgField('Фон','hero.bg');};
TABS.about=function(){return '<h2>О специалисте</h2>'+imgField('Фото','about.photo')+'<div class="row">'+field('Имя','about.name')+field('Должность','about.role')+'</div>'+field('Описание','about.text',{rows:3})+field('Надзаголовок','about.kicker')+field('Заголовок','about.title')+field('Текст','about.body',{rows:4})+imgField('Фон','about.bg');};
TABS.consult=function(){return '<h2>Консультация</h2>'+field('Надзаголовок','consult.kicker')+field('Заголовок','consult.title')+field('Текст','consult.text',{rows:4})+imgField('Фон','consult.bg');};
TABS.works=function(){var items=(DATA.works&&DATA.works.items)||[];return '<h2>Работы</h2>'+field('Надзаголовок','works.kicker')+field('Заголовок','works.title')+field('Подзаголовок','works.subtitle')+imgField('Фон','works.bg')+items.map(function(it,i){return '<div class="item"><div class="item-head"><strong>Фото '+(i+1)+'</strong><div><button class="btn mini" onclick="moveItem(\'works.items\','+i+',-1)">^</button> <button class="btn mini" onclick="moveItem(\'works.items\','+i+',1)">v</button> <button class="btn btn-red mini" onclick="delItem(\'works.items\','+i+')">Удалить</button></div></div>'+imgField('Картинка','works.items.'+i+'.url')+field('Alt','works.items.'+i+'.alt')+'</div>';}).join('')+'<button class="btn" onclick="addItem(\'works.items\',{url:\'\',alt:\'\'})">+ Добавить фото</button>';};
TABS.reviews=function(){var items=(DATA.reviews&&DATA.reviews.items)||[];return '<h2>Отзывы</h2>'+field('Надзаголовок','reviews.kicker')+field('Заголовок','reviews.title')+field('Подзаголовок','reviews.subtitle')+imgField('Фон','reviews.bg')+items.map(function(it,i){return '<div class="item"><div class="item-head"><strong>'+esc(it.name||'')+'</strong><div><button class="btn mini" onclick="moveItem(\'reviews.items\','+i+',-1)">^</button> <button class="btn mini" onclick="moveItem(\'reviews.items\','+i+',1)">v</button> <button class="btn btn-red mini" onclick="delItem(\'reviews.items\','+i+')">Удалить</button></div></div><div class="row">'+field('Имя','reviews.items.'+i+'.name')+field('Подпись','reviews.items.'+i+'.sub')+'</div>'+field('Звёзд','reviews.items.'+i+'.stars')+imgField('Аватар','reviews.items.'+i+'.avatar')+field('Текст','reviews.items.'+i+'.text',{rows:4})+'<div class="row">'+field('Видео URL','reviews.items.'+i+'.video')+field('Постер','reviews.items.'+i+'.video_poster')+'</div></div>';}).join('')+'<button class="btn" onclick="addItem(\'reviews.items\',{name:\'\',sub:\'\',stars:5,avatar:\'\',text:\'\',video:\'\',video_poster:\'\'})">+ Добавить отзыв</button>';};
TABS.services=function(){var items=(DATA.services&&DATA.services.items)||[];return '<h2>Услуги</h2>'+field('Надзаголовок','services.kicker')+field('Заголовок','services.title')+field('Подзаголовок','services.subtitle')+imgField('Фон','services.bg')+items.map(function(it,i){return '<div class="item"><div class="item-head"><strong>'+esc(it.title||'')+'</strong><button class="btn btn-red mini" onclick="delItem(\'services.items\','+i+')">Удалить</button></div>'+field('Название','services.items.'+i+'.title')+field('Описание','services.items.'+i+'.text',{rows:2})+field('SVG icon','services.items.'+i+'.icon')+'</div>';}).join('')+'<button class="btn" onclick="addItem(\'services.items\',{title:\'\',text:\'\',icon:\'\'})">+ Добавить</button>';};
TABS.process=function(){var items=(DATA.process&&DATA.process.items)||[];return '<h2>Этапы</h2>'+field('Надзаголовок','process.kicker')+field('Заголовок','process.title')+imgField('Фон','process.bg')+items.map(function(it,i){return '<div class="item"><div class="item-head"><strong>'+esc(it.n||'')+' '+esc(it.title||'')+'</strong><button class="btn btn-red mini" onclick="delItem(\'process.items\','+i+')">Удалить</button></div><div class="row">'+field('Номер','process.items.'+i+'.n')+field('Заголовок','process.items.'+i+'.title')+'</div>'+field('Текст','process.items.'+i+'.text',{rows:2})+'</div>';}).join('')+'<button class="btn" onclick="addItem(\'process.items\',{n:\'\',title:\'\',text:\'\'})">+ Добавить</button>';};
TABS.guarantees=function(){var items=(DATA.guarantees&&DATA.guarantees.items)||[];return '<h2>Гарантии</h2>'+field('Надзаголовок','guarantees.kicker')+field('Заголовок','guarantees.title')+imgField('Фон','guarantees.bg')+items.map(function(it,i){return '<div class="item"><div class="item-head"><strong>'+esc(it.title||'')+'</strong><button class="btn btn-red mini" onclick="delItem(\'guarantees.items\','+i+')">Удалить</button></div>'+field('Заголовок','guarantees.items.'+i+'.title')+field('Текст','guarantees.items.'+i+'.text',{rows:2})+field('SVG icon','guarantees.items.'+i+'.icon')+'</div>';}).join('')+'<button class="btn" onclick="addItem(\'guarantees.items\',{title:\'\',text:\'\',icon:\'\'})">+ Добавить</button>';};
TABS.cities=function(){var items=(DATA.cities&&DATA.cities.items)||[];return '<h2>Города</h2>'+field('Надзаголовок','cities.kicker')+field('Заголовок','cities.title')+field('Подзаголовок','cities.subtitle')+imgField('Фон','cities.bg')+items.map(function(it,i){return '<div class="item"><div class="item-head"><strong>'+esc(it.name||'')+'</strong><button class="btn btn-red mini" onclick="delItem(\'cities.items\','+i+')">Удалить</button></div>'+field('Название','cities.items.'+i+'.name')+field('Описание','cities.items.'+i+'.text',{rows:2})+'</div>';}).join('')+'<button class="btn" onclick="addItem(\'cities.items\',{name:\'\',text:\'\'})">+ Добавить</button>';};
TABS.cta=function(){return '<h2>CTA</h2>'+field('Заголовок','cta.title')+field('Текст','cta.text',{rows:3})+field('Кнопка','cta.button')+imgField('Фон','cta.bg');};
TABS.contacts=function(){return '<h2>Контакты</h2>'+field('Надзаголовок','contacts.kicker')+field('Заголовок','contacts.title')+field('Подзаголовок','contacts.subtitle',{rows:2})+field('Регионы','contacts.regions')+imgField('Фон','contacts.bg');};
TABS.footer=function(){return '<h2>Подвал</h2>'+field('Строка','footer.line')+field('Копирайт','footer.copyright');};
function render(){var a=document.querySelector('nav.side a.active');var tab=a?a.dataset.tab:'hero';document.getElementById('main').innerHTML=(TABS[tab]||function(){return '<h2>Раздел</h2>';})();bindInputs();}
document.querySelectorAll('nav.side a').forEach(function(x){x.addEventListener('click',function(){document.querySelectorAll('nav.side a').forEach(function(y){y.classList.remove('active');});x.classList.add('active');render();document.querySelector('nav.side').classList.remove('open');});});
async function checkStatus(){try{var r=await fetch('/admin/api/data',{credentials:'same-origin'});var el=document.getElementById('status');if(r.ok){el.className='status ok';el.textContent='Supabase OK';}else{el.className='status bad';el.textContent='Нет связи';}}catch(e){var el=document.getElementById('status');el.className='status bad';el.textContent='Ошибка';}}
loadData();
</script></body></html>"""


# =====================================================================
# HTTP СЕРВЕР
# =====================================================================
def parse_multipart(body, boundary):
    parts = body.split(b"--" + boundary)
    for p in parts:
        if b"Content-Disposition" not in p:
            continue
        head, _, data = p.partition(b"\r\n\r\n")
        if not data: continue
        data = data.rstrip(b"\r\n--")
        if b'name="file"' in head:
            return data, b"application/octet-stream", "file"
    return None, None, None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cookie_token(self):
        raw = self.headers.get("Cookie", "")
        if not raw: return None
        try:
            c = SimpleCookie(); c.load(raw)
            m = c.get("admin_session")
            return m.value if m else None
        except Exception:
            return None

    def _is_admin(self):
        return _check_session(self._cookie_token())

    def _send(self, code, body, ctype="text/plain; charset=utf-8", cache="no-cache", gzip_ok=True):
        data = body.encode("utf-8") if isinstance(body, str) else body
        etag = '"' + hashlib.sha256(data).hexdigest()[:20] + '"'
        if code == 200 and self.headers.get("If-None-Match") == etag:
            self.send_response(304); self.send_header("ETag", etag); self.send_header("Cache-Control", cache); self.end_headers(); return
        accept_encoding = self.headers.get("Accept-Encoding", "")
        if gzip_ok and isinstance(body, str) and "gzip" in accept_encoding and len(data) > 700:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz: gz.write(data)
            data = buf.getvalue()
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Encoding", "gzip"); self.send_header("Vary", "Accept-Encoding")
        else:
            self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag); self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers(); self.wfile.write(data)

    def _redirect(self, location, set_cookie=None):
        self.send_response(302); self.send_header("Location", location); self.send_header("Cache-Control", "no-cache")
        if set_cookie: self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", "0"); self.end_headers()

    def _read_body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n <= 0 or n > MAX_UPLOAD * 3: return b""
        return self.rfile.read(n)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def _serve_static(self, path):
        import mimetypes
        safe = path.lstrip("/")
        if not safe or ".." in safe or safe.startswith("."): return False
        allowed = {".html", ".txt", ".svg", ".png", ".jpg", ".jpeg", ".ico", ".xml", ".webmanifest", ".json", ".css", ".js", ".webp", ".gif"}
        ext = os.path.splitext(safe)[1].lower()
        if ext not in allowed: return False
        full = os.path.join(ROOT, safe)
        if not os.path.isfile(full): return False
        mime, _ = mimetypes.guess_type(full)
        mime = mime or "application/octet-stream"
        try:
            with open(full, "rb") as f: data = f.read()
        except Exception:
            return False
        self._send(200, data, mime, "public, max-age=3600", gzip_ok=False)
        return True

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/admin/login":
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", ""), "text/html; charset=utf-8"); return
        if path == "/admin/logout":
            _drop_session(self._cookie_token())
            self._redirect("/admin/login", "admin_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"); return
        if path == "/admin/api/data":
            if not self._is_admin(): self._json({"error": "unauthorized"}, 401); return
            self._json(load_data(force=True)); return
        if path == "/admin":
            if not self._is_admin(): self._redirect("/admin/login"); return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8"); return
        if path not in ("/", "/index.html"):
            if self._serve_static(path): return
        if path in ("/", "/index.html"):
            self._send(200, render_page(), "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, SITEMAP, "application/xml; charset=utf-8", "public, max-age=3600")
        elif path == "/favicon.ico":
            data = get_favicon()
            if not data: self._redirect(FAVICON_URL)
            elif _icons_cache["ico"]: self._send(200, _icons_cache["ico"], "image/x-icon", "public, max-age=86400", gzip_ok=False)
            else: self._send(200, data, "image/x-icon", "public, max-age=86400", gzip_ok=False)
        elif path == "/favicon-16x16.png":
            if _icons_cache["png16"]: self._send(200, _icons_cache["png16"], "image/png", "public, max-age=86400", gzip_ok=False)
            else: self._redirect(FAVICON_URL)
        elif path == "/favicon-32x32.png":
            if _icons_cache["png32"]: self._send(200, _icons_cache["png32"], "image/png", "public, max-age=86400", gzip_ok=False)
            else: self._redirect(FAVICON_URL)
        elif path == "/apple-touch-icon.png":
            if _icons_cache["png180"]: self._send(200, _icons_cache["png180"], "image/png", "public, max-age=86400", gzip_ok=False)
            else: self._redirect(FAVICON_URL)
        elif path == "/manifest.webmanifest":
            self._send(200, MANIFEST, "application/manifest+json; charset=utf-8", "public, max-age=3600")
        else:
            self._send(404, PAGE_404, "text/html; charset=utf-8", "no-cache")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/admin/login":
            body = self._read_body().decode("utf-8", "ignore")
            p = parse_qs(body)
            login = (p.get("login") or [""])[0]
            password = (p.get("password") or [""])[0]
            if login == ADMIN_LOGIN_ENV and password == ADMIN_PASSWORD_ENV:
                token = _new_session()
                self._redirect("/admin", "admin_session=" + token + "; Path=/; Max-Age=" + str(SESSION_TTL) + "; HttpOnly; SameSite=Lax")
            else:
                html = ADMIN_LOGIN_HTML.replace("__ERROR__", '<div class="err">Неверный логин или пароль</div>')
                self._send(200, html, "text/html; charset=utf-8")
            return
        if path == "/admin/api/save":
            if not self._is_admin(): self._json({"error": "unauthorized"}, 401); return
            try: obj = json.loads(self._read_body().decode("utf-8"))
            except Exception: self._json({"error": "bad json"}, 400); return
            ok = save_data(obj); self._json({"ok": ok}); return
        if path == "/admin/api/upload":
            if not self._is_admin(): self._json({"error": "unauthorized"}, 401); return
            body = self._read_body()
            ctype = self.headers.get("Content-Type", "")
            fb = None
            if "multipart/form-data" in ctype:
                m = re.search(r'boundary=([^;]+)', ctype)
                if m: fb, _, _ = parse_multipart(body, m.group(1).strip().strip('"').encode())
            if not fb: self._json({"error": "no file"}, 400); return
            if len(fb) > MAX_UPLOAD: self._json({"error": "too big"}, 413); return
            mime = "image/jpeg"
            if fb[:8] == b"\x89PNG\r\n\x1a\n": mime = "image/png"
            elif fb[:6] in (b"GIF87a", b"GIF89a"): mime = "image/gif"
            elif fb[:4] == b"RIFF" and fb[8:12] == b"WEBP": mime = "image/webp"
            elif fb[:4] == b"<svg" or fb[:5] == b"<?xml": mime = "image/svg+xml"
            data_url = "data:" + mime + ";base64," + base64.b64encode(fb).decode("ascii")
            self._json({"url": data_url}); return
        self._json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("BOOT: старт приложения", flush=True)
    print("BOOT: PORT = " + str(PORT), flush=True)
    print("BOOT: SUPABASE_LIB = " + str(_SUPABASE_LIB), flush=True)
    print("BOOT: SUPABASE_URL = " + SUPABASE_URL, flush=True)

    if _SUPABASE_LIB and SUPABASE_URL:
        try:
            load_data(force=True)
            print("BOOT: Supabase OK", flush=True)
        except Exception as e:
            print("BOOT: Supabase error: " + str(e), flush=True)
    else:
        print("BOOT: Supabase отключён — работаем на дефолтах", flush=True)

    try:
        server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
        print("BOOT: слушаем http://0.0.0.0:" + str(PORT), flush=True)
        print("BOOT: админка http://0.0.0.0:" + str(PORT) + "/admin", flush=True)
        server.serve_forever()
    except Exception as e:
        print("BOOT: FATAL — не смог занять порт: " + str(e), flush=True)
        raise
