# -*- coding: utf-8 -*-
"""
mebel.py — Кухни Островский: сайт + админка /admin (Supabase)
HTML читается из page.html (лежит рядом). Прокси VK-картинок, анимации, фоновый Supabase.
"""
import base64
import concurrent.futures
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
SUPABASE_ANON = os.environ.get("SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEyMDQ1NzYsImV4cCI6MjEwNjc4MDU3Nn0.yi57-Ty1iIfhnEh80_zvifhX1W_JX2qCl7QrARuJ2ns")
SUPABASE_SERVICE = os.environ.get("SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTIwNDU3NiwiZXhwIjoyMTA2NzgwNTc2fQ.Yr4z9vx6kF9ZINNNUjUn43GYi-A2BmBfg8uyrOtmDWo")
ADMIN_LOGIN_ENV = os.environ.get("ADMIN_LOGIN", "кухниост")
ADMIN_PASSWORD_ENV = os.environ.get("ADMIN_PASSWORD", "романкух")

SESSION_TTL = 86400 * 7
MAX_UPLOAD = 8 * 1024 * 1024
DATA_ROW_ID = 1
CACHE_TTL = 15

FAVICON_URL = ("https://sun9-20.vkuserphoto.ru/s/v1/ig2/"
               "2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg"
               "?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254"
               "&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0")

ROBOTS = "User-agent: *\nAllow: /\n\nHost: кухниостровский.рф\n\nSitemap: {}/sitemap.xml\n".format(DOMAIN)
SITEMAP = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '  <url>\n    <loc>' + DOMAIN + '/</loc>\n'
           '    <lastmod>' + date.today().isoformat() + '</lastmod>\n'
           '    <changefreq>weekly</changefreq>\n'
           '    <priority>1.0</priority>\n  </url>\n</urlset>\n')
MANIFEST = '{"name":"Кухни Островский","short_name":"Кухни Островский","start_url":"/",' \
           '"display":"standalone","background_color":"#0e0c09","theme_color":"#0e0c09","lang":"ru-RU"}'

