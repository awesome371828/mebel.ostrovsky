# -*- coding: utf-8 -*-
"""
mebel.py — сайт «Кухни Островский».

Эндпоинты:
  GET /                       — страница сайта
  GET /robots.txt             — правила для поисковиков
  GET /sitemap.xml            — карта сайта (с изображениями)
  GET /favicon.ico            — настоящий ICO-фавикон (аватарка)
  GET /favicon-16x16.png      — PNG 16px
  GET /favicon-32x32.png      — PNG 32px
  GET /apple-touch-icon.png   — иконка для iOS
  GET /manifest.webmanifest   — манифест
  (любой другой путь)         — красивая страница 404
"""
import gzip
import hashlib
import io
import os
import time
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8080"))
DOMAIN = "https://кухниостровский.рф"

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
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;background:#0e0c09;color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center}
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

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ</title>
<meta name="description" content="Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и 3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97">
<meta name="keywords" content="кухни остров, кухни островский, кухни островского, кухни островский ростов, кухни ростов островский, кухни батайск островский, кухни азов островский, кухни на заказ ростов, кухни на заказ батайск, кухни на заказ азов, мебель островского, мебель на заказ ростов, корпусная мебель, шкафы купе, гардеробные, прихожие, кухни под ключ, мебель островский">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="geo.region" content="RU-ROS">
<meta name="geo.placename" content="Ростов-на-Дону">
<meta name="geo.position" content="47.2357;39.7015">
<meta name="ICBM" content="47.2357, 39.7015">
<meta name="theme-color" content="#0e0c09">
<meta name="msapplication-TileColor" content="#0e0c09">
<link rel="canonical" href="https://кухниостровский.рф/">
<link rel="alternate" hreflang="ru" href="https://кухниостровский.рф/">
<link rel="alternate" hreflang="x-default" href="https://кухниостровский.рф/">
<meta name="yandex-verification" content="f7e96d07aee79bf3">
<meta name="google-site-verification" content="dNSAELu64Y7aK5sjz_zpmhoz6YKn2PIZ03UKPwrgnCI">
<link rel="shortcut icon" href="/favicon.ico">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/jpeg" sizes="any" href="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="apple-touch-icon" sizes="any" href="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0">
<meta name="msapplication-TileImage" content="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Кухни Островский">
<meta property="og:url" content="https://кухниостровский.рф/">
<meta property="og:title" content="Кухни Островский — кухни на заказ в Ростове, Батайске и Азове">
<meta property="og:description" content="Кухни и корпусная мебель под ключ. Бесплатный замер и 3D-проект, собственное производство, монтаж. ☎ +7 (950) 846-53-97">
<meta property="og:image" content="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0">
<meta property="og:image:width" content="1254">
<meta property="og:image:height" content="1254">
<meta property="og:image:alt" content="Кухни Островский — кухни на заказ в Ростове, Батайске и Азове">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Кухни Островский — кухни на заказ в Ростове, Батайске и Азове">
<meta name="twitter:description" content="Кухни и корпусная мебель под ключ. Бесплатный замер и 3D-проект. ☎ +7 (950) 846-53-97">
<meta name="twitter:image" content="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0">
<script type="application/ld+json">
[
{
  "@context": "https://schema.org",
  "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
  "@id": "https://кухниостровский.рф/#business",
  "name": "Кухни Островский",
  "alternateName": "Кухни Островский — мебель на заказ в Ростове, Батайске и Азове",
  "url": "https://кухниостровский.рф/",
  "logo": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0",
  "image": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0",
  "description": "Кухни и корпусная мебель на заказ в Ростове, Батайске и Азове. Полный цикл под ключ: замер, проект, производство, монтаж.",
  "telephone": "+79508465397",
  "priceRange": "₽₽",
  "currenciesAccepted": "RUB",
  "address": {"@type": "PostalAddress", "addressLocality": "Ростов-на-Дону", "addressRegion": "Ростовская область", "addressCountry": "RU"},
  "geo": {"@type": "GeoCoordinates", "latitude": 47.2357, "longitude": 39.7015},
  "areaServed": [
    {"@type": "City", "name": "Ростов-на-Дону"},
    {"@type": "City", "name": "Батайск"},
    {"@type": "City", "name": "Азов"}
  ],
  "sameAs": ["https://vk.com/mebel.ostrovsky", "https://t.me/fanny161"],
  "contactPoint": {"@type": "ContactPoint", "telephone": "+79508465397", "contactType": "customer service", "availableLanguage": "Russian"}
},
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://кухниостровский.рф/#website",
  "url": "https://кухниостровский.рф/",
  "name": "Кухни Островский",
  "inLanguage": "ru-RU",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://кухниостровский.рф/?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
},
{
  "@context": "https://schema.org",
  "@type": "ContactPage",
  "@id": "https://кухниостровский.рф/#contacts",
  "url": "https://кухниостровский.рф/#contacts",
  "name": "Контакты — Кухни Островский",
  "inLanguage": "ru-RU",
  "mainEntity": {"@id": "https://кухниостровский.рф/#business"}
},
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "https://кухниостровский.рф/#page",
  "url": "https://кухниостровский.рф/",
  "name": "Кухни Островский — кухни на заказ в Ростове, Батайске и Азове",
  "inLanguage": "ru-RU",
  "isPartOf": {"@id": "https://кухниостровский.рф/#website"},
  "about": {"@id": "https://кухниостровский.рф/#business"}
}
]
</script>
<link rel="preconnect" href="https://sun9-70.vkuserphoto.ru">
<link rel="preconnect" href="https://sun9-20.vkuserphoto.ru">
<link rel="preconnect" href="https://i.ibb.co">

<style>
:root{
  --bg:#0e0c09;
  --gold:#d4af6a;
  --gold-soft:#eccfa0;
  --gold-deep:#a37c3f;
  --text:#f5efe3;
  --muted:#b9ad9a;
  --line:rgba(212,175,106,.14);
  --line-strong:rgba(236,207,160,.38);
  --r-lg:24px;--r-md:16px;--r-sm:12px;
  --shadow-lg:0 34px 80px rgba(0,0,0,.5);
  --shadow-md:0 18px 46px rgba(0,0,0,.36);
  --shadow-gold:0 16px 42px rgba(212,175,106,.26);
  --serif:Georgia,'Times New Roman',serif;
  --sans:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;overflow-x:hidden}
