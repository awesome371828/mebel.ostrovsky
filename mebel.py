# -*- coding: utf-8 -*-
"""
mebel.py — сервер сайта «Кухни Островский» + серверный ИИ-чат.

Как запустить (docker):
  1. Задайте секреты в переменных окружения контейнера (НЕ в коде!):
       FOLDER_ID="..."
       YANDEX_API_KEY="..."          # запасная
       GIGACHAT_AUTH_KEY="..."       # основная
  2. Соберите и запустите контейнер (порт 8080).

Эндпоинты:
  GET  /              — страница сайта
  POST /api/chat      — {"message": "..."} -> {"reply": "..."}

Логика ИИ: сначала GigaChat, при сбое — YandexGPT.
"""
import os
import json
import uuid
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ----------------------- Секреты читаются ТОЛЬКО из окружения ----------------
FOLDER_ID          = os.environ.get("FOLDER_ID", "")
YANDEX_API_KEY     = os.environ.get("YANDEX_API_KEY", "")
GIGACHAT_AUTH_KEY  = os.environ.get("GIGACHAT_AUTH_KEY", "")
PORT               = int(os.environ.get("PORT", "8080"))

SYSTEM_PROMPT = (
    "Ты — вежливый консультант мебельной мастерской «Кухни Островский» в "
    "Ростове-на-Дону, Батайске и Азове. Руководитель мастерской — Роман "
    "Островский. Кухни и корпусная мебель на заказ: шкафы-купе, гардеробные, "
    "прихожие, стенки. Работаешь по Ростову, Батайску и Азову. Цена кухни — "
    "от 25 000 ₽ за погонный метр, замер и 3D-проект бесплатные, срок "
    "изготовления 14–30 дней, монтаж под ключ, гарантия качества. Телефон "
    "+7 (950) 846-53-97, Telegram t.me/fanny161, группа ВК vk.com/mebel.ostrovsky. "
    "Отвечай кратко, по делу, на русском, дружелюбно."
)

# ------------------------------- HTTP-помощник -------------------------------
def _post(url, headers, data):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

# ------------------------------ GigaChat (основная) --------------------------
def gigachat_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        # GIGACHAT_AUTH_KEY обычно уже закодирован в base64 client_id:client_secret
        "Authorization": "Basic " + GIGACHAT_AUTH_KEY,
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    resp = _post(url, headers, b"scope=GIGACHAT_API_PERS")
    return resp.get("access_token", "")

def ask_gigachat(message):
    token = gigachat_token()
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    payload = {
        "model": "GigaChat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    }
    resp = _post(url, headers, json.dumps(payload).encode("utf-8"))
    choices = resp.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "").strip()
    return ""

# -------------------------- YandexGPT (запасная) -----------------------------
def ask_yandex_gpt(message):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": "Api-Key " + YANDEX_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "modelUri": "gpt://{}/yandexgpt-lite".format(FOLDER_ID),
        "completionOptions": {"stream": False, "temperature": 0.5, "maxTokens": 800},
        "messages": [
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": message},
        ],
    }
    resp = _post(url, headers, json.dumps(payload).encode("utf-8"))
    alts = resp.get("result", {}).get("alternatives", [])
    if alts:
        return alts[0].get("message", {}).get("text", "").strip()
    return ""

# --------------------------------- Выбор ИИ ---------------------------------
def ask_ai(message):
    # Основная модель — GigaChat
    if GIGACHAT_AUTH_KEY:
        try:
            reply = ask_gigachat(message)
            if reply:
                return reply
        except Exception as exc:
            print("GigaChat error:", exc)
    # Запасная — YandexGPT
    if YANDEX_API_KEY and FOLDER_ID:
        try:
            reply = ask_yandex_gpt(message)
            if reply:
                return reply
        except Exception as exc:
            print("YandexGPT error:", exc)
    return "Извините, сейчас не удалось получить ответ от нейросети. Позвоните нам: +7 (950) 846-53-97"

# ------------------------------- HTML-страница ------------------------------
PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Кухни на заказ Ростов, Батайск, Азов — Кухни Островский | Мебель под ключ</title>
<meta name="description" content="Кухни на заказ в Ростове, Батайске и Азове. Руководитель мебельной мастерской Островского. Замер, проект, производство, монтаж под ключ. ☎ +7 (950) 846-53-97">
<meta name="keywords" content="кухни островский, кухни батайск, кухни ростов, кухни азов, кухни на заказ ростов, кухни на заказ батайск, кухни на заказ азов, мебель на заказ ростов, корпусная мебель, шкафы купе, гардеробные, прихожие, мебель островский, кухни под ключ, островский ростов">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<meta name="geo.region" content="RU-ROS">
<meta name="geo.placename" content="Ростов-на-Дону">
<meta name="theme-color" content="#17120d">
<link rel="canonical" href="https://кухниостровский.рф/">
<meta name="yandex-verification" content="f7e96d07aee79bf3">
<meta name="google-site-verification" content="dNSAELu64Y7aK5sjz_zpmhoz6YKn2PIZ03UKPwrgnCI">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%2317120d'/%3E%3Ctext x='50' y='72' font-size='62' font-family='Georgia,serif' font-weight='bold' fill='%23d4b06a' text-anchor='middle'%3EK%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&cs=1254x0">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:url" content="https://кухниостровский.рф/">
<meta property="og:title" content="Кухни на заказ Ростов, Батайск, Азов | Кухни Островский">
<meta property="og:description" content="Кухни и корпусная мебель под ключ. Руководитель мебельной мастерской Островского. Бесплатный замер и проект.">
<meta property="og:site_name" content="Кухни Островский">
<meta property="og:image" content="https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="855">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"LocalBusiness","name":"Кухни Островский","alternateName":"Кухни на Заказ — Ростов, Батайск, Азов","url":"https://кухниостровский.рф/","image":"https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0","description":"Кухни и корпусная мебель на заказ в Ростове, Батайске и Азове. Полный цикл под ключ.","telephone":"+79508465397","priceRange":"₽₽","currenciesAccepted":"RUB","address":{"@type":"PostalAddress","addressLocality":"Ростов-на-Дону","addressRegion":"Ростовская область","addressCountry":"RU"},"geo":{"@type":"GeoCoordinates","latitude":47.2357,"longitude":39.7015},"areaServed":[{"@type":"City","name":"Ростов-на-Дону"},{"@type":"City","name":"Батайск"},{"@type":"City","name":"Азов"}],"sameAs":["https://vk.com/mebel.ostrovsky"],"contactPoint":{"@type":"ContactPoint","telephone":"+79508465397","contactType":"customer service","availableLanguage":"Russian"}}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="preload" as="image" fetchpriority="high" href="https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0">
<link rel="preconnect" href="https://sun9-70.vkuserphoto.ru">
<link rel="preconnect" href="https://i.ibb.co">