PAGE_404 = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><meta name="robots" content="noindex"><title>404</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0e0c09;color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px}.code{font-family:Georgia,serif;font-size:clamp(80px,18vw,160px);background:linear-gradient(135deg,#eccfa0,#d4af6a,#a37c3f);-webkit-background-clip:text;-webkit-text-fill-color:transparent}h1{color:#fff;margin:14px 0}.btn{display:inline-block;padding:15px 30px;border-radius:14px;background:linear-gradient(135deg,#eccfa0,#d4af6a,#a37c3f);color:#17120b;font-weight:700;text-decoration:none;margin-top:20px}</style>
</head><body><div><div class="code">404</div><h1>Такой страницы нет</h1><a class="btn" href="/">На главную</a></div></body></html>"""

# =====================================================================
# DEFAULT_DATA — служит сидом и фоллбэком
# =====================================================================
WORKS = [
    ("https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1080x0", "Кухня на заказ в Ростове"),
    ("https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1080x0", "Кухня на заказ в Батайске"),
    ("https://sun9-11.vkuserphoto.ru/s/v1/ig2/Xh5Xw9Yb1reqhfFznlGk8NjvSQAxCbysuiL5IWRt_f3ELVb8fvoYPg00eFIHV-xiS9I4nhYBj4ttU_FHVkPpX8Z3.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,1600x1200&from=bu&u=pY-bjOidU1jjNjiF66Dn4Ycgmb6utH_d0Ti7oSJr0qA&cs=1080x0", "Кухня на заказ в Азове"),
    ("https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1080x0", "Мебель на заказ в Ростове"),
    ("https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1080x0", "Шкаф-купе на заказ"),
    ("https://sun9-24.vkuserphoto.ru/s/v1/ig2/lS8MpZ4V9XUKPJ7l9GmjnkCnHW2MGfnq86jH-Gzx6bAgr4m3azL5Xd_fkdPHY_NOsJjST3Zw2iQkuGKGBwYODdgM.jpg?quality=95&as=32x42,48x63,72x95,108x142,160x211,240x316,360x474,480x632,540x711,640x843,720x949,1080x1423,1280x1686,1440x1897,1943x2560&from=bu&u=dLnirpryCPR3qvUPphwt7JaP5ljnoIl1yyGyUNiUjZI&cs=1080x0", "Мебель на заказ в Батайске"),
    ("https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1080x0", "Кухня на заказ"),
    ("https://sun9-39.vkuserphoto.ru/s/v1/ig2/5cyrhjIBSWB5GGZATB29IrmjydaNdVOx-iP_dMNKsMbePp5Ccs2rnkEpLnfft3yAZGeMEE3IfInjMQ7aU6Z6jnHc.jpg?quality=95&as=32x24,48x36,72x54,108x82,160x121,240x181,360x272,480x363,540x408,640x484,720x544,1080x817,1280x968&from=bu&u=l1uWXrXXeEAKk1VMgGM5wyIo7DtKdQGhKlCwMjoS0t8&cs=1080x0", "Мебель на заказ"),
    ("https://sun9-68.vkuserphoto.ru/s/v1/ig2/6KwHlOiN9pxXNIwTImKO6QGkrSCTVqreybJu-63m8wbhdFFMIl06es9cPeurIdwuwXGtsFTkdJ6IOjMaS1qRtfxJ.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VgDjFEJKqpW6dWVO-E4y4Q6xcuyoqiL7LxhG36oLPjw&cs=1080x0", "Кухня на заказ в Батайске"),
    ("https://sun9-23.vkuserphoto.ru/s/v1/ig2/wfBQoeOzjZbCRCvxmIkx_V3xC0fgMd3TTxRDSRG2CHDMok6B2ZKrG7vCAJ_G1DmrZ6JS1_RC2tr87Q64wJJ4aW9w.jpg?quality=95&as=32x25,48x37,72x56,108x84,160x124,240x186,360x279,480x372,540x419,640x496,720x558,1080x837,1280x992,1440x1117,2560x1985&from=bu&u=kZXvrlzwGUvzrHmYa8tHXbvyhU_JlNlefLxxcCYqM1A&cs=1080x0", "Мебель на заказ"),
    ("https://sun9-33.vkuserphoto.ru/s/v1/ig2/TQbwf8FdMs_jwKfC_ONoxEHBIpc2L5yf_T0McNeUKRn0tK7fVbC5YbHfsB0TGLlNC_D55htM_2nREACuIw7ykLIx.jpg?quality=95&as=32x43,48x65,72x97,108x145,160x215,240x323,360x484,480x645,540x726,640x860,720x968,1080x1452,1280x1721,1440x1936,1904x2560&from=bu&u=rbH0OM9Bv0PnevamgtW5nYBm9jxFI28R6D1wxzq6fJA&cs=1080x0", "Кухня на заказ"),
    ("https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0", "Кухня на заказ"),
    ("https://sun9-65.vkuserphoto.ru/s/v1/ig2/z_wfZeGA9H6LHDsevjkijUHpbVyLGWFM38frX4hKrjgOnscfAloGdrVpPUwl4XoXCG_YgcKXTgeeTsDDcWEBvdi1.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YbZ1WmiK3ZCk0bKWZhf_YKp6dTUU2vbsQo7Ya4Hoi6s&cs=1080x0", "Кухня на заказ"),
]

REVIEWS = [
    ("Виктория Брандикова", "Кухня на заказ", 5,
     "https://sun9-3.vkuserphoto.ru/s/v1/ig2/-cVZEipS5I4ROZUZ2fxoIaGJBZXpUs76_WKoUZpPw_r2-gnqqUvgTqjLjYoTZ0R21nsCSvjUPyw_vSn1jxAYJC8K.jpg?quality=95&as=32x30,48x45,72x68,108x101,160x150,240x225,360x338,480x450,540x507,640x601,720x676,1080x1014,1280x1201,1440x1351,2505x2351&from=bu&cs=128x0",
     "Заказывали у Романа кухню, всё прошло на высшем уровне, начиная от замеров, до установки! Мы очень рады, что обратились именно к нему (нашли в объявлении и нам крупно повезло), Роман супер профессионал своего дела!!! Кухня у нас маленькая, не стандартная, сверху выступы, вся на трубах, расположение мойки и кухонной плиты не удобное и вытяжку мы хотели, но нам некуда было её устанавливать (как мы думали), но Роман всё разрешил, практично разместил технику (в том числе и вытяжку), переставил мойку, установил подсветку сделал кухню функциональной светлой, практичной и современной. Кухня была готова в короткие сроки, установкой очень довольны, всё под ключ с установкой техники и подключением, всё быстро, качественно, и чисто! Мы не ожидали такого результата, просто не верится, что у нас теперь удобная, вместительная, современная кухня, о такой даже и не мечтали, даже несмотря на то, что кухня бюджетная. За мебелью теперь только к Роману!!! Однозначно всем буду рекомендовать!!!", ""),
    ("Виктория Маренко", "Кухня и гардеробная", 5,
     "https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0",
     "И вновь мы обратились к Роману! Понадобилась кухня. Кухня на самом деле очень удобная! Как и хотелось она светлая, но не маркая. Как всегда учтены все пожелания и воплощены в жизнь! Очень трудно нам дался выбор цветов, но Роман спокойно вынес все наши метания, выполнил работу достойно, внимательно и аккуратно! Однозначно советую обращаться к нему. Гардеробную так же заказывали у Романа, и она идеальна! Ответственный подход, качество, внимательность и чистота исполнения - его качества, которые для нас важны.", ""),
    ("Любовь Петелько", "Шкаф, тумбы, прихожая", 5,
     "https://sun9-53.vkuserphoto.ru/s/v1/ig2/gZheSpaWhz7StIdwlzSoCIfA01e-x8jVUMESDK2u9ONRR1s3txB-b6F7lqLLj-Y6QFqFU5x463yoWmnTxf5T88g2.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&cs=128x0",
     "Всем здравствуйте. Я заказала у Романа шкаф купе в спальню. Когда Роман приехал, я не совсем понимала что я хочу, пообщавшись с ним, получила много советов и рекомендаций по составу и цвету шкафа. В итоге решила в комплект заказать сразу тумбы, гарнитур под телевизор, и прихожую. Установили все раньше обещанного срока. Я очень довольна и всем рекомендую. Роман специалист своего дела. Скоро буду заказывать зону хранения балкона и самое главное кухню мечты. Спасибо!", ""),
    ("Дмитрий Юшенко", "Шкаф и стенка", 5,
     "https://sun9-83.vkuserphoto.ru/s/v1/ig2/zYO0FQ_fFsgxDWhaTE85lNpixn2ikScuD58qVoXtqda8vFxoS-LGsT54k9pk9tDVEpzGpJfCw5eg5TNtYgE2Q8_y.jpg?quality=95&as=32x47,48x71,72x106,108x159,160x236,240x353,360x530,480x707,540x795,640x943,720x1061,869x1280&from=bu&cs=1280x0",
     "Заказывали у Романа шкаф и стенку в спальню. Работа вышла отличной, подсказал несколько удачных решений наших хотелок. Все супер! Спасибо!", ""),
    ("Екатерина Умнягина", "Кухня на заказ", 5,
     "https://sun9-46.vkuserphoto.ru/s/v1/ig2/bVm2vnJWOD92dzHJ3_21NbqhcwF7DW7a05XzjaTWteG9Dviu9nt8LlA5bgzdbsBhGtYbrs7rvOMTylQQIV43cl4T.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&cs=128x0",
     "Заказывали у Романа кухню, всё очень понравилось! Подбирали всё до мелочей, и Рома всё исполнил, как мы хотели, за это мы ему очень благодарны. Всё сделано идеально, спрятали то, что не должно быть видно, и получилось очень красиво. Спасибо, Рома, за эту крутую современную кухню!!!", ""),
    ("Анастасия Зайцева", "Два шкафа, гардеробная", 5,
     "https://sun9-48.vkuserphoto.ru/s/v1/ig2/OdS0JaUmpkj7vzQLNz1oyY6PBksnYylZuY54LZ2vnibrqxNc0IimIjE6d6NWySeMm6N2MLIUHG6WLKtAFJ82ICwE.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,960x1280&from=bu&cs=128x0",
     "Заказывали у Романа два шкафа. Во время замеров у нас не было определённой идеи, как сделать вместительный шкаф в нашу небольшую спальню, ещё и с несущей колонной. Роман подкинул прекрасную идею, в итоге получился не просто шкаф, а целая угловая гардеробная, я была в восторге! Большой выбор цветов и текстур. Работа выполнена в оговорённый срок и качественно. Большое спасибо за эстетичное воплощение нашей мечты!", ""),
    ("Александр Карташев", "Видеоотзыв · Кухня на заказ", 5,
     "",
     "«Прям гордость квартиры! За приемлемую цену получили отличную кухню: выступ стояка закрыли пеналом, а в ножку барного стола встроили розетки».",
     "https://vk.ru/video_ext.php?oid=-212015374&id=456239019&hash=6abf300a7c2518d4"),
]

DEFAULT_DATA = {
    "seo": {
        "title": "Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ",
        "description": "Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и 3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97",
        "keywords": "кухни остров, кухни островский, кухни на заказ ростов, кухни батайск, кухни азов, мебель на заказ",
        "og_image": FAVICON_URL,
    },
    "brand": {
        "name": "Кухни Островский",
        "sub": "Ростов · Батайск · Азов",
        "logo_url": FAVICON_URL,
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
        "bg": WORKS[0][0],
    },
    "stats": {"bg": WORKS[1][0]},
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
        "text": "Позвоните или напишите нам в Telegram или MAX — расскажем про кухни и мебель, всё обсудим и договоримся о бесплатном замере.",
    },
    "works": {
        "bg": "https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=q3wKCscaGbBU8n3umOUNA0wOvLkQBDAVXIkzDrivHgk&cs=1280x0",
        "kicker": "Наши работы",
        "title": "Кухни и мебель, которые мы сделали",
        "subtitle": "Нажмите на фото, чтобы рассмотреть в большом размере.",
        "items": [{"url": u, "alt": a} for (u, a) in WORKS],
    },
    "reviews": {
        "bg": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0",
        "kicker": "Отзывы",
        "title": "Что говорят наши клиенты",
        "subtitle": "Реальные отзывы о нашей работе. Листайте влево-вправо.",
        "items": [{"name": n, "sub": s, "stars": st, "avatar": av, "text": t, "video": v}
                  for (n, s, st, av, t, v) in REVIEWS],
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
# Анимации (вставляются в PAGE — CSS в </head>, JS в </body>)
# =====================================================================
ANIM_STYLE = """<style id="goldAnimations">
@keyframes shimmerX{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes goldGradient{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes particleFloat{0%{transform:translateY(100vh) scale(.5);opacity:0}10%{opacity:1}90%{opacity:.85}100%{transform:translateY(-100px) scale(1.1);opacity:0}}
@keyframes rippleAnim{to{transform:scale(4);opacity:0}}
@keyframes glowPulse{0%,100%{text-shadow:0 0 10px rgba(236,207,160,.3)}50%{text-shadow:0 0 30px rgba(236,207,160,.8),0 0 60px rgba(212,175,106,.5)}}
.js .anim-visible h1,.js h1.anim-visible,.js .anim-visible h2,.js h2.anim-visible{background-position:0% 0}
.js .stat,.js .svc,.js .step,.js .guar,.js .city,.js .car-slide,.js .rev-card,.js .about-card,.js .about-body,.js .call-block,.js .contact-info,.js .sec-head{opacity:0;transform:translateY(30px);transition:opacity .9s cubic-bezier(.22,.61,.36,1),transform .9s cubic-bezier(.22,.61,.36,1)}
.js .stat.anim-in,.js .svc.anim-in,.js .step.anim-in,.js .guar.anim-in,.js .city.anim-in,.js .car-slide.anim-in,.js .rev-card.anim-in,.js .about-card.anim-in,.js .about-body.anim-in,.js .call-block.anim-in,.js .contact-info.anim-in,.js .sec-head.anim-in{opacity:1;transform:translateY(0)}
.js .stats .stat:nth-child(2){transition-delay:.12s}.js .stats .stat:nth-child(3){transition-delay:.24s}.js .stats .stat:nth-child(4){transition-delay:.36s}
.js .svc-grid .svc:nth-child(2){transition-delay:.1s}.js .svc-grid .svc:nth-child(3){transition-delay:.2s}.js .svc-grid .svc:nth-child(4){transition-delay:.3s}.js .svc-grid .svc:nth-child(5){transition-delay:.4s}.js .svc-grid .svc:nth-child(6){transition-delay:.5s}
.js .steps .step:nth-child(2){transition-delay:.1s}.js .steps .step:nth-child(3){transition-delay:.2s}.js .steps .step:nth-child(4){transition-delay:.3s}.js .steps .step:nth-child(5){transition-delay:.4s}.js .steps .step:nth-child(6){transition-delay:.5s}
.js .guar-grid .guar:nth-child(2){transition-delay:.12s}.js .guar-grid .guar:nth-child(3){transition-delay:.24s}.js .guar-grid .guar:nth-child(4){transition-delay:.36s}
.js .city-grid .city:nth-child(2){transition-delay:.14s}.js .city-grid .city:nth-child(3){transition-delay:.28s}
.btn{position:relative;overflow:hidden;transform:translateZ(0)}
.btn .ripple-el{position:absolute;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.55),transparent 70%);transform:scale(0);animation:rippleAnim .8s ease-out forwards;pointer-events:none}
.btn-solid{background-size:200% 200%;animation:goldGradient 6s ease infinite}
.c-action{position:relative;overflow:hidden}
#goldParticles{position:fixed;inset:0;z-index:1;pointer-events:none;overflow:hidden}
#goldParticles span{position:absolute;width:6px;height:6px;border-radius:50%;background:radial-gradient(circle,rgba(236,207,160,.9),rgba(212,175,106,.4) 40%,transparent 70%);box-shadow:0 0 12px rgba(236,207,160,.55);animation:particleFloat linear infinite}
.svc svg,.guar .ico,.c-ico,.vb-play{transition:transform .55s cubic-bezier(.34,1.56,.64,1),filter .35s}
.svc:hover svg{transform:scale(1.18) rotate(-8deg);filter:drop-shadow(0 0 12px rgba(236,207,160,.9))}
.guar:hover .ico{transform:scale(1.18) rotate(8deg);box-shadow:0 0 30px rgba(236,207,160,.5)}
.c-line:hover .c-ico{transform:scale(1.16) rotate(-6deg);box-shadow:0 0 22px rgba(236,207,160,.55)}
.rev-stars{background:linear-gradient(90deg,#eccfa0,#fff 50%,#eccfa0 100%);background-size:200% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 3s linear infinite}
.consult .phone,.call-block .cb-num{transition:transform .4s,filter .4s;display:inline-block}
.consult .phone:hover,.call-block .cb-num:hover{transform:scale(1.04);filter:drop-shadow(0 10px 30px rgba(212,175,106,.6))}
.eyebrow,.kicker,.sec-head .kicker{background:linear-gradient(90deg,rgba(236,207,160,.85),#fff 50%,rgba(236,207,160,.85));background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 4.5s linear infinite}
.car-slide img{transition:transform 1.1s cubic-bezier(.22,.61,.36,1)}
.car-slide:hover img{transform:scale(1.12)}
.stat:hover{box-shadow:0 22px 54px rgba(0,0,0,.42),0 0 34px rgba(212,175,106,.18)}
.svc:hover,.guar:hover,.city:hover,.step:hover,.rev-card:hover{box-shadow:0 26px 60px rgba(0,0,0,.5),0 0 40px rgba(212,175,106,.12)}
.gold-divider b{animation:glowPulse 2.8s ease-in-out infinite}
footer .flogo{background:linear-gradient(120deg,#fff,#eccfa0,#fff);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 6s linear infinite}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.01ms !important;transition-duration:.01ms !important}.js .stat,.js .svc,.js .step,.js .guar,.js .city,.js .car-slide,.js .rev-card,.js .about-card,.js .about-body,.js .call-block,.js .contact-info,.js .sec-head{opacity:1 !important;transform:none !important}}
</style>"""

ANIM_SCRIPT = """<script id="goldAnimationScript">
(function(){
  if(!('IntersectionObserver' in window))return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){
    document.querySelectorAll('.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head').forEach(function(el){el.classList.add('anim-in')});
    document.documentElement.classList.remove('js');return;
  }
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('anim-in');io.unobserve(e.target)}})},{threshold:0.12});
  document.querySelectorAll('.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head').forEach(function(el){io.observe(el)});
  var headIo=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('anim-visible');headIo.unobserve(e.target)}})},{threshold:0.5});
  document.querySelectorAll('h1,h2.k,.sec-head h2,.about-body h2,.contact-info h2,.cta h2').forEach(function(el){headIo.observe(el)});
  (function(){var c=document.createElement('div');c.id='goldParticles';document.body.appendChild(c);var n=window.innerWidth<700?14:28;for(var i=0;i<n;i++){var s=document.createElement('span');var sz=3+Math.random()*5;s.style.width=sz+'px';s.style.height=sz+'px';s.style.left=(Math.random()*100)+'%';s.style.animationDuration=(14+Math.random()*18)+'s';s.style.animationDelay=(-Math.random()*20)+'s';s.style.opacity=(0.35+Math.random()*0.55);c.appendChild(s)}})();
  document.addEventListener('click',function(e){var btn=e.target.closest('.btn, .c-action, .car-dot, .soc');if(!btn)return;var r=btn.getBoundingClientRect();var rp=document.createElement('span');rp.className='ripple-el';var s=Math.max(r.width,r.height);rp.style.width=s+'px';rp.style.height=s+'px';rp.style.left=(e.clientX-r.left-s/2)+'px';rp.style.top=(e.clientY-r.top-s/2)+'px';btn.appendChild(rp);setTimeout(function(){rp.remove()},850)},{passive:true});
  var fine=matchMedia('(hover:hover) and (pointer:fine)').matches;
  if(fine){
    document.querySelectorAll('.btn-solid, .c-action.c-call').forEach(function(btn){btn.addEventListener('mousemove',function(e){var r=btn.getBoundingClientRect();var dx=(e.clientX-r.left-r.width/2)/r.width;var dy=(e.clientY-r.top-r.height/2)/r.height;btn.style.transform='translate('+(dx*5)+'px,'+(dy*5-3)+'px)'});btn.addEventListener('mouseleave',function(){btn.style.transform=''})});
    document.querySelectorAll('.car-slide').forEach(function(slide){var img=slide.querySelector('img');if(!img)return;slide.addEventListener('mousemove',function(e){var r=slide.getBoundingClientRect();var dx=(e.clientX-r.left)/r.width-.5;var dy=(e.clientY-r.top)/r.height-.5;img.style.transform='scale(1.12) translate('+(dx*10)+'px,'+(dy*10)+'px)'});slide.addEventListener('mouseleave',function(){img.style.transform=''})});
    var bgs=document.querySelectorAll('.panel .bg');var ticking=false;
    function updateBgs(){if(ticking)return;ticking=true;requestAnimationFrame(function(){bgs.forEach(function(bg){var r=bg.parentElement.getBoundingClientRect();var center=r.top+r.height/2;var offset=(center-window.innerHeight/2)/window.innerHeight;bg.style.transform='translateY('+(-offset*25)+'px) scale('+(1+Math.abs(offset)*0.05)+')'});ticking=false})}
    window.addEventListener('scroll',updateBgs,{passive:true});updateBgs();
  }
  document.querySelectorAll('#top .eyebrow, #top h1, #top .sub, #top .btn-row').forEach(function(el,i){el.style.opacity='0';el.style.transform='translateY(30px)';el.style.transition='opacity 1s cubic-bezier(.22,.61,.36,1), transform 1s cubic-bezier(.22,.61,.36,1)';setTimeout(function(){el.style.opacity='1';el.style.transform='none'},200+i*180)});
})();
</script>"""


def _inject_animations(html):
    if "</head>" in html and "goldAnimations" not in html:
        html = html.replace("</head>", ANIM_STYLE + "\n</head>", 1)
    if "</body>" in html and "goldAnimationScript" not in html:
        html = html.replace("</body>", ANIM_SCRIPT + "\n</body>", 1)
    return html


def _read_page():
    try:
        with open(os.path.join(ROOT, "page.html"), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("[page] error: " + str(e), flush=True)
        return "<!DOCTYPE html><html><body><h1>page.html не найден</h1></body></html>"


# =====================================================================
# Прокси картинок VK (обход hotlink-защиты)
# =====================================================================
_img_cache = {}
_img_lock = threading.Lock()
_IMG_TTL = 86400 * 7


def _fetch_image(url):
    now = time.time()
    with _img_lock:
        cached = _img_cache.get(url)
        if cached and now - cached[1] < _IMG_TTL:
            return cached[0], cached[2]
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Referer": "https://vk.com/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            ct = resp.headers.get("Content-Type", "image/jpeg")
            with _img_lock:
                _img_cache[url] = (data, now, ct)
            return data, ct
    except Exception as e:
        print("[img] error: " + str(e), flush=True)
        return None, None


def _proxify_urls(html):
    pattern = re.compile(r'https://sun9-\d+\.vkuserphoto\.ru/[^\s"\')<>]+')

    def repl(m):
        url = m.group(0)
        b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
        return "/img?u=" + b64

    return pattern.sub(repl, html)


# =====================================================================
# Supabase (фоновая синхронизация)
# =====================================================================
_sb_read = None
_sb_write = None
_sb_lock = threading.Lock()


def _sb_read_client():
    global _sb_read
    with _sb_lock:
        if _sb_read is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_ANON:
            try:
                _sb_read = create_client(SUPABASE_URL, SUPABASE_ANON)
            except Exception as e:
                print("[sb read] " + str(e), flush=True)
        return _sb_read


def _sb_write_client():
    global _sb_write
    with _sb_lock:
        if _sb_write is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_SERVICE:
            try:
                _sb_write = create_client(SUPABASE_URL, SUPABASE_SERVICE)
            except Exception as e:
                print("[sb write] " + str(e), flush=True)
        return _sb_write


def _sb_exec(fn, timeout=4):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(fn).result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        print("[sb] TIMEOUT " + str(timeout) + "s", flush=True)
        return None
    except Exception as e:
        print("[sb] error: " + str(e), flush=True)
        return None


_auth_lock = threading.Lock()
_sessions = {}


def _new_session():
    t = secrets.token_urlsafe(32)
    with _auth_lock:
        _sessions[t] = time.time() + SESSION_TTL
    return t


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


_data_cache = None
_cache_ts = 0.0
_data_lock = threading.Lock()
_seeded = False


def _merge_deep(base, over):
    """over перезаписывает base; словари сливаются рекурсивно."""
    if not isinstance(base, dict) or not isinstance(over, dict):
        return over
    result = dict(base)
    for k, v in over.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge_deep(result[k], v)
        else:
            result[k] = json.loads(json.dumps(v))
    return result


def _fetch_from_supabase(timeout=4):
    sb = _sb_read_client()
    if sb is None:
        return None
    res = _sb_exec(lambda: sb.table("site_content").select("data").eq("id", DATA_ROW_ID).execute(),
                   timeout=timeout)
    if res is not None and getattr(res, "data", None):
        raw = res.data[0].get("data") or {}
        if raw and isinstance(raw, dict) and len(raw) >= 3:
            return raw
    return None


def _save_to_supabase(data):
    sb = _sb_write_client()
    if sb is None:
        print("[save] service_role недоступен", flush=True)
        return False
    res = _sb_exec(lambda: sb.table("site_content").upsert({"id": DATA_ROW_ID, "data": data}).execute(),
                   timeout=8)
    if res is not None:
        print("[save] OK", flush=True)
        return True
    print("[save] FAIL", flush=True)
    return False


def _bg_refresh():
    global _data_cache, _cache_ts, _seeded
    raw = _fetch_from_supabase(timeout=6)
    if raw is None:
        if not _seeded:
            _seeded = True
            _save_to_supabase(json.loads(json.dumps(DEFAULT_DATA)))
        return
    data = _merge_deep(json.loads(json.dumps(DEFAULT_DATA)), raw)
    with _data_lock:
        _data_cache = data
        _cache_ts = time.time()
    print("[bg] кэш обновлён из БД", flush=True)


def load_data(force=False):
    """Никогда не блокирует: отдаёт кэш мгновенно, фоново обновляет из БД."""
    global _data_cache, _cache_ts
    now = time.time()
    with _data_lock:
        if _data_cache is not None and now - _cache_ts < CACHE_TTL:
            return _data_cache
        if _data_cache is None:
            _data_cache = json.loads(json.dumps(DEFAULT_DATA))
            _cache_ts = now
        threading.Thread(target=_bg_refresh, daemon=True).start()
        return _data_cache


def save_data(data):
    """Синхронная запись в Supabase — админ ждёт результат."""
    global _data_cache, _cache_ts
    with _data_lock:
        _data_cache = data
        _cache_ts = time.time()
    return _save_to_supabase(data)


# =====================================================================
# render_page — подстановки из CMS в PAGE
# =====================================================================
def render_page():
    html = _read_page()
    d = load_data()
    if not d or not isinstance(d, dict) or len(d) < 3:
        return _inject_animations(_proxify_urls(html))

    b = d.get("brand", {}) or {}
    seo = d.get("seo", {}) or {}
    hero = d.get("hero", {}) or {}
    about = d.get("about", {}) or {}
    works = d.get("works", {}) or {}
    reviews = d.get("reviews", {}) or {}
    services = d.get("services", {}) or {}
    proc = d.get("process", {}) or {}
    guar = d.get("guarantees", {}) or {}
    cities = d.get("cities", {}) or {}
    cta = d.get("cta", {}) or {}
    ftr = d.get("footer", {}) or {}

    if seo.get("title") and seo["title"] != DEFAULT_DATA["seo"]["title"]:
        html = html.replace("<title>" + DEFAULT_DATA["seo"]["title"] + "</title>",
                            "<title>" + seo["title"] + "</title>")
    if b.get("name") and b["name"] != "Кухни Островский":
        html = html.replace('<span class="name">Кухни Островский</span>',
                            '<span class="name">' + b["name"] + '</span>')
    if b.get("sub") and b["sub"] != "Ростов · Батайск · Азов":
        html = html.replace('<span class="sub">Ростов · Батайск · Азов</span>',
                            '<span class="sub">' + b["sub"] + '</span>')
    if b.get("phone") and b["phone"] != "+7 (950) 846-53-97":
        html = html.replace("+7 (950) 846-53-97", b["phone"])
    if b.get("phone_raw") and b["phone_raw"] != "+79508465397":
        html = html.replace("tel:+79508465397", "tel:" + b["phone_raw"])
    if b.get("telegram") and b["telegram"] != "https://t.me/fanny161":
        html = html.replace("https://t.me/fanny161", b["telegram"])
    if b.get("vk") and b["vk"] != "https://vk.com/mebel.ostrovsky":
        html = html.replace("https://vk.com/mebel.ostrovsky", b["vk"])
    if b.get("logo_url") and "2sp8pX" not in b["logo_url"]:
        html = html.replace(DEFAULT_DATA["brand"]["logo_url"], b["logo_url"])

    if hero.get("eyebrow") and hero["eyebrow"] != "Мебель и кухни на заказ":
        html = html.replace('<span class="eyebrow">Мебель и кухни на заказ</span>',
                            '<span class="eyebrow">' + hero["eyebrow"] + '</span>')
    if hero.get("title_before") or hero.get("title_em"):
        old = '<h1 id="heroTitle">Мебель, которая <em class="shimmer">создаёт настроение</em></h1>'
        new = ('<h1 id="heroTitle">' + hero.get("title_before", "Мебель, которая ") +
               '<em class="shimmer">' + hero.get("title_em", "создаёт настроение") + '</em></h1>')
        html = html.replace(old, new)
    if hero.get("btn1") and hero["btn1"] != "Получить консультацию":
        html = html.replace('>Получить консультацию<', '>' + hero["btn1"] + '<')
    if hero.get("btn2") and hero["btn2"] != "Смотреть работы":
        html = html.replace('>Смотреть работы<', '>' + hero["btn2"] + '<')

    if about.get("photo") and "mVchNnp1" not in about["photo"]:
        html = html.replace("https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg",
                            about["photo"])
    if about.get("name") and about["name"] != "Роман Островский":
        html = html.replace(">Роман Островский</h3>", ">" + about["name"] + "</h3>")
    if about.get("role") and about["role"] != "Руководитель мебельной мастерской Островского":
        html = html.replace(">Руководитель мебельной мастерской Островского<",
                            ">" + about["role"] + "<")
    if about.get("title") and about["title"] != "Кухни и мебель под ключ — с заботой о деталях":
        html = html.replace(">Кухни и мебель под ключ — с заботой о деталях<",
                            ">" + about["title"] + "<")

    for k in ("hero", "stats", "about", "consult", "works", "reviews",
              "services", "process", "guarantees", "cities", "cta", "contacts"):
        sec = d.get(k, {}) or {}
        new_bg = sec.get("bg")
        old_bg = (DEFAULT_DATA.get(k) or {}).get("bg") if k in DEFAULT_DATA else None
        if new_bg and old_bg and new_bg != old_bg:
            html = html.replace(old_bg, new_bg)

    items = works.get("items")
    if isinstance(items, list) and items:
        block = "".join(
            '<div class="car-slide"><img loading="lazy" src="' + (it or {}).get("url", "") +
            '" alt="' + (it or {}).get("alt", "") + '"></div>'
            for it in items if (it or {}).get("url")
        )
        if block:
            s = '<div class="car-track" id="carTrack">'
            e = '</div>\n      <button class="car-nav car-next" id="carNext">'
            i1 = html.find(s)
            if i1 >= 0:
                i2 = html.find(e, i1)
                if i2 >= 0:
                    html = html[:i1 + len(s)] + block + html[i2:]

    rev_items = reviews.get("items")
    if isinstance(rev_items, list) and rev_items:
        block = ""
        for r in rev_items:
            r = r or {}
            name = r.get("name", ""); sub = r.get("sub", "")
            stars = "★" * int(r.get("stars", 5))
            ava = r.get("avatar", ""); text = r.get("text", ""); video = r.get("video", "")
            ava_html = ('<img class="rev-ava" loading="lazy" width="50" height="50" src="' + ava +
                        '" alt="Отзыв: ' + name + '">') if ava else ""
            video_html = ""
            if video:
                video_html = ('<div class="rev-video"><div class="video-box" data-src="' + video +
                              '"><span class="vb-play"><svg viewBox="0 0 24 24">'
                              '<path d="M8 5v14l11-7z"/></svg></span></div></div>')
            block += ('<div class="rev-card"><div class="rev-head">' + ava_html +
                      '<div><div class="rev-name">' + name + '</div>' +
                      '<div class="rev-sub">' + sub + '</div></div>' +
                      '<div class="rev-stars">' + stars + '</div></div>' +
                      video_html + '<p class="rev-text">' + text + '</p></div>')
        if block:
            s = '<div class="car-track rev-track" id="revTrack">'
            e = '</div>\n      <button class="car-nav car-next" id="revNext">'
            i1 = html.find(s)
            if i1 >= 0:
                i2 = html.find(e, i1)
                if i2 >= 0:
                    html = html[:i1 + len(s)] + block + html[i2:]

    for key, box, cls in (("services", "svcGrid", "svc-grid"),
                          ("process", "stepsBox", "steps"),
                          ("guarantees", "guarGrid", "guar-grid"),
                          ("cities", "cityGrid", "city-grid")):
        sec = d.get(key, {}) or {}
        its = sec.get("items")
        if isinstance(its, list) and its:
            block = ""
            for it in its:
                it = it or {}
                if key == "services":
                    block += ('<div class="svc reveal"><svg viewBox="0 0 24 24"><path d="' +
                              it.get("icon", "") + '"/></svg><h3>' + it.get("title", "") +
                              '</h3><p>' + it.get("text", "") + '</p></div>')
                elif key == "process":
                    block += ('<div class="step reveal"><div class="n">' + it.get("n", "") +
                              '</div><h3>' + it.get("title", "") + '</h3><p>' +
                              it.get("text", "") + '</p></div>')
                elif key == "guarantees":
                    block += ('<div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24">'
                              '<path d="' + it.get("icon", "") + '"/></svg></div><h3>' +
                              it.get("title", "") + '</h3><p>' + it.get("text", "") + '</p></div>')
                elif key == "cities":
                    block += ('<div class="city reveal"><div class="city-name">' +
                              it.get("name", "") + '</div><div class="city-line"></div><p>' +
                              it.get("text", "") + '</p></div>')
            if block:
                old = '<div class="' + cls + '" id="' + box + '"></div>'
                new = '<div class="' + cls + '" id="' + box + '">' + block + '</div>'
                html = html.replace(old, new)

    if cta.get("title") and cta["title"] != "Готовы обсудить вашу мебель?":
        html = html.replace(">Готовы обсудить вашу мебель?<", ">" + cta["title"] + "<")
    if ftr.get("line") and ftr["line"] != "Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов":
        html = html.replace(">Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов<",
                            ">" + ftr["line"] + "<")

    html = _proxify_urls(html)
    return _inject_animations(html)


# =====================================================================
# Favicon
# =====================================================================
_fc = {"data": None, "ts": 0.0}
_ic = {"ico": None, "png16": None, "png32": None, "png180": None}


def _make_icons(data):
    try:
        from PIL import Image
    except Exception:
        return
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        _ic["ico"] = buf.getvalue()

        def png(size):
            c = img.copy(); c.thumbnail((size, size))
            b = io.BytesIO(); c.save(b, format="PNG"); return b.getvalue()
        _ic["png16"] = png(16); _ic["png32"] = png(32); _ic["png180"] = png(180)
    except Exception:
        pass


def get_favicon():
    now = time.time()
    if _fc["data"] is None or now - _fc["ts"] > 3600:
        try:
            req = urllib.request.Request(FAVICON_URL, headers={
                "User-Agent": "Mozilla/5.0", "Referer": "https://vk.com/"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                _fc["data"] = data; _fc["ts"] = now; _make_icons(data)
        except Exception:
            return None
    return _fc["data"]


# =====================================================================
# Админка (HTML)
# =====================================================================
ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Вход</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:linear-gradient(135deg,#0e0c09,#1a1611);color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.2);border-radius:20px;padding:42px 38px;width:100%;max-width:420px}
h1{font-family:Georgia,serif;font-size:28px;color:#fff;margin-bottom:8px;text-align:center;background:linear-gradient(120deg,#fff,#eccfa0);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p.sub{color:#b9ad9a;font-size:13.5px;text-align:center;margin-bottom:28px}
label{display:block;color:#eccfa0;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:600}
input{width:100%;padding:14px 16px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;font-size:15px;font-family:inherit;margin-bottom:18px}
input:focus{outline:none;border-color:#d4af6a;box-shadow:0 0 0 4px rgba(212,175,106,.15)}
button{width:100%;padding:15px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;font-size:14px;letter-spacing:1.2px;text-transform:uppercase;border:none;border-radius:12px;cursor:pointer}
.err{background:rgba(220,60,60,.14);border:1px solid rgba(220,60,60,.4);color:#ff9a9a;padding:12px 14px;border-radius:10px;font-size:13px;margin-bottom:18px;text-align:center}
</style></head><body>
<form class="card" method="POST" action="/admin/login">
<h1>Кухни Островский</h1><p class="sub">Вход в панель управления</p>__ERROR__
<label>Логин</label><input type="text" name="login" required autofocus>
<label>Пароль</label><input type="password" name="password" required>
<button type="submit">Войти</button></form></body></html>"""