body{overflow-x:hidden}
section{scroll-margin-top:88px}
body{font-family:var(--sans);color:var(--text);background:
radial-gradient(1100px 680px at 88% -8%,rgba(212,175,106,.12),transparent 62%),
radial-gradient(880px 560px at -12% 26%,rgba(212,175,106,.06),transparent 56%),
radial-gradient(1200px 760px at 50% 118%,rgba(163,124,63,.11),transparent 60%),
linear-gradient(180deg,#0e0c09,#0b0907 55%,#0e0b08);
line-height:1.72;-webkit-font-smoothing:antialiased}
body::after{content:"";position:fixed;inset:0;z-index:9998;pointer-events:none;opacity:.035;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E")}
::selection{background:rgba(212,175,106,.32);color:#fff}
h1,h2,h3{font-family:var(--serif);overflow-wrap:break-word;word-break:break-word;letter-spacing:.3px}
img{max-width:100%;display:block}
a{text-decoration:none;color:inherit}
ul{list-style:none}
button{font-family:inherit;cursor:pointer}
.wrap{width:100%;max-width:1180px;margin:0 auto;padding:0 20px}
.progress{position:fixed;top:0;left:0;height:3px;z-index:300;background:linear-gradient(90deg,var(--gold-deep),var(--gold-soft),var(--gold));width:0%;box-shadow:0 0 14px rgba(236,207,160,.7)}
header{position:fixed;top:0;left:0;right:0;z-index:200;background:rgba(14,12,9,.55);backdrop-filter:blur(18px) saturate(150%);-webkit-backdrop-filter:blur(18px) saturate(150%);transition:transform .45s cubic-bezier(.22,.61,.36,1),background .45s}
header.solid{background:rgba(14,12,9,.92);box-shadow:0 12px 44px rgba(0,0,0,.45),inset 0 -1px 0 var(--line)}
header.hide{transform:translateY(-100%)}
.nav{display:flex;align-items:center;justify-content:space-between;height:76px;gap:12px}
.logo{display:flex;align-items:center;gap:13px;min-width:0;max-width:100%;cursor:pointer;transition:opacity .3s}
.logo:hover{opacity:.86}
.logo .brand-ava{width:46px;height:46px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 5px rgba(212,175,106,.1),0 0 24px rgba(212,175,106,.4);flex-shrink:0;animation:logoPulse 4.5s ease-in-out infinite}
@keyframes logoPulse{0%,100%{box-shadow:0 0 0 5px rgba(212,175,106,.1),0 0 24px rgba(212,175,106,.4)}50%{box-shadow:0 0 0 7px rgba(212,175,106,.18),0 0 40px rgba(212,175,106,.65)}}
.logo .brand-txt{display:flex;flex-direction:column;min-width:0;line-height:1.15}
.logo .brand-txt .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:var(--serif);font-size:25px;font-weight:600;color:#fff;line-height:1.05;background:linear-gradient(120deg,#fff,var(--gold-soft));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:.3px}
.logo .brand-txt .sub{color:var(--gold-soft);font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:62vw;margin-top:3px;opacity:.85}
.menu{position:fixed;top:0;height:76px;right:max(20px,calc((100vw - 1220px)/2));display:flex;gap:24px;align-items:center;z-index:201}
.menu a{position:relative;color:rgba(255,255,255,.8);font-size:13px;font-weight:600;letter-spacing:.5px;transition:.3s;padding:6px 0;white-space:nowrap;min-height:40px;display:inline-flex;align-items:center}
.menu a::after{content:"";position:absolute;left:0;bottom:0;width:100%;height:1.5px;background:linear-gradient(90deg,var(--gold-soft),var(--gold));transform:scaleX(0);transform-origin:left;transition:transform .4s cubic-bezier(.22,.61,.36,1);border-radius:2px}
.menu a:hover{color:#fff}
.menu a:hover::after{transform:scaleX(1)}
.menu a.active{color:var(--gold-soft)}
.menu a.active::after{transform:scaleX(1)}
.menu-call{display:none}
.burger{display:none;background:none;border:none;cursor:pointer;width:44px;height:44px;position:relative;z-index:210;flex-shrink:0}
.burger span{position:absolute;left:8px;right:8px;height:2px;background:#fff;transition:.3s;border-radius:2px}
.burger span:nth-child(1){top:13px}
.burger span:nth-child(2){top:21px}
.burger span:nth-child(3){top:29px}
.burger.open span:nth-child(1){top:21px;transform:rotate(45deg)}
.burger.open span:nth-child(2){opacity:0}
.burger.open span:nth-child(3){top:21px;transform:rotate(-45deg)}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.5);opacity:0;visibility:hidden;transition:.35s;z-index:195;backdrop-filter:blur(3px)}
.scrim.show{opacity:1;visibility:visible}
.panel{position:relative;min-height:100vh;display:flex;align-items:center;padding:140px 0;overflow:hidden}
.panel .bg{position:absolute;inset:-14% 0;z-index:0;background-size:cover;background-position:center;will-change:transform;transform:translateZ(0)}
.panel .bg::after{content:"";position:absolute;inset:0;background:linear-gradient(to right,rgba(10,8,6,.94) 22%,rgba(10,8,6,.6) 58%,rgba(10,8,6,.75))}
.panel .content{position:relative;z-index:2;width:100%;will-change:transform;transform:translateZ(0)}
.panel--center .content{text-align:center}
.panel--center .bg::after{background:linear-gradient(180deg,rgba(10,8,6,.86),rgba(10,8,6,.62))}
.panel--dark .bg::after{background:linear-gradient(180deg,rgba(10,8,6,.9),rgba(10,8,6,.7))}
.panel + .panel{margin-top:18px}
.panel + .panel::before{content:"";position:absolute;top:-9px;left:50%;transform:translateX(-50%);width:74px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);z-index:6}
.panel + .panel::after{content:"";position:absolute;top:-13px;left:50%;transform:translateX(-50%) rotate(45deg);width:7px;height:7px;background:var(--gold);box-shadow:0 0 12px rgba(212,175,106,.55);z-index:6}
.water{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);z-index:1;font-family:var(--serif);font-size:clamp(90px,22vw,300px);font-weight:700;color:transparent;-webkit-text-stroke:1px rgba(212,175,106,.09);white-space:nowrap;pointer-events:none;user-select:none;line-height:1}
.eyebrow{display:inline-flex;align-items:center;gap:12px;color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:12px;font-weight:600;margin-bottom:20px}
.eyebrow::before{content:"";width:42px;height:1px;background:linear-gradient(90deg,transparent,var(--gold))}
.eyebrow::after{content:"";width:42px;height:1px;background:linear-gradient(90deg,var(--gold),transparent)}
h1{font-size:clamp(34px,6vw,76px);font-weight:500;line-height:1.08;color:#fff;letter-spacing:.4px;text-shadow:0 5px 30px rgba(0,0,0,.5);overflow-wrap:break-word;word-break:break-word;max-width:100%}
h1 em{font-style:italic}
.sub{color:rgba(245,239,227,.9);font-size:clamp(16px,1.8vw,19.5px);font-weight:300;margin:24px 0 34px;max-width:580px;text-shadow:0 2px 16px rgba(0,0,0,.55);letter-spacing:.3px}
.btn-row{display:flex;gap:16px;flex-wrap:wrap}
.btn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:10px;padding:16px 30px;min-height:52px;font-size:13px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;transition:transform .4s cubic-bezier(.22,.61,.36,1),box-shadow .4s,filter .4s,background .4s,color .4s;border-radius:13px;border:none}
.btn-solid{background:linear-gradient(135deg,var(--gold-soft),var(--gold) 55%,var(--gold-deep));color:#17120b;box-shadow:var(--shadow-gold);animation:btnGlow 3.6s ease-in-out infinite}
.btn-solid:hover{transform:translateY(-4px);box-shadow:0 26px 60px rgba(212,175,106,.45)}
.btn-line{border:1px solid rgba(255,255,255,.4);color:#fff;background:rgba(255,255,255,.04);backdrop-filter:blur(8px)}
.btn-line:hover{background:rgba(255,255,255,.12);color:#fff;transform:translateY(-4px);box-shadow:0 20px 50px rgba(0,0,0,.35)}
.btn::after{content:"";position:absolute;top:0;left:-130%;width:55%;height:100%;background:linear-gradient(120deg,transparent,rgba(255,255,255,.4),transparent);transform:skewX(-20deg);transition:left .7s ease}
.btn:hover::after{left:145%}
@keyframes btnGlow{0%,100%{box-shadow:0 16px 42px rgba(212,175,106,.26)}50%{box-shadow:0 24px 62px rgba(236,207,160,.5)}}
.shimmer{background:linear-gradient(90deg,var(--gold-soft),#fff 35%,var(--gold-soft) 70%);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerMove 3.4s linear infinite}
@keyframes shimmerMove{0%{background-position:0% center}100%{background-position:-220% center}}
h1 em.shimmer{-webkit-text-fill-color:transparent}
.cta h2.shimmer{-webkit-text-fill-color:transparent}
.kenburns .bg{animation:kenburns 24s ease-in-out infinite alternate}
@keyframes kenburns{0%{transform:scale(1) translateZ(0)}100%{transform:scale(1.12) translateZ(0)}}
.scroll-cue{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);z-index:5;color:rgba(255,255,255,.75);font-size:11px;letter-spacing:4px;text-transform:uppercase;text-align:center;animation:fadeInUp 1s ease .8s both}
.scroll-cue .line{width:1px;height:46px;background:linear-gradient(180deg,var(--gold-soft),transparent);margin:10px auto 0;animation:drip 2.4s infinite}
@keyframes drip{0%{transform:scaleY(0);transform-origin:top}50%{transform:scaleY(1);transform-origin:top}51%{transform-origin:bottom}100%{transform:scaleY(0);transform-origin:bottom}}
@keyframes fadeInUp{from{opacity:0;transform:translate(-50%,10px)}to{opacity:1;transform:translate(-50%,0)}}
.sec-head{max-width:740px;margin:0 auto 50px;text-align:center}
.sec-head .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.sec-head h2{position:relative;font-size:clamp(30px,4.4vw,48px);font-weight:500;margin:16px 0 14px;line-height:1.14;color:#faf3e6;text-shadow:0 4px 22px rgba(0,0,0,.45),0 0 34px rgba(212,175,106,.12);letter-spacing:.3px}
.sec-head h2::before,.sec-head h2::after{content:"";position:absolute;top:50%;width:56px;height:1px;background:linear-gradient(90deg,transparent,var(--gold));transform:translateY(-50%);opacity:.7}
.sec-head h2::before{right:calc(100% + 26px)}
.sec-head h2::after{left:calc(100% + 26px)}
.sec-head p{color:var(--muted);font-size:15.5px;max-width:620px;margin:0 auto;letter-spacing:.2px}
h2.k{position:relative;font-size:clamp(32px,4.6vw,48px);color:#faf3e6;font-weight:500;margin:16px 0 14px;text-align:center;text-shadow:0 4px 22px rgba(0,0,0,.45);letter-spacing:.3px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;text-align:center}
.stat{padding:30px 16px;border-radius:var(--r-md);background:linear-gradient(165deg,rgba(255,255,255,.05),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.07);transition:.45s}
.stat:hover{transform:translateY(-6px);border-color:rgba(236,207,160,.3);box-shadow:0 22px 54px rgba(0,0,0,.42),0 0 34px rgba(212,175,106,.05)}
.stat .num{font-family:var(--serif);font-size:58px;font-weight:500;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold) 60%,var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 5px 16px rgba(212,175,106,.35))}
.stat .lbl{color:var(--muted);font-size:13.5px;margin-top:12px;letter-spacing:.3px}
.about{display:grid;grid-template-columns:1fr 1.1fr;gap:64px;align-items:center}
.about-card{background:linear-gradient(165deg,rgba(255,255,255,.055),rgba(255,255,255,.015));border:1px solid rgba(255,255,255,.07);padding:48px 40px;text-align:center;border-radius:var(--r-lg);box-shadow:var(--shadow-md);position:relative;overflow:hidden}
.about-card::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.6}
.avatar{width:130px;height:130px;border-radius:50%;margin:0 auto 22px;overflow:hidden;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 7px rgba(212,175,106,.12),0 16px 40px rgba(0,0,0,.5);position:relative}
.avatar img{width:100%;height:100%;object-fit:cover}
.about-card h3{font-size:29px;color:#fff;letter-spacing:.3px}
.about-card .role{color:var(--gold-soft);font-size:13px;margin-top:5px;letter-spacing:.7px}
.about-card .sep{width:52px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:22px auto}
.about-card p{color:var(--muted);font-size:14.5px;line-height:1.76}
.about-body .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.about-body h2{font-size:clamp(30px,3.6vw,44px);font-weight:500;margin:16px 0 22px;line-height:1.14;color:#faf3e6;text-shadow:0 4px 22px rgba(0,0,0,.45);letter-spacing:.3px}
.about-body p{color:var(--muted);font-size:15.5px;margin-bottom:26px;letter-spacing:.2px}
.features{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.features li{position:relative;padding-left:36px;color:var(--text);font-size:14.5px;overflow-wrap:break-word;transition:transform .3s;letter-spacing:.2px;min-height:28px;display:flex;align-items:center}
.features li:hover{transform:translateX(5px)}
.features li::before{content:"";position:absolute;left:0;top:50%;transform:translateY(-50%);width:18px;height:18px;border:1.5px solid rgba(212,175,106,.6);border-radius:50%;background:rgba(212,175,106,.08)}
.features li::after{content:"✓";position:absolute;left:4px;top:50%;transform:translateY(-50%);font-size:11px;color:var(--gold-soft);font-weight:800}
.consult .phone{display:inline-block;font-family:var(--sans);font-weight:800;font-size:clamp(30px,4.4vw,52px);letter-spacing:1px;margin-top:12px;white-space:nowrap;background:linear-gradient(120deg,var(--gold-soft),var(--gold));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 7px 22px rgba(212,175,106,.35))}
.consult p{color:var(--muted);font-size:15.5px;margin:30px auto 0;max-width:630px;line-height:1.82;overflow-wrap:break-word;letter-spacing:.2px}
.carousel{position:relative;max-width:1120px;margin:0 auto}
.car-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain;padding:12px 8px 24px;scrollbar-width:none}
.car-track::-webkit-scrollbar{display:none}
.swipe-hint{display:none;text-align:center;color:var(--muted);font-size:12px;letter-spacing:2px;text-transform:uppercase;margin:-6px 0 10px;animation:fadeSoft 2s ease both}
@keyframes fadeSoft{from{opacity:0}to{opacity:1}}
.car-nav{position:absolute;top:38%;transform:translateY(-50%);width:48px;height:48px;border-radius:50%;background:rgba(14,12,9,.68);backdrop-filter:blur(10px);border:1px solid rgba(236,207,160,.35);color:var(--gold-soft);font-size:21px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.4s;z-index:5;box-shadow:var(--shadow-md)}
.car-nav:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-50%) scale(1.08)}
.car-prev{left:-16px}.car-next{right:-16px}
.car-dots{display:flex;justify-content:center;gap:8px;margin-top:12px;flex-wrap:wrap;min-height:10px}
.car-dot{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.2);cursor:pointer;transition:.35s;border:none;padding:0}
.car-dot:hover{background:rgba(236,207,160,.55)}
.car-dot.active{width:28px;border-radius:5px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));box-shadow:0 0 12px rgba(236,207,160,.6)}
.car-slide{flex:0 0 auto;width:min(78vw,440px);scroll-snap-align:center;border-radius:var(--r-lg);overflow:hidden;border:1px solid rgba(255,255,255,.08);background:linear-gradient(120deg,rgba(255,255,255,.045),rgba(255,255,255,.01));cursor:zoom-in;transition:transform .5s cubic-bezier(.22,.61,.36,1),box-shadow .5s,border-color .5s;box-shadow:var(--shadow-md);position:relative;transform-style:preserve-3d;will-change:transform}
.car-slide:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.3);box-shadow:var(--shadow-lg)}
.car-slide img{width:100%;height:300px;object-fit:cover;display:block;transition:transform .7s ease,opacity .6s ease;opacity:0}
.car-slide img.loaded{opacity:1}
.car-slide.loaded-img{background:linear-gradient(120deg,rgba(255,255,255,.045),rgba(255,255,255,.01))}
.car-slide:hover img{transform:scale(1.07)}
.rev-track{align-items:flex-start}
.rev-card{scroll-snap-align:center;background:linear-gradient(160deg,rgba(255,255,255,.05),rgba(255,255,255,.012));border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);padding:24px 26px;width:min(82vw,520px);flex:0 0 auto;display:flex;flex-direction:column;box-shadow:var(--shadow-md);position:relative;overflow:hidden;transition:transform .5s,box-shadow .5s,border-color .5s}
.rev-card:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.28);box-shadow:var(--shadow-lg)}
.rev-card::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.75}
.rev-head{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.rev-ava{width:50px;height:50px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.6);box-shadow:0 0 0 4px rgba(212,175,106,.1),0 0 14px rgba(212,175,106,.32);flex-shrink:0;opacity:0;transition:opacity .6s}
.rev-ava.loaded{opacity:1}
.rev-name{color:#fff;font-weight:700;font-size:14.5px}
.rev-sub{color:var(--muted);font-size:11px;margin-top:2px}
.rev-stars{color:var(--gold-soft);letter-spacing:3px;font-size:14px;margin-left:auto;white-space:nowrap;text-shadow:0 0 14px rgba(236,207,160,.45)}
.rev-text{color:#ece2cd;font-size:13.5px;line-height:1.66;font-weight:300;text-align:left;overflow-wrap:break-word;word-break:break-word;letter-spacing:.1px}
.rev-video{margin-top:14px;border-radius:var(--r-md);overflow:hidden;border:1px solid rgba(255,255,255,.08);box-shadow:var(--shadow-md);position:relative}
.rev-video iframe{width:100%;height:250px;border:0;display:block}
.video-box{position:relative;max-width:860px;margin:0 auto;border-radius:var(--r-lg);overflow:hidden;border:1px solid var(--line-strong);box-shadow:var(--shadow-lg);cursor:pointer;background:#000}
.video-box img{width:100%;height:430px;object-fit:cover;opacity:.85;transition:opacity .5s,transform 1s ease}
.video-box:hover img{opacity:1;transform:scale(1.03)}
.video-play{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:78px;height:78px;border-radius:50%;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 10px rgba(212,175,106,.2),var(--shadow-gold);transition:transform .4s,box-shadow .4s;font-size:0}
.video-play::after{content:"";width:0;height:0;border-left:18px solid #17120b;border-top:11px solid transparent;border-bottom:11px solid transparent;margin-left:4px}
.video-box:hover .video-play{transform:translate(-50%,-50%) scale(1.12);box-shadow:0 0 0 16px rgba(212,175,106,.16),var(--shadow-gold)}
.video-box iframe{width:100%;height:430px;border:0;display:block}
.video-note{max-width:680px;margin:22px auto 0;color:var(--muted);font-size:15px;text-align:center;line-height:1.7;letter-spacing:.2px}
.video-note b{color:var(--gold-soft)}
.svc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.svc{position:relative;background:linear-gradient(160deg,rgba(255,255,255,.045),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.07);padding:36px 30px;transition:.5s cubic-bezier(.22,.61,.36,1);border-radius:var(--r-lg);overflow-wrap:break-word;overflow:hidden}
.svc::before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;background:linear-gradient(120deg,var(--gold-soft),transparent 35%,transparent 65%,var(--gold-soft));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:opacity .5s;background-size:250% 250%;animation:borderMove 5s linear infinite}
@keyframes borderMove{0%{background-position:0% 0}100%{background-position:250% 0}}
.svc:hover{transform:translateY(-8px);background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.015));box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.svc:hover::before{opacity:1}
.svc svg{width:34px;height:34px;stroke:var(--gold-soft);fill:none;stroke-width:1.4;margin-bottom:20px;stroke-dasharray:140;stroke-dashoffset:140;transition:stroke-dashoffset 1.2s cubic-bezier(.22,.61,.36,1),transform .55s cubic-bezier(.22,.61,.36,1)}
.svc.in svg{stroke-dashoffset:0}
.svc:hover svg{transform:scale(1.1) rotate(-3deg)}
.svc h3{font-size:23px;color:#fff;margin-bottom:9px;letter-spacing:.3px}
.svc p{color:var(--muted);font-size:14px;line-height:1.7;letter-spacing:.1px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.step{position:relative;padding:32px 26px;background:linear-gradient(160deg,rgba(255,255,255,.04),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);transition:.45s cubic-bezier(.22,.61,.36,1);overflow-wrap:break-word;overflow:hidden}
.step:hover{transform:translateY(-7px);border-color:rgba(236,207,160,.28);box-shadow:var(--shadow-md)}
.step .n{font-family:var(--serif);font-size:54px;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;transition:transform .45s}
.step:hover .n{transform:scale(1.1)}
.step h3{font-size:22px;color:#fff;margin:14px 0 8px;letter-spacing:.3px}
.step p{color:var(--muted);font-size:14px;line-height:1.7;letter-spacing:.1px}
.guar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.guar{position:relative;background:linear-gradient(160deg,rgba(255,255,255,.045),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.07);padding:36px 26px;text-align:center;transition:.45s;border-radius:var(--r-lg);overflow-wrap:break-word;overflow:hidden}
.guar::before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;background:linear-gradient(120deg,var(--gold-soft),transparent 40%,transparent 60%,var(--gold-soft));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:opacity .45s;background-size:250% 250%;animation:borderMove 6s linear infinite}
.guar:hover{transform:translateY(-8px);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.guar:hover::before{opacity:1}
.guar .ico{width:54px;height:54px;margin:0 auto 18px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);background:radial-gradient(circle at 30% 30%,rgba(236,207,160,.16),rgba(212,175,106,.03));box-shadow:0 0 22px rgba(212,175,106,.16);transition:transform .45s}
.guar:hover .ico{transform:scale(1.12) rotate(6deg)}
.guar .ico svg{width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:1.5}
.guar h3{font-size:18px;color:#fff;margin-bottom:8px;letter-spacing:.2px}
.guar p{color:var(--muted);font-size:13px;line-height:1.7;letter-spacing:.1px}
.city-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.city{position:relative;padding:36px 28px;border-radius:var(--r-lg);background:linear-gradient(160deg,rgba(255,255,255,.045),rgba(255,255,255,.01));border:1px solid rgba(255,255,255,.07);text-align:center;transition:.45s;overflow:hidden}
.city::before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;background:linear-gradient(120deg,var(--gold-soft),transparent 40%,transparent 60%,var(--gold-soft));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:opacity .45s;background-size:250% 250%;animation:borderMove 6s linear infinite}
.city:hover{transform:translateY(-7px);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.city:hover::before{opacity:1}
.city .city-name{font-family:var(--serif);font-size:28px;color:#fff;font-weight:500;letter-spacing:.4px}
.city .city-line{width:42px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:14px auto}
.city p{color:var(--muted);font-size:14px;line-height:1.68;letter-spacing:.1px}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:start}
.contact-info h2{font-size:clamp(30px,4.1vw,46px);color:#faf3e6;margin:16px 0 14px;line-height:1.12;text-shadow:0 4px 22px rgba(0,0,0,.45);letter-spacing:.3px}
.contact-info .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.contact-info>p{color:var(--muted);font-size:15.5px;margin-bottom:32px;letter-spacing:.2px}
.c-line{display:flex;align-items:flex-start;gap:20px;margin-bottom:24px;transition:transform .4s}
.c-line:hover{transform:translateX(6px)}
.c-ico{width:44px;height:44px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);background:radial-gradient(circle at 30% 30%,rgba(236,207,160,.15),rgba(212,175,106,.02));flex-shrink:0;box-shadow:0 0 18px rgba(212,175,106,.14);transition:transform .45s}
.c-line:hover .c-ico{transform:scale(1.1)}
.c-ico svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.5}
.c-line .lab{font-size:10.5px;letter-spacing:2.5px;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.c-line .val{font-size:18px;font-weight:600;color:var(--text);overflow-wrap:break-word;word-break:break-word;letter-spacing:.2px}
.c-line a.val:hover{color:var(--gold-soft)}
.call-block{background:linear-gradient(165deg,rgba(255,255,255,.055),rgba(255,255,255,.015));border:1px solid rgba(255,255,255,.07);padding:44px 36px;text-align:center;border-radius:var(--r-lg);box-shadow:var(--shadow-md);position:relative;overflow:hidden}
.call-block::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.6}
.call-block .cb-lab{font-size:12px;letter-spacing:4px;text-transform:uppercase;color:var(--gold-soft)}
.call-block .cb-num{display:block;font-family:var(--sans);font-weight:800;font-size:clamp(27px,3.6vw,44px);color:#fff;margin:14px 0 18px;white-space:nowrap;transition:color .3s,text-shadow .3s;text-shadow:0 5px 22px rgba(0,0,0,.42);letter-spacing:.4px}
.call-block .cb-num:hover{color:var(--gold-soft);text-shadow:0 0 30px rgba(236,207,160,.5)}
.call-block .cb-hint{color:var(--muted);font-size:14px;line-height:1.82;overflow-wrap:break-word;letter-spacing:.1px}
.contact-actions{display:flex;flex-direction:column;gap:12px;margin-top:24px}
.c-action{display:flex;align-items:center;justify-content:center;gap:11px;width:100%;padding:16px 18px;min-height:52px;border-radius:var(--r-sm);font-weight:700;font-size:14.5px;letter-spacing:.4px;transition:.4s;color:#fff}
.c-action svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8}
.c-action.c-call{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;box-shadow:var(--shadow-gold)}
.c-action.c-call:hover{filter:brightness(1.08);transform:translateY(-4px);box-shadow:0 22px 50px rgba(212,175,106,.42)}
.c-action.c-tg{background:rgba(64,169,242,.12);border:1px solid rgba(64,169,242,.38);color:#8fd0ff}
.c-action.c-tg:hover{background:rgba(64,169,242,.24);transform:translateY(-4px)}
.c-action.c-max{background:rgba(177,88,252,.12);border:1px solid rgba(177,88,252,.38);color:#e0b8ff}
.c-action.c-max:hover{background:rgba(177,88,252,.24);transform:translateY(-4px)}
.cta{text-align:center;padding:104px 0;position:relative}
.cta h2{font-size:clamp(32px,4.6vw,52px);color:#faf3e6;font-weight:500;margin-bottom:16px;text-shadow:0 5px 26px rgba(0,0,0,.45);letter-spacing:.3px}
.cta p{color:var(--muted);font-size:16.5px;max-width:630px;margin:0 auto 34px;overflow-wrap:break-word;letter-spacing:.2px}
footer{position:relative;background:linear-gradient(180deg,rgba(14,12,9,.4),rgba(10,8,6,.97));color:var(--muted);padding:50px 20px 58px;text-align:center;font-size:13px;border-top:1px solid rgba(255,255,255,.06)}
footer::before{content:"";position:absolute;top:-1px;left:50%;transform:translateX(-50%);width:min(420px,72%);height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
footer .flogo{font-family:var(--serif);font-size:28px;color:#fff;margin-bottom:8px;line-height:1.3;letter-spacing:.3px}
footer .flogo span{color:var(--gold-soft);font-size:13px;font-family:var(--sans);font-weight:500;letter-spacing:1px}
.social-row{display:flex;justify-content:center;gap:14px;margin:22px 0 18px;flex-wrap:wrap}
.soc{display:inline-flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:50%;border:1px solid rgba(236,207,160,.32);color:var(--gold-soft);background:rgba(212,175,106,.06);transition:.35s}
.soc svg{width:19px;height:19px;stroke:currentColor;fill:none;stroke-width:1.6}
.soc:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-4px);box-shadow:var(--shadow-gold)}
.cookie-bar{position:fixed;bottom:16px;left:50%;transform:translate(-50%,140%);z-index:400;background:rgba(14,12,9,.93);backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.08);border-radius:var(--r-md);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;box-shadow:var(--shadow-lg);width:min(680px,calc(100vw - 32px));transition:transform .6s cubic-bezier(.22,.61,.36,1)}
.cookie-bar.show{transform:translate(-50%,0)}
.cookie-bar p{color:var(--muted);font-size:13px;max-width:720px;line-height:1.5}
.cookie-bar .btn{flex-shrink:0;padding:12px 26px;min-height:46px}
.lightbox{position:fixed;inset:0;z-index:3000;background:rgba(8,6,4,.95);backdrop-filter:blur(10px);display:none;align-items:center;justify-content:center;flex-direction:column;gap:16px;touch-action:pan-y}
.lightbox.open{display:flex;animation:lbFade .3s ease}
@keyframes lbFade{from{opacity:0}to{opacity:1}}
.lightbox .lb-stage{position:relative;width:100%;height:100%;display:flex;align-items:center;justify-content:center;overflow:hidden}
.lightbox img{max-width:92vw;max-height:84vh;border-radius:var(--r-lg);border:1px solid rgba(236,207,160,.55);box-shadow:0 26px 90px rgba(0,0,0,.8);animation:lbZoom .3s ease;transition:transform .3s ease;transform-origin:center center;user-select:none;-webkit-user-select:none;touch-action:none}
.lightbox img.zoomed{transform:scale(2.4)}
@keyframes lbZoom{from{transform:scale(.92);opacity:0}to{transform:scale(1);opacity:1}}
.lb-close{position:absolute;top:18px;right:24px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#fff;font-size:30px;cursor:pointer;z-index:5;line-height:1;width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:transform .3s,background .3s}
.lb-close:hover{transform:rotate(90deg);background:rgba(236,207,160,.18)}
.lb-nav{position:absolute;top:50%;transform:translateY(-50%);width:52px;height:52px;border-radius:50%;background:rgba(14,12,9,.6);border:1px solid rgba(236,207,160,.5);color:var(--gold-soft);font-size:25px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.35s}
.lb-nav:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b}
.lb-prev{left:18px}.lb-next{right:18px}
.lb-count{color:var(--muted);font-size:13px;position:absolute;bottom:18px;left:50%;transform:translateX(-50%);background:rgba(14,12,9,.6);padding:6px 14px;border-radius:20px;border:1px solid rgba(255,255,255,.1)}
.reveal{opacity:0;transform:translateY(30px) scale(.985);filter:blur(6px);transition:opacity .85s ease,transform .85s cubic-bezier(.22,.61,.36,1),filter .85s ease}
.reveal.in{opacity:1;transform:none;filter:blur(0)}
.stats .reveal:nth-child(1){transition-delay:.05s}.stats .reveal:nth-child(2){transition-delay:.15s}.stats .reveal:nth-child(3){transition-delay:.25s}.stats .reveal:nth-child(4){transition-delay:.35s}
.steps .reveal:nth-child(2){transition-delay:.08s}.steps .reveal:nth-child(3){transition-delay:.16s}.steps .reveal:nth-child(4){transition-delay:.24s}.steps .reveal:nth-child(5){transition-delay:.32s}.steps .reveal:nth-child(6){transition-delay:.4s}
.svc-grid .reveal:nth-child(2){transition-delay:.08s}.svc-grid .reveal:nth-child(3){transition-delay:.16s}.svc-grid .reveal:nth-child(4){transition-delay:.24s}.svc-grid .reveal:nth-child(5){transition-delay:.32s}.svc-grid .reveal:nth-child(6){transition-delay:.4s}
.guar-grid .reveal:nth-child(2){transition-delay:.08s}.guar-grid .reveal:nth-child(3){transition-delay:.16s}.guar-grid .reveal:nth-child(4){transition-delay:.24s}
.city-grid .reveal:nth-child(2){transition-delay:.12s}.city-grid .reveal:nth-child(3){transition-delay:.24s}
@media(max-width:1180px){.car-prev{left:0}.car-next{right:0}}
@media(max-width:1024px){.stats{grid-template-columns:repeat(2,1fr);gap:30px}.svc-grid{grid-template-columns:repeat(2,1fr)}.guar-grid{grid-template-columns:repeat(2,1fr)}.city-grid{grid-template-columns:repeat(3,1fr)}.video-box img,.video-box iframe{height:380px}}
@media(max-width:860px){.menu{position:fixed;top:auto;bottom:0;left:0;right:0;width:100%;max-height:76vh;background:linear-gradient(180deg,#16130e,#0b0907);flex-direction:column;justify-content:flex-start;gap:4px;padding:28px 28px calc(28px + env(safe-area-inset-bottom));transform:translateY(110%);transition:transform .45s cubic-bezier(.22,.61,.36,1);z-index:205;opacity:1;visibility:visible;border-radius:26px 26px 0 0;box-shadow:0 -24px 70px rgba(0,0,0,.65);overflow-y:auto;border-top:1px solid var(--line)}.menu.open{transform:none}.menu a{font-size:19px;font-family:var(--serif);color:#fff;border-bottom:1px solid rgba(236,207,160,.12);padding:14px 0;display:block;min-height:52px;align-items:center}.menu a::after{display:none}.menu a:hover{color:var(--gold-soft)}.menu a.active{color:var(--gold-soft)}.menu-call{display:block;margin-top:auto;padding-top:18px}.menu-call a{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#fff;font-family:var(--sans);font-size:15px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;border:none;border-radius:var(--r-sm);padding:16px 18px;min-height:54px;box-shadow:var(--shadow-gold)}.burger{display:block}.scrim{display:block}.about{grid-template-columns:1fr;gap:36px}.features{grid-template-columns:1fr}.steps{grid-template-columns:1fr;gap:20px}.contact-grid{grid-template-columns:1fr;gap:36px}.city-grid{grid-template-columns:1fr}.panel{padding:116px 0}.car-nav{display:none}.rev-card{width:86vw}.rev-video iframe{height:230px}.swipe-hint{display:block}.water{font-size:clamp(70px,30vw,150px)}}
@media(max-width:768px){.panel{padding:100px 0 60px}.panel + .panel{margin-top:10px}.stats{gap:18px}.about{gap:28px}.contact-grid{gap:28px}.video-box img,.video-box iframe{height:300px}}
@media(max-width:520px){.logo .brand-ava{width:40px;height:40px}.logo .brand-txt .name{font-size:20px}.logo .brand-txt .sub{font-size:9.5px;max-width:54vw;letter-spacing:1.2px}.nav{height:62px}.panel{min-height:auto;padding:88px 0 48px}h1{font-size:31px}.sub{font-size:15px;margin:18px 0 26px}.btn-row{width:100%}.btn{width:100%;text-align:center;padding:15px 20px;font-size:12px;min-height:50px}.stat .num{font-size:44px}.sec-head{margin-bottom:34px}.sec-head h2::before,.sec-head h2::after{display:none}.scroll-cue{display:none}.car-slide{width:84vw}.car-slide img{height:205px}.svc-grid{grid-template-columns:1fr}.guar-grid{grid-template-columns:1fr}.rev-card{width:92vw;padding:17px}.rev-head{gap:10px}.rev-ava{width:44px;height:44px}.rev-name{font-size:13.5px}.rev-sub{font-size:10px}.rev-stars{font-size:12.5px;display:block;margin:6px 0 0}.rev-text{font-size:12.5px;line-height:1.56}.rev-video iframe{height:190px}.consult .phone{font-size:25px}.call-block .cb-num{font-size:22px}.menu{padding:24px 22px calc(24px + env(safe-area-inset-bottom))}.lb-nav{width:44px;height:44px;font-size:22px}.lb-close{width:46px;height:46px}.cookie-bar{bottom:10px;padding:14px 16px}.city{padding:28px 22px}.contact-info>p{margin-bottom:24px}.video-box img,.video-box iframe{height:220px}.video-play{width:62px;height:62px}}
@media(max-width:380px){.car-slide{width:88vw}.car-slide img{height:190px}.rev-card{width:94vw;padding:14px}.rev-text{font-size:12px}.rev-video iframe{height:170px}.btn{font-size:11px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important;scroll-behavior:auto!important}.reveal{opacity:1;transform:none;filter:none}.car-slide img,.rev-ava{opacity:1}}
</style>
</head>
<body>

<div class="progress" id="progress"></div>

<header id="header">
  <div class="wrap nav">
    <a href="#top" class="logo" id="logo">
      <img class="brand-ava" src="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0" width="46" height="46" alt="Кухни Островский — кухни на заказ в Ростове, Батайске и Азове">
      <span class="brand-txt"><span class="name">Кухни Островский</span><span class="sub">Ростов · Батайск · Азов</span></span>
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
  <li class="menu-call"><a href="tel:+79508465397">📞 Позвонить специалисту</a></li>
</ul>
<div class="scrim" id="scrim"></div>

<section class="panel kenburns" id="top">
  <div class="bg" style="background-image:url('https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0')"></div>
  <div class="water">Кухни</div>
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
  <div class="bg" style="background-image:url('https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1280x0')"></div>
  <div class="water">Мебель</div>
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
  <div class="bg" style="background-image:url('https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2208x1656&from=bu&u=9_d3vo4cDIif_5OxDZbDgMLFC1xuAQSKRY1zAPscIwM&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="about">
      <div class="about-card reveal">
        <div class="avatar"><img src="https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg" width="130" height="130" loading="lazy" decoding="async" alt="Роман Островский — руководитель мебельной мастерской Кухни Островский"></div>
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

<section class="panel panel--center panel--dark" id="consult">
  <div class="bg" style="background-image:url('https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0')"></div>
  <div class="wrap"><div class="content consult">
    <span class="kicker reveal" style="color:var(--gold-soft);letter-spacing:6px;text-transform:uppercase;font-size:12px;font-weight:600">Бесплатно</span>
    <h2 class="k reveal">Консультация</h2>
    <a href="tel:+79508465397" class="phone reveal">+7 (950) 846-53-97</a>
    <p class="reveal">Позвоните или напишите нам в <b style="color:#fff">Telegram</b> или <b style="color:#fff">MAX</b> — расскажем про кухни и мебель, всё обсудим и договоримся о бесплатном замере.</p>
  </div></div>
</section>

<section class="panel panel--center panel--dark" id="works">
  <div class="bg" style="background-image:url('https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=q3wKCscaGbBU8n3umOUNA0wOvLkQBDAVXIkzDrivHgk&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Наши работы</div>
      <h2>Кухни и мебель, которые мы сделали</h2>
      <p>Нажмите на фото, чтобы рассмотреть в большом размере.</p>
    </div>
    <div class="swipe-hint">Листайте →</div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="carPrev">❮</button>
      <div class="car-track" id="carTrack">
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1080x0" alt="Кухня на заказ в Ростове — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1080x0" alt="Кухня на заказ в Батайске — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-11.vkuserphoto.ru/s/v1/ig2/Xh5Xw9Yb1reqhfFznlGk8NjvSQAxCbysuiL5IWRt_f3ELVb8fvoYPg00eFIHV-xiS9I4nhYBj4ttU_FHVkPpX8Z3.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,1600x1200&from=bu&u=pY-bjOidU1jjNjiF66Dn4Ycgmb6utH_d0Ti7oSJr0qA&cs=1080x0" alt="Кухня на заказ в Азове — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1080x0" alt="Мебель на заказ в Ростове — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1080x0" alt="Шкаф-купе на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-24.vkuserphoto.ru/s/v1/ig2/lS8MpZ4V9XUKPJ7l9GmjnkCnHW2MGfnq86jH-Gzx6bAgr4m3azL5Xd_fkdPHY_NOsJjST3Zw2iQkuGKGBwYODdgM.jpg?quality=95&as=32x42,48x63,72x95,108x142,160x211,240x316,360x474,480x632,540x711,640x843,720x949,1080x1423,1280x1686,1440x1897,1943x2560&from=bu&u=dLnirpryCPR3qvUPphwt7JaP5ljnoIl1yyGyUNiUjZI&cs=1080x0" alt="Мебель на заказ в Батайске — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1080x0" alt="Кухня на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-39.vkuserphoto.ru/s/v1/ig2/5cyrhjIBSWB5GGZATB29IrmjydaNdVOx-iP_dMNKsMbePp5Ccs2rnkEpLnfft3yAZGeMEE3IfInjMQ7aU6Z6jnHc.jpg?quality=95&as=32x24,48x36,72x54,108x82,160x121,240x181,360x272,480x363,540x408,640x484,720x544,1080x817,1280x968&from=bu&u=l1uWXrXXeEAKk1VMgGM5wyIo7DtKdQGhKlCwMjoS0t8&cs=1080x0" alt="Мебель на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-68.vkuserphoto.ru/s/v1/ig2/6KwHlOiN9pxXNIwTImKO6QGkrSCTVqreybJu-63m8wbhdFFMIl06es9cPeurIdwuwXGtsFTkdJ6IOjMaS1qRtfxJ.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VgDjFEJKqpW6dWVO-E4y4Q6xcuyoqiL7LxhG36oLPjw&cs=1080x0" alt="Кухня на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-23.vkuserphoto.ru/s/v1/ig2/wfBQoeOzjZbCRCvxmIkx_V3xC0fgMd3TTxRDSRG2CHDMok6B2ZKrG7vCAJ_G1DmrZ6JS1_RC2tr87Q64wJJ4aW9w.jpg?quality=95&as=32x25,48x37,72x56,108x84,160x124,240x186,360x279,480x372,540x419,640x496,720x558,1080x837,1280x992,1440x1117,2560x1985&from=bu&u=kZXvrlzwGUvzrHmYa8tHXbvyhU_JlNlefLxxcCYqM1A&cs=1080x0" alt="Мебель на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-33.vkuserphoto.ru/s/v1/ig2/TQbwf8FdMs_jwKfC_ONoxEHBIpc2L5yf_T0McNeUKRn0tK7fVbC5YbHfsB0TGLlNC_D55htM_2nREACuIw7ykLIx.jpg?quality=95&as=32x43,48x65,72x97,108x145,160x215,240x323,360x484,480x645,540x726,640x860,720x968,1080x1452,1280x1721,1440x1936,1904x2560&from=bu&u=rbH0OM9Bv0PnevamgtW5nYBm9jxFI28R6D1wxzq6fJA&cs=1080x0" alt="Кухня на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0" alt="Кухня на заказ — Кухни Островский"></div>
        <div class="car-slide"><img loading="lazy" decoding="async" src="https://sun9-65.vkuserphoto.ru/s/v1/ig2/z_wfZeGA9H6LHDsevjkijUHpbVyLGWFM38frX4hKrjgOnscfAloGdrVpPUwl4XoXCG_YgcKXTgeeTsDDcWEBvdi1.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YbZ1WmiK3ZCk0bKWZhf_YKp6dTUU2vbsQo7Ya4Hoi6s&cs=1080x0" alt="Кухня на заказ — Кухни Островский"></div>
      </div>
      <button class="car-nav car-next" id="carNext">❯</button>
      <div class="car-dots" id="carDots"></div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше работ — в сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>

<div class="lightbox" id="lightbox">
  <button class="lb-close" id="lbClose">×</button>
  <button class="lb-nav lb-prev" id="lbPrev">❮</button>
  <div class="lb-stage"><img id="lbImg" alt="Работа"></div>
  <div class="lb-count" id="lbCount"></div>
  <button class="lb-nav lb-next" id="lbNext">❯</button>
</div>

<section class="panel panel--center" id="reviews">
  <div class="bg" style="background-image:url('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0')"></div>
  <div class="water">Отзывы</div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Отзывы</div>
      <h2>Что говорят наши клиенты</h2>
      <p>Реальные отзывы о нашей работе. Листайте влево-вправо.</p>
    </div>
    <div class="swipe-hint">Листайте →</div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="revPrev">❮</button>
      <div class="car-track rev-track" id="revTrack">
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="https://sun9-3.vkuserphoto.ru/s/v1/ig2/-cVZEipS5I4ROZUZ2fxoIaGJBZXpUs76_WKoUZpPw_r2-gnqqUvgTqjLjYoTZ0R21nsCSvjUPyw_vSn1jxAYJC8K.jpg?quality=95&as=32x30,48x45,72x68,108x101,160x150,240x225,360x338,480x450,540x507,640x601,720x676,1080x1014,1280x1201,1440x1351,2505x2351&from=bu&cs=128x0" alt="Отзыв: Виктория Брандикова">
            <div><div class="rev-name">Виктория Брандикова</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа кухню, всё прошло на высшем уровне, начиная от замеров, до установки! Мы очень рады, что обратились именно к нему (нашли в объявлении и нам крупно повезло), Роман супер профессионал своего дела!!! Кухня у нас маленькая, не стандартная, сверху выступы, вся на трубах, расположение мойки и кухонной плиты не удобное и вытяжку мы хотели, но нам некуда было её устанавливать (как мы думали), но Роман всё разрешил, практично разместил технику (в том числе и вытяжку), переставил мойку, установил подсветку сделал кухню функциональной светлой, практичной и современной. Кухня была готова в короткие сроки, установкой очень довольны, всё под ключ с установкой техники и подключением, всё быстро, качественно, и чисто! Мы не ожидали такого результата 😍, просто не верится, что у нас теперь удобная, вместительная, современная кухня 🔥, о такой даже и не мечтали, даже несмотря на то, что кухня бюджетная. За мебелью теперь только к Роману!!! Однозначно всем буду рекомендовать!!!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0" alt="Отзыв: Виктория Маренко">
            <div><div class="rev-name">Виктория Маренко</div><div class="rev-sub">Кухня и гардеробная</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">И вновь мы обратились к Роману! Понадобилась кухня😊Кухня на самом деле очень удобная! Как и хотелось она светлая, но не маркая. Как всегда учтены все пожелания и воплощены в жизнь! Очень трудно нам дался выбор цветов😂но Роман спокойно вынес все наши метания🙏 выполнил работу достойно, внимательно и аккуратно! Однозначно советую обращаться к нему👍 гардеробную так же заказывали у Романа, и она идеальна👏 ответственный подход, качество, внимательность и чистота исполнения - его качества, которые для нас важны, поэтому если нам понадобится мебель- обязательно еще раз встретимся😊</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="https://sun9-53.vkuserphoto.ru/s/v1/ig2/gZheSpaWhz7StIdwlzSoCIfA01e-x8jVUMESDK2u9ONRR1s3txB-b6F7lqLLj-Y6QFqFU5x463yoWmnTxf5T88g2.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&cs=128x0" alt="Отзыв: Любовь Петелько">
            <div><div class="rev-name">Любовь Петелько</div><div class="rev-sub">Шкаф, тумбы, прихожая</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Всем здравствуйте. Я заказала у Романа шкаф купе в спальню. Когда Роман приехал, я не совсем понимала что я хочу, пообщавшись с ним, получила много советов и рекомендаций по составу и цвету шкафа. В итоге решила в комплект заказать сразу тумбы, гарнитур под телевизор, и прихожую. Установили все раньше обещанного срока. Я очень довольна и всем рекомендую. Роман специалист своего дела. Скоро буду заказывать зону хранения балкона и самое главное кухню мечты). Спасибо</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="https://sun9-83.vkuserphoto.ru/s/v1/ig2/zYO0FQ_fFsgxDWhaTE85lNpixn2ikScuD58qVoXtqda8vFxoS-LGsT54k9pk9tDVEpzGpJfCw5eg5TNtYgE2Q8_y.jpg?quality=95&as=32x47,48x71,72x106,108x159,160x236,240x353,360x530,480x707,540x795,640x943,720x1061,869x1280&from=bu&cs=1280x0" alt="Отзыв: Дмитрий Юшенко">
            <div><div class="rev-name">Дмитрий Юшенко</div><div class="rev-sub">Шкаф и стенка</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа шкаф и стенку в спальню. Работа вышла отличной, подсказал несколько удачных решений наших хотелок. Все супер! Спасибо!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="https://sun9-46.vkuserphoto.ru/s/v1/ig2/bVm2vnJWOD92dzHJ3_21NbqhcwF7DW7a05XzjaTWteG9Dviu9nt8LlA5bgzdbsBhGtYbrs7rvOMTylQQIV43cl4T.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&cs=128x0" alt="Отзыв: Екатерина Умнягина">
            <div><div class="rev-name">Екатерина Умнягина</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа кухню, всё очень понравилось! Подбирали всё до мелочей, и Рома всё исполнил, как мы хотели, за это мы ему очень благодарны. Всё сделано идеально, спрятали то, что не должно быть видно, и получилось очень красиво. Спасибо, Рома, за эту крутую современную кухню!!!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="https://sun9-48.vkuserphoto.ru/s/v1/ig2/OdS0JaUmpkj7vzQLNz1oyY6PBksnYylZuY54LZ2vnibrqxNc0IimIjE6d6NWySeMm6N2MLIUHG6WLKtAFJ82ICwE.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,960x1280&from=bu&cs=128x0" alt="Отзыв: Анастасия Зайцева">
            <div><div class="rev-name">Анастасия Зайцева</div><div class="rev-sub">Два шкафа, гардеробная</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа два шкафа. Во время замеров у нас не было определённой идеи, как сделать вместительный шкаф в нашу небольшую спальню, ещё и с несущей колонной. Роман подкинул прекрасную идею, в итоге получился не просто шкаф, а целая угловая гардеробная, я была в восторге 🤩 Большой выбор цветов и текстур. Работа выполнена в оговорённый срок и качественно. 👍🏻 Большое спасибо за эстетичное воплощение нашей мечты 🤩😊</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <div><div class="rev-name">Александр Карташев</div><div class="rev-sub">Видеоотзыв · Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <div class="rev-video">
            <div class="video-box" data-video="https://vk.ru/video_ext.php?oid=-212015374&id=456239019&hash=6abf300a7c2518d4">
              <img loading="lazy" decoding="async" src="https://sun9-44.vkuserphoto.ru/s/v1/ig2/z3K7MYc56nf_4Ek_wkhJ-j-VZt7iv_VEt9wUN0gJSY0VORuRVxQCX1S5baisBgJyoYuCcrENJNxLajL1WKwdFS91.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x541,1080x811,1280x961,1440x1081,2560x1922&from=bu&u=Fj3HDKPJXUOEmCWl6MePYyPYB6lNmsGien6u_9mlUi8&cs=1280x0" alt="Видеоотзыв Александра Карташева о кухне на заказ — Кухни Островский" style="height:250px;width:100%;object-fit:cover">
              <div class="video-play"></div>
            </div>
          </div>
          <p class="rev-text">«<b>Прям гордость квартиры 😀</b> За приемлемую цену получили отличную кухню: выступ стояка закрыли пеналом, а в ножку барного стола встроили розетки».</p>
        </div>
      </div>
      <button class="car-nav car-next" id="revNext">❯</button>
      <div class="car-dots" id="revDots"></div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше отзывов — в нашем сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>

<section class="panel panel--dark" id="services">
  <div class="bg" style="background-image:url('https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1280x0')"></div>
  <div class="water">Услуги</div>
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
      <div class="svc reveal"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6L5.6 18.4"/></svg><h3>Замер и проект</h3><p>Выезжаем на замер, делаем планировку и 3D-проект — бесплатно.</p></div>
      <div class="svc reveal"><svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9M3 12h6M3 12l4-4M3 12l4 4"/></svg><h3>Обновление мебели</h3><p>Освежим фасады и фурнитуру существующей кухни — дешевле, чем новая.</p></div>
    </div>
  </div></div>
</section>

<section class="panel" id="process">
  <div class="bg" style="background-image:url('https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VpmAnVyzkXcBCcJLy2DSlVkJJG2zYnSPbLzk7-TXGGk&cs=1280x0')"></div>
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
  <div class="bg" style="background-image:url('https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YCey971XM2nuNjhkwSaIOfPMTMneMAyHLaPyHT4mLyY&cs=1280x0')"></div>
  <div class="water">Гарантии</div>
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
  <div class="bg" style="background-image:url('https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1280x0')"></div>
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
  <div class="bg" style="background-image:url('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0')"></div>
  <div class="wrap"><div class="content cta">
    <h2 class="reveal shimmer">Готовы обсудить вашу мебель?</h2>
    <p class="reveal">Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.</p>
    <a href="tel:+79508465397" class="btn btn-solid reveal">📞 Позвонить специалисту</a>
  </div></div>
</section>

<section class="panel panel--dark" id="contacts">
  <div class="bg" style="background-image:url('https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0')"></div>
  <div class="water">Контакты</div>
  <div class="wrap"><div class="content">
    <div class="contact-grid">
      <div class="contact-info reveal">
        <div class="kicker">Контакты</div>
        <h2>Создадим мебель, о которой вы мечтали</h2>
        <p>Позвоните или напишите — ответим быстро и подскажем по всем вопросам.</p>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6L5.6 18.4"/></svg></div><div><div class="lab">Регион работы</div><div class="val">Ростов-на-Дону, Батайск, Азов</div></div></div>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><path d="M4 20h16M6 20V8l6-4 6 4v12"/></svg></div><div><div class="lab">Сайт в VK</div><a class="val" href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener">mebel.ostrovsky</a></div></div>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/></svg></div><div><div class="lab">Telegram / MAX</div><div class="val">по номеру +7 (950) 846-53-97</div></div></div>
        <div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg></div><div><div class="lab">Сообщения VK</div><div class="val">личные сообщения сообщества</div></div></div>
      </div>
      <div class="reveal">
        <div class="call-block">
          <div class="cb-lab">Свяжитесь с нами удобным способом</div>
          <a class="cb-num" href="tel:+79508465397">+7 (950) 846-53-97</a>
          <div class="cb-hint">Бесплатная консультация и запись на замер.<br>Звоните или пишите в любой мессенджер.</div>
          <div class="contact-actions">
            <a class="c-action c-call" href="tel:+79508465397"><svg viewBox="0 0 24 24"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 2z"/></svg>Позвонить</a>
            <a class="c-action c-tg" href="https://t.me/fanny161" target="_blank" rel="noopener"><svg viewBox="0 0 24 24"><path d="M21.9 4.6L18.8 19c-.2 1-.8 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.8L18 6.4c.4-.3-.1-.5-.6-.2L6.7 13.4l-4.6-1.4c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.6 1z"/></svg>Написать в Telegram</a>
            <a class="c-action c-max" href="tel:+79508465397"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>Написать в MAX</a>
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
    <a class="soc" href="tel:+79508465397" title="MAX"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></a>
  </div>
  <p>Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов</p>
  <p style="margin-top:8px">© <span id="year"></span> Кухни Островский. Все права защищены.</p>
</footer>

<div class="cookie-bar" id="cookieBar">
  <p>Мы используем файлы cookie для корректной работы сайта и улучшения сервиса. Продолжая пользоваться сайтом, вы соглашаетесь с <a href="#" style="color:var(--gold-soft)">политикой конфиденциальности</a>.</p>
  <button class="btn btn-solid" id="cookieOk">Принять</button>
</div>

<script>
const progress=document.getElementById('progress');
const header=document.getElementById('header');
let lastScrollY=window.scrollY;
function onScroll(){const h=document.documentElement;const sc=h.scrollHeight>h.clientHeight?h.scrollTop/(h.scrollHeight-h.clientHeight):0;progress.style.width=(sc*100)+'%';header.classList.toggle('solid',h.scrollTop>40);if(h.scrollTop>260&&h.scrollTop>lastScrollY){header.classList.add('hide');}else{header.classList.remove('hide');}lastScrollY=h.scrollTop;}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
document.getElementById('logo').addEventListener('click',e=>{e.preventDefault();window.scrollTo({top:0,behavior:'smooth'});});
const burger=document.getElementById('burger'),menu=document.getElementById('menu'),scrim=document.getElementById('scrim');
function closeMenu(){burger.classList.remove('open');menu.classList.remove('open');scrim.classList.remove('show');}
burger.addEventListener('click',()=>{const open=menu.classList.contains('open');if(open)closeMenu();else{burger.classList.add('open');menu.classList.add('open');scrim.classList.add('show');}});
scrim.addEventListener('click',closeMenu);
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
const sections=['about','works','reviews','services','process','cities','contacts'];
const navLinks=menu.querySelectorAll('a[href^="#"]');
window.addEventListener('scroll',()=>{let current='';sections.forEach(id=>{const el=document.getElementById(id);if(el&&el.getBoundingClientRect().top<=120)current=id;});navLinks.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+current));},{passive:true});
function supportsFX(){return window.matchMedia('(min-width:861px)').matches&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches;}
if(supportsFX()){const bgs=document.querySelectorAll('.panel .bg');const contents=document.querySelectorAll('.panel .content');function parallax(){bgs.forEach(bg=>{if(bg.closest('.kenburns'))return;const r=bg.parentElement.getBoundingClientRect();const c=(r.top+r.height/2)-innerHeight/2;bg.style.transform='translateY('+(-c*0.22)+'px)';});contents.forEach(cn=>{const r=cn.parentElement.getBoundingClientRect();const c=(r.top+r.height/2)-innerHeight/2;cn.style.transform='translateY('+(-c*0.06)+'px)';});}window.addEventListener('scroll',parallax,{passive:true});parallax();}
function animateCount(el){const target=parseFloat(el.dataset.count);const dec=parseInt(el.dataset.decimal||'0');const suffix=el.dataset.suffix||'';const dur=1200,start=performance.now();function tick(t){let p=Math.min((t-start)/dur,1);p=1-Math.pow(1-p,3);let val=(target*p).toFixed(dec);el.textContent=(dec?val:Math.round(val))+suffix;if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}
const statIO=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){animateCount(e.target);statIO.unobserve(e.target);}});},{threshold:.5});
document.querySelectorAll('.stat .num').forEach(el=>statIO.observe(el));
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
document.querySelectorAll('.car-slide img,.rev-ava,.video-box img').forEach(img=>{if(img.complete){img.classList.add('loaded');}else{img.addEventListener('load',()=>img.classList.add('loaded'),{once:true});}});
function initCarousel(trackId,prevId,nextId,dotsId){const track=document.getElementById(trackId),prev=document.getElementById(prevId),next=document.getElementById(nextId),dotsBox=document.getElementById(dotsId),items=[...track.children];dotsBox.innerHTML='';items.forEach((_,i)=>{const d=document.createElement('button');d.className='car-dot'+(i===0?' active':'');d.setAttribute('aria-label','Слайд '+(i+1));d.addEventListener('click',()=>items[i].scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'}));dotsBox.appendChild(d);});const dots=[...dotsBox.children];const step=()=>items[0].offsetWidth+20;track.addEventListener('scroll',()=>{const idx=Math.round(track.scrollLeft/step());dots.forEach((d,i)=>d.classList.toggle('active',i===idx));},{passive:true});prev.addEventListener('click',()=>track.scrollBy({left:-step(),behavior:'smooth'}));next.addEventListener('click',()=>track.scrollBy({left:step(),behavior:'smooth'}));}
initCarousel('carTrack','carPrev','carNext','carDots');
initCarousel('revTrack','revPrev','revNext','revDots');
const lightbox=document.getElementById('lightbox'),lbImg=document.getElementById('lbImg'),lbCount=document.getElementById('lbCount');
const lbItems=[...document.querySelectorAll('#carTrack .car-slide img')];let lbIdx=0;
function openLb(i){lbIdx=i;lbImg.src=lbItems[i].src;lbImg.alt=lbItems[i].alt;lbImg.classList.remove('zoomed');lbCount.textContent=(i+1)+' / '+lbItems.length;lightbox.classList.add('open');}
function closeLb(){lightbox.classList.remove('open');lbImg.classList.remove('zoomed');}
function lbStep(d){openLb((lbIdx+d+lbItems.length)%lbItems.length);}
lbItems.forEach((img,i)=>img.addEventListener('click',()=>openLb(i)));
document.getElementById('lbClose').addEventListener('click',closeLb);
document.getElementById('lbPrev').addEventListener('click',e=>{e.stopPropagation();lbStep(-1);});
document.getElementById('lbNext').addEventListener('click',e=>{e.stopPropagation();lbStep(1);});
lightbox.addEventListener('click',e=>{if(e.target===lightbox||e.target.classList.contains('lb-stage'))closeLb();});
document.addEventListener('keydown',e=>{if(lightbox.classList.contains('open')){if(e.key==='Escape')closeLb();if(e.key==='ArrowLeft')lbStep(-1);if(e.key==='ArrowRight')lbStep(1);}});
let lbTap=0;
lightbox.addEventListener('click',e=>{if(e.target===lbImg){lbTap++;if(lbTap===1){setTimeout(()=>lbTap=0,280);}else{lbTap=0;lbImg.classList.toggle('zoomed');}}});
let pinchStart=0;
lightbox.addEventListener('touchstart',e=>{if(e.touches.length===2){pinchStart=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);}},{passive:true});
lightbox.addEventListener('touchmove',e=>{if(e.touches.length===2){const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);if(pinchStart&&d>pinchStart*1.25){lbImg.classList.add('zoomed');}else if(pinchStart&&d<pinchStart*0.8){lbImg.classList.remove('zoomed');}}},{passive:true});
let startX=0;
lightbox.addEventListener('touchstart',e=>{if(e.touches.length===1)startX=e.touches[0].clientX;},{passive:true});
lightbox.addEventListener('touchend',e=>{if(e.changedTouches.length===1){const dx=e.changedTouches[0].clientX-startX;if(Math.abs(dx)>60&&!lbImg.classList.contains('zoomed')){if(dx<0)lbStep(1);else lbStep(-1);}}},{passive:true});
document.querySelectorAll('.video-box').forEach(box=>{box.addEventListener('click',()=>{const url=box.dataset.video;const iframe=document.createElement('iframe');iframe.src=url;iframe.frameBorder='0';iframe.allowFullscreen=true;iframe.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';iframe.title='Видеоотзыв о кухне на заказ — Кухни Островский';iframe.loading='lazy';box.innerHTML='';box.appendChild(iframe);});});
if(supportsFX()){let raf=null;document.querySelectorAll('.car-slide').forEach(slide=>{slide.addEventListener('mousemove',e=>{const r=slide.getBoundingClientRect();const px=(e.clientX-r.left)/r.width-0.5;const py=(e.clientY-r.top)/r.height-0.5;if(raf)cancelAnimationFrame(raf);raf=requestAnimationFrame(()=>{slide.style.transform='translateY(-6px) perspective(900px) rotateY('+(px*5)+'deg) rotateX('+(-py*5)+'deg)';});});slide.addEventListener('mouseleave',()=>{if(raf)cancelAnimationFrame(raf);slide.style.transform='';});});}
const cookieBar=document.getElementById('cookieBar'),cookieOk=document.getElementById('cookieOk');
if(!localStorage.getItem('cookiesAccepted')){setTimeout(()=>cookieBar.classList.add('show'),900);}
cookieOk.addEventListener('click',()=>{localStorage.setItem('cookiesAccepted','1');cookieBar.classList.remove('show');});
document.getElementById('year').textContent=new Date().getFullYear();
</script>
</body>
</html>
"""

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
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, SITEMAP, "application/xml; charset=utf-8", "public, max-age=3600")
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

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("Кухни Островский сервер запущен на http://0.0.0.0:{}".format(PORT))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