<style>
:root{
  --gold:#b3873f;
  --gold-soft:#d4b06a;
  --muted:#ded2bb;
  --line:rgba(212,176,106,.28);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
section{scroll-margin-top:90px}
body{font-family:'Manrope',system-ui,sans-serif;color:#efe6d6;background:#17120d;line-height:1.7;-webkit-font-smoothing:antialiased;overflow-x:hidden}
h1,h2,h3{font-family:'Cormorant Garamond',Georgia,serif;overflow-wrap:break-word;word-break:break-word}
img{max-width:100%;display:block}
a{text-decoration:none;color:inherit}
ul{list-style:none}
.wrap{width:100%;max-width:1180px;margin:0 auto;padding:0 20px}
.progress{position:fixed;top:0;left:0;height:3px;z-index:200;background:linear-gradient(90deg,var(--gold),var(--gold-soft));width:0%}
header{position:fixed;top:0;left:0;right:0;z-index:120;background:rgba(16,12,8,.9);backdrop-filter:blur(14px);transition:background .4s,box-shadow .4s}
header.solid{background:rgba(23,18,13,.98);box-shadow:0 6px 26px rgba(0,0,0,.5)}
.nav{display:flex;align-items:center;justify-content:space-between;height:76px;gap:12px}
.logo{display:flex;align-items:center;gap:12px;min-width:0;max-width:100%;cursor:pointer}
.logo .brand-ava{width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid var(--gold);box-shadow:0 0 16px rgba(179,135,63,.55);flex-shrink:0}
.logo .brand-txt{display:flex;flex-direction:column;min-width:0;line-height:1.15}
.logo .brand-txt .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:'Cormorant Garamond',serif;font-size:24px;font-weight:700;color:#fff;line-height:1.05;text-shadow:0 2px 10px rgba(0,0,0,.6)}
.logo .brand-txt .sub{color:var(--gold-soft);font-family:'Manrope',sans-serif;font-size:12px;font-weight:600;letter-spacing:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:62vw;margin-top:2px}
.menu{position:fixed;top:0;height:76px;right:max(20px,calc((100vw - 1220px)/2));display:flex;gap:22px;align-items:center;z-index:121}
.menu a{color:rgba(255,255,255,.9);font-size:14px;font-weight:500;transition:.3s;border-bottom:1px solid transparent;padding-bottom:4px;white-space:nowrap}
.menu a:hover{color:#fff;border-color:var(--gold)}
.menu a.active{color:var(--gold-soft);border-color:var(--gold)}
.menu-call{display:none}
.burger{display:none;background:none;border:none;cursor:pointer;width:38px;height:38px;position:relative;z-index:130;flex-shrink:0}
.burger span{position:absolute;left:7px;right:7px;height:2px;background:#fff;transition:.3s;border-radius:2px}
.burger span:nth-child(1){top:12px}
.burger span:nth-child(2){top:18px}
.burger span:nth-child(3){top:24px}
.burger.open span:nth-child(1){top:18px;transform:rotate(45deg)}
.burger.open span:nth-child(2){opacity:0}
.burger.open span:nth-child(3){top:18px;transform:rotate(-45deg)}
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.55);opacity:0;visibility:hidden;transition:.35s;z-index:119;backdrop-filter:blur(2px)}
.scrim.show{opacity:1;visibility:visible}
.panel{position:relative;min-height:100vh;display:flex;align-items:center;padding:140px 0;overflow:hidden}
.panel .bg{position:absolute;inset:-20% 0;z-index:0;background-size:cover;background-position:center;will-change:transform;transform:translateZ(0)}
.panel .bg::after{content:"";position:absolute;inset:0;background:linear-gradient(to right,rgba(23,18,13,.93) 30%,rgba(23,18,13,.62) 65%,rgba(23,18,13,.7))}
.panel .content{position:relative;z-index:2;width:100%;will-change:transform;transform:translateZ(0)}
.panel--center .content{text-align:center}
.panel--center .bg::after{background:rgba(23,18,13,.68)}
.panel--dark .bg::after{background:rgba(23,18,13,.86)}
.panel + .panel{margin-top:14px}
.eyebrow{display:inline-block;color:var(--gold-soft);letter-spacing:4px;text-transform:uppercase;font-size:13px;font-weight:600;margin-bottom:18px;border-top:1px solid var(--gold);padding-top:13px}
h1{font-size:clamp(32px,6.4vw,74px);font-weight:600;line-height:1.12;color:#fff;letter-spacing:.5px;text-shadow:0 3px 22px rgba(0,0,0,.45);overflow-wrap:break-word;word-break:break-word;max-width:100%}
h1 em{font-style:italic}
.sub{color:#fff;font-size:clamp(17px,2vw,20px);font-weight:300;margin:24px 0 34px;max-width:560px;text-shadow:0 2px 14px rgba(0,0,0,.55)}
.btn-row{display:flex;gap:16px;flex-wrap:wrap}
.btn{position:relative;overflow:hidden;display:inline-block;padding:15px 30px;font-size:14px;font-weight:600;letter-spacing:.6px;text-transform:uppercase;transition:.35s;cursor:pointer;border-radius:8px}
.btn-solid{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#fff;box-shadow:0 10px 30px rgba(179,135,63,.45);animation:btnGlow 3.2s ease-in-out infinite}
.btn-solid:hover{filter:brightness(1.1);transform:translateY(-3px)}
.btn-line{border:1px solid rgba(255,255,255,.55);color:#fff;backdrop-filter:blur(4px)}
.btn-line:hover{background:#fff;color:#17120d}
.btn::after{content:"";position:absolute;top:0;left:-120%;width:60%;height:100%;background:linear-gradient(120deg,transparent,rgba(255,255,255,.45),transparent);transform:skewX(-20deg);transition:.6s}
.btn:hover::after{left:130%}
@keyframes btnGlow{0%,100%{box-shadow:0 10px 30px rgba(179,135,63,.4)}50%{box-shadow:0 10px 46px rgba(212,176,106,.85)}}
#heroTitle .t-word{background:linear-gradient(120deg,#f4e2b5,var(--gold-soft) 45%,#a9843f);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none}
.shimmer{background:linear-gradient(90deg,var(--gold-soft),#fff 35%,var(--gold-soft) 70%);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerMove 3.2s linear infinite}
@keyframes shimmerMove{0%{background-position:0% center}100%{background-position:-220% center}}
h1 em.shimmer{-webkit-text-fill-color:transparent}
.cta h2.shimmer{-webkit-text-fill-color:transparent}
.scroll-cue{position:absolute;bottom:26px;left:50%;transform:translateX(-50%);z-index:5;color:rgba(255,255,255,.8);font-size:11px;letter-spacing:3px;text-transform:uppercase;text-align:center}
.scroll-cue .line{width:1px;height:44px;background:rgba(255,255,255,.55);margin:10px auto 0;animation:drip 2s infinite}
@keyframes drip{0%{transform:scaleY(0);transform-origin:top}50%{transform:scaleY(1);transform-origin:top}51%{transform-origin:bottom}100%{transform:scaleY(0);transform-origin:bottom}}
.sec-head{max-width:680px;margin:0 auto 50px;text-align:center}
.sec-head .kicker{color:var(--gold-soft);letter-spacing:4px;text-transform:uppercase;font-size:12px;font-weight:600}
.sec-head h2{font-size:clamp(32px,5vw,48px);font-weight:600;margin:16px 0 14px;line-height:1.15;color:#fff;text-shadow:0 2px 18px rgba(0,0,0,.45)}
.sec-head p{color:var(--muted);font-size:16px}
h2.k{font-size:clamp(32px,5vw,46px);color:#fff;font-weight:600;margin:16px 0 14px;text-align:center;text-shadow:0 2px 18px rgba(0,0,0,.45)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:30px;text-align:center}
.stat .num{font-family:'Cormorant Garamond',serif;font-size:60px;font-weight:600;color:var(--gold-soft);line-height:1;text-shadow:0 3px 22px rgba(0,0,0,.55)}
.stat .lbl{color:var(--muted);font-size:14px;margin-top:10px}
.about{display:grid;grid-template-columns:1fr 1.1fr;gap:70px;align-items:center}
.about-card{background:rgba(23,18,13,.78);backdrop-filter:blur(12px);border:1px solid var(--line);padding:50px 42px;text-align:center;border-radius:16px}
.avatar{width:130px;height:130px;border-radius:50%;margin:0 auto 22px;overflow:hidden;border:2px solid var(--gold);position:relative}
.avatar img{width:100%;height:100%;object-fit:cover}
.avatar::after{content:"";position:absolute;inset:0;border-radius:50%;box-shadow:inset 0 0 0 3px rgba(212,176,106,.4)}
.about-card h3{font-size:28px;color:#fff}
.about-card .role{color:var(--gold-soft);font-size:14px;margin-top:4px}
.about-card .sep{width:46px;height:1px;background:var(--gold);margin:22px auto}
.about-card p{color:var(--muted);font-size:15px}
.about-body .kicker{color:var(--gold-soft);letter-spacing:4px;text-transform:uppercase;font-size:12px;font-weight:600}
.about-body h2{font-size:clamp(30px,4vw,44px);font-weight:600;margin:16px 0 22px;line-height:1.15;color:#fff;text-shadow:0 2px 18px rgba(0,0,0,.45)}
.about-body p{color:var(--muted);font-size:16px;margin-bottom:26px}
.features{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.features li{position:relative;padding-left:34px;color:#efe6d6;font-size:15px;overflow-wrap:break-word}
.features li::before{content:"";position:absolute;left:0;top:6px;width:16px;height:16px;border:1.5px solid var(--gold);border-radius:50%}
.features li::after{content:"✓";position:absolute;left:3px;top:5px;font-size:11px;color:var(--gold-soft);font-weight:700}
.consult .phone{display:block;font-family:'Manrope',sans-serif;font-weight:700;font-size:clamp(30px,5vw,50px);color:var(--gold-soft);letter-spacing:1px;margin-top:10px;white-space:nowrap}
.consult p{color:var(--muted);font-size:16px;margin:30px auto 0;max-width:600px;line-height:1.8;overflow-wrap:break-word}
.carousel{position:relative;max-width:1120px;margin:0 auto}
.car-track{display:flex;gap:18px;overflow-x:auto;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;padding:8px 6px 20px;scrollbar-width:none}
.car-track::-webkit-scrollbar{display:none}
.car-nav{position:absolute;top:38%;transform:translateY(-50%);width:46px;height:46px;border-radius:50%;background:rgba(23,18,13,.75);backdrop-filter:blur(8px);border:1px solid var(--gold);color:var(--gold-soft);font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.3s;z-index:5}
.car-nav:hover{background:var(--gold);color:#17120d}
.car-prev{left:-14px}
.car-next{right:-14px}
.car-dots{display:flex;justify-content:center;gap:8px;margin-top:10px;flex-wrap:wrap}
.car-dot{width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.3);cursor:pointer;transition:.3s;border:none}
.car-dot.active{background:var(--gold-soft);transform:scale(1.3)}
.car-slide{flex:0 0 auto;width:min(78vw,440px);scroll-snap-align:center;border-radius:16px;overflow:hidden;border:1px solid var(--line);background:rgba(23,18,13,.7);cursor:zoom-in}
.car-slide img{width:100%;height:300px;object-fit:cover;display:block;transition:transform .5s ease;loading:lazy;decoding:async}
.car-slide:hover img{transform:scale(1.06)}
.rev-track{align-items:flex-start}
.rev-card{scroll-snap-align:center;background:linear-gradient(160deg,rgba(23,18,13,.92),rgba(23,18,13,.8));backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:18px;padding:22px 24px;width:min(82vw,520px);flex:0 0 auto;display:flex;flex-direction:column;box-shadow:0 14px 40px rgba(0,0,0,.45);position:relative;overflow:hidden}
.rev-card::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.7}
.rev-head{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}
.rev-ava{width:50px;height:50px;border-radius:50%;object-fit:cover;border:2px solid var(--gold);box-shadow:0 0 12px rgba(179,135,63,.4);flex-shrink:0;loading:lazy;decoding:async}
.rev-name{color:#fff;font-weight:700;font-size:15px}
.rev-sub{color:var(--muted);font-size:11px;margin-top:2px}
.rev-stars{color:var(--gold-soft);letter-spacing:3px;font-size:14px;margin-left:auto;white-space:nowrap}
.rev-text{color:#e7ddc8;font-size:14px;line-height:1.6;font-weight:300;text-align:left;overflow-wrap:break-word;word-break:break-word}
.rev-video{margin-top:12px;border-radius:12px;overflow:hidden;border:1px solid var(--line)}
.rev-video iframe{width:100%;height:200px;border:0;display:block;loading:lazy}
.svc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.svc{position:relative;background:rgba(23,18,13,.68);backdrop-filter:blur(10px);border:1px solid var(--line);padding:36px 30px;transition:.4s;border-radius:14px;overflow-wrap:break-word}
.svc::before{content:"";position:absolute;inset:0;border-radius:14px;padding:1px;background:linear-gradient(135deg,var(--gold-soft),transparent 40%,transparent 60%,var(--gold-soft));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:.4s;pointer-events:none}
.svc:hover{transform:translateY(-6px);background:rgba(23,18,13,.88)}
.svc:hover::before{opacity:1}
.svc svg{width:34px;height:34px;stroke:var(--gold-soft);fill:none;stroke-width:1.4;margin-bottom:20px}
.svc h3{font-size:23px;color:#fff;margin-bottom:10px}
.svc p{color:var(--muted);font-size:14.5px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.step{position:relative;padding:30px 24px;background:rgba(23,18,13,.65);backdrop-filter:blur(8px);border:1px solid var(--line);border-radius:14px;transition:.3s;overflow-wrap:break-word}
.step:hover{transform:translateY(-4px);border-color:var(--gold)}
.step .n{font-family:'Cormorant Garamond',serif;font-size:56px;color:var(--gold-soft);line-height:1}
.step h3{font-size:22px;color:#fff;margin:14px 0 8px}
.step p{color:var(--muted);font-size:14.5px}
.guar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.guar{position:relative;background:rgba(23,18,13,.68);backdrop-filter:blur(10px);border:1px solid var(--line);padding:36px 26px;text-align:center;transition:.35s;border-radius:14px;overflow-wrap:break-word}
.guar::before{content:"";position:absolute;inset:0;border-radius:14px;padding:1px;background:linear-gradient(135deg,var(--gold-soft),transparent 40%,transparent 60%,var(--gold-soft));-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:.4s}
.guar:hover{transform:translateY(-5px);background:rgba(23,18,13,.85)}
.guar:hover::before{opacity:1}
.guar .ico{width:52px;height:52px;margin:0 auto 18px;border:1px solid var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft)}
.guar .ico svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.5}
.guar h3{font-size:19px;color:#fff;margin-bottom:8px}
.guar p{color:var(--muted);font-size:13.5px}
.contact-grid{display:grid;grid-template-columns:1fr 1fr;gap:60px;align-items:start}
.contact-info h2{font-size:clamp(30px,4.5vw,46px);color:#fff;margin:16px 0 14px;line-height:1.1;text-shadow:0 2px 18px rgba(0,0,0,.45)}
.contact-info .kicker{color:var(--gold-soft);letter-spacing:4px;text-transform:uppercase;font-size:12px;font-weight:600}
.contact-info>p{color:var(--muted);font-size:16px;margin-bottom:32px}
.c-line{display:flex;align-items:flex-start;gap:20px;margin-bottom:26px}
.c-ico{width:44px;height:44px;border:1px solid var(--gold);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);flex-shrink:0}
.c-ico svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.5}
.c-line .lab{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:3px}
.c-line .val{font-size:19px;font-weight:600;color:#efe6d6;overflow-wrap:break-word;word-break:break-word}
.c-line a.val:hover{color:var(--gold-soft)}
.call-block{background:rgba(23,18,13,.78);backdrop-filter:blur(12px);border:1px solid var(--line);padding:44px 34px;text-align:center;border-radius:16px}
.call-block .cb-lab{font-size:14px;letter-spacing:3px;text-transform:uppercase;color:var(--gold-soft)}
.call-block .cb-num{display:block;font-family:'Manrope',sans-serif;font-weight:700;font-size:clamp(28px,4vw,44px);color:#fff;margin:14px 0 20px;white-space:nowrap}
.call-block .cb-num:hover{color:var(--gold-soft)}
.call-block .cb-hint{color:var(--muted);font-size:14.5px;line-height:1.8;overflow-wrap:break-word}
.contact-actions{display:flex;flex-direction:column;gap:12px;margin-top:24px}
.c-action{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;padding:15px 18px;border-radius:12px;font-weight:700;font-size:15px;letter-spacing:.4px;transition:.3s;color:#fff}
.c-action svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8}
.c-action.c-call{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120d;box-shadow:0 10px 26px rgba(179,135,63,.4)}
.c-action.c-call:hover{filter:brightness(1.1);transform:translateY(-2px)}
.c-action.c-tg{background:rgba(64,169,242,.16);border:1px solid rgba(64,169,242,.45);color:#8fd0ff}
.c-action.c-tg:hover{background:rgba(64,169,242,.28);transform:translateY(-2px)}
.c-action.c-max{background:rgba(177,88,252,.16);border:1px solid rgba(177,88,252,.45);color:#e0b8ff}
.c-action.c-max:hover{background:rgba(177,88,252,.28);transform:translateY(-2px)}
.cta{text-align:center;padding:100px 0;position:relative}
.cta h2{font-size:clamp(32px,5vw,52px);color:#fff;font-weight:600;margin-bottom:16px;text-shadow:0 3px 20px rgba(0,0,0,.45)}
.cta p{color:var(--muted);font-size:17px;max-width:600px;margin:0 auto 34px;overflow-wrap:break-word}
footer{background:rgba(16,12,8,.97);color:var(--muted);padding:44px 20px;text-align:center;font-size:13.5px;border-top:1px solid rgba(179,135,63,.2)}
footer .flogo{font-family:'Cormorant Garamond',serif;font-size:26px;color:#fff;margin-bottom:10px;line-height:1.3}
footer .flogo span{color:var(--gold-soft);font-size:15px;font-family:'Manrope',sans-serif;font-weight:500;letter-spacing:1px}
.cookie-bar{position:fixed;bottom:0;left:0;right:0;z-index:150;background:rgba(16,12,8,.97);backdrop-filter:blur(10px);border-top:1px solid var(--line);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;transform:translateY(100%);transition:.5s}
.cookie-bar.show{transform:none}
.cookie-bar p{color:var(--muted);font-size:13px;max-width:720px;line-height:1.5}
.cookie-bar .btn{flex-shrink:0;padding:12px 24px}
.lightbox{position:fixed;inset:0;z-index:3000;background:rgba(10,7,4,.94);display:none;align-items:center;justify-content:center;flex-direction:column;gap:16px}
.lightbox.open{display:flex}
.lightbox img{max-width:92vw;max-height:84vh;border-radius:12px;border:1px solid var(--gold);box-shadow:0 20px 70px rgba(0,0,0,.7)}
.lb-close{position:absolute;top:18px;right:24px;background:none;border:none;color:#fff;font-size:44px;cursor:pointer;z-index:5;line-height:1}
.lb-nav{position:absolute;top:50%;transform:translateY(-50%);width:52px;height:52px;border-radius:50%;background:rgba(212,176,106,.15);border:1px solid var(--gold);color:var(--gold-soft);font-size:26px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.3s}
.lb-nav:hover{background:var(--gold);color:#17120d}
.lb-prev{left:18px}.lb-next{right:18px}
.lb-count{color:var(--muted);font-size:13px}
.reveal{opacity:0;transform:translateY(36px);transition:opacity .9s ease,transform .9s ease}
.reveal.in{opacity:1;transform:none}
.stats .reveal:nth-child(1){transition-delay:.05s}.stats .reveal:nth-child(2){transition-delay:.15s}.stats .reveal:nth-child(3){transition-delay:.25s}.stats .reveal:nth-child(4){transition-delay:.35s}
.steps .reveal:nth-child(2){transition-delay:.08s}.steps .reveal:nth-child(3){transition-delay:.16s}.steps .reveal:nth-child(4){transition-delay:.24s}.steps .reveal:nth-child(5){transition-delay:.32s}.steps .reveal:nth-child(6){transition-delay:.4s}
.svc-grid .reveal:nth-child(2){transition-delay:.08s}.svc-grid .reveal:nth-child(3){transition-delay:.16s}.svc-grid .reveal:nth-child(4){transition-delay:.24s}.svc-grid .reveal:nth-child(5){transition-delay:.32s}.svc-grid .reveal:nth-child(6){transition-delay:.4s}
.guar-grid .reveal:nth-child(2){transition-delay:.08s}.guar-grid .reveal:nth-child(3){transition-delay:.16s}.guar-grid .reveal:nth-child(4){transition-delay:.24s}
.t-word{display:inline-block;opacity:0;transform:translateY(12px);transition:opacity .5s ease,transform .5s ease;word-break:break-word}
.t-word.on{opacity:1;transform:none}

/* ===== ИИ-чат ===== */
.ai-fab{position:fixed;right:22px;bottom:22px;z-index:160;display:flex;align-items:center;gap:10px;padding:14px 20px;border:none;border-radius:50px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120d;font-weight:700;font-size:14px;cursor:pointer;box-shadow:0 12px 34px rgba(179,135,63,.55);transition:.3s}
.ai-fab:hover{transform:translateY(-3px);filter:brightness(1.08)}
.ai-fab-icon{font-size:20px}
@media(max-width:520px){.ai-fab{width:58px;height:58px;padding:0;justify-content:center;border-radius:50%}.ai-fab-label{display:none}}
.ai-chat{position:fixed;right:22px;bottom:96px;z-index:170;width:min(360px,92vw);max-height:70vh;display:none;flex-direction:column;background:#1c160e;border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 24px 70px rgba(0,0,0,.6)}
.ai-chat.open{display:flex}
.ai-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:14px 16px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120d;font-weight:700;font-size:14px}
.ai-close{background:none;border:none;color:#17120d;font-size:24px;line-height:1;cursor:pointer}
.ai-body{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;min-height:180px;max-height:44vh}
.ai-msg{max-width:85%;padding:10px 13px;border-radius:14px;font-size:14px;line-height:1.5;white-space:pre-wrap;word-break:break-word}
.ai-msg.bot{background:rgba(212,176,106,.12);border:1px solid var(--line);color:#efe6d6;align-self:flex-start;border-bottom-left-radius:4px}
.ai-msg.user{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120d;align-self:flex-end;border-bottom-right-radius:4px}
.ai-input-row{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line)}
.ai-input-row input{flex:1;padding:11px 13px;border-radius:10px;border:1px solid var(--line);background:rgba(255,255,255,.05);color:#fff;font-size:14px;outline:none}
.ai-input-row input::placeholder{color:var(--muted)}
.ai-input-row button{width:44px;border:none;border-radius:10px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120d;font-size:18px;cursor:pointer}
@media(max-width:520px){.ai-chat{bottom:88px;right:12px;left:12px;width:auto}}

@media(max-width:1024px){
  .stats{grid-template-columns:repeat(2,1fr);gap:40px}
  .svc-grid{grid-template-columns:repeat(2,1fr)}
  .guar-grid{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:860px){
  .menu{position:fixed;top:0;right:0;bottom:0;width:min(320px,84vw);background:linear-gradient(180deg,#1c160e,#12100a);flex-direction:column;justify-content:flex-start;gap:6px;padding:100px 36px 40px;transform:translateX(100%);transition:transform .4s cubic-bezier(.22,.61,.36,1);z-index:125;opacity:0;visibility:hidden;box-shadow:-20px 0 50px rgba(0,0,0,.5);overflow-y:auto;height:auto}
  .menu.open{transform:none;opacity:1;visibility:visible}
  .menu a{font-size:20px;font-family:'Cormorant Garamond',serif;color:#fff;border-bottom:1px solid rgba(212,176,106,.15);padding:14px 0;display:block}
  .menu a:hover{color:var(--gold-soft)}
  .menu a.active{color:var(--gold-soft);border-color:var(--gold);border-bottom-color:var(--gold)}
  .menu-call{display:block;margin-top:auto;padding-top:20px}
  .menu-call a{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#fff;font-family:'Manrope',sans-serif;font-size:15px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;border:none;border-radius:12px;padding:16px 18px;box-shadow:0 10px 26px rgba(179,135,63,.4)}
  .burger{display:block}
  .scrim{display:block}
  .about{grid-template-columns:1fr;gap:40px}
  .features{grid-template-columns:1fr}
  .steps{grid-template-columns:1fr;gap:22px}
  .contact-grid{grid-template-columns:1fr;gap:40px}
  .panel{padding:120px 0}
  .car-nav{display:none}
  .rev-card{width:86vw}
}
@media(max-width:520px){
  .logo .brand-ava{width:40px;height:40px}
  .logo .brand-txt .name{font-size:20px}
  .logo .brand-txt .sub{font-size:11px;max-width:54vw}
  .nav{height:66px}
  .panel{min-height:auto;padding:100px 0 60px}
  h1{font-size:33px}
  .btn-row{width:100%}
  .btn{width:100%;text-align:center}
  .stat .num{font-size:46px}
  .scroll-cue{display:none}
  .car-slide{width:84vw}
  .car-slide img{height:210px}
  .svc-grid{grid-template-columns:1fr}
  .guar-grid{grid-template-columns:1fr}
  .rev-card{width:92vw;padding:16px}
  .rev-head{gap:10px}
  .rev-ava{width:46px;height:46px}
  .rev-name{font-size:14px}
  .rev-sub{font-size:10px}
  .rev-stars{font-size:13px;display:block;margin:6px 0 0}
  .rev-text{font-size:13px;line-height:1.55}
  .rev-video iframe{height:180px}
  .consult .phone{font-size:26px}
  .call-block .cb-num{font-size:24px}
  .menu{padding:92px 28px 30px}
  .lb-nav{width:44px;height:44px;font-size:22px}
}
@media(max-width:380px){
  .car-slide{width:88vw}
  .car-slide img{height:190px}
  .rev-card{width:94vw;padding:14px}
  .rev-text{font-size:12.5px}
  .rev-video iframe{height:160px}
}
</style>
</head>
<body>

<div class="progress" id="progress"></div>

<header id="header">
  <div class="wrap nav">
    <a href="#top" class="logo" id="logo">
      <img class="brand-ava" src="https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&cs=1254x0" alt="Кухни Островский">
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
  <li><a href="#contacts">Контакты</a></li>
  <li class="menu-call"><a href="tel:+79508465397">📞 Позвонить специалисту</a></li>
</ul>
<div class="scrim" id="scrim"></div>

<section class="panel" id="top">
  <div class="bg" style="background-image:url('https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <span class="eyebrow">Мебель и кухни на заказ</span>
    <h1 id="heroTitle">Создаём мебель, которая <em class="shimmer">создаёт настроение</em></h1>
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
        <div class="avatar"><img src="https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg" alt="Роман Островский"></div>
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
    <span class="kicker reveal" style="color:var(--gold-soft);letter-spacing:6px;text-transform:uppercase;font-size:13px;font-weight:600">Бесплатно</span>
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
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="carPrev">❮</button>
      <div class="car-track" id="carTrack">
        <div class="car-slide"><img src="https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1080x0" alt="Кухня на заказ Ростов"></div>
        <div class="car-slide"><img src="https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1080x0" alt="Кухня на заказ Батайск"></div>
        <div class="car-slide"><img src="https://sun9-11.vkuserphoto.ru/s/v1/ig2/Xh5Xw9Yb1reqhfFznlGk8NjvSQAxCbysuiL5IWRt_f3ELVb8fvoYPg00eFIHV-xiS9I4nhYBj4ttU_FHVkPpX8Z3.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,1600x1200&from=bu&u=pY-bjOidU1jjNjiF66Dn4Ycgmb6utH_d0Ti7oSJr0qA&cs=1080x0" alt="Кухня на заказ Азов"></div>
        <div class="car-slide"><img src="https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1080x0" alt="Мебель на заказ Ростов"></div>
        <div class="car-slide"><img src="https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1080x0" alt="Шкаф купе Ростов"></div>
        <div class="car-slide"><img src="https://sun9-24.vkuserphoto.ru/s/v1/ig2/lS8MpZ4V9XUKPJ7l9GmjnkCnHW2MGfnq86jH-Gzx6bAgr4m3azL5Xd_fkdPHY_NOsJjST3Zw2iQkuGKGBwYODdgM.jpg?quality=95&as=32x42,48x63,72x95,108x142,160x211,240x316,360x474,480x632,540x711,640x843,720x949,1080x1423,1280x1686,1440x1897,1943x2560&from=bu&u=dLnirpryCPR3qvUPphwt7JaP5ljnoIl1yyGyUNiUjZI&cs=1080x0" alt="Мебель на заказ Батайск"></div>
        <div class="car-slide"><img src="https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1080x0" alt="Кухня на заказ"></div>
        <div class="car-slide"><img src="https://sun9-39.vkuserphoto.ru/s/v1/ig2/5cyrhjIBSWB5GGZATB29IrmjydaNdVOx-iP_dMNKsMbePp5Ccs2rnkEpLnfft3yAZGeMEE3IfInjMQ7aU6Z6jnHc.jpg?quality=95&as=32x24,48x36,72x54,108x82,160x121,240x181,360x272,480x363,540x408,640x484,720x544,1080x817,1280x968&from=bu&u=l1uWXrXXeEAKk1VMgGM5wyIo7DtKdQGhKlCwMjoS0t8&cs=1080x0" alt="Мебель на заказ"></div>
        <div class="car-slide"><img src="https://sun9-68.vkuserphoto.ru/s/v1/ig2/6KwHlOiN9pxXNIwTImKO6QGkrSCTVqreybJu-63m8wbhdFFMIl06es9cPeurIdwuwXGtsFTkdJ6IOjMaS1qRtfxJ.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VgDjFEJKqpW6dWVO-E4y4Q6xcuyoqiL7LxhG36oLPjw&cs=1080x0" alt="Кухня на заказ"></div>
        <div class="car-slide"><img src="https://sun9-23.vkuserphoto.ru/s/v1/ig2/wfBQoeOzjZbCRCvxmIkx_V3xC0fgMd3TTxRDSRG2CHDMok6B2ZKrG7vCAJ_G1DmrZ6JS1_RC2tr87Q64wJJ4aW9w.jpg?quality=95&as=32x25,48x37,72x56,108x84,160x124,240x186,360x279,480x372,540x419,640x496,720x558,1080x837,1280x992,1440x1117,2560x1985&from=bu&u=kZXvrlzwGUvzrHmYa8tHXbvyhU_JlNlefLxxcCYqM1A&cs=1080x0" alt="Мебель на заказ"></div>
        <div class="car-slide"><img src="https://sun9-33.vkuserphoto.ru/s/v1/ig2/TQbwf8FdMs_jwKfC_ONoxEHBIpc2L5yf_T0McNeUKRn0tK7fVbC5YbHfsB0TGLlNC_D55htM_2nREACuIw7ykLIx.jpg?quality=95&as=32x43,48x65,72x97,108x145,160x215,240x323,360x484,480x645,540x726,640x860,720x968,1080x1452,1280x1721,1440x1936,1904x2560&from=bu&u=rbH0OM9Bv0PnevamgtW5nYBm9jxFI28R6D1wxzq6fJA&cs=1080x0" alt="Кухня на заказ"></div>
        <div class="car-slide"><img src="https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0" alt="Кухня на заказ"></div>
        <div class="car-slide"><img src="https://sun9-65.vkuserphoto.ru/s/v1/ig2/z_wfZeGA9H6LHDsevjkijUHpbVyLGWFM38frX4hKrjgOnscfAloGdrVpPUwl4XoXCG_YgcKXTgeeTsDDcWEBvdi1.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YbZ1WmiK3ZCk0bKWZhf_YKp6dTUU2vbsQo7Ya4Hoi6s&cs=1080x0" alt="Кухня на заказ"></div>
      </div>
      <button class="car-nav car-next" id="carNext">❯</button>
      <div class="car-dots" id="carDots"></div>
    </div>
    <p style="color:var(--muted);margin-top:26px;text-align:center;font-size:14px">Больше работ — в сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>

<div class="lightbox" id="lightbox">
  <button class="lb-close" id="lbClose">×</button>
  <button class="lb-nav lb-prev" id="lbPrev">❮</button>
  <img id="lbImg" alt="Работа">
  <div class="lb-count" id="lbCount"></div>
  <button class="lb-nav lb-next" id="lbNext">❯</button>
</div>

<section class="panel panel--center" id="reviews">
  <div class="bg" style="background-image:url('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">Отзывы</div>
      <h2>Что говорят наши клиенты</h2>
      <p>Реальные отзывы о нашей работе. Листайте влево-вправо.</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="revPrev">❮</button>
      <div class="car-track rev-track" id="revTrack">
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-3.vkuserphoto.ru/s/v1/ig2/-cVZEipS5I4ROZUZ2fxoIaGJBZXpUs76_WKoUZpPw_r2-gnqqUvgTqjLjYoTZ0R21nsCSvjUPyw_vSn1jxAYJC8K.jpg?quality=95&as=32x30,48x45,72x68,108x101,160x150,240x225,360x338,480x450,540x507,640x601,720x676,1080x1014,1280x1201,1440x1351,2505x2351&from=bu&cs=128x0" alt="">
            <div><div class="rev-name">Виктория Брандикова</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа кухню, всё прошло на высшем уровне, начиная от замеров, до установки! Мы очень рады, что обратились именно к нему (нашли в объявлении и нам крупно повезло), Роман супер профессионал своего дела!!! Кухня у нас маленькая, не стандартная, сверху выступы, вся на трубах, расположение мойки и кухонной плиты не удобное и вытяжку мы хотели, но нам некуда было её устанавливать (как мы думали), но Роман всё разрешил, практично разместил технику (в том числе и вытяжку), переставил мойку, установил подсветку сделал кухню функциональной светлой, практичной и современной. Кухня была готова в короткие сроки, установкой очень довольны, всё под ключ с установкой техники и подключением, всё быстро, качественно, и чисто! Мы не ожидали такого результата 😍, просто не верится, что у нас теперь удобная, вместительная, современная кухня 🔥, о такой даже и не мечтали, даже несмотря на то, что кухня бюджетная. За мебелью теперь только к Роману!!! Однозначно всем буду рекомендовать!!!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=128x0" alt="">
            <div><div class="rev-name">Виктория Маренко</div><div class="rev-sub">Кухня и гардеробная</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">И вновь мы обратились к Роману! Понадобилась кухня😊Кухня на самом деле очень удобная! Как и хотелось она светлая, но не маркая. Как всегда учтены все пожелания и воплощены в жизнь! Очень трудно нам дался выбор цветов😂но Роман спокойно вынес все наши метания🙏 выполнил работу достойно, внимательно и аккуратно! Однозначно советую обращаться к нему👍 гардеробную так же заказывали у Романа, и она идеальна👏 ответственный подход, качество, внимательность и чистота исполнения - его качества, которые для нас важны, поэтому если нам понадобится мебель- обязательно еще раз встретимся😊</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-53.vkuserphoto.ru/s/v1/ig2/gZheSpaWhz7StIdwlzSoCIfA01e-x8jVUMESDK2u9ONRR1s3txB-b6F7lqLLj-Y6QFqFU5x463yoWmnTxf5T88g2.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&cs=128x0" alt="">
            <div><div class="rev-name">Любовь Петелько</div><div class="rev-sub">Шкаф, тумбы, прихожая</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Всем здравствуйте. Я заказала у Романа шкаф купе в спальню. Когда Роман приехал, я не совсем понимала что я хочу, пообщавшись с ним, получила много советов и рекомендаций по составу и цвету шкафа. В итоге решила в комплект заказать сразу тумбы, гарнитур под телевизор, и прихожую. Установили все раньше обещанного срока. Я очень довольна и всем рекомендую. Роман специалист своего дела. Скоро буду заказывать зону хранения балкона и самое главное кухню мечты). Спасибо</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-83.vkuserphoto.ru/s/v1/ig2/zYO0FQ_fFsgxDWhaTE85lNpixn2ikScuD58qVoXtqda8vFxoS-LGsT54k9pk9tDVEpzGpJfCw5eg5TNtYgE2Q8_y.jpg?quality=95&as=32x47,48x71,72x106,108x159,160x236,240x353,360x530,480x707,540x795,640x943,720x1061,869x1280&from=bu&cs=128x0" alt="">
            <div><div class="rev-name">Дмитрий Юшенко</div><div class="rev-sub">Шкаф и стенка</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа шкаф и стенку в спальню. Работа вышла отличной, подсказал несколько удачных решений наших хотелок. Все супер! Спасибо!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-46.vkuserphoto.ru/s/v1/ig2/bVm2vnJWOD92dzHJ3_21NbqhcwF7DW7a05XzjaTWteG9Dviu9nt8LlA5bgzdbsBhGtYbrs7rvOMTylQQIV43cl4T.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&cs=128x0" alt="">
            <div><div class="rev-name">Екатерина Умнягина</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа кухню, всё очень понравилось! Подбирали всё до мелочей, и Рома всё исполнил, как мы хотели, за это мы ему очень благодарны. Всё сделано идеально, спрятали то, что не должно быть видно, и получилось очень красиво. Спасибо, Рома, за эту крутую современную кухню!!!</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-48.vkuserphoto.ru/s/v1/ig2/OdS0JaUmpkj7vzQLNz1oyY6PBksnYylZuY54LZ2vnibrqxNc0IimIjE6d6NWySeMm6N2MLIUHG6WLKtAFJ82ICwE.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,960x1280&from=bu&cs=128x0" alt="">
            <div><div class="rev-name">Анастасия Зайцева</div><div class="rev-sub">Два шкафа, гардеробная</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Заказывали у Романа два шкафа. Во время замеров у нас не было определённой идеи, как сделать вместительный шкаф в нашу небольшую спальню, ещё и с несущей колонной. Роман подкинул прекрасную идею, в итоге получился не просто шкаф, а целая угловая гардеробная, я была в восторге 🤩 Большой выбор цветов и текстур. Работа выполнена в оговорённый срок и качественно. 👍🏻 Большое спасибо за эстетичное воплощение нашей мечты 🤩😊</p>
        </div>
        <div class="rev-card">
          <div class="rev-head">
            <img class="rev-ava" src="https://sun9-44.vkuserphoto.ru/s/v1/ig2/z3K7MYc56nf_4Ek_wkhJ-j-VZt7iv_VEt9wUN0gJSY0VORuRVxQCX1S5baisBgJyoYuCcrENJNxLajL1WKwdFS91.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x541,1080x811,1280x961,1440x1081,2560x1922&from=bu&u=Fj3HDKPJXUOEmCWl6MePYyPYB6lNmsGien6u_9mlUi8&cs=128x0" alt="">
            <div><div class="rev-name">Александр Карташев</div><div class="rev-sub">Кухня на заказ</div></div>
            <div class="rev-stars">★★★★★</div>
          </div>
          <p class="rev-text">Обратились к Роману за изготовлением кухни. Изначально не было конкретного проекта, были лишь несколько «хотелок» и нестандартная планировка. В стене были выступы, которые нужно было замаскировать. В итоге Роман предложил несколько очень практичных решений, которые идеально вписались в интерьер. Выступ стояка закрыли пеналом, а большой барный стол (длиной в 2 метра) смонтировали так, чтобы встроить в одну из ножек электрические розетки. В итоге получилось все очень органично. Работу мастера выполнили в поставленные сроки – без задержек – через месяц наша кухня уже была смонтирована. По качеству материалов никаких нареканий. Все подбирали индивидуально. Нам предложили большой выбор фасадов и оформления основных коробов. В итоге подобрали все идеально подходяще к основному интерьеру квартиры. Шкафчики с доводчиками, антресоли с пуш-механизмами. Очень стильный дизайн. Технику и сантехнику тоже вмонтировали очень аккуратно и хорошо. Особая благодарность за идею с подсветкой. Изначально о ней даже не задумывались, но Роман предложил сделать. Теперь без нее процесс готовки вообще не представляем. Очень удобно и очень стильно. Так что, в итоге за приемлемую цену получили отличную кухню. Прям гордость квартиры 😀</p>
          <div class="rev-video">
            <iframe src="https://vk.ru/video_ext.php?oid=-212015374&id=456239019&hash=6abf300a7c2518d4" frameborder="0" allowfullscreen="1" allow="autoplay; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
          </div>
        </div>
      </div>
      <button class="car-nav car-next" id="revNext">❯</button>
      <div class="car-dots" id="revDots"></div>
    </div>
    <p style="color:var(--muted);margin-top:26px;text-align:center;font-size:14px">Больше отзывов — в нашем сообществе <a href="https://vk.com/mebel.ostrovsky" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>

<section class="panel panel--dark" id="services">
  <div class="bg" style="background-image:url('https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1280x0')"></div>
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
      <div class="step reveal"><div class="n">01</div><h3>Заявка</h3><p>Вы звоните или пишете — обговариваем задачу и пожелания.</p></div>
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

<section class="panel panel--center panel--dark">
  <div class="bg" style="background-image:url('https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1280x0')"></div>
  <div class="wrap"><div class="content cta">
    <h2 class="reveal shimmer">Готовы обсудить вашу мебель?</h2>
    <p class="reveal">Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.</p>
    <a href="tel:+79508465397" class="btn btn-solid reveal">📞 Позвонить специалисту</a>
  </div></div>
</section>

<section class="panel panel--dark" id="contacts">
  <div class="bg" style="background-image:url('https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1280x0')"></div>
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
  <p>Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов</p>
  <p style="margin-top:8px">© <span id="year"></span> Кухни Островский. Все права защищены.</p>
</footer>

<div class="cookie-bar" id="cookieBar">
  <p>Мы используем файлы cookie для корректной работы сайта и улучшения сервиса. Продолжая пользоваться сайтом, вы соглашаетесь с <a href="#" style="color:var(--gold-soft)">политикой конфиденциальности</a>.</p>
  <button class="btn btn-solid" id="cookieOk">Принять</button>
</div>

<!-- Кнопка и панель ИИ-чата -->
<button id="aiBtn" class="ai-fab" aria-label="Посоветоваться с ИИ">
  <span class="ai-fab-icon">🤖</span>
  <span class="ai-fab-label">Посоветоваться с ИИ</span>
</button>

<div class="ai-chat" id="aiChat">
  <div class="ai-head">
    <span>🤖 Консультант Кухни Островский</span>
    <button id="aiClose" class="ai-close">×</button>
  </div>
  <div class="ai-body" id="aiBody">
    <div class="ai-msg bot">Здравствуйте! Я ИИ-консультант мастерской «Кухни Островский». Расскажу про кухни и мебель в Ростове, Батайске и Азове, цены, сроки и условия. Что вас интересует?</div>
  </div>
  <div class="ai-input-row">
    <input id="aiInput" type="text" placeholder="Введите ваш вопрос..." autocomplete="off">
    <button id="aiSend">➤</button>
  </div>
</div>

<script>
const progress=document.getElementById('progress');
const header=document.getElementById('header');
function onScroll(){
  const h=document.documentElement;
  const sc=h.scrollHeight>h.clientHeight?h.scrollTop/(h.scrollHeight-h.clientHeight):0;
  progress.style.width=(sc*100)+'%';
  header.classList.toggle('solid',h.scrollTop>40);
}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
document.getElementById('logo').addEventListener('click',e=>{e.preventDefault();window.scrollTo({top:0,behavior:'smooth'});});
const burger=document.getElementById('burger'),menu=document.getElementById('menu'),scrim=document.getElementById('scrim');
function closeMenu(){burger.classList.remove('open');menu.classList.remove('open');scrim.classList.remove('show');}
burger.addEventListener('click',()=>{
  const open=menu.classList.contains('open');
  if(open)closeMenu();else{burger.classList.add('open');menu.classList.add('open');scrim.classList.add('show');}
});
scrim.addEventListener('click',closeMenu);
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
const sections=['about','works','reviews','services','process','contacts'];
const navLinks=menu.querySelectorAll('a[href^="#"]');
window.addEventListener('scroll',()=>{
  let current='';
  sections.forEach(id=>{const el=document.getElementById(id);if(el&&el.getBoundingClientRect().top<=120)current=id;});
  navLinks.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+current));
},{passive:true});
function supportsParallax(){return window.matchMedia('(min-width:861px)').matches;}
if(supportsParallax()){
  const bgs=document.querySelectorAll('.panel .bg');
  const contents=document.querySelectorAll('.panel .content');
  function parallax(){
    bgs.forEach(bg=>{const r=bg.parentElement.getBoundingClientRect();const c=(r.top+r.height/2)-innerHeight/2;bg.style.transform='translateY('+(-c*0.25)+'px)';});
    contents.forEach(cn=>{const r=cn.parentElement.getBoundingClientRect();const c=(r.top+r.height/2)-innerHeight/2;cn.style.transform='translateY('+(-c*0.08)+'px)';});
  }
  window.addEventListener('scroll',parallax,{passive:true});parallax();
}
function animateCount(el){
  const target=parseFloat(el.dataset.count);
  const dec=parseInt(el.dataset.decimal||'0');
  const suffix=el.dataset.suffix||'';
  const dur=1200,start=performance.now();
  function tick(t){
    let p=Math.min((t-start)/dur,1);
    p=1-Math.pow(1-p,3);
    let val=(target*p).toFixed(dec);
    el.textContent=(dec?val:Math.round(val))+suffix;
    if(p<1)requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
const statIO=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){animateCount(e.target);statIO.unobserve(e.target);}});},{threshold:.5});
document.querySelectorAll('.stat .num').forEach(el=>statIO.observe(el));
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
(function(){
  const h=document.getElementById('heroTitle');
  const tokens=h.innerHTML.split(/(<[^>]+>)/);
  let html='';
  tokens.forEach(t=>{if(/^<[^>]+>$/.test(t)){html+=t;}else{html+=t.split(/\s+/).filter(w=>w).map(w=>'<span class="t-word">'+w+'</span>').join(' ');}});
  h.innerHTML=html;
  h.querySelectorAll('.t-word').forEach((s,i)=>setTimeout(()=>s.classList.add('on'),120+i*70));
})();
function initCarousel(trackId,prevId,nextId,dotsId){
  const track=document.getElementById(trackId),prev=document.getElementById(prevId),next=document.getElementById(nextId),dotsBox=document.getElementById(dotsId),items=[...track.children];
  dotsBox.innerHTML='';
  items.forEach((_,i)=>{const d=document.createElement('button');d.className='car-dot'+(i===0?' active':'');d.addEventListener('click',()=>items[i].scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'}));dotsBox.appendChild(d);});
  const dots=[...dotsBox.children];
  const step=()=>items[0].offsetWidth+18;
  track.addEventListener('scroll',()=>{const idx=Math.round(track.scrollLeft/step());dots.forEach((d,i)=>d.classList.toggle('active',i===idx));},{passive:true});
  prev.addEventListener('click',()=>track.scrollBy({left:-step(),behavior:'smooth'}));
  next.addEventListener('click',()=>track.scrollBy({left:step(),behavior:'smooth'}));
}
initCarousel('carTrack','carPrev','carNext','carDots');
initCarousel('revTrack','revPrev','revNext','revDots');
const lightbox=document.getElementById('lightbox'),lbImg=document.getElementById('lbImg'),lbCount=document.getElementById('lbCount');
const lbItems=[...document.querySelectorAll('#carTrack .car-slide img')];
let lbIdx=0;
function openLb(i){lbIdx=i;lbImg.src=lbItems[i].src;lbImg.alt=lbItems[i].alt;lbCount.textContent=(i+1)+' / '+lbItems.length;lightbox.classList.add('open');}
function closeLb(){lightbox.classList.remove('open');}
function lbStep(d){openLb((lbIdx+d+lbItems.length)%lbItems.length);}
lbItems.forEach((img,i)=>img.addEventListener('click',()=>openLb(i)));
document.getElementById('lbClose').addEventListener('click',closeLb);
document.getElementById('lbPrev').addEventListener('click',e=>{e.stopPropagation();lbStep(-1);});
document.getElementById('lbNext').addEventListener('click',e=>{e.stopPropagation();lbStep(1);});
lightbox.addEventListener('click',e=>{if(e.target===lightbox)closeLb();});
document.addEventListener('keydown',e=>{if(lightbox.classList.contains('open')){if(e.key==='Escape')closeLb();if(e.key==='ArrowLeft')lbStep(-1);if(e.key==='ArrowRight')lbStep(1);}});
const cookieBar=document.getElementById('cookieBar'),cookieOk=document.getElementById('cookieOk');
if(!localStorage.getItem('cookiesAccepted')){setTimeout(()=>cookieBar.classList.add('show'),900);}
cookieOk.addEventListener('click',()=>{localStorage.setItem('cookiesAccepted','1');cookieBar.classList.remove('show');});

// ИИ-чат
const aiBtn=document.getElementById('aiBtn'),aiChat=document.getElementById('aiChat'),
      aiClose=document.getElementById('aiClose'),aiBody=document.getElementById('aiBody'),
      aiInput=document.getElementById('aiInput'),aiSend=document.getElementById('aiSend');
function aiAdd(text,who){const m=document.createElement('div');m.className='ai-msg '+who;m.textContent=text;aiBody.appendChild(m);aiBody.scrollTop=aiBody.scrollHeight;}
aiBtn.addEventListener('click',()=>{aiChat.classList.add('open');aiInput.focus();});
aiClose.addEventListener('click',()=>aiChat.classList.remove('open'));
async function aiAsk(){
  const q=aiInput.value.trim();if(!q)return;
  aiAdd(q,'user');aiInput.value='';aiAdd('Печатает...','bot typing');
  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})});
    const data=await res.json();
    const t=aiBody.querySelector('.typing');if(t)t.remove();
    aiAdd(data.reply||'Не удалось получить ответ. Попробуйте позже.','bot');
  }catch(e){
    const t=aiBody.querySelector('.typing');if(t)t.remove();
    aiAdd('Ошибка соединения с ИИ. Позвоните нам: +7 (950) 846-53-97','bot');
  }
}
aiSend.addEventListener('click',aiAsk);
aiInput.addEventListener('keydown',e=>{if(e.key==='Enter')aiAsk();});
document.getElementById('year').textContent=new Date().getFullYear();
</script>
</body>
</html>
"""

# ------------------------------- HTTP-сервер ---------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, "Not found")

    def do_POST(self):
        if self.path.split("?")[0] != "/api/chat":
            self._send(404, "Not found")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
            question = (data.get("message") or "").strip()
            if not question:
                self._send(400, json.dumps({"error": "empty message"}, ensure_ascii=False), "application/json")
                return
            reply = ask_ai(question) or "Извините, не удалось получить ответ. Попробуйте позже."
            self._send(200, json.dumps({"reply": reply}, ensure_ascii=False), "application/json")
        except Exception as exc:  # noqa: BLE001
            self._send(500, json.dumps({"error": str(exc)}, ensure_ascii=False), "application/json")

    def log_message(self, *args):  # тихие логи
        pass

if __name__ == "__main__":
    print("Кухни Островский сервер запущен на http://127.0.0.1:{}".format(PORT))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