ADMIN_HTML = r"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Админка</title><style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--gold:#d4af6a;--gold-soft:#eccfa0;--bg:#0e0c09;--line:rgba(236,207,160,.16)}
body{font-family:system-ui,sans-serif;background:var(--bg);color:#f5efe3;min-height:100vh;line-height:1.55}
body::before{content:"";position:fixed;inset:0;z-index:-1;background:radial-gradient(1200px 700px at 85% -10%,rgba(212,175,106,.14),transparent 60%),linear-gradient(180deg,#12100b,#0c0a07 45%,#100d09)}
@keyframes particleFloat{0%{transform:translateY(100vh) scale(.5);opacity:0}10%{opacity:1}90%{opacity:.85}100%{transform:translateY(-100px) scale(1.1);opacity:0}}
#goldParticles{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
#goldParticles span{position:absolute;width:5px;height:5px;border-radius:50%;background:radial-gradient(circle,rgba(236,207,160,.9),rgba(212,175,106,.4) 40%,transparent 70%);box-shadow:0 0 12px rgba(236,207,160,.55);animation:particleFloat linear infinite}
header{background:rgba(14,12,9,.95);border-bottom:1px solid var(--line);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;flex-wrap:wrap;gap:12px}
.brand{font-family:Georgia,serif;font-size:20px;background:linear-gradient(120deg,#fff,var(--gold-soft));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.brand span{color:var(--gold-soft);font-size:13px;margin-left:8px;-webkit-text-fill-color:var(--gold-soft)}
.actions{display:flex;gap:10px;flex-wrap:wrap}
.btn{position:relative;overflow:hidden;padding:10px 18px;border-radius:10px;border:1px solid var(--line);background:rgba(255,255,255,.04);color:#f5efe3;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px;font-family:inherit;transition:.3s}
.btn:hover{border-color:var(--gold);color:var(--gold-soft);transform:translateY(-2px)}
.btn-gold{background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;border:none}
.btn-red{background:rgba(220,60,60,.14);border-color:rgba(220,60,60,.35);color:#ff9a9a}
.layout{display:flex;min-height:calc(100vh - 65px)}
nav.side{width:240px;background:rgba(0,0,0,.28);border-right:1px solid var(--line);padding:16px 0;flex-shrink:0;overflow-y:auto;position:sticky;top:65px;height:calc(100vh - 65px)}
nav.side a{display:block;padding:12px 22px;color:#b9ad9a;font-size:14px;border-left:3px solid transparent;cursor:pointer;user-select:none;transition:.25s}
nav.side a:hover{color:#fff;background:rgba(255,255,255,.04);padding-left:26px}
nav.side a.active{color:var(--gold-soft);border-left-color:var(--gold);background:rgba(212,175,106,.08)}
main{flex:1;padding:28px 34px;max-width:1200px;overflow-x:hidden}
h2{font-family:Georgia,serif;font-size:26px;margin-bottom:6px;background:linear-gradient(120deg,#fff,var(--gold-soft));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p.hint{color:#b9ad9a;font-size:13px;margin-bottom:22px}
.field{margin-bottom:16px}
.field label{display:block;color:var(--gold-soft);font-size:11.5px;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:7px;font-weight:600}
.field input,.field textarea{width:100%;padding:11px 14px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.12);border-radius:9px;color:#fff;font-size:14px;font-family:inherit;transition:.25s}
.field textarea{resize:vertical;min-height:80px}
.field input:focus,.field textarea:focus{outline:none;border-color:var(--gold);box-shadow:0 0 0 4px rgba(212,175,106,.15);background:rgba(0,0,0,.5)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.item{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:18px;margin-bottom:14px;transition:.3s}
.item:hover{border-color:rgba(236,207,160,.28);transform:translateY(-2px)}
.item-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:10px;flex-wrap:wrap}
.item-head strong{color:var(--gold-soft);font-size:13.5px}
.mini{padding:6px 12px;font-size:12px;border-radius:8px}
.img-preview{width:100%;max-width:220px;height:auto;border-radius:10px;border:1px solid var(--line);margin-top:8px;display:block}
.toast{position:fixed;bottom:24px;left:50%;transform:translate(-50%,140%);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;padding:14px 26px;border-radius:12px;font-weight:700;font-size:14px;z-index:9999;transition:transform .4s;box-shadow:0 18px 44px rgba(212,175,106,.45)}
.toast.show{transform:translate(-50%,0)}
.toast.err{background:linear-gradient(135deg,#ff8a8a,#e04a4a);color:#fff}
.drop{display:block;border:2px dashed var(--line);border-radius:12px;padding:22px;text-align:center;color:#b9ad9a;font-size:13px;cursor:pointer;margin-top:8px;transition:.25s}
.drop:hover{border-color:var(--gold);color:var(--gold-soft);background:rgba(212,175,106,.05)}
.status{font-size:12px;padding:6px 12px;border-radius:8px;display:inline-block}
.status.ok{background:rgba(80,200,120,.15);color:#7ee0a0;border:1px solid rgba(80,200,120,.4)}
.status.bad{background:rgba(220,60,60,.15);color:#ff9a9a;border:1px solid rgba(220,60,60,.4)}
.status.saving{background:rgba(212,175,106,.2);color:#eccfa0;border:1px solid rgba(212,175,106,.5)}
@media(max-width:800px){nav.side{position:fixed;left:0;top:65px;bottom:0;transform:translateX(-100%);transition:.3s;z-index:99}nav.side.open{transform:none}.row{grid-template-columns:1fr}main{padding:20px 18px}}
</style></head><body>
<header>
<div style="display:flex;align-items:center;gap:14px"><div class="brand">Кухни Островский<span>CMS</span></div><span class="status" id="status">Загрузка...</span></div>
<div class="actions"><a class="btn" href="/" target="_blank">Сайт</a><button class="btn btn-gold" id="saveBtn">Сохранить</button><a class="btn btn-red" href="/admin/logout">Выйти</a></div>
</header>
<div class="layout">
<nav class="side" id="sideNav">
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
<main id="main"><p class="hint">Загрузка данных...</p></main>
</div>
<div class="toast" id="toast"></div>
<script>
(function(){var c=document.createElement('div');c.id='goldParticles';document.body.appendChild(c);for(var i=0;i<18;i++){var s=document.createElement('span');var sz=3+Math.random()*4;s.style.width=sz+'px';s.style.height=sz+'px';s.style.left=(Math.random()*100)+'%';s.style.animationDuration=(14+Math.random()*18)+'s';s.style.animationDelay=(-Math.random()*20)+'s';s.style.opacity=(0.3+Math.random()*0.5);c.appendChild(s);}})();
var DATA=null;var currentTab='hero';
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function toast(m,e){var t=document.getElementById('toast');t.textContent=m;t.classList.toggle('err',!!e);t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2500)}
function setStatus(text,cls){var el=document.getElementById('status');el.className='status '+(cls||'ok');el.textContent=text}
function getPath(o,p){return p.split('.').reduce(function(a,k){return a==null?undefined:a[k]},o)}
function setPath(o,p,v){var a=p.split('.');var c=o;for(var i=0;i<a.length-1;i++){var k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k]}c[a[a.length-1]]=v}
function loadData(){fetch('/admin/api/data',{credentials:'same-origin'}).then(function(r){if(r.status===401){location.href='/admin/login';return null}if(!r.ok)throw new Error('HTTP '+r.status);return r.json()}).then(function(j){if(!j)return;DATA=j;setStatus('Готово','ok');render()}).catch(function(e){setStatus('Ошибка загрузки','bad');document.getElementById('main').innerHTML='<h2>Ошибка</h2><p class="hint">'+esc(e.message)+'</p>'})}
function saveAll(){if(!DATA){toast('Нет данных',true);return}setStatus('Сохранение...','saving');fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)}).then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);return r.json()}).then(function(j){if(j&&j.ok){setStatus('Сохранено','ok');toast('Сохранено')}else{setStatus('Ошибка','bad');toast('Ошибка сохранения',true)}}).catch(function(e){setStatus('Ошибка','bad');toast('Ошибка: '+e.message,true)})}
function field(l,p,o){o=o||{};var v=getPath(DATA,p);var html;if(o.rows){html='<textarea data-path="'+p+'" rows="'+o.rows+'">'+esc(v)+'</textarea>'}else{html='<input type="text" data-path="'+p+'" value="'+esc(v)+'">'}return '<div class="field"><label>'+l+'</label>'+html+'</div>'}
function imgField(l,p){var v=getPath(DATA,p);var u='data-upload-path="'+p+'"';var prev=v?'<img class="img-preview" src="'+esc(v)+'">':'';return '<div class="field"><label>'+l+'</label><input type="text" data-path="'+p+'" value="'+esc(v)+'"><label class="drop" '+u+'>загрузить файл<input type="file" accept="image/*" style="display:none"></label>'+prev+'</div>'}
function render(){if(!DATA)return;var map={seo:rSeo,brand:rBrand,hero:rHero,about:rAbout,consult:rConsult,works:rWorks,reviews:rReviews,services:rServices,process:rProcess,guarantees:rGuarantees,cities:rCities,cta:rCta,contacts:rContacts,footer:rFooter};var fn=map[currentTab];document.getElementById('main').innerHTML=fn?fn():'<h2>Раздел</h2>';bindInputs()}
function bindInputs(){document.querySelectorAll('[data-path]').forEach(function(el){el.addEventListener('input',function(){setPath(DATA,el.dataset.path,el.value)})});document.querySelectorAll('[data-upload-path]').forEach(function(lbl){var fi=lbl.querySelector('input[type="file"]');if(!fi)return;fi.addEventListener('change',function(){uploadImage(fi,lbl.dataset.uploadPath)})})}
function uploadImage(input,path){var f=input.files[0];if(!f)return;if(f.size>8*1024*1024){toast('Файл > 8 МБ',true);return}var fd=new FormData();fd.append('file',f);toast('Загрузка...');fetch('/admin/api/upload',{method:'POST',body:fd,credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){if(j.url){setPath(DATA,path,j.url);render();toast('Загружено')}else{toast('Ошибка',true)}}).catch(function(){toast('Ошибка загрузки',true)})}
function rSeo(){return '<h2>SEO</h2><p class="hint">Мета-теги.</p>'+field('Title','seo.title',{rows:2})+field('Description','seo.description',{rows:3})+field('Keywords','seo.keywords',{rows:3})+field('OG-картинка','seo.og_image')}
function rBrand(){return '<h2>Бренд</h2>'+field('Название','brand.name')+field('Подзаголовок','brand.sub')+imgField('Логотип','brand.logo_url')+field('Телефон (визуал)','brand.phone')+field('Телефон (tel:)','brand.phone_raw')+field('Telegram','brand.telegram')+field('VK','brand.vk')}
function rHero(){return '<h2>Главный экран</h2>'+field('Надзаголовок','hero.eyebrow')+field('Заголовок до','hero.title_before')+field('Заголовок выделенный','hero.title_em')+field('Подзаголовок','hero.sub',{rows:3})+field('Кнопка 1','hero.btn1')+field('Кнопка 2','hero.btn2')+imgField('Фон','hero.bg')}
function rAbout(){return '<h2>О специалисте</h2>'+imgField('Фото','about.photo')+field('Имя','about.name')+field('Должность','about.role')+field('Описание','about.text',{rows:3})+field('Заголовок','about.title')+field('Текст','about.body',{rows:4})+imgField('Фон','about.bg')}
function rConsult(){return '<h2>Консультация</h2>'+field('Надзаголовок','consult.kicker')+field('Заголовок','consult.title')+field('Текст','consult.text',{rows:4})+imgField('Фон','consult.bg')}
function rWorks(){var items=(DATA.works&&DATA.works.items)||[];var html='<h2>Работы</h2>'+field('Надзаголовок','works.kicker')+field('Заголовок','works.title')+field('Подзаголовок','works.subtitle')+imgField('Фон','works.bg')+'<div class="item-head"><strong>Фото ('+items.length+')</strong></div>';items.forEach(function(it,i){html+='<div class="item"><div class="item-head"><strong>Фото '+(i+1)+'</strong><div><button class="btn mini" data-action="moveItem" data-list="works.items" data-index="'+i+'" data-delta="-1">↑</button> <button class="btn mini" data-action="moveItem" data-list="works.items" data-index="'+i+'" data-delta="1">↓</button> <button class="btn btn-red mini" data-action="delItem" data-list="works.items" data-index="'+i+'">Удалить</button></div></div>'+imgField('Картинка','works.items.'+i+'.url')+field('Alt','works.items.'+i+'.alt')+'</div>'});html+='<button class="btn" data-action="addItem" data-list="works.items" data-template=\'{"url":"","alt":""}\'>+ Добавить фото</button>';return html}
function rReviews(){var items=(DATA.reviews&&DATA.reviews.items)||[];var html='<h2>Отзывы</h2>'+field('Надзаголовок','reviews.kicker')+field('Заголовок','reviews.title')+field('Подзаголовок','reviews.subtitle')+imgField('Фон','reviews.bg')+'<div class="item-head"><strong>Отзывы ('+items.length+')</strong></div>';items.forEach(function(it,i){html+='<div class="item"><div class="item-head"><strong>'+esc(it.name||('Отзыв '+(i+1)))+'</strong><div><button class="btn mini" data-action="moveItem" data-list="reviews.items" data-index="'+i+'" data-delta="-1">↑</button> <button class="btn mini" data-action="moveItem" data-list="reviews.items" data-index="'+i+'" data-delta="1">↓</button> <button class="btn btn-red mini" data-action="delItem" data-list="reviews.items" data-index="'+i+'">Удалить</button></div></div><div class="row">'+field('Имя','reviews.items.'+i+'.name')+field('Подпись','reviews.items.'+i+'.sub')+'</div>'+field('Звёзд','reviews.items.'+i+'.stars')+imgField('Аватар','reviews.items.'+i+'.avatar')+field('Текст','reviews.items.'+i+'.text',{rows:5})+field('Видео URL','reviews.items.'+i+'.video')+'</div>'});html+='<button class="btn" data-action="addItem" data-list="reviews.items" data-template=\'{"name":"","sub":"","stars":5,"avatar":"","text":"","video":""}\'>+ Добавить отзыв</button>';return html}
function rServices(){var items=(DATA.services&&DATA.services.items)||[];var html='<h2>Услуги</h2>'+field('Надзаголовок','services.kicker')+field('Заголовок','services.title')+field('Подзаголовок','services.subtitle')+imgField('Фон','services.bg');items.forEach(function(it,i){html+='<div class="item"><div class="item-head"><strong>'+esc(it.title||('Услуга '+(i+1)))+'</strong><button class="btn btn-red mini" data-action="delItem" data-list="services.items" data-index="'+i+'">Удалить</button></div>'+field('Название','services.items.'+i+'.title')+field('Описание','services.items.'+i+'.text',{rows:2})+field('SVG-иконка','services.items.'+i+'.icon')+'</div>'});html+='<button class="btn" data-action="addItem" data-list="services.items" data-template=\'{"title":"","text":"","icon":""}\'>+ Добавить</button>';return html}
function rProcess(){var items=(DATA.process&&DATA.process.items)||[];var html='<h2>Этапы</h2>'+field('Надзаголовок','process.kicker')+field('Заголовок','process.title')+imgField('Фон','process.bg');items.forEach(function(it,i){html+='<div class="item"><div class="item-head"><strong>'+esc((it.n||'')+' '+(it.title||''))+'</strong><button class="btn btn-red mini" data-action="delItem" data-list="process.items" data-index="'+i+'">Удалить</button></div><div class="row">'+field('Номер','process.items.'+i+'.n')+field('Заголовок','process.items.'+i+'.title')+'</div>'+field('Текст','process.items.'+i+'.text',{rows:2})+'</div>'});html+='<button class="btn" data-action="addItem" data-list="process.items" data-template=\'{"n":"","title":"","text":""}\'>+ Добавить</button>';return html}
function rGuarantees(){var items=(DATA.guarantees&&DATA.guarantees.items)||[];var html='<h2>Гарантии</h2>'+field('Надзаголовок','guarantees.kicker')+field('Заголовок','guarantees.title')+imgField('Фон','guarantees.bg');items.forEach(function(it,i){html+='<div class="item"><div class="item-head"><strong>'+esc(it.title||('Гарантия '+(i+1)))+'</strong><button class="btn btn-red mini" data-action="delItem" data-list="guarantees.items" data-index="'+i+'">Удалить</button></div>'+field('Заголовок','guarantees.items.'+i+'.title')+field('Текст','guarantees.items.'+i+'.text',{rows:2})+field('SVG-иконка','guarantees.items.'+i+'.icon')+'</div>'});html+='<button class="btn" data-action="addItem" data-list="guarantees.items" data-template=\'{"title":"","text":"","icon":""}\'>+ Добавить</button>';return html}
function rCities(){var items=(DATA.cities&&DATA.cities.items)||[];var html='<h2>Города</h2>'+field('Надзаголовок','cities.kicker')+field('Заголовок','cities.title')+field('Подзаголовок','cities.subtitle')+imgField('Фон','cities.bg');items.forEach(function(it,i){html+='<div class="item"><div class="item-head"><strong>'+esc(it.name||('Город '+(i+1)))+'</strong><button class="btn btn-red mini" data-action="delItem" data-list="cities.items" data-index="'+i+'">Удалить</button></div>'+field('Название','cities.items.'+i+'.name')+field('Описание','cities.items.'+i+'.text',{rows:2})+'</div>'});html+='<button class="btn" data-action="addItem" data-list="cities.items" data-template=\'{"name":"","text":""}\'>+ Добавить</button>';return html}
function rCta(){return '<h2>CTA</h2>'+field('Заголовок','cta.title')+field('Текст','cta.text',{rows:3})+field('Кнопка','cta.button')+imgField('Фон','cta.bg')}
function rContacts(){return '<h2>Контакты</h2>'+field('Надзаголовок','contacts.kicker')+field('Заголовок','contacts.title')+field('Подзаголовок','contacts.subtitle',{rows:2})+field('Регионы','contacts.regions')+imgField('Фон','contacts.bg')}
function rFooter(){return '<h2>Подвал</h2>'+field('Строка','footer.line')+field('Копирайт','footer.copyright')}
function addItem(list,tpl){var arr=getPath(DATA,list);if(!Array.isArray(arr))arr=[];var t=typeof tpl==='string'?JSON.parse(tpl):tpl;arr.push(JSON.parse(JSON.stringify(t)));setPath(DATA,list,arr);render();toast('Добавлено — не забудьте Сохранить')}
function delItem(list,index){if(!confirm('Удалить?'))return;var arr=getPath(DATA,list);arr.splice(index,1);setPath(DATA,list,arr);render();toast('Удалено — не забудьте Сохранить')}
function moveItem(list,index,delta){var arr=getPath(DATA,list);var j=index+delta;if(j<0||j>=arr.length)return;var tmp=arr[index];arr[index]=arr[j];arr[j]=tmp;render()}
document.addEventListener('click',function(e){var t=e.target;var tabLink=t.closest('nav.side a[data-tab]');if(tabLink){document.querySelectorAll('nav.side a').forEach(function(y){y.classList.remove('active')});tabLink.classList.add('active');currentTab=tabLink.dataset.tab;render();var nav=document.querySelector('nav.side');if(nav)nav.classList.remove('open');return}if(t.closest('#saveBtn')){e.preventDefault();saveAll();return}var btn=t.closest('[data-action]');if(btn){var action=btn.dataset.action;var list=btn.dataset.list;var index=parseInt(btn.dataset.index||'0',10);var delta=parseInt(btn.dataset.delta||'0',10);var tpl=btn.dataset.template;if(action==='addItem'){addItem(list,tpl)}else if(action==='delItem'){delItem(list,index)}else if(action==='moveItem'){moveItem(list,index,delta)}return}});
loadData();
</script>
</body></html>"""


# =====================================================================
# HTTP сервер
# =====================================================================
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
            return data, b"application/octet-stream", "file"
    return None, None, None


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

    def _send(self, code, body, ctype="text/plain; charset=utf-8", cache="no-cache", gzip_ok=True):
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
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n <= 0 or n > MAX_UPLOAD * 3:
            return b""
        return self.rfile.read(n)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?")[0]

        # --- Прокси VK-картинок ---
        if path == "/img":
            qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            u = (qs.get("u") or [""])[0]
            if not u:
                self._send(404, "not found", "text/plain"); return
            try:
                padding = "=" * (-len(u) % 4)
                url = base64.urlsafe_b64decode(u + padding).decode("utf-8")
            except Exception:
                self._send(400, "bad url", "text/plain"); return
            if not url.startswith("https://") or "vkuserphoto.ru" not in url:
                self._send(403, "forbidden", "text/plain"); return
            data, ct = _fetch_image(url)
            if data is None:
                self._redirect(url); return
            self._send(200, data, ct, "public, max-age=604800", gzip_ok=False)
            return

        if path == "/admin/login":
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", ""), "text/html; charset=utf-8"); return
        if path == "/admin/logout":
            _drop_session(self._cookie_token())
            self._redirect("/admin/login", "admin_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"); return
        if path == "/admin/api/data":
            if not self._is_admin():
                self._json({"error": "unauthorized"}, 401); return
            self._json(load_data()); return
        if path == "/admin":
            if not self._is_admin():
                self._redirect("/admin/login"); return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8"); return
        if path in ("/", "/index.html"):
            self._send(200, render_page(), "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, SITEMAP, "application/xml; charset=utf-8", "public, max-age=3600")
        elif path == "/favicon.ico":
            data = get_favicon()
            if not data:
                self._redirect(FAVICON_URL)
            elif _ic["ico"]:
                self._send(200, _ic["ico"], "image/x-icon", "public, max-age=86400", gzip_ok=False)
            else:
                self._send(200, data, "image/x-icon", "public, max-age=86400", gzip_ok=False)
        elif path == "/favicon-16x16.png":
            if _ic["png16"]:
                self._send(200, _ic["png16"], "image/png", "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/favicon-32x32.png":
            if _ic["png32"]:
                self._send(200, _ic["png32"], "image/png", "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
        elif path == "/apple-touch-icon.png":
            if _ic["png180"]:
                self._send(200, _ic["png180"], "image/png", "public, max-age=86400", gzip_ok=False)
            else:
                self._redirect(FAVICON_URL)
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
                self._redirect("/admin",
                               "admin_session=" + token + "; Path=/; Max-Age=" + str(SESSION_TTL) +
                               "; HttpOnly; SameSite=Lax")
            else:
                html = ADMIN_LOGIN_HTML.replace("__ERROR__",
                                                '<div class="err">Неверный логин или пароль</div>')
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
            if fb[:8] == b"\x89PNG\r\n\x1a\n":
                mime = "image/png"
            elif fb[:6] in (b"GIF87a", b"GIF89a"):
                mime = "image/gif"
            elif fb[:4] == b"RIFF" and fb[8:12] == b"WEBP":
                mime = "image/webp"
            data_url = "data:" + mime + ";base64," + base64.b64encode(fb).decode("ascii")
            self._json({"url": data_url})
            return
        self._json({"error": "not found"}, 404)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("BOOT: старт", flush=True)
    print("BOOT: PORT = " + str(PORT), flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("BOOT: слушаем http://0.0.0.0:" + str(PORT), flush=True)
    server.serve_forever()
