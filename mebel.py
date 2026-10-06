# -*- coding: utf-8 -*-
"""
mebel.py — «Кухни Островский»: сайт + админка (CMS) на Supabase + AI-помощник.
Всё в одном файле: шаблон страницы, админка, Supabase, AI, прокси VK, favicon.

Переменные окружения (RelaxDev → Environment)
---------------------------------------------
PORT, DOMAIN, ADMIN_LOGIN, ADMIN_PASSWORD,
SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, SUPABASE_BUCKET,
YANDEX_API_KEY, FOLDER_ID, GIGACHAT_AUTH_KEY, AI_PROVIDER (yandex|gigachat|auto)
"""

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

# ============================================================
#  КОНФИГ
# ============================================================
PORT = int(os.environ.get("PORT", "8080"))
DOMAIN = os.environ.get("DOMAIN", "https://кухниостровский.рф").rstrip("/")
ROOT = os.path.dirname(os.path.abspath(__file__))

SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "https://hliafkrpvmntpctmqwfu.supabase.co").rstrip("/")
SUPABASE_ANON = os.environ.get("SUPABASE_ANON_KEY") or (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6ImFub24i"
    "LCJpYXQiOjE3OTEyMDQ1NzYsImV4cCI6MjEwNjc4MDU3Nn0.yi57-Ty1iIfhnEh80_zvifhX1W_JX2qCl7QrARuJ2ns")
SUPABASE_SERVICE = os.environ.get("SUPABASE_SERVICE_KEY") or (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaWFma3Jwdm1udHBjdG1xd2Z1Iiwicm9sZSI6InNlcnZpY2Vfcm9s"
    "ZSIsImlhdCI6MTc5MTIwNDU3NiwiZXhwIjoyMTA2NzgwNTc2fQ.Yr4z9vx6kF9ZINNNUjUn43GYi-A2BmBfg8uyrOtmDWo")
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
IMG_TTL = 604800
HTTP_TIMEOUT = 12

FAVICON_URL = ("https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg"
               "?quality=95&cs=1254x0")

# ============================================================
#  АНИМАЦИИ (вставляются в шаблон, если их там ещё нет)
# ============================================================
ANIM_STYLE = """<style id="goldAnimations">
@keyframes shimmerX{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes goldGradient{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes particleFloat{0%{transform:translateY(100vh) scale(.5);opacity:0}10%{opacity:1}90%{opacity:.85}100%{transform:translateY(-100px) scale(1.1);opacity:0}}
@keyframes rippleAnim{to{transform:scale(4);opacity:0}}
@keyframes glowPulse{0%,100%{text-shadow:0 0 10px rgba(236,207,160,.3)}50%{text-shadow:0 0 30px rgba(236,207,160,.8),0 0 60px rgba(212,175,106,.5)}}
h1,h2.k,.sec-head h2,.about-body h2,.contact-info h2,.cta h2{background-image:linear-gradient(90deg,#faf3e6 0%,#faf3e6 30%,#eccfa0 50%,#faf3e6 70%,#faf3e6 100%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;transition:background-position 1.6s ease;background-position:100% 0}
h1 em,.shimmer,h1 em.shimmer{background-image:linear-gradient(90deg,#eccfa0,#fff 35%,#eccfa0 70%,#eccfa0 100%);background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 4s linear infinite}
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
#goldParticles{position:fixed;inset:0;z-index:1;pointer-events:none;overflow:hidden}
#goldParticles span{position:absolute;width:6px;height:6px;border-radius:50%;background:radial-gradient(circle,rgba(236,207,160,.9),rgba(212,175,106,.4) 40%,transparent 70%);box-shadow:0 0 12px rgba(236,207,160,.55);animation:particleFloat linear infinite}
.svc svg,.guar .ico,.c-ico,.vb-play{transition:transform .55s cubic-bezier(.34,1.56,.64,1),filter .35s}
.svc:hover svg{transform:scale(1.18) rotate(-8deg);filter:drop-shadow(0 0 12px rgba(236,207,160,.9))}
.guar:hover .ico{transform:scale(1.18) rotate(8deg);box-shadow:0 0 30px rgba(236,207,160,.5)}
.c-line:hover .c-ico{transform:scale(1.16) rotate(-6deg);box-shadow:0 0 22px rgba(236,207,160,.55)}
.rev-stars{background:linear-gradient(90deg,#eccfa0,#fff 50%,#eccfa0 100%);background-size:200% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 3s linear infinite}
.eyebrow,.kicker,.sec-head .kicker{background:linear-gradient(90deg,rgba(236,207,160,.85),#fff 50%,rgba(236,207,160,.85));background-size:220% auto;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:shimmerX 4.5s linear infinite}
.car-slide img{transition:transform 1.1s cubic-bezier(.22,.61,.36,1)}
.car-slide:hover img{transform:scale(1.12)}
.gold-divider b{animation:glowPulse 2.8s ease-in-out infinite}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.01ms !important;transition-duration:.01ms !important}}
</style>"""

ANIM_SCRIPT = """<script id="goldAnimationScript">
(function(){
  var SEL='.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head';
  function showAll(){var n=document.querySelectorAll(SEL);for(var i=0;i<n.length;i++)n[i].classList.add('anim-in')}
  if(!('IntersectionObserver' in window)){showAll();document.documentElement.classList.remove('js');return;}
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){showAll();document.documentElement.classList.remove('js');return;}
  try{
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('anim-in');io.unobserve(e.target)}})},{threshold:0.12});
    document.querySelectorAll(SEL).forEach(function(el){io.observe(el)});
    var headIo=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('anim-visible');headIo.unobserve(e.target)}})},{threshold:0.5});
    document.querySelectorAll('h1,h2.k,.sec-head h2,.about-body h2,.contact-info h2,.cta h2').forEach(function(el){headIo.observe(el)});
  }catch(err){showAll()}
  setTimeout(showAll,3000);
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

# ============================================================
#  ДЕФОЛТНЫЙ КОНТЕНТ
# ============================================================
DEFAULT_DATA = {
    'seo': {
        'title': 'Кухни Островский — кухни на заказ в Ростове, Батайске и Азове | Мебель под ключ',
        'keywords': ('кухни остров, кухни островский, кухни островского, кухни островский ростов, кухни ростов островский, '
                     'кухни батайск островский, кухни азов островский, кухни на заказ ростов, кухни на заказ батайск, '
                     'кухни на заказ азов, мебель островского, мебель на заказ ростов, корпусная мебель, шкафы купе, '
                     'гардеробные, прихожие, кухни под ключ, мебель островский'),
        'og_image': ('https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg'
                     '?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0'),
        'description': ('Кухни на заказ в Ростове-на-Дону, Батайске и Азове от мастерской «Кухни Островский». Бесплатный замер и '
                        '3D-проект, собственное производство, монтаж под ключ. ☎ +7 (950) 846-53-97'),
        'og_title': 'Кухни Островский — кухни и корпусная мебель на заказ',
        'og_description': 'Кухни, шкафы и гардеробные под ключ в Ростове-на-Дону, Батайске и Азове. Бесплатный замер и 3D-проект.',
        'domain': 'https://кухниостровский.рф',
        'canonical': 'https://кухниостровский.рф/',
        'yandex_verification': 'f7e96d07aee79bf3',
        'google_verification': 'dNSAELu64Y7aK5sjz_zpmhoz6YKn2PIZ03UKPwrgnCI',
        'metrika_id': '',
        'robots': '',
        'extra_urls': []
    },
    'code': {'head': '', 'body': ''},
    'design': {
        'bg': '#0e0c09',
        'gold': '#d4af6a',
        'gold_soft': '#eccfa0',
        'gold_deep': '#a37c3f',
        'text': '#f5efe3',
        'muted': '#b9ad9a',
        'fonts_url': ('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,500'
                      '&family=Manrope:wght@300;400;500;600;700;800&display=swap'),
        'custom_css': ''
    },
    'brand': {
        'vk': 'https://vk.com/mebel.ostrovsky',
        'sub': 'Ростов · Батайск · Азов',
        'name': 'Кухни Островский',
        'phone': '+7 (950) 846-53-97',
        'logo_url': ('https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg'
                     '?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0'),
        'telegram': 'https://t.me/fanny161',
        'phone_raw': '+79508465397'
    },
    'nav': {
        'items': [
            {'label': 'Специалист', 'href': '#about'},
            {'label': 'Работы', 'href': '#works'},
            {'label': 'Отзывы', 'href': '#reviews'},
            {'label': 'Услуги', 'href': '#services'},
            {'label': 'Как работаем', 'href': '#process'},
            {'label': 'Города', 'href': '#cities'},
            {'label': 'Контакты', 'href': '#contacts'}
        ],
        'cta_label': 'Позвонить',
        'cta_href': 'tel:+79508465397'
    },
    'hero': {
        'bg': ('https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg'
               '?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1080x0'),
        'sub': ('Проектируем и изготавливаем кухни, шкафы, гардеробные и другую корпусную мебель в Ростове, Батайске и Азове — по '
                'вашему проекту, от замера до монтажа.'),
        'btn1': 'Получить консультацию',
        'btn2': 'Смотреть работы',
        'eyebrow': 'Мебель и кухни на заказ',
        'title_em': 'создаёт настроение',
        'title_before': 'Мебель, которая ',
        'btn1_href': '#consult',
        'btn2_href': '#works'
    },
    'stats': {
        'bg': ('https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg'
               '?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1080x0'),
        'items': [
            {'prefix': '', 'num': '10', 'suffix': '+', 'decimal': '', 'label': 'лет опыта'},
            {'prefix': '', 'num': '5', 'suffix': '', 'decimal': '1', 'label': 'средняя оценка клиентов'},
            {'prefix': '', 'num': '8', 'suffix': '/10', 'decimal': '', 'label': 'клиентов по рекомендации'},
            {'prefix': '', 'num': '100', 'suffix': '%', 'decimal': '', 'label': 'полный цикл под ключ'}
        ]
    },
    'about': {
        'bg': ('https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg'
               '?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2208x1656&from=bu&u=9_d3vo4cDIif_5OxDZbDgMLFC1xuAQSKRY1zAPscIwM&cs=1280x0'),
        'name': 'Роман Островский',
        'role': 'Руководитель мебельной мастерской Островского',
        'photo': 'https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg',
        'title': 'Кухни и мебель под ключ — с заботой о деталях',
        'kicker': 'О руководителе',
        'features': ['Кухни, шкафы, гардеробные и прихожие',
                     'Честный расчёт — без навязывания лишнего',
                     'Аккуратность, пунктуальность, сопровождение',
                     'Гарантия качества'],
        'card_text': ('С командой изготавливаем кухни и корпусную мебель по индивидуальным проектам — с учётом ваших идей, размеров '
                      'и задач.'),
        'text': ('Мы помогаем с планировкой и подбором материалов, предлагаем решения даже для сложных задач — когда другие разводят '
                 'руками. Ведём вас от консультации и замера до сборки и установки.')
    },
    'consult': {
        'bg': ('https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg'
               '?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0'),
        'text': ('Позвоните или напишите нам в Telegram или MAX — расскажем про кухни и мебель, всё обсудим и договоримся о '
                 'бесплатном замере.'),
        'title': 'Консультация',
        'kicker': 'Бесплатно',
        'phone': '+7 (950) 846-53-97',
        'phone_raw': '+79508465397'
    },
    'works': {
        'bg': ('https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg'
               '?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=q3wKCscaGbBU8n3umOUNA0wOvLkQBDAVXIkzDrivHgk&cs=1280x0'),
        'items': [
            {'alt': 'Кухня на заказ в Ростове', 'url': 'https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1080x0'},
            {'alt': 'Кухня на заказ в Батайске', 'url': 'https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1080x0'},
            {'alt': 'Кухня на заказ в Азове', 'url': 'https://sun9-11.vkuserphoto.ru/s/v1/ig2/Xh5Xw9Yb1reqhfFznlGk8NjvSQAxCbysuiL5IWRt_f3ELVb8fvoYPg00eFIHV-xiS9I4nhYBj4ttU_FHVkPpX8Z3.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,1600x1200&from=bu&u=pY-bjOidU1jjNjiF66Dn4Ycgmb6utH_d0Ti7oSJr0qA&cs=1080x0'},
            {'alt': 'Мебель на заказ в Ростове', 'url': 'https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1080x0'},
            {'alt': 'Шкаф-купе на заказ', 'url': 'https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1080x0'},
            {'alt': 'Мебель на заказ в Батайске', 'url': 'https://sun9-24.vkuserphoto.ru/s/v1/ig2/lS8MpZ4V9XUKPJ7l9GmjnkCnHW2MGfnq86jH-Gzx6bAgr4m3azL5Xd_fkdPHY_NOsJjST3Zw2iQkuGKGBwYODdgM.jpg?quality=95&as=32x42,48x63,72x95,108x142,160x211,240x316,360x474,480x632,540x711,640x843,720x949,1080x1423,1280x1686,1440x1897,1943x2560&from=bu&u=dLnirpryCPR3qvUPphwt7JaP5ljnoIl1yyGyUNiUjZI&cs=1080x0'},
            {'alt': 'Кухня на заказ', 'url': 'https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1080x0'},
            {'alt': 'Мебель на заказ', 'url': 'https://sun9-39.vkuserphoto.ru/s/v1/ig2/5cyrhjIBSWB5GGZATB29IrmjydaNdVOx-iP_dMNKsMbePp5Ccs2rnkEpLnfft3yAZGeMEE3IfInjMQ7aU6Z6jnHc.jpg?quality=95&as=32x24,48x36,72x54,108x82,160x121,240x181,360x272,480x363,540x408,640x484,720x544,1080x817,1280x968&from=bu&u=l1uWXrXXeEAKk1VMgGM5wyIo7DtKdQGhKlCwMjoS0t8&cs=1080x0'},
            {'alt': 'Кухня на заказ в Батайске', 'url': 'https://sun9-68.vkuserphoto.ru/s/v1/ig2/6KwHlOiN9pxXNIwTImKO6QGkrSCTVqreybJu-63m8wbhdFFMIl06es9cPeurIdwuwXGtsFTkdJ6IOjMaS1qRtfxJ.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VgDjFEJKqpW6dWVO-E4y4Q6xcuyoqiL7LxhG36oLPjw&cs=1080x0'},
            {'alt': 'Мебель на заказ', 'url': 'https://sun9-23.vkuserphoto.ru/s/v1/ig2/wfBQoeOzjZbCRCvxmIkx_V3xC0fgMd3TTxRDSRG2CHDMok6B2ZKrG7vCAJ_G1DmrZ6JS1_RC2tr87Q64wJJ4aW9w.jpg?quality=95&as=32x25,48x37,72x56,108x84,160x124,240x186,360x279,480x372,540x419,640x496,720x558,1080x837,1280x992,1440x1117,2560x1985&from=bu&u=kZXvrlzwGUvzrHmYa8tHXbvyhU_JlNlefLxxcCYqM1A&cs=1080x0'},
            {'alt': 'Кухня на заказ', 'url': 'https://sun9-33.vkuserphoto.ru/s/v1/ig2/TQbwf8FdMs_jwKfC_ONoxEHBIpc2L5yf_T0McNeUKRn0tK7fVbC5YbHfsB0TGLlNC_D55htM_2nREACuIw7ykLIx.jpg?quality=95&as=32x43,48x65,72x97,108x145,160x215,240x323,360x484,480x645,540x726,640x860,720x968,1080x1452,1280x1721,1440x1936,1904x2560&from=bu&u=rbH0OM9Bv0PnevamgtW5nYBm9jxFI28R6D1wxzq6fJA&cs=1080x0'},
            {'alt': 'Кухня на заказ', 'url': 'https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0'},
            {'alt': 'Кухня на заказ', 'url': 'https://sun9-65.vkuserphoto.ru/s/v1/ig2/z_wfZeGA9H6LHDsevjkijUHpbVyLGWFM38frX4hKrjgOnscfAloGdrVpPUwl4XoXCG_YgcKXTgeeTsDDcWEBvdi1.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YbZ1WmiK3ZCk0bKWZhf_YKp6dTUU2vbsQo7Ya4Hoi6s&cs=1080x0'}
        ],
        'title': 'Кухни и мебель, которые мы сделали',
        'kicker': 'Наши работы',
        'subtitle': 'Нажмите на фото, чтобы рассмотреть в большом размере.',
        'hint': 'Листайте'
    },
    'reviews': {
        'bg': ('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg'
               '?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0'),
        'items': [
            {'sub': 'Кухня на заказ',
             'name': 'Виктория Брандикова',
             'text': ('Заказывали у Романа кухню, всё прошло на высшем уровне, начиная от замеров, до установки! Мы очень рады, '
                      'что обратились именно к нему (нашли в объявлении и нам крупно повезло), Роман супер профессионал своего дела!!! '
                      'Кухня у нас маленькая, не стандартная, сверху выступы, вся на трубах, расположение мойки и кухонной плиты не '
                      'удобное и вытяжку мы хотели, но нам некуда было её устанавливать (как мы думали), но Роман всё разрешил, '
                      'практично разместил технику (в том числе и вытяжку), переставил мойку, установил подсветку сделал кухню '
                      'функциональной светлой, практичной и современной. Кухня была готова в короткие сроки, установкой очень '
                      'довольны, всё под ключ с установкой техники и подключением, всё быстро, качественно, и чисто! Мы не ожидали '
                      'такого результата, просто не верится, что у нас теперь удобная, вместительная, современная кухня, о такой '
                      'даже и не мечтали, даже несмотря на то, что кухня бюджетная. За мебелью теперь только к Роману!!! Однозначно '
                      'всем буду рекомендовать!!!'),
             'stars': 5,
             'video': '',
             'avatar': ('https://sun9-3.vkuserphoto.ru/s/v1/ig2/-cVZEipS5I4ROZUZ2fxoIaGJBZXpUs76_WKoUZpPw_r2-gnqqUvgTqjLjYoTZ0R21nsCSvjUPyw_vSn1jxAYJC8K.jpg'
                        '?quality=95&as=32x30,48x45,72x68,108x101,160x150,240x225,360x338,480x450,540x507,640x601,720x676,1080x1014,1280x1201,1440x1351,2505x2351&from=bu&cs=128x0')},
            {'sub': 'Кухня и гардеробная',
             'name': 'Виктория Маренко',
             'text': ('И вновь мы обратились к Роману! Понадобилась кухня. Кухня на самом деле очень удобная! Как и хотелось она '
                      'светлая, но не маркая. Как всегда учтены все пожелания и воплощены в жизнь! Очень трудно нам дался выбор '
                      'цветов, но Роман спокойно вынес все наши метания, выполнил работу достойно, внимательно и аккуратно! '
                      'Однозначно советую обращаться к нему. Гардеробную так же заказывали у Романа, и она идеальна! Ответственный '
                      'подход, качество, внимательность и чистота исполнения - его качества, которые для нас важны.'),
             'stars': 5,
             'video': '',
             'avatar': ('https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg'
                        '?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0')},
            {'sub': 'Шкаф, тумбы, прихожая',
             'name': 'Любовь Петелько',
             'text': ('Всем здравствуйте. Я заказала у Романа шкаф купе в спальню. Когда Роман приехал, я не совсем понимала что я '
                      'хочу, пообщавшись с ним, получила много советов и рекомендаций по составу и цвету шкафа. В итоге решила в '
                      'комплект заказать сразу тумбы, гарнитур под телевизор, и прихожую. Установили все раньше обещанного срока. Я '
                      'очень довольна и всем рекомендую. Роман специалист своего дела. Скоро буду заказывать зону хранения балкона и '
                      'самое главное кухню мечты. Спасибо!'),
             'stars': 5,
             'video': '',
             'avatar': ('https://sun9-53.vkuserphoto.ru/s/v1/ig2/gZheSpaWhz7StIdwlzSoCIfA01e-x8jVUMESDK2u9ONRR1s3txB-b6F7lqLLj-Y6QFqFU5x463yoWmnTxf5T88g2.jpg'
                        '?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&cs=128x0')},
            {'sub': 'Шкаф и стенка',
             'name': 'Дмитрий Юшенко',
             'text': ('Заказывали у Романа шкаф и стенку в спальню. Работа вышла отличной, подсказал несколько удачных решений наших '
                      'хотелок. Все супер! Спасибо!'),
             'stars': 5,
             'video': '',
             'avatar': ('https://sun9-83.vkuserphoto.ru/s/v1/ig2/zYO0FQ_fFsgxDWhaTE85lNpixn2ikScuD58qVoXtqda8vFxoS-LGsT54k9pk9tDVEpzGpJfCw5eg5TNtYgE2Q8_y.jpg'
                        '?quality=95&as=32x47,48x71,72x106,108x159,160x236,240x353,360x530,480x707,540x795,640x943,720x1061,869x1280&from=bu&cs=1280x0')},
            {'sub': 'Кухня на заказ',
             'name': 'Екатерина Умнягина',
             'text': ('Заказывали у Романа кухню, всё очень понравилось! Подбирали всё до мелочей, и Рома всё исполнил, как мы хотели, '
                      'за это мы ему очень благодарны. Всё сделано идеально, спрятали то, что не должно быть видно, и получилось очень '
                      'красиво. Спасибо, Рома, за эту крутую современную кухню!!!'),
             'stars': 5,
             'video': '',
             'avatar': ('https://sun9-46.vkuserphoto.ru/s/v1/ig2/bVm2vnJWOD92dzHJ3_21NbqhcwF7DW7a05XzjaTWteG9Dviu9nt8LlA5bgzdbsBhGtYbrs7rvOMTylQQIV43cl4T.jpg'
                        '?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&cs=128x0')},
            {'sub': 'Два шкафа, гардеробная',
             'name': 'Анастасия Зайцева',
             'text': ('Заказывали у Романа два шкафа. Во время замеров у нас не было определённой идеи, как сделать вместительный '
                      'шкаф в нашу небольшую спальню, ещё и с несущей колонной. Роман подкинул прекрасную идею, в итоге получился не '
                      'просто шкаф, а целая угловая гардеробная, я была в восторге! Большой выбор цветов и текстур. Работа выполнена '
                      'в оговорённый срок и качественно. Большое спасибо за эстетичное воплощение нашей мечты!'),
             'stars': 5,
             'video': '',
             'avatar': ('https://sun9-48.vkuserphoto.ru/s/v1/ig2/OdS0JaUmpkj7vzQLNz1oyY6PBksnYylZuY54LZ2vnibrqxNc0IimIjE6d6NWySeMm6N2MLIUHG6WLKtAFJ82ICwE.jpg'
                        '?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,960x1280&from=bu&cs=128x0')},
            {'sub': 'Видеоотзыв · Кухня на заказ',
             'name': 'Александр Карташев',
             'text': ('«Прям гордость квартиры! За приемлемую цену получили отличную кухню: выступ стояка закрыли пеналом, а '
                      'в ножку барного стола встроили розетки».'),
             'stars': 5,
             'video': 'https://vk.ru/video_ext.php?oid=-212015374&id=456239019&hash=6abf300a7c2518d4',
             'avatar': ''}
        ],
        'title': 'Что говорят наши клиенты',
        'kicker': 'Отзывы',
        'subtitle': 'Реальные отзывы о нашей работе. Листайте влево-вправо.',
        'hint': 'Листайте',
        'video_poster': ('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg'
                         '?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0')
    },
    'services': {
        'bg': ('https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg'
               '?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1280x0'),
        'items': [
            {'icon': 'M3 9h18M3 9v10a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V9M3 9l2-4h14l2 4M8 9v2M12 9v2M16 9v2',
             'text': 'Проектируем кухню точно под ваш размер, стиль и привычки — от классики до минимализма.',
             'title': 'Кухни на заказ'},
            {'icon': 'M3 3h18v18H3zM3 8h18M8 8v13M16 8v13',
             'text': 'Шкафы-купе, гардеробные, тумбы и комоды — встроенные и отдельно стоящие.',
             'title': 'Шкафы и гардеробные'},
            {'icon': 'M12 3v18M3 12h18M5 5l14 14M19 5L5 19',
             'text': 'Прихожие, стенки, гарнитуры под ТВ — аккуратно впишем в ваш интерьер.',
             'title': 'Прихожие и стенки'},
            {'icon': 'M14 6l4 4M5 19l7-7M17 3l4 4-4 4-1-1-1 1-4-4 1-1-1-1 4-4z',
             'text': 'Профессиональная установка, аккуратная сборка и подключение техники.',
             'title': 'Сборка и монтаж'},
            {'icon': 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 3v18M3 12h18',
             'text': 'Выезжаем на замер, делаем планировку и 3D-проект — бесплатно.',
             'title': 'Замер и проект'},
            {'icon': 'M3 12a9 9 0 1 0 9-9M3 12h6M3 12l4-4M3 12l4 4',
             'text': 'Освежим фасады и фурнитуру существующей кухни — дешевле, чем новая.',
             'title': 'Обновление мебели'}
        ],
        'title': 'Услуги',
        'kicker': 'Что мы делаем',
        'subtitle': 'Индивидуальный подход к каждому проекту и полный цикл производства.'
    },
    'process': {
        'bg': ('https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg'
               '?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VpmAnVyzkXcBCcJLy2DSlVkJJG2zYnSPbLzk7-TXGGk&cs=1280x0'),
        'items': [
            {'n': '01', 'text': 'Вы звоните или пишете — обговариваем задачу и пожелания.', 'title': 'Обращение'},
            {'n': '02', 'text': 'Выезжаем, снимаем размеры и обсуждаем планировку. Бесплатно.', 'title': 'Замер'},
            {'n': '03', 'text': 'Готовим 3D-проект и подбираем материалы с фурнитурой.', 'title': 'Проект'},
            {'n': '04', 'text': 'Фиксируем стоимость и условия, подписываем договор.', 'title': 'Договор'},
            {'n': '05', 'text': 'Изготавливаем мебель на собственном производстве.', 'title': 'Производство'},
            {'n': '06', 'text': 'Привозим, собираем и устанавливаем. Сдаём с гарантией.', 'title': 'Доставка и монтаж'}
        ],
        'title': 'Путь от идеи до готовой мебели',
        'kicker': 'Как мы работаем'
    },
    'guarantees': {
        'bg': ('https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg'
               '?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YCey971XM2nuNjhkwSaIOfPMTMneMAyHLaPyHT4mLyY&cs=1280x0'),
        'items': [
            {'icon': 'M12 3l7 3v6c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3zM9 12l2 2 4-4',
             'text': 'Отвечаем за свою работу и сопровождаем после установки.',
             'title': 'Гарантия качества'},
            {'icon': 'M4 20h16M6 20V8l6-4 6 4v12M9 11h6M9 15h6M10 11v8M14 11v8',
             'text': 'Без навязывания лишнего и скрытых доплат.',
             'title': 'Честный расчёт'},
            {'icon': 'M3 21V9l9-5 9 5v12M3 21h18M9 21v-6h6v6M12 9v2',
             'text': 'Без посредников — контролируем качество на каждом этапе.',
             'title': 'Собственное производство'},
            {'icon': 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM4 21c0-4 3.6-6 8-6s8 2 8 6',
             'text': 'Вы всегда на связи со специалистом — от замера до монтажа.',
             'title': 'Личное сопровождение'}
        ],
        'title': 'Гарантии и преимущества',
        'kicker': 'Почему мы'
    },
    'cities': {
        'bg': ('https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg'
               '?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1280x0'),
        'items': [
            {'name': 'Ростов-на-Дону', 'text': 'Выезд на замер, проектирование, производство и монтаж мебели под ключ.'},
            {'name': 'Батайск', 'text': 'Кухни и корпусная мебель с бесплатным замером и 3D-проектом.'},
            {'name': 'Азов', 'text': 'Индивидуальные проекты, доставка, сборка и установка с гарантией.'}
        ],
        'title': 'Три города — один стандарт качества',
        'kicker': 'Где работаем',
        'subtitle': 'Бесплатный замер и проект в каждом из городов.'
    },
    'cta': {
        'bg': ('https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg'
               '?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0'),
        'text': 'Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.',
        'title': 'Готовы обсудить вашу мебель?',
        'button': '📞 Позвонить специалисту'
    },
    'contacts': {
        'bg': ('https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg'
               '?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0'),
        'title': 'Создадим мебель, о которой вы мечтали',
        'kicker': 'Контакты',
        'regions': 'Ростов-на-Дону, Батайск, Азов',
        'subtitle': 'Позвоните или напишите — ответим быстро и подскажем по всем вопросам.',
        'call_label': 'Свяжитесь с нами удобным способом',
        'call_number': '+7 (950) 846-53-97',
        'call_hint': 'Бесплатная консультация и запись на замер.\nЗвоните или пишите в любой мессенджер.',
        'lines': [
            {'label': 'Регион работы', 'value': 'Ростов-на-Дону, Батайск, Азов', 'href': '',
             'icon': 'M12 21.5S5.5 15.9 5.5 10.5a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11zM12 13a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z'},
            {'label': 'Сайт в VK', 'value': 'mebel.ostrovsky', 'href': 'https://vk.com/mebel.ostrovsky',
             'icon': 'M14 19c-6 0-9.5-4.5-9.7-12h3c.1 5 2.5 8 4.3 8.8V7h3v5c1.8-.2 3.6-2.6 4.2-5h3c-.6 3.4-2.8 5.8-4.6 6.6 1.8.9 4.6 3.6 5.4 8.4h-3.4c-.6-2.5-2.4-4.4-4.3-4.9V19H14z'},
            {'label': 'Telegram / MAX', 'value': 'по номеру +7 (950) 846-53-97', 'href': 'https://t.me/fanny161',
             'icon': 'M21.9 4.6L18.8 19c-.2 1-.8 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.8L18 6.4c.4-.3-.1-.5-.6-.2L6.7 13.4l-4.6-1.4c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.6 1z'}
        ],
        'buttons': [
            {'label': 'Позвонить', 'href': 'tel:+79508465397', 'cls': 'c-call', 'external': False,
             'icon': 'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 2z'},
            {'label': 'Написать в Telegram', 'href': 'https://t.me/fanny161', 'cls': 'c-tg', 'external': True,
             'icon': 'M21.9 4.6L18.8 19c-.2 1-.8 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.8L18 6.4c.4-.3-.1-.5-.6-.2L6.7 13.4l-4.6-1.4c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.6 1z'},
            {'label': 'Написать в MAX', 'href': 'tel:+79508465397', 'cls': 'c-max', 'external': False,
             'icon': 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'}
        ]
    },
    'footer': {
        'line': 'Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов',
        'copyright': 'Кухни Островский. Все права защищены.',
        'socials': [
            {'label': 'Позвонить', 'href': 'tel:+79508465397',
             'icon': 'M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 2z'},
            {'label': 'Telegram', 'href': 'https://t.me/fanny161',
             'icon': 'M21.9 4.6L18.8 19c-.2 1-.8 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.8L18 6.4c.4-.3-.1-.5-.6-.2L6.7 13.4l-4.6-1.4c-1-.3-1-1 .2-1.5l18-6.9c.8-.3 1.6.2 1.6 1z'},
            {'label': 'ВКонтакте', 'href': 'https://vk.com/mebel.ostrovsky',
             'icon': 'M14 19c-6 0-9.5-4.5-9.7-12h3c.1 5 2.5 8 4.3 8.8V7h3v5c1.8-.2 3.6-2.6 4.2-5h3c-.6 3.4-2.8 5.8-4.6 6.6 1.8.9 4.6 3.6 5.4 8.4h-3.4c-.6-2.5-2.4-4.4-4.3-4.9V19H14z'},
            {'label': 'MAX', 'href': 'tel:+79508465397', 'icon': 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'}
        ]
    },
    'cookie': {'text': 'Мы используем файлы cookie для корректной работы сайта.', 'button': 'Принять'},
    'page404': {
        'title': 'Страница не найдена',
        'text': 'Возможно, страница переехала или удалена. Посмотрите наши работы или позвоните нам.',
        'button': 'На главную'
    }
}

# ============================================================
#  ШАБЛОНИЗАТОР  {{path}}  {{{path|raw}}}  {{#each list}}  {{#if x}} {{else}}
# ============================================================
_TAG_RE = re.compile(r"\{\{\{?(.*?)\}\}\}?", re.S)


def _escape(s):
    return _html.escape(s, quote=True)


def _stringify(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return ("%f" % v).rstrip("0").rstrip(".")
    if isinstance(v, (int,)):
        return str(v)
    if isinstance(v, (dict, list, tuple)):
        return ""
    return str(v)


def _truthy(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (list, tuple, dict)):
        return len(v) > 0
    s = str(v).strip()
    return s != "" and s.lower() not in ("0", "false", "none", "null", "нет")


def _lookup(ctx, path):
    path = (path or "").strip()
    if not path:
        return ""
    if path == "this":
        return ctx.get("this", "")
    if path.startswith("this."):
        cur = ctx.get("this")
        rest = path[5:]
    elif path.startswith("@"):
        return ctx.get(path, "")
    else:
        cur = ctx
        rest = path
    for part in rest.split("."):
        if part == "":
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, (list, tuple)):
            if part.lstrip("-").isdigit():
                i = int(part)
                cur = cur[i] if -len(cur) <= i < len(cur) else None
            else:
                return ""
        else:
            return ""
        if cur is None:
            return ""
    return cur


def _apply_filter(name, value):
    name = (name or "").strip()
    if name == "nl2br":
        return _escape(_stringify(value)).replace("\r\n", "\n").replace("\n", "<br>")
    if name == "stars":
        try:
            n = int(float(str(value).strip()))
        except Exception:
            return _escape(_stringify(value))
        n = max(0, min(5, n))
        return "\u2605" * n + "\u2606" * (5 - n)
    if name == "json":
        return json.dumps(_stringify(value), ensure_ascii=False)[1:-1]
    if name == "up":
        return _escape(_stringify(value).upper())
    return _escape(_stringify(value))


def _extract_block(tpl, pos):
    """Возвращает (тело, else-ветка, новая_позиция) для блока #each/#if/#unless."""
    depth = 0
    main, alt, cur = [], [], main
    seen_else = False
    p = pos
    while True:
        m = _TAG_RE.search(tpl, p)
        if not m:
            cur.append(tpl[p:])
            return "".join(main), ("".join(alt) if seen_else else ""), len(tpl)
        expr = m.group(1).strip()
        cur.append(tpl[p:m.start()])
        p = m.end()
        if expr.startswith("#each ") or expr.startswith("#if ") or expr.startswith("#unless "):
            depth += 1
            cur.append(m.group(0))
        elif expr in ("/each", "/if", "/unless"):
            if depth == 0:
                return "".join(main), ("".join(alt) if seen_else else ""), p
            depth -= 1
            cur.append(m.group(0))
        elif expr == "else" and depth == 0 and not seen_else:
            seen_else = True
            cur = alt
        else:
            cur.append(m.group(0))


def render(tpl, ctx):
    out = []
    pos = 0
    while True:
        m = _TAG_RE.search(tpl, pos)
        if not m:
            out.append(tpl[pos:])
            break
        out.append(tpl[pos:m.start()])
        token, expr = m.group(0), m.group(1).strip()
        is_raw = token.startswith("{{{")
        pos = m.end()

        if expr.startswith("#each "):
            body, _alt, pos = _extract_block(tpl, pos)
            val = _lookup(ctx, expr[6:])
            if isinstance(val, dict):
                val = [val]
            if isinstance(val, (list, tuple)):
                total = len(val)
                for i, item in enumerate(val):
                    sub = dict(ctx)
                    sub["this"] = item
                    sub["@index"] = i + 1
                    sub["@first"] = (i == 0)
                    sub["@last"] = (i == total - 1)
                    out.append(render(body, sub))
        elif expr.startswith("#if ") or expr.startswith("#unless "):
            neg = expr.startswith("#unless ")
            body, alt, pos = _extract_block(tpl, pos)
            cond = _truthy(_lookup(ctx, expr.split(" ", 1)[1]))
            if neg:
                cond = not cond
            out.append(render(body if cond else alt, ctx))
        elif expr.startswith("#"):
            _b, _a, pos = _extract_block(tpl, pos)
        elif expr.startswith(("/", "else", "!")):
            continue
        else:
            name, _, filt = expr.partition("|")
            val = _lookup(ctx, name)
            if is_raw or filt.strip() == "raw":
                out.append(_stringify(val))
            else:
                out.append(_apply_filter(filt, val))
    return "".join(out)


# ============================================================
#  ВСТРОЕННЫЙ ШАБЛОН СТРАНИЦЫ (page.html)
#  Разметка/CSS/JS сохранены как в исходном сайте, но с подстановками.
# ============================================================
PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru" class="js">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{seo.title}}</title>
<meta name="description" content="{{seo.description}}">
<meta name="keywords" content="{{seo.keywords}}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="geo.region" content="RU-ROS">
<meta name="geo.placename" content="Ростов-на-Дону">
<meta name="geo.position" content="47.2357;39.7015">
<meta name="ICBM" content="47.2357, 39.7015">
<meta name="theme-color" content="{{design.bg}}">
<meta name="msapplication-TileColor" content="{{design.bg}}">
<link rel="canonical" href="{{seo.canonical}}">
<link rel="alternate" hreflang="ru" href="{{seo.canonical}}">
<link rel="alternate" hreflang="x-default" href="{{seo.canonical}}">
{{#if seo.yandex_verification}}<meta name="yandex-verification" content="{{seo.yandex_verification}}">{{/if}}
{{#if seo.google_verification}}<meta name="google-site-verification" content="{{seo.google_verification}}">{{/if}}
<link rel="shortcut icon" href="/favicon.ico">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="{{brand.name}}">
<meta property="og:url" content="{{seo.canonical}}">
<meta property="og:title" content="{{seo.og_title}}">
<meta property="og:description" content="{{seo.og_description}}">
<meta property="og:image" content="{{seo.og_image}}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{seo.og_title}}">
<meta name="twitter:description" content="{{seo.og_description}}">
<meta name="twitter:image" content="{{seo.og_image}}">
{{#if code.head}}{{{code.head|raw}}}{{/if}}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{{design.fonts_url}}" rel="stylesheet">
<link rel="preconnect" href="https://sun9-70.vkuserphoto.ru">
<link rel="preconnect" href="https://sun9-20.vkuserphoto.ru">
<link rel="preconnect" href="https://i.ibb.co">
<style>
:root{
  --bg:{{design.bg}};
  --gold:{{design.gold}};
  --gold-soft:{{design.gold_soft}};
  --gold-deep:{{design.gold_deep}};
  --text:{{design.text}};
  --muted:{{design.muted}};
  --line:rgba(212,175,106,.14);
  --line-strong:rgba(236,207,160,.38);
  --r-lg:24px;--r-md:16px;--r-sm:12px;
  --shadow-lg:0 34px 80px rgba(0,0,0,.5);
  --shadow-md:0 18px 46px rgba(0,0,0,.36);
  --shadow-gold:0 16px 42px rgba(212,175,106,.26);
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'Manrope',system-ui,sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth;overflow-x:hidden}
section{scroll-margin-top:92px}
body{font-family:var(--sans);color:var(--text);line-height:1.72;-webkit-font-smoothing:antialiased;overflow-x:hidden;position:relative;min-height:100vh}
body::before{content:"";position:fixed;inset:0;z-index:-2;background:
radial-gradient(1200px 700px at 85% -10%,rgba(212,175,106,.16),transparent 60%),
radial-gradient(1000px 640px at -10% 30%,rgba(212,175,106,.09),transparent 55%),
radial-gradient(1400px 900px at 50% 120%,rgba(163,124,63,.14),transparent 60%),
linear-gradient(180deg,#12100b,#0c0a07 45%,#100d09)}
body::after{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background:
linear-gradient(115deg,transparent 30%,rgba(236,207,160,.028) 50%,transparent 70%),
radial-gradient(900px 600px at 50% 0%,rgba(0,0,0,0),rgba(0,0,0,.28))}
.orb{position:fixed;border-radius:50%;pointer-events:none;z-index:-1;will-change:transform}
.orb-1{width:560px;height:560px;left:-180px;top:10%;background:radial-gradient(circle,rgba(212,175,106,.13),transparent 65%);animation:orbFloat 18s ease-in-out infinite alternate}
.orb-2{width:480px;height:480px;right:-160px;top:40%;background:radial-gradient(circle,rgba(163,124,63,.12),transparent 65%);animation:orbFloat 24s ease-in-out infinite alternate-reverse}
.orb-3{width:640px;height:640px;left:28%;bottom:-240px;background:radial-gradient(circle,rgba(212,175,106,.08),transparent 65%);animation:orbFloat 30s ease-in-out infinite alternate}
@keyframes orbFloat{from{transform:translateY(-36px)}to{transform:translateY(44px)}}
.grain{position:fixed;inset:0;z-index:2147480000;pointer-events:none;opacity:.03;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.6'/%3E%3C/svg%3E")}
::selection{background:rgba(212,175,106,.32);color:#fff}
h1,h2,h3{font-family:var(--serif);overflow-wrap:break-word;word-break:break-word;letter-spacing:.3px}
img{max-width:100%;display:block}
a{text-decoration:none;color:inherit}
ul{list-style:none}
button{font-family:inherit;cursor:pointer}
.wrap{width:100%;max-width:1180px;margin:0 auto;padding:0 20px}
.progress{position:fixed;top:0;left:0;height:3px;z-index:300;background:linear-gradient(90deg,var(--gold-deep),var(--gold-soft),var(--gold));width:0%;box-shadow:0 0 14px rgba(236,207,160,.7);will-change:width}
#cursorGlow{position:fixed;left:0;top:0;width:340px;height:340px;border-radius:50%;pointer-events:none;z-index:55;background:radial-gradient(circle,rgba(212,175,106,.09),transparent 66%);mix-blend-mode:screen;will-change:transform;display:none}
@media(hover:hover) and (pointer:fine){#cursorGlow{display:block}}
header{position:fixed;top:0;left:0;right:0;z-index:200;background:rgba(14,12,9,.55);backdrop-filter:blur(18px) saturate(150%);-webkit-backdrop-filter:blur(18px) saturate(150%);transition:background .45s,box-shadow .45s}
header.solid{background:rgba(14,12,9,.92);box-shadow:0 12px 44px rgba(0,0,0,.45),inset 0 -1px 0 var(--line)}
.nav{display:flex;align-items:center;justify-content:space-between;height:78px;gap:12px}
.logo{display:flex;align-items:center;gap:13px;min-width:0;max-width:100%;cursor:pointer;transition:opacity .3s}
.logo:hover{opacity:.86}
.brand-ava-w{position:relative;flex-shrink:0;display:inline-flex}
.brand-ava-w::before{content:"";position:absolute;inset:-5px;border-radius:50%;border:1px solid rgba(236,207,160,.5);opacity:.7;animation:ringPulse 3.6s ease-in-out infinite}
@keyframes ringPulse{0%,100%{transform:scale(.94);opacity:.35}50%{transform:scale(1.08);opacity:.75}}
.brand-ava{width:46px;height:46px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 5px rgba(212,175,106,.1),0 0 24px rgba(212,175,106,.4);position:relative;z-index:1}
.logo .brand-txt{display:flex;flex-direction:column;min-width:0;line-height:1.15}
.logo .brand-txt .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:var(--serif);font-size:26px;font-weight:600;color:#fff;line-height:1.05;background:linear-gradient(120deg,#fff,var(--gold-soft));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:.3px}
.logo .brand-txt .sub{color:var(--gold-soft);font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:62vw;margin-top:3px;opacity:.85}
.menu{position:fixed;top:0;height:78px;right:max(20px,calc((100vw - 1220px)/2));display:flex;gap:24px;align-items:center;z-index:201}
.menu a{position:relative;color:rgba(255,255,255,.8);font-size:13px;font-weight:600;letter-spacing:.5px;transition:.3s;padding:6px 0;white-space:nowrap}
.menu a::after{content:"";position:absolute;left:0;bottom:0;width:100%;height:1.5px;background:linear-gradient(90deg,var(--gold-soft),var(--gold));transform:scaleX(0);transform-origin:left;transition:transform .4s cubic-bezier(.22,.61,.36,1);border-radius:2px}
.menu a:hover{color:#fff}
.menu a:hover::after{transform:scaleX(1)}
.menu a.active{color:var(--gold-soft)}
.menu a.active::after{transform:scaleX(1)}
.sheet-handle{display:none}
.menu-call{display:none}
.burger{display:none;background:none;border:none;cursor:pointer;width:44px;height:44px;position:relative;z-index:210;flex-shrink:0}
.burger span{position:absolute;left:7px;right:7px;height:2px;background:#fff;transition:.3s;border-radius:2px}
.burger span:nth-child(1){top:13px}
.burger span:nth-child(2){top:21px}
.burger span:nth-child(3){top:29px}
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
h1{font-size:clamp(34px,6vw,76px);font-weight:500;line-height:1.08;color:#fff;letter-spacing:.4px;text-shadow:0 5px 30px rgba(0,0,0,.5);overflow-wrap:break-word;word-break:break-word;max-width:100%}
h1 em{font-style:italic}
.sub{color:rgba(245,239,227,.9);font-size:clamp(16px,1.8vw,19.5px);font-weight:300;margin:24px 0 34px;max-width:580px;text-shadow:0 2px 16px rgba(0,0,0,.55);letter-spacing:.3px}
.btn-row{display:flex;gap:16px;flex-wrap:wrap}
.btn{position:relative;overflow:hidden;display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:15px 30px;font-size:13px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;transition:transform .4s cubic-bezier(.22,.61,.36,1),box-shadow .4s,filter .4s,background .4s,color .4s;cursor:pointer;border-radius:13px;border:none}
.btn-solid{background:linear-gradient(135deg,var(--gold-soft),var(--gold) 55%,var(--gold-deep));color:#17120b;box-shadow:var(--shadow-gold);animation:btnGlow 3.6s ease-in-out infinite}
@keyframes btnGlow{0%,100%{box-shadow:0 16px 42px rgba(212,175,106,.26)}50%{box-shadow:0 24px 62px rgba(236,207,160,.5)}}
.btn-solid:hover{transform:translateY(-4px);box-shadow:0 26px 60px rgba(212,175,106,.45)}
.btn-line{border:1px solid rgba(255,255,255,.4);color:#fff;background:rgba(255,255,255,.04)}
.btn-line:hover{background:rgba(255,255,255,.12);color:#fff;transform:translateY(-4px);box-shadow:0 20px 50px rgba(0,0,0,.35)}
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
.sec-head h2{position:relative;font-size:clamp(30px,4.4vw,48px);font-weight:500;margin:16px 0 14px;line-height:1.14;color:#faf3e6;text-shadow:0 4px 22px rgba(0,0,0,.45),0 0 40px rgba(212,175,106,.14);letter-spacing:.3px}
.sec-head h2::before,.sec-head h2::after{content:"";position:absolute;top:50%;width:56px;height:1px;background:linear-gradient(90deg,transparent,var(--gold));transform:translateY(-50%);opacity:.7}
.sec-head h2::before{right:calc(100% + 26px)}
.sec-head h2::after{left:calc(100% + 26px)}
.sec-head p{color:var(--muted);font-size:15.5px;max-width:620px;margin:0 auto;letter-spacing:.2px}
h2.k{position:relative;font-size:clamp(32px,4.6vw,48px);color:#faf3e6;font-weight:500;margin:16px 0 14px;text-align:center;text-shadow:0 4px 22px rgba(0,0,0,.45),0 0 40px rgba(212,175,106,.14);letter-spacing:.3px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;text-align:center}
.stat{padding:32px 16px;border-radius:var(--r-md);background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);transition:transform .45s,border-color .45s,box-shadow .45s}
.stat:hover{transform:translateY(-6px);border-color:rgba(236,207,160,.3);box-shadow:0 22px 54px rgba(0,0,0,.42),0 0 34px rgba(212,175,106,.05)}
.stat .num{font-family:var(--serif);font-size:58px;font-weight:500;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold) 60%,var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 5px 16px rgba(212,175,106,.35))}
.stat .lbl{color:var(--muted);font-size:13.5px;margin-top:12px;letter-spacing:.3px}
.about{display:grid;grid-template-columns:1fr 1.1fr;gap:64px;align-items:center}
.about-card{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:48px 40px;text-align:center;border-radius:var(--r-lg);box-shadow:var(--shadow-md);position:relative;overflow:hidden}
.about-card::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.6}
.avatar{width:130px;height:130px;border-radius:50%;margin:0 auto 22px;overflow:hidden;border:1.5px solid rgba(236,207,160,.65);box-shadow:0 0 0 7px rgba(212,175,106,.12),0 16px 40px rgba(0,0,0,.5);position:relative}
.avatar img{width:100%;height:100%;object-fit:cover}
.avatar::after{content:"";position:absolute;inset:0;border-radius:50%;box-shadow:inset 0 0 0 3px rgba(236,207,160,.4)}
.about-card h3{font-size:29px;color:#fff;letter-spacing:.3px}
.about-card .role{color:var(--gold-soft);font-size:13px;margin-top:5px;letter-spacing:.7px}
.about-card .sep{width:52px;height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent);margin:22px auto}
.about-card p{color:var(--muted);font-size:14.5px;line-height:1.76}
.about-body .kicker{color:var(--gold-soft);letter-spacing:5px;text-transform:uppercase;font-size:11px;font-weight:600}
.about-body h2{font-size:clamp(30px,3.6vw,44px);font-weight:500;margin:16px 0 22px;line-height:1.14;color:#faf3e6;text-shadow:0 4px 22px rgba(0,0,0,.45);letter-spacing:.3px}
.about-body p{color:var(--muted);font-size:15.5px;margin-bottom:26px;letter-spacing:.2px}
.features{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.features li{position:relative;padding-left:36px;color:var(--text);font-size:14.5px;overflow-wrap:break-word;transition:transform .3s;letter-spacing:.2px}
.features li:hover{transform:translateX(5px)}
.features li::before{content:"";position:absolute;left:0;top:4px;width:18px;height:18px;border:1.5px solid rgba(212,175,106,.6);border-radius:50%;background:rgba(212,175,106,.08)}
.features li::after{content:"✓";position:absolute;left:4px;top:4px;font-size:11px;color:var(--gold-soft);font-weight:800}
.consult .phone{display:inline-block;font-family:var(--sans);font-weight:800;font-size:clamp(30px,4.4vw,52px);letter-spacing:1px;margin-top:12px;white-space:nowrap;background:linear-gradient(120deg,var(--gold-soft),var(--gold));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 7px 22px rgba(212,175,106,.35))}
.consult p{color:var(--muted);font-size:15.5px;margin:30px auto 0;max-width:630px;line-height:1.82;overflow-wrap:break-word;letter-spacing:.2px}
.carousel{position:relative;max-width:1120px;margin:0 auto}
.car-track{display:flex;gap:20px;overflow-x:auto;scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;overscroll-behavior-x:contain;touch-action:pan-x;padding:12px 8px 24px;scrollbar-width:none}
.car-track::-webkit-scrollbar{display:none}
.car-nav{position:absolute;top:38%;transform:translateY(-50%);width:48px;height:48px;border-radius:50%;background:rgba(14,12,9,.68);border:1px solid rgba(236,207,160,.35);color:var(--gold-soft);font-size:21px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:transform .4s,border-color .4s,background .4s;z-index:5;box-shadow:var(--shadow-md)}
.car-nav:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-50%) scale(1.08)}
.car-prev{left:-16px}.car-next{right:-16px}
.car-dots{display:flex;justify-content:center;gap:10px;margin-top:12px;flex-wrap:wrap}
.car-dot{width:8px;height:8px;min-width:8px;border-radius:99px;background:rgba(255,255,255,.2);cursor:pointer;transition:width .35s,background .35s,transform .35s;border:none;padding:0}
.car-dot:hover{background:rgba(236,207,160,.55)}
.car-dot.active{width:26px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));box-shadow:0 0 12px rgba(236,207,160,.6)}
.swipe-hint{display:flex;align-items:center;justify-content:center;gap:8px;color:var(--muted);font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-top:10px;animation:hintPulse 1.8s ease-in-out infinite}
.swipe-hint::after{content:"→";display:inline-block;animation:hintArrow 1.4s ease-in-out infinite}
@keyframes hintArrow{0%,100%{transform:translateX(0);opacity:.5}50%{transform:translateX(7px);opacity:1}}
@keyframes hintPulse{0%,100%{opacity:.55}50%{opacity:1}}
.car-slide{flex:0 0 auto;width:min(78vw,440px);scroll-snap-align:center;border-radius:var(--r-lg);overflow:hidden;border:1px solid rgba(255,255,255,.08);background:rgba(14,12,9,.55);cursor:zoom-in;transition:transform .5s cubic-bezier(.22,.61,.36,1),box-shadow .5s,border-color .5s;box-shadow:var(--shadow-md);position:relative}
.car-slide::before{content:"";position:absolute;inset:0;z-index:1;background:linear-gradient(100deg,rgba(255,255,255,.02),rgba(255,255,255,.07),rgba(255,255,255,.02));background-size:200% 100%;animation:shim 1.4s infinite}
@keyframes shim{0%{background-position:120% 0}100%{background-position:-120% 0}}
.car-slide:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.3);box-shadow:var(--shadow-lg)}
.car-slide img{width:100%;height:300px;object-fit:cover;display:block;position:relative;z-index:2}
.car-slide:hover img{transform:scale(1.07)}
.rev-track{align-items:flex-start}
.rev-card{scroll-snap-align:center;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);padding:24px 26px;width:min(82vw,520px);flex:0 0 auto;display:flex;flex-direction:column;box-shadow:var(--shadow-md);position:relative;overflow:hidden;transition:transform .5s,box-shadow .5s,border-color .5s}
.rev-card:hover{transform:translateY(-8px);border-color:rgba(236,207,160,.28);box-shadow:var(--shadow-lg)}
.rev-card::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.75}
.rev-head{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap}
.rev-ava{width:50px;height:50px;border-radius:50%;object-fit:cover;border:1.5px solid rgba(236,207,160,.6);box-shadow:0 0 0 4px rgba(212,175,106,.1),0 0 14px rgba(212,175,106,.32);flex-shrink:0}
.rev-name{color:#fff;font-weight:700;font-size:14.5px}
.rev-sub{color:var(--muted);font-size:11px;margin-top:2px}
.rev-stars{color:var(--gold-soft);letter-spacing:3px;font-size:14px;margin-left:auto;white-space:nowrap;text-shadow:0 0 14px rgba(236,207,160,.45)}
.rev-text{color:#ece2cd;font-size:13.5px;line-height:1.66;font-weight:300;text-align:left;overflow-wrap:break-word;word-break:break-word;letter-spacing:.1px}
.rev-video{margin-top:14px;border-radius:var(--r-md);overflow:hidden;border:1px solid rgba(255,255,255,.08);box-shadow:var(--shadow-md)}
.video-box{position:relative;width:100%;height:260px;background-size:cover;background-position:center;cursor:pointer;display:flex;align-items:center;justify-content:center}
.video-box::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,8,6,.12),rgba(10,8,6,.34));transition:.3s}
.video-box:hover::after{background:linear-gradient(180deg,rgba(10,8,6,.02),rgba(10,8,6,.2))}
.vb-play{position:relative;z-index:2;width:64px;height:64px;border-radius:50%;border:1px solid rgba(236,207,160,.7);background:rgba(14,12,9,.55);color:var(--gold-soft);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:transform .35s,background .35s;box-shadow:0 0 0 8px rgba(212,175,106,.14),0 0 30px rgba(212,175,106,.4);animation:playPulse 2.4s ease-in-out infinite}
@keyframes playPulse{0%,100%{box-shadow:0 0 0 8px rgba(212,175,106,.14),0 0 30px rgba(212,175,106,.4)}50%{box-shadow:0 0 0 14px rgba(212,175,106,.08),0 0 44px rgba(212,175,106,.6)}}
.video-box:hover .vb-play{transform:scale(1.1);background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b}
.vb-play svg{width:22px;height:22px;fill:currentColor;margin-left:3px}
.video-box iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.svc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.svc{position:relative;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 30px;transition:transform .5s cubic-bezier(.22,.61,.36,1),box-shadow .5s,border-color .5s;border-radius:var(--r-lg);overflow-wrap:break-word;overflow:hidden}
.svc::before{content:"";position:absolute;top:0;left:22%;right:22%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:0;transition:.5s}
.svc:hover{transform:translateY(-8px);background:rgba(255,255,255,.05);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.svc:hover::before{opacity:.7}
.svc svg{width:34px;height:34px;stroke:var(--gold-soft);fill:none;stroke-width:1.4;margin-bottom:20px;transition:transform .55s cubic-bezier(.22,.61,.36,1)}
.svc:hover svg{transform:scale(1.12) rotate(-4deg)}
.svc h3{font-size:23px;color:#fff;margin-bottom:9px;letter-spacing:.3px}
.svc p{color:var(--muted);font-size:14px;line-height:1.7;letter-spacing:.1px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.step{position:relative;padding:34px 26px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:var(--r-lg);transition:transform .45s cubic-bezier(.22,.61,.36,1),box-shadow .45s,border-color .45s;overflow-wrap:break-word;overflow:hidden}
.step:hover{transform:translateY(-7px);border-color:rgba(236,207,160,.28);box-shadow:var(--shadow-md)}
.step .n{font-family:var(--serif);font-size:54px;line-height:1;background:linear-gradient(160deg,var(--gold-soft),var(--gold-deep));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;transition:transform .45s}
.step:hover .n{transform:scale(1.1)}
.step h3{font-size:22px;color:#fff;margin:14px 0 8px;letter-spacing:.3px}
.step p{color:var(--muted);font-size:14px;line-height:1.7;letter-spacing:.1px}
.guar-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.guar{position:relative;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);padding:38px 26px;text-align:center;transition:transform .45s,box-shadow .45s,border-color .45s;border-radius:var(--r-lg);overflow-wrap:break-word;overflow:hidden}
.guar::before{content:"";position:absolute;top:0;left:25%;right:25%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:0;transition:.45s}
.guar:hover{transform:translateY(-8px);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.guar:hover::before{opacity:.7}
.guar .ico{width:54px;height:54px;margin:0 auto 18px;border:1px solid rgba(236,207,160,.35);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--gold-soft);background:radial-gradient(circle at 30% 30%,rgba(236,207,160,.16),rgba(212,175,106,.03));box-shadow:0 0 22px rgba(212,175,106,.16);transition:transform .45s}
.guar:hover .ico{transform:scale(1.12) rotate(6deg)}
.guar .ico svg{width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:1.5}
.guar h3{font-size:18px;color:#fff;margin-bottom:8px;letter-spacing:.2px}
.guar p{color:var(--muted);font-size:13px;line-height:1.7;letter-spacing:.1px}
.city-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px}
.city{position:relative;padding:38px 28px;border-radius:var(--r-lg);background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);text-align:center;transition:transform .45s,box-shadow .45s,border-color .45s;overflow:hidden}
.city::before{content:"";position:absolute;top:0;left:25%;right:25%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:0;transition:.45s}
.city:hover{transform:translateY(-7px);box-shadow:var(--shadow-lg);border-color:rgba(236,207,160,.26)}
.city:hover::before{opacity:.7}
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
.call-block{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);padding:46px 36px;text-align:center;border-radius:var(--r-lg);box-shadow:var(--shadow-md);position:relative;overflow:hidden}
.call-block::before{content:"";position:absolute;top:0;left:20%;right:20%;height:1px;background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);opacity:.6}
.call-block .cb-lab{font-size:12px;letter-spacing:4px;text-transform:uppercase;color:var(--gold-soft)}
.call-block .cb-num{display:block;font-family:var(--sans);font-weight:800;font-size:clamp(27px,3.6vw,44px);color:#fff;margin:14px 0 18px;white-space:nowrap;transition:color .3s,text-shadow .3s;text-shadow:0 5px 22px rgba(0,0,0,.42);letter-spacing:.4px}
.call-block .cb-num:hover{color:var(--gold-soft);text-shadow:0 0 30px rgba(236,207,160,.5)}
.call-block .cb-hint{color:var(--muted);font-size:14px;line-height:1.82;overflow-wrap:break-word;letter-spacing:.1px}
.contact-actions{display:flex;flex-direction:column;gap:12px;margin-top:24px}
.c-action{display:flex;align-items:center;justify-content:center;gap:11px;width:100%;min-height:52px;padding:15px 18px;border-radius:var(--r-sm);font-weight:700;font-size:14.5px;letter-spacing:.4px;transition:transform .4s,background .4s,filter .4s,box-shadow .4s;color:#fff}
.c-action svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8}
.c-action.c-call{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;box-shadow:var(--shadow-gold)}
.c-action.c-call:hover{filter:brightness(1.08);transform:translateY(-4px);box-shadow:0 22px 50px rgba(212,175,106,.42)}
.c-action.c-tg{background:rgba(64,169,242,.12);border:1px solid rgba(64,169,242,.38);color:#8fd0ff}
.c-action.c-tg:hover{background:rgba(64,169,242,.24);transform:translateY(-4px)}
.c-action.c-max{background:rgba(177,88,252,.12);border:1px solid rgba(177,88,252,.38);color:#e0b8ff}
.c-action.c-max:hover{background:rgba(177,88,252,.24);transform:translateY(-4px)}
.cta{text-align:center;padding:110px 0;position:relative}
.cta h2{font-size:clamp(32px,4.6vw,52px);color:#faf3e6;font-weight:500;margin-bottom:16px;text-shadow:0 5px 26px rgba(0,0,0,.45);letter-spacing:.3px}
.cta p{color:var(--muted);font-size:16.5px;max-width:630px;margin:0 auto 34px;overflow-wrap:break-word;letter-spacing:.2px}
footer{position:relative;background:linear-gradient(180deg,rgba(14,12,9,.4),rgba(10,8,6,.97));color:var(--muted);padding:52px 20px 60px;text-align:center;font-size:13px;border-top:1px solid rgba(255,255,255,.06)}
footer::before{content:"";position:absolute;top:-1px;left:50%;transform:translateX(-50%);width:min(420px,72%);height:1px;background:linear-gradient(90deg,transparent,var(--gold),transparent)}
footer .flogo{font-family:var(--serif);font-size:28px;color:#fff;margin-bottom:8px;line-height:1.3;letter-spacing:.3px}
footer .flogo span{color:var(--gold-soft);font-size:13px;font-family:var(--sans);font-weight:500;letter-spacing:1px}
.social-row{display:flex;justify-content:center;gap:14px;margin:22px 0 18px;flex-wrap:wrap}
.soc{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;min-width:46px;min-height:46px;border-radius:50%;border:1px solid rgba(236,207,160,.32);color:var(--gold-soft);background:rgba(212,175,106,.06);transition:transform .35s,background .35s,box-shadow .35s}
.soc svg{width:19px;height:19px;stroke:currentColor;fill:none;stroke-width:1.6}
.soc:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:translateY(-4px);box-shadow:var(--shadow-gold)}
.cookie-bar{position:fixed;bottom:16px;left:50%;transform:translate(-50%,140%);z-index:400;background:rgba(14,12,9,.93);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.08);border-radius:var(--r-md);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;box-shadow:var(--shadow-lg);width:min(680px,calc(100vw - 32px));transition:transform .6s cubic-bezier(.22,.61,.36,1)}
.cookie-bar.show{transform:translate(-50%,0)}
.cookie-bar p{color:var(--muted);font-size:13px;max-width:720px;line-height:1.5}
.cookie-bar .btn{flex-shrink:0;padding:12px 26px}
.lightbox{position:fixed;inset:0;z-index:3000;background:rgba(8,6,4,.96);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);display:none;align-items:center;justify-content:center;flex-direction:column;gap:14px}
.lightbox.open{display:flex;animation:lbFade .3s ease}
@keyframes lbFade{from{opacity:0}to{opacity:1}}
.lb-stage{position:relative;width:100%;max-width:1180px;height:calc(100vh - 130px);display:flex;align-items:center;justify-content:center;overflow:hidden;touch-action:none}
.lb-stage img{max-width:94%;max-height:100%;border-radius:var(--r-lg);border:1px solid rgba(236,207,160,.55);box-shadow:0 26px 90px rgba(0,0,0,.8);cursor:grab;transition:transform .18s ease-out;will-change:transform;user-select:none;-webkit-user-drag:none}
.lb-stage img:active{cursor:grabbing}
.lb-bar{display:flex;align-items:center;justify-content:center;gap:20px}
.lb-count{color:var(--muted);font-size:13px;min-width:70px;text-align:center}
.lb-close{position:absolute;top:18px;right:24px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);color:#fff;font-size:28px;cursor:pointer;z-index:5;line-height:1;width:48px;height:48px;min-width:48px;min-height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;transition:transform .3s,background .3s}
.lb-close:hover{transform:rotate(90deg);background:rgba(236,207,160,.18)}
.lb-nav{width:50px;height:50px;min-width:50px;min-height:50px;border-radius:50%;background:rgba(14,12,9,.6);border:1px solid rgba(236,207,160,.5);color:var(--gold-soft);font-size:24px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .3s,transform .3s}
.lb-nav:hover{background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;transform:scale(1.06)}
.js .reveal{opacity:0;transform:translateY(26px);filter:blur(10px);transition:opacity .8s ease,transform .8s cubic-bezier(.22,.61,.36,1),filter .8s ease}
.js .reveal.in{opacity:1;transform:none;filter:none}
.stats .reveal:nth-child(1){transition-delay:.05s}.stats .reveal:nth-child(2){transition-delay:.15s}.stats .reveal:nth-child(3){transition-delay:.25s}.stats .reveal:nth-child(4){transition-delay:.35s}
.steps .reveal:nth-child(2){transition-delay:.08s}.steps .reveal:nth-child(3){transition-delay:.16s}.steps .reveal:nth-child(4){transition-delay:.24s}.steps .reveal:nth-child(5){transition-delay:.32s}.steps .reveal:nth-child(6){transition-delay:.4s}
.svc-grid .reveal:nth-child(2){transition-delay:.08s}.svc-grid .reveal:nth-child(3){transition-delay:.16s}.svc-grid .reveal:nth-child(4){transition-delay:.24s}.svc-grid .reveal:nth-child(5){transition-delay:.32s}.svc-grid .reveal:nth-child(6){transition-delay:.4s}
.guar-grid .reveal:nth-child(2){transition-delay:.08s}.guar-grid .reveal:nth-child(3){transition-delay:.16s}.guar-grid .reveal:nth-child(4){transition-delay:.24s}
.city-grid .reveal:nth-child(2){transition-delay:.12s}.city-grid .reveal:nth-child(3){transition-delay:.24s}
@supports (content-visibility:auto){.panel{content-visibility:auto;contain-intrinsic-size:auto 820px}}
@media(max-width:1180px){.menu{right:max(16px,calc((100vw - 1080px)/2));gap:20px}}
@media(max-width:1024px){.stats{grid-template-columns:repeat(2,1fr);gap:30px}.svc-grid{grid-template-columns:repeat(2,1fr)}.guar-grid{grid-template-columns:repeat(2,1fr)}.city-grid{grid-template-columns:repeat(3,1fr)}.panel{padding:132px 0}}
@media(max-width:860px){.menu{position:fixed;top:auto;left:0;right:0;bottom:0;width:100%;max-height:82vh;background:linear-gradient(180deg,#16130e,#0b0907);flex-direction:column;justify-content:flex-start;gap:4px;padding:12px 24px calc(22px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .45s cubic-bezier(.22,.61,.36,1);z-index:205;opacity:1;visibility:visible;box-shadow:0 -22px 54px rgba(0,0,0,.55);border-radius:26px 26px 0 0;overflow-y:auto;height:auto;border-top:1px solid rgba(236,207,160,.2)}.menu.open{transform:none}.sheet-handle{display:flex;justify-content:center;padding:4px 0 8px}.sheet-handle span{width:42px;height:4px;border-radius:99px;background:rgba(236,207,160,.35)}.menu a{font-size:19px;font-family:var(--serif);color:#fff;border-bottom:1px solid rgba(236,207,160,.12);padding:13px 6px;display:flex;align-items:center;min-height:48px}.menu a::after{display:none}.menu a:hover{color:var(--gold-soft)}.menu a.active{color:var(--gold-soft)}.menu-call{display:block;margin-top:10px;padding-top:10px;border-top:1px solid rgba(236,207,160,.14)}.menu-call a{display:flex;align-items:center;justify-content:center;gap:10px;width:100%;min-height:52px;background:linear-gradient(135deg,var(--gold-soft),var(--gold));color:#17120b;font-family:var(--sans);font-size:14.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;border:none;border-radius:var(--r-sm);padding:15px 18px;box-shadow:var(--shadow-gold)}.burger{display:block}.scrim{display:block}.about{grid-template-columns:1fr;gap:36px}.features{grid-template-columns:1fr}.steps{grid-template-columns:1fr;gap:20px}.contact-grid{grid-template-columns:1fr;gap:36px}.city-grid{grid-template-columns:1fr}.panel{padding:116px 0}.car-nav{display:none}.rev-card{width:86vw}.video-box{height:230px}}
@media(max-width:768px){.stats{grid-template-columns:1fr 1fr}.guar-grid{grid-template-columns:1fr 1fr}.svc-grid{grid-template-columns:1fr}.steps{grid-template-columns:1fr}.panel{padding:104px 0 60px}}
@media(max-width:520px){.logo .brand-ava{width:40px;height:40px}.logo .brand-txt .name{font-size:20px}.logo .brand-txt .sub{font-size:9.5px;max-width:54vw;letter-spacing:1.2px}.nav{height:64px}.panel{min-height:auto;padding:96px 0 56px}h1{font-size:31px}.sub{font-size:15px;margin:18px 0 26px}.btn-row{width:100%}.btn{width:100%;text-align:center;padding:14px 20px;font-size:12px}.stat .num{font-size:44px}.sec-head{margin-bottom:38px}.sec-head h2::before,.sec-head h2::after{display:none}.scroll-cue{display:none}.car-slide{width:84vw}.car-slide img{height:205px}.rev-card{width:92vw;padding:17px}.rev-head{gap:10px}.rev-ava{width:44px;height:44px}.rev-name{font-size:13.5px}.rev-sub{font-size:10px}.rev-stars{font-size:12.5px;display:block;margin:6px 0 0}.rev-text{font-size:12.5px;line-height:1.56}.video-box{height:190px}.consult .phone{font-size:25px}.call-block .cb-num{font-size:22px}.menu{padding:10px 20px calc(18px + env(safe-area-inset-bottom))}.lb-nav{width:44px;height:44px;min-width:44px;min-height:44px;font-size:22px}.lb-close{width:44px;height:44px;min-width:44px;min-height:44px}.cookie-bar{bottom:10px;padding:14px 16px}.city{padding:28px 22px}.contact-info>p{margin-bottom:24px}}
@media(max-width:380px){.car-slide{width:88vw}.car-slide img{height:190px}.rev-card{width:94vw;padding:14px}.rev-text{font-size:12px}.video-box{height:170px}.btn{font-size:11px}}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;transition-duration:.01ms !important;scroll-behavior:auto !important}.js .reveal{opacity:1;transform:none;filter:none}}
{{#if design.custom_css}}{{{design.custom_css|raw}}}{{/if}}
</style>
</head>
<body>
<div class="progress" id="progress"></div>
<div class="grain" aria-hidden="true"></div>
<div id="cursorGlow" aria-hidden="true"></div>
<div class="orb orb-1" aria-hidden="true"></div>
<div class="orb orb-2" aria-hidden="true"></div>
<div class="orb orb-3" aria-hidden="true"></div>
<header id="header">
  <div class="wrap nav">
    <a href="#top" class="logo" id="logo">
      <span class="brand-ava-w">
        <img class="brand-ava" src="{{brand.logo_url}}" width="46" height="46" alt="{{brand.name}} — кухни на заказ в Ростове, Батайске и Азове">
      </span>
      <span class="brand-txt"><span class="name">{{brand.name}}</span><span class="sub">{{brand.sub}}</span></span>
    </a>
    <button class="burger" id="burger" aria-label="Меню"><span></span><span></span><span></span></button>
  </div>
</header>
<ul class="menu" id="menu">
  <li class="sheet-handle"><span></span></li>
  {{#each nav.items}}<li><a href="{{this.href}}">{{this.label}}</a></li>
  {{/each}}
  <li class="menu-call"><a href="{{brand.phone_raw}}"><svg viewBox="0 0 24 24" style="width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 2z"/></svg>{{nav.cta_label}}</a></li>
</ul>
<div class="scrim" id="scrim"></div>
<section class="panel panel--hero" id="top" data-watermark="Мебель">
  <div class="bg" style="background-image:url('{{hero.bg}}')"></div>
  <div class="wrap"><div class="content">
    <span class="eyebrow">{{hero.eyebrow}}</span>
    <h1 id="heroTitle">{{hero.title_before}}<em class="shimmer">{{hero.title_em}}</em></h1>
    <p class="sub">{{hero.sub}}</p>
    <div class="btn-row">
      <a href="{{hero.btn1_href}}" class="btn btn-solid">{{hero.btn1}}</a>
      <a href="{{hero.btn2_href}}" class="btn btn-line">{{hero.btn2}}</a>
    </div>
  </div></div>
  <div class="scroll-cue">Листайте<div class="line"></div></div>
</section>
<section class="panel panel--dark">
  <div class="bg" style="background-image:url('{{stats.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="stats">
      {{#each stats.items}}<div class="stat reveal"><div class="num" data-count="{{this.num}}"{{#if this.suffix}} data-suffix="{{this.suffix}}"{{/if}}{{#if this.decimal}} data-decimal="{{this.decimal}}"{{/if}}>0</div><div class="lbl">{{this.label}}</div></div>
      {{/each}}
    </div>
  </div></div>
</section>
<section class="panel" id="about">
  <div class="bg" style="background-image:url('{{about.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="about">
      <div class="about-card reveal">
        <div class="avatar"><img src="{{about.photo}}" width="130" height="130" loading="lazy" decoding="async" alt="{{about.name}} — {{about.role}}"></div>
        <h3>{{about.name}}</h3>
        <div class="role">{{about.role}}</div>
        <div class="sep"></div>
        <p>{{about.card_text}}</p>
      </div>
      <div class="about-body reveal">
        <div class="kicker">{{about.kicker}}</div>
        <h2>{{about.title}}</h2>
        <p>{{about.text}}</p>
        <ul class="features">
          {{#each about.features}}<li>{{this}}</li>
          {{/each}}
        </ul>
      </div>
    </div>
  </div></div>
</section>
<div class="gold-divider"><i></i><b></b><i></i></div>
<section class="panel panel--center panel--dark" id="consult">
  <div class="bg" style="background-image:url('{{consult.bg}}')"></div>
  <div class="wrap"><div class="content consult">
    <span class="kicker reveal" style="color:var(--gold-soft);letter-spacing:6px;text-transform:uppercase;font-size:12px;font-weight:600">{{consult.kicker}}</span>
    <h2 class="k reveal">{{consult.title}}</h2>
    <a href="{{consult.phone_raw}}" class="phone reveal">{{consult.phone}}</a>
    <p class="reveal">{{consult.text}}</p>
  </div></div>
</section>
<section class="panel panel--center panel--dark" id="works" data-watermark="Работы">
  <div class="bg" style="background-image:url('{{works.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{{works.kicker}}</div>
      <h2>{{works.title}}</h2>
      <p>{{works.subtitle}}</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="carPrev">❮</button>
      <div class="car-track" id="carTrack">
        {{#each works.items}}<div class="car-slide"><img loading="lazy" decoding="async" src="{{this.url}}" alt="{{this.alt}}"></div>
        {{/each}}
      </div>
      <button class="car-nav car-next" id="carNext">❯</button>
      <div class="car-dots" id="carDots"></div>
      <div class="swipe-hint">{{works.hint}}</div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше работ — в сообществе <a href="{{brand.vk}}" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>
<div class="lightbox" id="lightbox">
  <button class="lb-close" id="lbClose">×</button>
  <div class="lb-stage" id="lbStage">
    <img id="lbImg" alt="Работа">
  </div>
  <div class="lb-bar">
    <button class="lb-nav lb-prev" id="lbPrev">❮</button>
    <div class="lb-count" id="lbCount"></div>
    <button class="lb-nav lb-next" id="lbNext">❯</button>
  </div>
</div>
<section class="panel panel--center" id="reviews" data-watermark="Отзывы">
  <div class="bg" style="background-image:url('{{reviews.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{{reviews.kicker}}</div>
      <h2>{{reviews.title}}</h2>
      <p>{{reviews.subtitle}}</p>
    </div>
    <div class="carousel reveal">
      <button class="car-nav car-prev" id="revPrev">❮</button>
      <div class="car-track rev-track" id="revTrack">
        {{#each reviews.items}}<div class="rev-card">
          <div class="rev-head">
            {{#if this.avatar}}<img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" src="{{this.avatar}}" alt="Отзыв: {{this.name}}">{{/if}}
            <div><div class="rev-name">{{this.name}}</div><div class="rev-sub">{{this.sub}}</div></div>
            <div class="rev-stars">{{this.stars|stars}}</div>
          </div>
          {{#if this.video}}<div class="rev-video">
            <div class="video-box" data-src="{{this.video}}"{{#if this.poster}} style="background-image:url('{{this.poster}}')"{{else}}{{#if reviews.video_poster}} style="background-image:url('{{reviews.video_poster}}')"{{/if}}{{/if}} role="button" aria-label="Смотреть видеоотзыв {{this.name}}">
              <span class="vb-play"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>
            </div>
          </div>{{/if}}
          <p class="rev-text">{{this.text}}</p>
        </div>
        {{/each}}
      </div>
      <button class="car-nav car-next" id="revNext">❯</button>
      <div class="car-dots" id="revDots"></div>
      <div class="swipe-hint">{{reviews.hint}}</div>
    </div>
    <p style="color:var(--muted);margin-top:24px;text-align:center;font-size:13.5px">Больше отзывов — в нашем сообществе <a href="{{brand.vk}}" target="_blank" rel="noopener" style="color:var(--gold-soft);font-weight:600">ВКонтакте</a></p>
  </div></div>
</section>
<div class="gold-divider"><i></i><b></b><i></i></div>
<section class="panel panel--dark" id="services" data-watermark="Услуги">
  <div class="bg" style="background-image:url('{{services.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{{services.kicker}}</div>
      <h2>{{services.title}}</h2>
      <p>{{services.subtitle}}</p>
    </div>
    <div class="svc-grid">
      {{#each services.items}}<div class="svc reveal"><svg viewBox="0 0 24 24"><path d="{{this.icon}}"/></svg><h3>{{this.title}}</h3><p>{{this.text}}</p></div>
      {{/each}}
    </div>
  </div></div>
</section>
<section class="panel" id="process">
  <div class="bg" style="background-image:url('{{process.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{{process.kicker}}</div>
      <h2>{{process.title}}</h2>
    </div>
    <div class="steps">
      {{#each process.items}}<div class="step reveal"><div class="n">{{this.n}}</div><h3>{{this.title}}</h3><p>{{this.text}}</p></div>
      {{/each}}
    </div>
  </div></div>
</section>
<section class="panel panel--dark">
  <div class="bg" style="background-image:url('{{guarantees.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{{guarantees.kicker}}</div>
      <h2>{{guarantees.title}}</h2>
    </div>
    <div class="guar-grid">
      {{#each guarantees.items}}<div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24"><path d="{{this.icon}}"/></svg></div><h3>{{this.title}}</h3><p>{{this.text}}</p></div>
      {{/each}}
    </div>
  </div></div>
</section>
<section class="panel panel--center panel--dark" id="cities">
  <div class="bg" style="background-image:url('{{cities.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="sec-head reveal">
      <div class="kicker">{{cities.kicker}}</div>
      <h2>{{cities.title}}</h2>
      <p>{{cities.subtitle}}</p>
    </div>
    <div class="city-grid">
      {{#each cities.items}}<div class="city reveal"><div class="city-name">{{this.name}}</div><div class="city-line"></div><p>{{this.text}}</p></div>
      {{/each}}
    </div>
  </div></div>
</section>
<section class="panel panel--center panel--dark">
  <div class="bg" style="background-image:url('{{cta.bg}}')"></div>
  <div class="wrap"><div class="content cta">
    <h2 class="reveal shimmer">{{cta.title}}</h2>
    <p class="reveal">{{cta.text}}</p>
    <a href="{{brand.phone_raw}}" class="btn btn-solid reveal">{{cta.button}}</a>
  </div></div>
</section>
<section class="panel panel--dark" id="contacts">
  <div class="bg" style="background-image:url('{{contacts.bg}}')"></div>
  <div class="wrap"><div class="content">
    <div class="contact-grid">
      <div class="contact-info reveal">
        <div class="kicker">{{contacts.kicker}}</div>
        <h2>{{contacts.title}}</h2>
        <p>{{contacts.subtitle}}</p>
        {{#each contacts.lines}}<div class="c-line"><div class="c-ico"><svg viewBox="0 0 24 24"><path d="{{this.icon}}"/></svg></div><div><div class="lab">{{this.label}}</div>{{#if this.href}}<a class="val" href="{{this.href}}"{{#if this.external}} target="_blank" rel="noopener"{{/if}}>{{this.value}}</a>{{else}}<div class="val">{{this.value}}</div>{{/if}}</div></div>
        {{/each}}
      </div>
      <div class="reveal">
        <div class="call-block">
          <div class="cb-lab">{{contacts.call_label}}</div>
          <a class="cb-num" href="{{brand.phone_raw}}">{{contacts.call_number}}</a>
          <div class="cb-hint">{{contacts.call_hint|nl2br}}</div>
          <div class="contact-actions">
            {{#each contacts.buttons}}<a class="c-action {{this.cls}}" href="{{this.href}}"{{#if this.external}} target="_blank" rel="noopener"{{/if}}><svg viewBox="0 0 24 24"><path d="{{this.icon}}"/></svg>{{this.label}}</a>
            {{/each}}
          </div>
        </div>
      </div>
    </div>
  </div></div>
</section>
<footer>
  <div class="flogo">{{brand.name}}<span> · {{brand.sub}}</span></div>
  <div class="social-row">
    {{#each footer.socials}}<a class="soc" href="{{this.href}}"{{#if this.external}} target="_blank" rel="noopener"{{/if}} title="{{this.label}}"><svg viewBox="0 0 24 24"><path d="{{this.icon}}"/></svg></a>
    {{/each}}
  </div>
  <p>{{footer.line}}</p>
  <p style="margin-top:8px">© <span id="year"></span> {{footer.copyright}}</p>
</footer>
<div class="cookie-bar" id="cookieBar">
  <p>{{cookie.text}}</p>
  <button class="btn btn-solid" id="cookieOk">{{cookie.button}}</button>
</div>
<script>
(function(){
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const fine=matchMedia('(hover:hover) and (pointer:fine)').matches;
const progress=document.getElementById('progress');
const header=document.getElementById('header');
const burger=document.getElementById('burger'),menu=document.getElementById('menu'),scrim=document.getElementById('scrim');
let ticking=false,menuOpen=false;
function onScroll(){if(ticking)return;ticking=true;requestAnimationFrame(()=>{
  const h=document.documentElement;
  const sc=h.scrollHeight>h.clientHeight?h.scrollTop/(h.scrollHeight-h.clientHeight):0;
  progress.style.width=(sc*100)+'%';
  header.classList.toggle('solid',h.scrollTop>40);
  let current='';
  ['about','works','reviews','services','process','cities','contacts'].forEach(id=>{const el=document.getElementById(id);if(el&&el.getBoundingClientRect().top<=120)current=id;});
  menu.querySelectorAll('a[href^="#"]').forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+current));
  ticking=false;
});}
window.addEventListener('scroll',onScroll,{passive:true});onScroll();
document.getElementById('logo').addEventListener('click',e=>{e.preventDefault();window.scrollTo({top:0,behavior:'smooth'});});
function closeMenu(){burger.classList.remove('open');menu.classList.remove('open');scrim.classList.remove('show');menuOpen=false;}
function openMenu(){burger.classList.add('open');menu.classList.add('open');scrim.classList.add('show');menuOpen=true;}
burger.addEventListener('click',()=>{if(menuOpen)closeMenu();else openMenu();});
scrim.addEventListener('click',closeMenu);
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));
if(fine&&!reduced){
  const bgs=document.querySelectorAll('.panel .bg');
  const contents=document.querySelectorAll('.panel .content');
  let pTicking=false;
  function parallax(){if(pTicking)return;pTicking=true;requestAnimationFrame(()=>{
    bgs.forEach(bg=>{const r=bg.parentElement.getBoundingClientRect();const c=(r.top+r.height/2)-innerHeight/2;bg.style.transform='translateY('+(-c*0.25)+'px)';});
    contents.forEach(cn=>{const r=cn.parentElement.getBoundingClientRect();const c=(r.top+r.height/2)-innerHeight/2;cn.style.transform='translateY('+(-c*0.06)+'px)';});
    pTicking=false;});}
  window.addEventListener('scroll',parallax,{passive:true});parallax();
}
if(fine){
  const g=document.getElementById('cursorGlow');
  let gx=innerWidth/2,gy=innerHeight/2,cx=gx,cy=gy;
  window.addEventListener('mousemove',e=>{gx=e.clientX;gy=e.clientY;},{passive:true});
  (function loop(){cx+=(gx-cx)*.12;cy+=(gy-cy)*.12;g.style.transform='translate('+(cx-170)+'px,'+(cy-170)+'px)';requestAnimationFrame(loop);})();
}
function animateCount(el){const target=parseFloat(el.dataset.count);const dec=parseInt(el.dataset.decimal||'0');const suffix=el.dataset.suffix||'';const dur=1200,start=performance.now();function tick(t){let p=Math.min((t-start)/dur,1);p=1-Math.pow(1-p,3);let val=(target*p).toFixed(dec);el.textContent=(dec?val:Math.round(val))+suffix;if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);}
const statIO=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){animateCount(e.target);statIO.unobserve(e.target);}});},{threshold:.5});
document.querySelectorAll('.stat .num').forEach(el=>statIO.observe(el));
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
function initCarousel(trackId,prevId,nextId,dotsId){const track=document.getElementById(trackId),prev=document.getElementById(prevId),next=document.getElementById(nextId),dotsBox=document.getElementById(dotsId),items=[...track.children];dotsBox.innerHTML='';items.forEach((_,i)=>{const d=document.createElement('button');d.className='car-dot'+(i===0?' active':'');d.setAttribute('aria-label','Слайд '+(i+1));d.addEventListener('click',()=>items[i].scrollIntoView({behavior:'smooth',inline:'center',block:'nearest'}));dotsBox.appendChild(d);});const dots=[...dotsBox.children];const step=()=>items[0].offsetWidth+20;let sTick=false;track.addEventListener('scroll',()=>{if(sTick)return;sTick=true;requestAnimationFrame(()=>{const idx=Math.round(track.scrollLeft/step());dots.forEach((d,i)=>d.classList.toggle('active',i===idx));sTick=false;});},{passive:true});prev.addEventListener('click',()=>track.scrollBy({left:-step(),behavior:'smooth'}));next.addEventListener('click',()=>track.scrollBy({left:step(),behavior:'smooth'}));}
initCarousel('carTrack','carPrev','carNext','carDots');
initCarousel('revTrack','revPrev','revNext','revDots');
if(fine&&!reduced){
  document.querySelectorAll('.car-slide').forEach(slide=>{const img=slide.querySelector('img');slide.addEventListener('mousemove',e=>{const r=slide.getBoundingClientRect();const dx=(e.clientX-r.left)/r.width-.5;const dy=(e.clientY-r.top)/r.height-.5;img.style.transform='scale(1.07) translate('+(dx*8)+'px,'+(dy*8)+'px)';});slide.addEventListener('mouseleave',()=>{img.style.transform='';});});
}
const lightbox=document.getElementById('lightbox'),lbStage=document.getElementById('lbStage'),lbImg=document.getElementById('lbImg'),lbCount=document.getElementById('lbCount');
const lbItems=[...document.querySelectorAll('#carTrack .car-slide img')];let lbIdx=0;
let scale=1,tx=0,ty=0,startX=0,startY=0,startDist=0,startScale=1,moved=false;
function lbApply(){lbImg.style.transform='translate('+tx+'px,'+ty+'px) scale('+scale+')';}
function lbReset(){scale=1;tx=0;ty=0;lbApply();lbImg.style.transition='transform .25s ease';setTimeout(()=>{lbImg.style.transition='transform .18s ease-out';},260);}
function openLb(i){lbIdx=i;lbImg.src=lbItems[i].src;lbImg.alt=lbItems[i].alt;lbCount.textContent=(i+1)+' / '+lbItems.length;lbReset();lightbox.classList.add('open');document.body.style.overflow='hidden';}
function closeLb(){lightbox.classList.remove('open');document.body.style.overflow='';}
function lbStep(d){openLb((lbIdx+d+lbItems.length)%lbItems.length);}
lbItems.forEach((img,i)=>img.addEventListener('click',()=>openLb(i)));
document.getElementById('lbClose').addEventListener('click',closeLb);
document.getElementById('lbPrev').addEventListener('click',e=>{e.stopPropagation();lbStep(-1);});
document.getElementById('lbNext').addEventListener('click',e=>{e.stopPropagation();lbStep(1);});
lightbox.addEventListener('click',e=>{if(e.target===lightbox)closeLb();});
document.addEventListener('keydown',e=>{if(lightbox.classList.contains('open')){if(e.key==='Escape')closeLb();if(e.key==='ArrowLeft')lbStep(-1);if(e.key==='ArrowRight')lbStep(1);}});
let lastTap=0;
lbStage.addEventListener('touchstart',e=>{
  if(e.touches.length===2){startDist=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);startScale=scale;moved=true;}
  else if(e.touches.length===1){startX=e.touches[0].clientX;startY=e.touches[0].clientY;moved=false;}
  const now=Date.now();if(now-lastTap<280){if(scale>1){lbReset();}else{scale=2;tx=0;ty=0;lbApply();}lastTap=0;}else{lastTap=now;}
},{passive:true});
lbStage.addEventListener('touchmove',e=>{
  if(e.touches.length===2){e.preventDefault();const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);scale=Math.min(4,Math.max(1,startScale*d/startDist));tx=0;ty=0;lbApply();}
  else if(e.touches.length===1&&scale>1){const dx=e.touches[0].clientX-startX,dy=e.touches[0].clientY-startY;tx+=dx;ty+=dy;startX=e.touches[0].clientX;startY=e.touches[0].clientY;lbApply();}
},{passive:false});
lbStage.addEventListener('touchend',e=>{
  if(e.touches.length===0&&scale===1&&!moved){const dx=e.changedTouches[0].clientX-startX;if(Math.abs(dx)>60){lbStep(dx<0?1:-1);}}
  if(e.touches.length===0&&scale<1)scale=1;
},{passive:true});
document.querySelectorAll('.video-box').forEach(box=>{
  box.addEventListener('click',()=>{
    if(box.querySelector('iframe'))return;
    const iframe=document.createElement('iframe');
    iframe.src=box.dataset.src;
    iframe.setAttribute('allow','autoplay; encrypted-media; fullscreen; picture-in-picture');
    iframe.setAttribute('allowfullscreen','1');
    iframe.title='Видеоотзыв';
    box.innerHTML='';
    box.appendChild(iframe);
  });
});
const cookieBar=document.getElementById('cookieBar'),cookieOk=document.getElementById('cookieOk');
if(!localStorage.getItem('cookiesAccepted')){setTimeout(()=>cookieBar.classList.add('show'),900);}
cookieOk.addEventListener('click',()=>{localStorage.setItem('cookiesAccepted','1');cookieBar.classList.remove('show');});
document.getElementById('year').textContent=new Date().getFullYear();
})();
</script>
{{#if code.body}}{{{code.body|raw}}}{{/if}}
</body>
</html>"""


# ============================================================
#  РАБОТА С ДАННЫМИ
# ============================================================
def _json_clone(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False))


def _merge_deep(base, over):
    if not isinstance(base, dict) or not isinstance(over, dict):
        return _json_clone(over)
    res = dict(base)
    for k, v in over.items():
        if k in res and isinstance(res[k], dict) and isinstance(v, dict):
            res[k] = _merge_deep(res[k], v)
        else:
            res[k] = _json_clone(v)
    return res


def _migrate(raw):
    if not isinstance(raw, dict):
        return {}
    d = _json_clone(raw)
    about = d.get("about")
    if isinstance(about, dict):
        if "body" in about and "card_text" not in about:
            about["card_text"] = about.pop("text", "")
            about["text"] = about.pop("body", "")
        about.pop("body", None)
    hero = d.get("hero")
    if isinstance(hero, dict):
        if hero.get("eyebrow", "").strip() == "Мебель и кухни на заказ1":
            hero["eyebrow"] = "Мебель и кухни на заказ"
        hero.setdefault("btn1_href", "#consult")
        hero.setdefault("btn2_href", "#works")
    contacts = d.get("contacts")
    if isinstance(contacts, dict) and "lines" not in contacts:
        lines = _json_clone(DEFAULT_DATA.get("contacts", {}).get("lines") or [])
        if lines and contacts.get("regions"):
            lines[0]["value"] = contacts["regions"]
        if lines:
            contacts["lines"] = lines
    if "stats" in d and isinstance(d["stats"], dict):
        d["stats"].setdefault("items", _json_clone(DEFAULT_DATA.get("stats", {}).get("items") or []))
    return d


_ICON_KEYS = (("services", "items"), ("guarantees", "items"))


def _normalize_context(data):
    ctx = _json_clone(data)
    for section, key in _ICON_KEYS:
        items = (ctx.get(section) or {}).get(key)
        if isinstance(items, list):
            for it in items:
                if not isinstance(it, dict):
                    continue
                icon = str(it.get("icon") or "")
                if "<" in icon:
                    it["icon_svg"] = icon
                    it["icon"] = ""
    ctx["year"] = str(date.today().year)
    ctx["domain"] = _domain(ctx)
    return ctx


def _domain(data=None):
    dom = DOMAIN
    if isinstance(data, dict):
        seo = data.get("seo") or {}
        dom = (seo.get("domain") or "").strip() or DOMAIN
    dom = dom.rstrip("/")
    if "//" not in dom:
        dom = "https://" + dom
    scheme, _, host = dom.partition("://")
    return scheme + "://" + _punycode(host)


def _host(data=None):
    return _domain(data).split("://", 1)[-1]


def _punycode(host):
    try:
        return host.encode("idna").decode("ascii")
    except Exception:
        return host


# ============================================================
#  SUPABASE (REST + Storage, без внешних библиотек)
# ============================================================
def _http(method, url, payload=None, headers=None, timeout=HTTP_TIMEOUT, raw_body=None):
    data = raw_body
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            try:
                return r.status, json.loads(body.decode("utf-8")) if body else None, body
            except Exception:
                return r.status, None, body
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body.decode("utf-8")), body
        except Exception:
            return e.code, None, body
    except Exception as e:
        return 0, None, str(e).encode("utf-8")


def _sb_headers():
    key = SUPABASE_SERVICE or SUPABASE_ANON
    return {"apikey": key, "Authorization": "Bearer " + key}


def _fetch_from_supabase(timeout=8):
    if not SUPABASE_URL:
        return None, False
    url = "{}/rest/v1/{}?id=eq.{}&select=data".format(SUPABASE_URL, DATA_TABLE, DATA_ROW_ID)
    keys = [k for k in (SUPABASE_SERVICE, SUPABASE_ANON) if k]
    last = None
    for i, key in enumerate(keys):
        st, js, body = _http("GET", url, headers={"apikey": key, "Authorization": "Bearer " + key}, timeout=timeout)
        if st == 200 and isinstance(js, list):
            if js and isinstance(js[0].get("data"), dict) and js[0]["data"]:
                return js[0]["data"], True
            return None, True
        last = "HTTP {} {}".format(st, (body or b"")[:200])
        print("[sb] read({}) {}".format("service" if i == 0 else "anon", last), flush=True)
    return None, False


def _save_to_supabase(data):
    if not SUPABASE_URL:
        return False
    key = SUPABASE_SERVICE or SUPABASE_ANON
    if not key:
        return False
    url = "{}/rest/v1/{}".format(SUPABASE_URL, DATA_TABLE)
    headers = {"apikey": key, "Authorization": "Bearer " + key,
               "Prefer": "resolution=merge-duplicates,return=minimal"}
    st, js, body = _http("POST", url, payload=[{"id": DATA_ROW_ID, "data": data}], headers=headers, timeout=25)
    if 200 <= st < 300:
        print("[save] OK: записано в Supabase ({} КБ)".format(len(json.dumps(data, ensure_ascii=False)) // 1024), flush=True)
        return True
    print("[save] FAIL: HTTP {} {}".format(st, (body or b"")[:300]), flush=True)
    return False


_bucket_state = {"checked": False, "ok": False}
_bucket_lock = threading.Lock()


def _bucket_ensure():
    global _bucket_state
    with _bucket_lock:
        if _bucket_state["checked"]:
            return _bucket_state["ok"]
        _bucket_state["checked"] = True
        if not (SUPABASE_URL and SUPABASE_SERVICE):
            return False
        base = SUPABASE_URL + "/storage/v1/bucket"
        st, js, body = _http("GET", base + "/" + BUCKET, headers=_sb_headers())
        if st == 200:
            _bucket_state["ok"] = True
            return True
        st, js, body = _http("POST", base, payload={"id": BUCKET, "name": BUCKET, "public": True}, headers=_sb_headers())
        _bucket_state["ok"] = st in (200, 201)
        print("[storage] создать бакет {}: HTTP {}".format(BUCKET, st), (body or b"")[:200], flush=True)
        return _bucket_state["ok"]


def _storage_public_url(name):
    return "{}/storage/v1/object/public/{}/{}".format(SUPABASE_URL, BUCKET, name)


def _storage_upload(filename, blob, mime):
    if not _bucket_ensure():
        return None
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".avif", ".ico"):
        ext = {"image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/svg+xml": ".svg"}.get(mime, ".jpg")
    name = "{}/{}{}".format(date.today().isoformat(), secrets.token_hex(6), ext)
    url = "{}/storage/v1/object/{}/{}".format(SUPABASE_URL, BUCKET, name)
    headers = _sb_headers()
    headers.update({"Content-Type": mime, "x-upsert": "true", "Cache-Control": "max-age=31536000"})
    st, js, body = _http("POST", url, headers=headers, raw_body=blob, timeout=45)
    if 200 <= st < 300:
        return _storage_public_url(name)
    print("[storage] upload HTTP {} {}".format(st, (body or b"")[:200]), flush=True)
    return None


def _storage_list(limit=120):
    if not _bucket_ensure():
        return []
    url = "{}/storage/v1/object/list/{}".format(SUPABASE_URL, BUCKET)
    payload = {"prefix": "", "limit": limit, "offset": 0, "sortBy": {"column": "created_at", "order": "desc"}}
    st, js, body = _http("POST", url, payload=payload, headers=_sb_headers(), timeout=20)
    if st == 200 and isinstance(js, list):
        out = []
        for it in js:
            nm = it.get("name") if isinstance(it, dict) else None
            if nm:
                out.append({"name": nm, "url": _storage_public_url(nm)})
        return out
    return []


# ============================================================
#  AI (YandexGPT / GigaChat)
# ============================================================
def _ai_yandex(system, user, max_tokens=700):
    if not (YANDEX_API_KEY and FOLDER_ID):
        return None, "нет YANDEX_API_KEY / FOLDER_ID"
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    payload = {
        "modelUri": "gpt://{}/yandexgpt-lite/latest".format(FOLDER_ID),
        "completionOptions": {"stream": False, "temperature": 0.55, "maxTokens": str(int(max_tokens))},
        "messages": [{"role": "system", "text": system}, {"role": "user", "text": user}],
    }
    st, js, body = _http("POST", url, payload=payload,
                         headers={"Authorization": "Api-Key " + YANDEX_API_KEY}, timeout=60)
    if st == 200 and isinstance(js, dict):
        try:
            return js["result"]["alternatives"][0]["message"]["text"], None
        except Exception:
            return None, "неожиданный ответ YandexGPT"
    return None, "YandexGPT HTTP {}: {}".format(st, (body or b"")[:200])


_gc = {"token": "", "exp": 0.0}
_gc_lock = threading.Lock()


def _gigachat_token():
    with _gc_lock:
        if _gc["token"] and _gc["exp"] > time.time() + 60:
            return _gc["token"], None
        if not GIGACHAT_AUTH_KEY:
            return None, "нет GIGACHAT_AUTH_KEY"
        req = urllib.request.Request("https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                                     data=b"scope=GIGACHAT_API_PERS", method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Accept", "application/json")
        req.add_header("RqUID", str(uuid.uuid4()))
        req.add_header("Authorization", "Basic " + GIGACHAT_AUTH_KEY)
        ctx = ssl._create_unverified_context()
        try:
            with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
                js = json.loads(r.read().decode("utf-8"))
            tok = js.get("access_token")
            if not tok:
                return None, "GigaChat: нет access_token"
            _gc["token"] = tok
            _gc["exp"] = (time.time() + float(js.get("expires_at", 0)) / 1000.0
                          if js.get("expires_at") else time.time() + 1500)
            return tok, None
        except urllib.error.HTTPError as e:
            return None, "GigaChat oauth HTTP {}: {}".format(e.code, e.read()[:200])
        except Exception as e:
            return None, "GigaChat oauth: {}".format(e)


def _ai_gigachat(system, user, max_tokens=700):
    tok, err = _gigachat_token()
    if not tok:
        return None, err
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    payload = {"model": "GigaChat", "temperature": 0.6, "max_tokens": int(max_tokens),
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    ctx = ssl._create_unverified_context()
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    req.add_header("Authorization", "Bearer " + tok)
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            js = json.loads(r.read().decode("utf-8"))
        return js["choices"][0]["message"]["content"], None
    except urllib.error.HTTPError as e:
        return None, "GigaChat HTTP {}: {}".format(e.code, e.read()[:200])
    except Exception as e:
        return None, "GigaChat: {}".format(e)


def _ai_generate(system, user, max_tokens=700):
    order = ["yandex", "gigachat"] if AI_PROVIDER == "auto" else [AI_PROVIDER]
    errors = []
    for p in order:
        if p == "yandex":
            text, err = _ai_yandex(system, user, max_tokens)
        elif p == "gigachat":
            text, err = _ai_gigachat(system, user, max_tokens)
        else:
            continue
        if text:
            return _clean_ai(text), p, None
        if err:
            errors.append(err)
    return None, None, "; ".join(errors) or "AI не настроен (нет ключей)"


def _clean_ai(text):
    t = (text or "").strip()
    t = re.sub(r"^(?:вариант\s*\d+\s*[:.\-]\s*)", "", t, flags=re.I)
    t = re.sub(r"^\*\*(.+?)\*\*$", r"\1", t)
    t = t.strip().strip('"').strip("«»").strip()
    t = re.sub(r"^(?:Title|Заголовок|Description|Описание|Keywords|Ключевые слова|Текст)\s*[:：]\s*", "", t, flags=re.I)
    t = t.replace("**", "").strip()
    return t


def _ai_ask(data, task, path, value):
    brand = (data.get("brand") or {})
    cities = ", ".join([c.get("name", "") for c in ((data.get("cities") or {}).get("items") or []) if isinstance(c, dict)])
    services = ", ".join([s.get("title", "") for s in ((data.get("services") or {}).get("items") or []) if isinstance(s, dict)])
    seo = data.get("seo") or {}
    base = ("Компания: {}. Города: {}. Услуги: {}. Телефон: {}. Сайт: {}."
            .format(brand.get("name", "Кухни Островский"), cities or "Ростов-на-Дону, Батайск, Азов",
                    services or "кухни и корпусная мебель на заказ",
                    brand.get("phone", ""), seo.get("domain") or DOMAIN))
    system = ("Ты опытный русскоязычный копирайтер и SEO-специалист для локального бизнеса "
              "(мебель на заказ). Пиши живым, конкретным языком, без воды, без markdown, "
              "без кавычек вокруг ответа, без слова «Вариант». Отвечай ТОЛЬКО готовым текстом.")
    rules = "Без emoji. Без англицизмов. Не выдумывай цены, сроки и проценты."
    user = base + "\n" + rules + "\n\n"
    if task == "seo_title":
        user += "Составь SEO Title (title страницы) до 65 символов: название компании + услуга + 2 города + выгода. Верни одну строку."
    elif task == "seo_description":
        user += ("Составь meta description до 160 символов: что делаем, где, выгода (бесплатный замер и проект), "
                 "телефон в конце. Верни одну строку.")
    elif task == "seo_keywords":
        user += "Составь 12-15 ключевых фраз через запятую (поисковые запросы по кухням и мебели на заказ в этих городах)."
    elif task == "hero_sub":
        user += "Напиши подзаголовок на главном экране: 1-2 предложения, до 220 символов, про кухни и корпусную мебель под ключ."
    elif task == "about_text":
        user += "Напиши блок «о нас» (3-4 предложения, до 400 символов) от лица руководителя мастерской."
    elif task == "service_text":
        user += "Опиши услугу одним предложением до 130 символов. Название услуги: " + (value or "")
    elif task == "city_text":
        user += "Напиши одно предложение до 120 символов про работу в городе: " + (value or "")
    elif task == "cta_text":
        user += "Напиши короткий призыв к действию (1-2 предложения, до 180 символов) с приглашением позвонить."
    elif task == "shorten":
        user += "Сократи текст до 1-2 предложений, сохранив смысл и ключевые слова:\n" + (value or "")
    elif task == "expand":
        user += "Дополни и улучши текст (до 3 предложений), сохранив смысл:\n" + (value or "")
    else:
        user += "Улучши текст: убери ошибки и воду, сделай живее, сохрани смысл и длину:\n" + (value or "")
    return system, user


# ============================================================
#  КЭШ ДАННЫХ / СЕССИИ
# ============================================================
_data_lock = threading.Lock()
_data_cache = None
_cache_ts = 0.0
_db_state = {"read": None, "write": None, "last_error": ""}

_auth_lock = threading.Lock()
_sessions = {}
_login_fails = {}


def _new_session():
    t = secrets.token_urlsafe(32)
    with _auth_lock:
        _sessions[t] = time.time() + SESSION_TTL
        if len(_sessions) > 200:
            now = time.time()
            for k in [k for k, v in _sessions.items() if v < now]:
                _sessions.pop(k, None)
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


def _login_blocked(ip):
    with _auth_lock:
        rec = _login_fails.get(ip)
        if not rec:
            return False
        cnt, until = rec
        if until and until < time.time():
            _login_fails.pop(ip, None)
            return False
        return cnt >= 8


def _login_note(ip, ok):
    with _auth_lock:
        if ok:
            _login_fails.pop(ip, None)
            return
        cnt, _ = _login_fails.get(ip, (0, 0))
        _login_fails[ip] = (cnt + 1, time.time() + 600)


def load_fresh():
    global _data_cache, _cache_ts
    raw, ok = _fetch_from_supabase()
    _db_state["read"] = ok
    if not ok:
        with _data_lock:
            if _data_cache is not None:
                _cache_ts = time.time()
                print("[load] БД недоступна — отдаю кэш", flush=True)
                return _data_cache
        with _data_lock:
            _data_cache = _json_clone(DEFAULT_DATA)
            _cache_ts = time.time()
        print("[load] БД недоступна — дефолтный контент", flush=True)
        return _data_cache
    if raw is None:
        data = _json_clone(DEFAULT_DATA)
        print("[load] строка в БД пустая — дефолтный контент", flush=True)
    else:
        data = _merge_deep(DEFAULT_DATA, _migrate(raw))
        print("[load] из БД: {} разделов".format(len(raw)), flush=True)
    with _data_lock:
        _data_cache = data
        _cache_ts = time.time()
    return data


def load_data():
    global _cache_ts
    now = time.time()
    with _data_lock:
        if _data_cache is not None and now - _cache_ts < CACHE_TTL:
            return _data_cache
    return load_fresh()


def save_data(data):
    global _data_cache, _cache_ts
    ok = _save_to_supabase(data)
    _db_state["write"] = ok
    if ok:
        with _data_lock:
            _data_cache = _merge_deep(DEFAULT_DATA, _migrate(data))
            _cache_ts = time.time()
    return ok


# ============================================================
#  ПРОКСИ VK-КАРТИНОК
# ============================================================
_img_cache = {}
_img_lock = threading.Lock()
_VK_RE = re.compile(r'https://(?:sun\d+-\d+\.)?vkuserphoto\.ru/[^\s"\'\)<>]+')
_PROT_RE = re.compile(r"\x00PROT(\d+)\x00")


def _fetch_image(url):
    now = time.time()
    with _img_lock:
        c = _img_cache.get(url)
        if c and now - c[1] < IMG_TTL:
            return c[0], c[2]
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"),
            "Referer": "https://vk.com/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            ct = resp.headers.get("Content-Type", "image/jpeg")
        if data:
            with _img_lock:
                if len(_img_cache) > 400:
                    _img_cache.clear()
                _img_cache[url] = (data, now, ct)
            return data, ct
    except Exception as e:
        print("[img] {} -> {}".format(url[:60], e), flush=True)
    return None, None


def _img_proxy_url(url):
    return "/img?u=" + base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


def _proxify_urls(html):
    stash = []

    def keep(m):
        stash.append(m.group(0))
        return "\x00PROT%d\x00" % (len(stash) - 1)

    html = re.sub(r'<script type="application/ld\+json">.*?</script>', keep, html, flags=re.S)
    html = re.sub(r'<meta property="og:image"[^>]*>', keep, html)
    html = _VK_RE.sub(lambda m: _img_proxy_url(m.group(0)), html)
    if stash:
        html = _PROT_RE.sub(lambda m: stash[int(m.group(1))], html)
    return html


# ============================================================
#  РЕНДЕР СТРАНИЦЫ
# ============================================================
_page_lock = threading.Lock()
_page_cache = {"tpl": ""}


def _page_template():
    with _page_lock:
        if _page_cache["tpl"]:
            return _page_cache["tpl"]
        tpl = PAGE_TEMPLATE
        if "</head>" in tpl and "goldAnimations" not in tpl:
            tpl = tpl.replace("</head>", ANIM_STYLE + "\n</head>", 1)
        if "</body>" in tpl and "goldAnimationScript" not in tpl:
            tpl = tpl.replace("</body>", ANIM_SCRIPT + "\n</body>", 1)
        _page_cache["tpl"] = tpl
        print("[page] шаблон готов: {} байт".format(len(tpl)), flush=True)
        return tpl


def render_site():
    data = load_data()
    ctx = _normalize_context(data)
    try:
        html = render(_page_template(), ctx)
    except Exception as e:
        print("[render] ОШИБКА: {}".format(e), flush=True)
        html = _page_template()
    return _proxify_urls(html)


def build_robots(data):
    dom, host = _domain(data), _host(data)
    seo = data.get("seo") or {}
    custom = (seo.get("robots") or "").strip()
    if custom:
        return custom.replace("{{domain}}", dom).replace("{{host}}", host) + "\n"
    return ("User-agent: *\n"
            "Allow: /\n"
            "Disallow: /admin\n"
            "Disallow: /img?\n"
            "Clean-param: utm_source&utm_medium&utm_campaign&utm_term&utm_content&yclid&gclid\n\n"
            "Host: {}\n"
            "Sitemap: {}/sitemap.xml\n").format(host, dom)


def build_sitemap(data):
    dom = _domain(data)
    today = date.today().isoformat()
    seo = data.get("seo") or {}
    urls = [{"loc": dom + "/", "changefreq": "weekly", "priority": "1.0"}]
    for it in (seo.get("extra_urls") or []):
        if not isinstance(it, dict):
            continue
        loc = (it.get("loc") or "").strip()
        if not loc:
            continue
        if loc.startswith("/"):
            loc = dom + loc
        urls.append({"loc": loc,
                     "changefreq": (it.get("changefreq") or "monthly").strip(),
                     "priority": (it.get("priority") or "0.6").strip()})
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        parts.append("  <url>\n    <loc>{}</loc>\n    <lastmod>{}</lastmod>\n"
                     "    <changefreq>{}</changefreq>\n    <priority>{}</priority>\n  </url>".format(
                         _escape(u["loc"]), today, _escape(u["changefreq"]), _escape(u["priority"])))
    parts.append("</urlset>")
    return "\n".join(parts) + "\n"


def build_manifest(data):
    brand = data.get("brand") or {}
    design = data.get("design") or {}
    return json.dumps({
        "name": brand.get("name", "Кухни Островский"),
        "short_name": brand.get("name", "Кухни Островский"),
        "start_url": "/", "display": "standalone",
        "background_color": design.get("bg", "#0e0c09"),
        "theme_color": design.get("bg", "#0e0c09"),
        "lang": "ru-RU",
        "icons": [{"src": "/favicon-192x192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}],
    }, ensure_ascii=False)


def build_404(data):
    p = data.get("page404") or {}
    title = p.get("title") or "Страница не найдена"
    text = p.get("text") or "Возможно, страница переехала или удалена."
    btn = p.get("button") or "На главную"
    return ("<!DOCTYPE html><html lang=\"ru\"><head><meta charset=\"UTF-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<meta name=\"robots\" content=\"noindex\"><title>{t}</title>"
            "<style>body{{margin:0;background:#0e0c09;color:#f5efe3;font-family:system-ui;"
            "display:flex;align-items:center;justify-content:center;min-height:100vh;text-align:center}}"
            "h1{{font-family:Georgia,serif;font-size:72px;margin:0 0 10px;color:#eccfa0}}"
            "a{{display:inline-block;margin-top:22px;padding:14px 26px;border-radius:12px;"
            "background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;"
            "font-weight:700;text-decoration:none;text-transform:uppercase;letter-spacing:1px}}</style></head>"
            "<body><div><h1>404</h1><p>{t}</p><p>{x}</p><a href=\"/\">{b}</a></div></body></html>").format(
        t=_escape(title), x=_escape(text), b=_escape(btn))


# ============================================================
#  FAVICON
# ============================================================
_fc = {"data": None, "ts": 0.0}
_ic = {"ico": None, "png16": None, "png32": None, "png180": None, "png192": None}
_fc_lock = threading.Lock()


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
            c = img.copy()
            c.thumbnail((size, size))
            b = io.BytesIO()
            c.save(b, format="PNG")
            return b.getvalue()

        _ic["png16"] = png(16)
        _ic["png32"] = png(32)
        _ic["png180"] = png(180)
        _ic["png192"] = png(192)
    except Exception as e:
        print("[favicon] {}".format(e), flush=True)


def get_favicon():
    now = time.time()
    with _fc_lock:
        if _fc["data"] is not None and now - _fc["ts"] < 3600:
            return _fc["data"]
    data, _ct = _fetch_image(FAVICON_URL)
    if data:
        with _fc_lock:
            _fc["data"] = data
            _fc["ts"] = now
        _make_icons(data)
    return data


# ============================================================
#  СХЕМА АДМИНКИ
# ============================================================
def _svg_icon(_unused=None):
    return {"path": "icon", "label": "Иконка", "type": "textarea", "rows": 2, "mono": True,
            "hint": "Только содержимое атрибута d у <path viewBox=\"0 0 24 24\">. "
                    "Например: M3 9h18M3 9v10a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V9"}


ADMIN_SCHEMA = [
    {"id": "seo", "group": "SEO и код", "title": "SEO и мета", "hint": "Заголовок и описание страницы, Open Graph, robots, sitemap.",
     "fields": [
         {"path": "seo.title", "label": "Title", "type": "textarea", "rows": 2, "ai": "seo_title"},
         {"path": "seo.description", "label": "Description", "type": "textarea", "rows": 3, "ai": "seo_description"},
         {"path": "seo.keywords", "label": "Keywords", "type": "textarea", "rows": 2, "ai": "seo_keywords"},
         {"path": "seo.domain", "label": "Домен сайта", "type": "text", "hint": "Используется в canonical, robots и sitemap. Можно писать кириллицей."},
         {"path": "seo.canonical", "label": "Canonical URL", "type": "text"},
         {"path": "seo.og_title", "label": "OG title", "type": "text"},
         {"path": "seo.og_description", "label": "OG description", "type": "textarea", "rows": 2},
         {"path": "seo.og_image", "label": "OG картинка (превью в соцсетях)", "type": "image"},
         {"path": "seo.yandex_verification", "label": "Яндекс: мета-код подтверждения", "type": "text"},
         {"path": "seo.google_verification", "label": "Google: мета-код подтверждения", "type": "text"},
         {"path": "seo.metrika_id", "label": "Номер счётчика Яндекс.Метрики", "type": "text", "hint": "Если заполнить — счётчик вставится автоматически."},
         {"path": "seo.robots", "label": "robots.txt (весь файл)", "type": "textarea", "rows": 6, "mono": True,
          "hint": "Пусто = сгенерировать автоматически ({{domain}} подставится сам)."},
     ],
     "lists": [
         {"path": "seo.extra_urls", "label": "Доп. страницы в sitemap", "titleField": "loc",
          "tpl": {"loc": "/", "changefreq": "monthly", "priority": "0.6"},
          "item": [
              {"path": "loc", "label": "URL (можно /ceny/ или полный)", "type": "text"},
              {"path": "changefreq", "label": "changefreq", "type": "select", "options": ["daily", "weekly", "monthly", "yearly"]},
              {"path": "priority", "label": "priority", "type": "text"},
          ]},
     ]},

    {"id": "code", "group": "SEO и код", "title": "Коды и скрипты",
     "hint": "Сюда вставляются коды счётчиков, пикселей, чатов. HTML вставляется как есть.",
     "fields": [
         {"path": "code.head", "label": "Код в <head> (Метрика, Google, пиксели)", "type": "textarea", "rows": 8, "mono": True},
         {"path": "code.body", "label": "Код перед </body> (чаты, виджеты)", "type": "textarea", "rows": 8, "mono": True},
     ]},

    {"id": "design", "group": "SEO и код", "title": "Дизайн и цвета", "hint": "Цвета и шрифты всего сайта.",
     "fields": [
         {"path": "design.bg", "label": "Фон сайта", "type": "color"},
         {"path": "design.gold", "label": "Золотой (основной акцент)", "type": "color"},
         {"path": "design.gold_soft", "label": "Светлое золото (текст-акцент)", "type": "color"},
         {"path": "design.gold_deep", "label": "Тёмное золото (градиент)", "type": "color"},
         {"path": "design.text", "label": "Основной текст", "type": "color"},
         {"path": "design.muted", "label": "Второстепенный текст", "type": "color"},
         {"path": "design.fonts_url", "label": "Ссылка на шрифты Google", "type": "text", "mono": True},
         {"path": "design.custom_css", "label": "Свой CSS", "type": "textarea", "rows": 8, "mono": True},
     ]},

    {"id": "brand", "group": "Контент", "title": "Бренд и меню", "fields": [
        {"path": "brand.name", "label": "Название", "type": "text"},
        {"path": "brand.sub", "label": "Подпись под названием", "type": "text"},
        {"path": "brand.logo_url", "label": "Логотип / аватар", "type": "image"},
        {"path": "brand.phone", "label": "Телефон (как показывать)", "type": "text"},
        {"path": "brand.phone_raw", "label": "Телефон для ссылок tel:", "type": "text"},
        {"path": "brand.telegram", "label": "Telegram (ссылка)", "type": "text"},
        {"path": "brand.vk", "label": "VK (ссылка)", "type": "text"},
        {"path": "nav.cta_label", "label": "Кнопка в меню (текст)", "type": "text", "hint": "Пусто = кнопки нет."},
        {"path": "nav.cta_href", "label": "Кнопка в меню (ссылка)", "type": "text"},
     ],
     "lists": [
         {"path": "nav.items", "label": "Пункты меню", "titleField": "label", "tpl": {"label": "Новый пункт", "href": "#top"},
          "item": [{"path": "label", "label": "Текст", "type": "text"}, {"path": "href", "label": "Ссылка (#якорь)", "type": "text"}]},
     ]},

    {"id": "hero", "group": "Контент", "title": "Главный экран", "fields": [
        {"path": "hero.eyebrow", "label": "Надзаголовок", "type": "text"},
        {"path": "hero.title_before", "label": "Заголовок (начало)", "type": "text"},
        {"path": "hero.title_em", "label": "Заголовок (золотые слова)", "type": "text"},
        {"path": "hero.sub", "label": "Подзаголовок", "type": "textarea", "rows": 3, "ai": "hero_sub"},
        {"path": "hero.btn1", "label": "Кнопка 1 — текст", "type": "text"},
        {"path": "hero.btn1_href", "label": "Кнопка 1 — ссылка", "type": "text"},
        {"path": "hero.btn2", "label": "Кнопка 2 — текст", "type": "text"},
        {"path": "hero.btn2_href", "label": "Кнопка 2 — ссылка", "type": "text"},
        {"path": "hero.bg", "label": "Фон", "type": "image"},
     ]},

    {"id": "stats", "group": "Контент", "title": "Цифры (счётчики)", "fields": [
        {"path": "stats.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "stats.items", "label": "Цифры", "titleField": "label",
          "tpl": {"prefix": "", "num": "10", "suffix": "+", "decimal": "", "label": "лет опыта"},
          "item": [
              {"path": "num", "label": "Число", "type": "text"},
              {"path": "decimal", "label": "Знаков после запятой (0 или пусто)", "type": "text"},
              {"path": "prefix", "label": "Префикс", "type": "text"},
              {"path": "suffix", "label": "Суффикс (%, +, /10)", "type": "text"},
              {"path": "label", "label": "Подпись", "type": "text"},
          ]},
     ]},

    {"id": "about", "group": "Контент", "title": "О специалисте", "fields": [
        {"path": "about.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "about.title", "label": "Заголовок", "type": "text"},
        {"path": "about.text", "label": "Текст справа", "type": "textarea", "rows": 4, "ai": "about_text"},
        {"path": "about.photo", "label": "Фото", "type": "image"},
        {"path": "about.name", "label": "Имя", "type": "text"},
        {"path": "about.role", "label": "Должность", "type": "text"},
        {"path": "about.card_text", "label": "Текст в карточке", "type": "textarea", "rows": 3, "ai": "improve"},
        {"path": "about.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "about.features", "label": "Плюсы (галочки)", "titleField": "", "tpl": "Новое преимущество",
          "item": [{"path": "", "label": "", "type": "text", "placeholder": "Например: Гарантия качества"}]},
     ]},

    {"id": "consult", "group": "Контент", "title": "Блок консультации", "fields": [
        {"path": "consult.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "consult.title", "label": "Заголовок", "type": "text"},
        {"path": "consult.phone", "label": "Телефон (как показывать)", "type": "text"},
        {"path": "consult.phone_raw", "label": "Телефон для tel:", "type": "text"},
        {"path": "consult.text", "label": "Текст", "type": "textarea", "rows": 3, "ai": "improve"},
        {"path": "consult.bg", "label": "Фон", "type": "image"},
     ]},

    {"id": "works", "group": "Контент", "title": "Работы (фото)", "fields": [
        {"path": "works.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "works.title", "label": "Заголовок", "type": "text"},
        {"path": "works.subtitle", "label": "Подзаголовок", "type": "textarea", "rows": 2},
        {"path": "works.hint", "label": "Подпись «Листайте»", "type": "text"},
        {"path": "works.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "works.items", "label": "Фотографии работ", "titleField": "alt", "tpl": {"url": "", "alt": "Кухня на заказ"},
          "item": [
              {"path": "url", "label": "Картинка", "type": "image"},
              {"path": "alt", "label": "Alt (для SEO)", "type": "text"},
          ]},
     ]},

    {"id": "reviews", "group": "Контент", "title": "Отзывы", "fields": [
        {"path": "reviews.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "reviews.title", "label": "Заголовок", "type": "text"},
        {"path": "reviews.subtitle", "label": "Подзаголовок", "type": "textarea", "rows": 2},
        {"path": "reviews.hint", "label": "Подпись «Листайте»", "type": "text"},
        {"path": "reviews.bg", "label": "Фон", "type": "image"},
        {"path": "reviews.video_poster", "label": "Превью для видеоотзывов", "type": "image"},
     ],
     "lists": [
         {"path": "reviews.items", "label": "Отзывы", "titleField": "name",
          "tpl": {"name": "", "sub": "", "stars": 5, "avatar": "", "text": "", "video": "", "poster": ""},
          "item": [
              {"path": "name", "label": "Имя", "type": "text"},
              {"path": "sub", "label": "Что заказывали", "type": "text"},
              {"path": "stars", "label": "Звёзд (1-5)", "type": "text"},
              {"path": "avatar", "label": "Аватар", "type": "image"},
              {"path": "text", "label": "Текст отзыва", "type": "textarea", "rows": 4},
              {"path": "video", "label": "Видео: ссылка для iframe (vk video_ext.php)", "type": "text"},
              {"path": "poster", "label": "Превью видео", "type": "image"},
          ]},
     ]},

    {"id": "services", "group": "Контент", "title": "Услуги", "fields": [
        {"path": "services.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "services.title", "label": "Заголовок", "type": "text"},
        {"path": "services.subtitle", "label": "Подзаголовок", "type": "textarea", "rows": 2},
        {"path": "services.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "services.items", "label": "Услуги", "titleField": "title",
          "tpl": {"title": "", "text": "", "icon": ""},
          "item": [
              {"path": "title", "label": "Название", "type": "text"},
              {"path": "text", "label": "Описание", "type": "textarea", "rows": 2, "ai": "improve"},
              _svg_icon(None),
          ]},
     ]},

    {"id": "process", "group": "Контент", "title": "Этапы работы", "fields": [
        {"path": "process.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "process.title", "label": "Заголовок", "type": "text"},
        {"path": "process.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "process.items", "label": "Этапы", "titleField": "title",
          "tpl": {"n": "07", "title": "", "text": ""},
          "item": [
              {"path": "n", "label": "Номер", "type": "text"},
              {"path": "title", "label": "Заголовок", "type": "text"},
              {"path": "text", "label": "Текст", "type": "textarea", "rows": 2},
          ]},
     ]},

    {"id": "guarantees", "group": "Контент", "title": "Гарантии", "fields": [
        {"path": "guarantees.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "guarantees.title", "label": "Заголовок", "type": "text"},
        {"path": "guarantees.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "guarantees.items", "label": "Пункты", "titleField": "title",
          "tpl": {"title": "", "text": "", "icon": ""},
          "item": [
              {"path": "title", "label": "Заголовок", "type": "text"},
              {"path": "text", "label": "Текст", "type": "textarea", "rows": 2},
              _svg_icon(None),
          ]},
     ]},

    {"id": "cities", "group": "Контент", "title": "Города", "fields": [
        {"path": "cities.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "cities.title", "label": "Заголовок", "type": "text"},
        {"path": "cities.subtitle", "label": "Подзаголовок", "type": "textarea", "rows": 2},
        {"path": "cities.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "cities.items", "label": "Города", "titleField": "name",
          "tpl": {"name": "", "text": ""},
          "item": [
              {"path": "name", "label": "Город", "type": "text"},
              {"path": "text", "label": "Текст", "type": "textarea", "rows": 2, "ai": "city_text"},
          ]},
     ]},

    {"id": "cta", "group": "Контент", "title": "Призыв к действию", "fields": [
        {"path": "cta.title", "label": "Заголовок", "type": "text"},
        {"path": "cta.text", "label": "Текст", "type": "textarea", "rows": 3, "ai": "cta_text"},
        {"path": "cta.button", "label": "Кнопка", "type": "text"},
        {"path": "cta.phone_raw", "label": "Телефон для tel:", "type": "text"},
        {"path": "cta.bg", "label": "Фон", "type": "image"},
     ]},

    {"id": "contacts", "group": "Контент", "title": "Контакты", "fields": [
        {"path": "contacts.kicker", "label": "Надзаголовок", "type": "text"},
        {"path": "contacts.title", "label": "Заголовок", "type": "text"},
        {"path": "contacts.subtitle", "label": "Подзаголовок", "type": "textarea", "rows": 2},
        {"path": "contacts.call_label", "label": "Подпись в карточке звонка", "type": "text"},
        {"path": "contacts.call_number", "label": "Телефон в карточке", "type": "text"},
        {"path": "contacts.call_hint", "label": "Текст под телефоном", "type": "textarea", "rows": 2},
        {"path": "contacts.bg", "label": "Фон", "type": "image"},
     ],
     "lists": [
         {"path": "contacts.lines", "label": "Строки контактов", "titleField": "label",
          "tpl": {"label": "", "value": "", "href": "", "icon": ""},
          "item": [
              {"path": "label", "label": "Подпись", "type": "text"},
              {"path": "value", "label": "Значение", "type": "text"},
              {"path": "href", "label": "Ссылка (если нужна)", "type": "text"},
              _svg_icon(None),
          ]},
         {"path": "contacts.buttons", "label": "Кнопки связи", "titleField": "label",
          "tpl": {"label": "", "href": "", "cls": "c-call", "external": False, "icon": ""},
          "item": [
              {"path": "label", "label": "Текст", "type": "text"},
              {"path": "href", "label": "Ссылка", "type": "text"},
              {"path": "cls", "label": "Вид", "type": "select", "options": ["c-call", "c-tg", "c-max"]},
              {"path": "external", "label": "Открывать в новой вкладке", "type": "check"},
              _svg_icon(None),
          ]},
     ]},

    {"id": "footer", "group": "Контент", "title": "Подвал", "fields": [
        {"path": "footer.line", "label": "Строка описания", "type": "text"},
        {"path": "footer.copyright", "label": "Копирайт", "type": "text"},
     ],
     "lists": [
         {"path": "footer.socials", "label": "Кнопки соцсетей", "titleField": "label",
          "tpl": {"label": "", "href": "", "icon": ""},
          "item": [
              {"path": "label", "label": "Подпись (title)", "type": "text"},
              {"path": "href", "label": "Ссылка", "type": "text"},
              _svg_icon(None),
          ]},
     ]},

    {"id": "cookie", "group": "Контент", "title": "Cookie-баннер", "fields": [
        {"path": "cookie.text", "label": "Текст", "type": "textarea", "rows": 2},
        {"path": "cookie.button", "label": "Кнопка", "type": "text"},
     ]},

    {"id": "page404", "group": "Контент", "title": "Страница 404", "fields": [
        {"path": "page404.title", "label": "Заголовок", "type": "text"},
        {"path": "page404.text", "label": "Текст", "type": "textarea", "rows": 2},
        {"path": "page404.button", "label": "Кнопка", "type": "text"},
     ]},

    {"id": "tools", "group": "Инструменты", "title": "Инструменты и связь",
     "hint": "Проверка связей, бэкап контента, генерация SEO через AI.",
     "fields": [
         {"type": "buttons", "buttons": [
             {"act": "status", "label": "Проверить связи", "cls": "btn-gold"},
             {"act": "ai-seo", "label": "Сгенерировать SEO через AI", "cls": ""},
             {"act": "export", "label": "Скачать бэкап (JSON)", "cls": ""},
             {"act": "import", "label": "Загрузить бэкап", "cls": ""},
             {"act": "open", "label": "Открыть сайт", "cls": ""},
             {"act": "reload", "label": "Отменить изменения", "cls": "btn-red"},
         ]},
         {"type": "info", "text": "<div id=\"toolsOut\" class=\"info\">Нажмите «Проверить связи», чтобы увидеть состояние базы, хранилища и AI.</div>"},
     ]},
]

_SCHEMA_JSON = json.dumps(ADMIN_SCHEMA, ensure_ascii=False)


# ============================================================
#  АДМИНКА (HTML)
# ============================================================
ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход — Кухни Островский</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:linear-gradient(135deg,#0e0c09,#1a1611);color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.2);border-radius:20px;padding:42px 38px;width:100%;max-width:420px}
h1{font-family:Georgia,serif;font-size:28px;color:#fff;margin-bottom:8px;text-align:center}
p.sub{color:#b9ad9a;font-size:13.5px;text-align:center;margin-bottom:28px}
label{display:block;color:#eccfa0;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:600}
input{width:100%;padding:14px 16px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;font-size:15px;margin-bottom:18px}
input:focus{outline:none;border-color:#d4af6a}
button{width:100%;padding:15px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;border:none;border-radius:12px;cursor:pointer;text-transform:uppercase;letter-spacing:1px;font-family:inherit}
.err{background:rgba(220,60,60,.14);border:1px solid rgba(220,60,60,.4);color:#ff9a9a;padding:12px;border-radius:10px;font-size:13px;margin-bottom:18px;text-align:center}
.hint{margin-top:18px;color:#6f6659;font-size:11.5px;text-align:center;line-height:1.5}
</style></head><body>
<form class="card" method="POST" action="/admin/login">
<h1>Кухни Островский</h1><p class="sub">Панель управления сайтом</p>__ERROR__
<label>Логин</label><input type="text" name="login" required autofocus autocomplete="username">
<label>Пароль</label><input type="password" name="password" required autocomplete="current-password">
<button>Войти</button>
<div class="hint">Логин и пароль задаются переменными ADMIN_LOGIN и ADMIN_PASSWORD на хостинге.</div>
</form></body></html>"""


ADMIN_HTML = r"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Админка — Кухни Островский</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0e0c09;color:#f5efe3;line-height:1.5}
header{background:rgba(14,12,9,.96);border-bottom:1px solid rgba(236,207,160,.16);padding:12px 18px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:20;backdrop-filter:blur(10px)}
.brand{font-family:Georgia,serif;font-size:19px;color:#eccfa0;display:flex;align-items:center;gap:10px}.brand span{font-size:11px;opacity:.65;font-family:system-ui;letter-spacing:1px;text-transform:uppercase}
.actions{display:flex;gap:8px;flex-wrap:wrap}
.btn{padding:9px 15px;border-radius:9px;border:1px solid rgba(236,207,160,.16);background:rgba(255,255,255,.04);color:#f5efe3;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;font-family:inherit;display:inline-flex;align-items:center;gap:6px;transition:.2s}
.btn:hover{border-color:#d4af6a;background:rgba(212,175,106,.1)}
.btn:disabled{opacity:.5;cursor:default}
.btn-gold{background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;border:none}
.btn-red{background:rgba(220,60,60,.14);border-color:rgba(220,60,60,.35);color:#ff9a9a}
.btn.pulse{box-shadow:0 0 0 0 rgba(236,207,160,.7);animation:pulse 1.6s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(236,207,160,.55)}70%{box-shadow:0 0 0 14px rgba(236,207,160,0)}100%{box-shadow:0 0 0 0 rgba(236,207,160,0)}}
.layout{display:flex;min-height:calc(100vh - 58px)}
nav.side{width:232px;background:rgba(0,0,0,.3);border-right:1px solid rgba(236,207,160,.16);padding:10px 0 40px;flex-shrink:0;overflow-y:auto;max-height:calc(100vh - 58px);position:sticky;top:58px}
nav.side a{display:block;padding:10px 18px;color:#b9ad9a;font-size:13.5px;cursor:pointer;border-left:3px solid transparent}
nav.side a:hover{color:#fff;background:rgba(255,255,255,.04)}
nav.side a.active{color:#eccfa0;border-left-color:#d4af6a;background:rgba(212,175,106,.08)}
.nav-group{padding:14px 18px 6px;font-size:10.5px;letter-spacing:2px;text-transform:uppercase;color:#6f6659;font-weight:700}
main{flex:1;padding:22px 26px 120px;max-width:1080px;min-width:0}
h2{font-family:Georgia,serif;font-size:23px;color:#fff;margin-bottom:6px}
p.hint{color:#b9ad9a;font-size:13px;margin-bottom:18px}
.field{margin-bottom:14px}
.field>label{display:flex;align-items:center;gap:8px;color:#eccfa0;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:6px;font-weight:700}
.field input,.field textarea,.field select{width:100%;padding:10px 13px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.12);border-radius:9px;color:#fff;font-size:14px;font-family:inherit}
.field textarea{resize:vertical;min-height:60px;line-height:1.5}
.field input:focus,.field textarea:focus,.field select:focus{outline:none;border-color:#d4af6a}
.field .mono{font-family:ui-monospace,Consolas,monospace;font-size:12.5px}
.fhint{color:#6f6659;font-size:11.5px;margin-top:5px}
.img-row{display:flex;gap:6px;align-items:stretch}
.img-row input{flex:1}
.prev{margin-top:8px}.prev img{max-width:190px;border-radius:8px;display:block;border:1px solid rgba(255,255,255,.1)}
.color-row{display:flex;gap:8px;align-items:center}.color-row input[type=color]{width:52px;height:40px;padding:2px;cursor:pointer}
.chk{display:flex;align-items:center;gap:8px;font-size:14px;color:#d8cfbe}.chk input{width:18px;height:18px;accent-color:#d4af6a}
.ai{padding:2px 8px;font-size:12px;border-radius:7px;background:rgba(212,175,106,.14);border-color:rgba(212,175,106,.4);color:#eccfa0}
.mini{padding:5px 10px;font-size:12px;border-radius:7px}
.item{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:15px;margin-bottom:12px}
.item-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:8px;flex-wrap:wrap}
.item-head strong{color:#eccfa0;font-size:13px;word-break:break-word}
.item-tools{display:flex;gap:6px}
.list-head{display:flex;justify-content:space-between;align-items:baseline;margin:22px 0 10px;border-top:1px solid rgba(236,207,160,.16);padding-top:14px}
.list-head strong{color:#fff;font-family:Georgia,serif;font-size:17px}
.list-head .muted{color:#6f6659;font-size:12px}
.info{background:rgba(212,175,106,.07);border:1px solid rgba(212,175,106,.22);border-radius:11px;padding:14px 16px;font-size:13px;color:#e0d6c4;margin-bottom:14px;white-space:pre-wrap}
.info b{color:#eccfa0}
.status{font-size:11.5px;padding:4px 10px;border-radius:7px;display:inline-block;font-weight:600}
.status.ok{background:rgba(80,200,120,.15);color:#7ee0a0;border:1px solid rgba(80,200,120,.4)}
.status.bad{background:rgba(220,60,60,.15);color:#ff9a9a;border:1px solid rgba(220,60,60,.4)}
.status.saving{background:rgba(212,175,106,.2);color:#eccfa0;border:1px solid rgba(212,175,106,.5)}
.toast{position:fixed;bottom:20px;left:50%;transform:translate(-50%,150%);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;padding:12px 22px;border-radius:11px;font-weight:700;font-size:13.5px;z-index:9999;transition:transform .35s;max-width:92vw;text-align:center}
.toast.show{transform:translate(-50%,0)}.toast.err{background:linear-gradient(135deg,#ff8a8a,#e04a4a);color:#fff}
.modal{position:fixed;inset:0;background:rgba(6,5,3,.86);display:none;align-items:center;justify-content:center;z-index:9000;padding:18px}
.modal.open{display:flex}
.modal-card{background:#15120d;border:1px solid rgba(236,207,160,.22);border-radius:16px;width:min(920px,100%);max-height:86vh;display:flex;flex-direction:column}
.modal-head{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;border-bottom:1px solid rgba(236,207,160,.16)}
.media-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;padding:16px;overflow-y:auto}
.media-grid button{padding:0;border:1px solid rgba(255,255,255,.12);border-radius:10px;overflow:hidden;background:#0b0907;cursor:pointer}
.media-grid img{width:100%;height:110px;object-fit:cover;display:block}
.media-grid .nm{font-size:10.5px;color:#b9ad9a;padding:5px;word-break:break-all}
@media(max-width:820px){.layout{flex-direction:column}nav.side{width:100%;max-height:none;position:static;display:flex;overflow-x:auto;padding:8px;border-right:none;border-bottom:1px solid rgba(236,207,160,.16)}nav.side a{white-space:nowrap;border-left:none;border-bottom:2px solid transparent;padding:8px 12px}nav.side a.active{border-left:none;border-bottom-color:#d4af6a}.nav-group{display:none}main{padding:16px 14px 100px}}
</style></head><body>
<header>
<div class="brand">Кухни Островский<span>CMS</span><span class="status" id="status">Загрузка…</span></div>
<div class="actions">
<a class="btn" href="/" target="_blank">Сайт</a>
<button class="btn" id="reloadBtn" title="Отменить изменения">↻</button>
<button class="btn btn-gold" id="saveBtn" title="Ctrl+S">💾 Сохранить</button>
<a class="btn btn-red" href="/admin/logout">Выйти</a>
</div>
</header>
<div class="layout"><nav class="side" id="side"></nav><main id="main"><p class="hint">Загрузка…</p></main></div>
<div class="toast" id="toast"></div>
<div class="modal" id="modal"><div class="modal-card"><div class="modal-head"><strong>Медиатека (Supabase Storage)</strong><button class="btn mini" id="mClose">✕ Закрыть</button></div><div class="media-grid" id="mediaGrid"></div></div></div>
<input type="file" id="importFile" accept="application/json,.json" hidden>
<script>
var SCHEMA=__SCHEMA__, DATA=null, TAB=(__SCHEMA__[0]||{}).id, dirty=false, mediaTarget=null;

function q(s){return document.querySelector(s)}
function qa(s){return Array.prototype.slice.call(document.querySelectorAll(s))}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function getPath(o,p){if(!p)return o;return p.split('.').reduce(function(a,k){if(a==null)return undefined;if(Array.isArray(a))return a[parseInt(k,10)];return a[k]},o)}
function setPath(o,p,v){var a=p.split('.'),c=o;for(var i=0;i<a.length-1;i++){var k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k]}c[a[a.length-1]]=v}
function toast(m,bad){var t=q('#toast');t.textContent=m;t.classList.toggle('err',!!bad);t.classList.add('show');clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove('show')},3000)}
function setStatus(txt,cls){var el=q('#status');el.className='status '+(cls||'ok');el.textContent=txt}
function setDirty(v){dirty=v;document.title=(v?'● ':'')+'Админка — Кухни Островский';q('#saveBtn').classList.toggle('pulse',v)}
function api(url,opts){return fetch(url,Object.assign({credentials:'same-origin'},opts||{})).then(function(r){if(r.status===401){location.href='/admin/login';throw new Error('Нужно войти')}return r.json()})}
function normColor(v){v=String(v||'').trim();return /^#[0-9a-f]{6}$/i.test(v)?v:'#000000'}

function render(){
  var groups={},order=[];
  SCHEMA.forEach(function(t){if(!groups[t.group]){groups[t.group]=[];order.push(t.group)}groups[t.group].push(t)});
  var nav='';
  order.forEach(function(g){
    nav+='<div class="nav-group">'+esc(g)+'</div>';
    groups[g].forEach(function(t){nav+='<a data-tab="'+t.id+'"'+(t.id===TAB?' class="active"':'')+'>'+esc(t.title)+'</a>'});
  });
  q('#side').innerHTML=nav;
  var tab=SCHEMA.filter(function(t){return t.id===TAB})[0]||SCHEMA[0];
  var h='<h2>'+esc(tab.title)+'</h2>'+(tab.hint?'<p class="hint">'+tab.hint+'</p>':'');
  (tab.fields||[]).forEach(function(f){h+=fieldHTML(f,'')});
  (tab.lists||[]).forEach(function(l){h+=listHTML(l)});
  q('#main').innerHTML=h;
  bind();
  window.scrollTo(0,0);
}

function aiBtn(p,task){return '<button class="btn mini ai" data-ai="'+task+'" data-ai-path="'+p+'" title="Сгенерировать через AI">✨</button>'}

function fieldHTML(f,base){
  var p=f.path?(base?base+'.'+f.path:f.path):base;
  if(f.type==='info')return '<div class="info">'+(f.text||'')+'</div>';
  if(f.type==='buttons'){
    var b='<div class="actions" style="margin-bottom:14px">';
    (f.buttons||[]).forEach(function(x){b+='<button class="btn '+(x.cls||'')+'" data-act="'+x.act+'">'+esc(x.label)+'</button>'});
    return b+'</div>';
  }
  var v=getPath(DATA,p),inp;
  if(f.type==='image'){
    return '<div class="field"><label>'+esc(f.label)+'</label><div class="img-row">'
      +'<input type="text" data-path="'+p+'" value="'+esc(v)+'" placeholder="https://… или загрузите файл">'
      +'<label class="btn mini" title="Загрузить файл">📁<input type="file" accept="image/*" data-upload="'+p+'" hidden></label>'
      +'<button class="btn mini" data-media="'+p+'" title="Выбрать из медиатеки">🗂</button></div>'
      +'<div class="prev" data-prev="'+p+'">'+(v?'<img src="'+esc(v)+'" loading="lazy">':'')+'</div>'
      +(f.hint?'<div class="fhint">'+f.hint+'</div>':'')+'</div>';
  }
  if(f.type==='textarea')inp='<textarea data-path="'+p+'" rows="'+(f.rows||3)+'"'+(f.mono?' class="mono"':'')+' placeholder="'+esc(f.placeholder||'')+'">'+esc(v)+'</textarea>';
  else if(f.type==='check')inp='<label class="chk"><input type="checkbox" data-path="'+p+'"'+(v?' checked':'')+'> '+(f.chkLabel||'включено')+'</label>';
  else if(f.type==='select')inp='<select data-path="'+p+'">'+(f.options||[]).map(function(o){return '<option value="'+esc(o)+'"'+(String(v)===o?' selected':'')+'>'+esc(o)+'</option>'}).join('')+'</select>';
  else if(f.type==='color')inp='<div class="color-row"><input type="color" data-path="'+p+'" value="'+esc(normColor(v))+'"><input type="text" data-path="'+p+'" value="'+esc(v)+'"></div>';
  else inp='<input type="text" data-path="'+p+'" value="'+esc(v)+'" placeholder="'+esc(f.placeholder||'')+'">';
  return '<div class="field">'+(f.label?'<label>'+esc(f.label)+(f.ai?aiBtn(p,f.ai):'')+'</label>':'')+inp+(f.hint?'<div class="fhint">'+f.hint+'</div>':'')+'</div>';
}

function listHTML(l){
  var arr=getPath(DATA,l.path); if(!Array.isArray(arr))arr=[];
  var h='<div class="list-head"><strong>'+esc(l.label)+' ('+arr.length+')</strong><span class="muted">↑↓ — порядок</span></div>';
  arr.forEach(function(item,i){
    var t=l.titleField?String(getPath(item,l.titleField)||''):'';
    h+='<div class="item"><div class="item-head"><strong>#'+(i+1)+(t?' · '+esc(t):'')+'</strong><div class="item-tools">'
      +'<button class="btn mini" data-mv="'+l.path+'" data-i="'+i+'" data-d="-1">↑</button>'
      +'<button class="btn mini" data-mv="'+l.path+'" data-i="'+i+'" data-d="1">↓</button>'
      +'<button class="btn btn-red mini" data-del="'+l.path+'" data-i="'+i+'">Удалить</button></div></div>';
    (l.item||[]).forEach(function(f){h+=fieldHTML(f,l.path+'.'+i)});
    h+='</div>';
  });
  var tpl=typeof l.tpl==='string'?l.tpl:JSON.stringify(l.tpl||{});
  h+='<button class="btn" data-add="'+l.path+'" data-tpl="'+esc(tpl)+'">+ Добавить</button>';
  return h;
}

function bind(){
  qa('[data-path]').forEach(function(el){
    var handler=function(){
      var p=el.dataset.path;
      var val=(el.type==='checkbox')?!!el.checked:el.value;
      setPath(DATA,p,val); setDirty(true);
      qa('[data-path="'+p+'"]').forEach(function(o){if(o!==el){if(o.type==='checkbox')o.checked=!!val;else o.value=val}});
      var pv=q('[data-prev="'+p+'"]'); if(pv)pv.innerHTML=val?'<img src="'+esc(val)+'" loading="lazy">':'';
    };
    el.addEventListener(el.tagName==='SELECT'||el.type==='checkbox'?'change':'input',handler);
  });
  qa('[data-upload]').forEach(function(inp){inp.addEventListener('change',function(){upload(inp)})});
  qa('[data-media]').forEach(function(b){b.addEventListener('click',function(){openMedia(b.dataset.media)})});
  qa('[data-ai]').forEach(function(b){b.addEventListener('click',function(){runAI(b)})});
  qa('[data-del]').forEach(function(b){b.addEventListener('click',function(){delItem(b.dataset.del,+b.dataset.i)})});
  qa('[data-mv]').forEach(function(b){b.addEventListener('click',function(){moveItem(b.dataset.mv,+b.dataset.i,+b.dataset.d)})});
  qa('[data-add]').forEach(function(b){b.addEventListener('click',function(){addItem(b.dataset.add,b.dataset.tpl)})});
  qa('[data-act]').forEach(function(b){b.addEventListener('click',function(){doAction(b.dataset.act)})});
}

function addItem(path,tpl){
  var arr=getPath(DATA,path); if(!Array.isArray(arr)){arr=[];setPath(DATA,path,arr)}
  var item; try{item=JSON.parse(tpl)}catch(e){item=tpl}
  arr.push(item); setDirty(true); render();
}
function delItem(path,i){
  if(!confirm('Удалить этот элемент?'))return;
  var arr=getPath(DATA,path); arr.splice(i,1); setDirty(true); render();
}
function moveItem(path,i,d){
  var arr=getPath(DATA,path),j=i+d;
  if(j<0||j>=arr.length)return;
  var x=arr[i];arr[i]=arr[j];arr[j]=x;
  setDirty(true); render();
}
function refreshField(p,val){
  qa('[data-path="'+p+'"]').forEach(function(o){o.value=val});
  var pv=q('[data-prev="'+p+'"]'); if(pv)pv.innerHTML=val?'<img src="'+esc(val)+'" loading="lazy">':'';
}

function upload(inp){
  var p=inp.dataset.upload,f=inp.files[0];
  if(!f)return;
  if(f.size>8*1024*1024){toast('Файл больше 8 МБ',true);return}
  var fd=new FormData(); fd.append('file',f);
  toast('Загружаю…');
  fetch('/admin/api/upload',{method:'POST',body:fd,credentials:'same-origin'})
    .then(function(r){return r.json()})
    .then(function(j){
      if(j&&j.url){setPath(DATA,p,j.url);setDirty(true);refreshField(p,j.url);toast(j.storage?'Загружено в Supabase Storage':'Загружено (data-URL)')}
      else toast('Не загрузилось: '+((j&&j.error)||'ошибка'),true);
    }).catch(function(e){toast('Ошибка: '+e.message,true)});
  inp.value='';
}

function runAI(b){
  var p=b.dataset.aiPath,task=b.dataset.ai,cur=String(getPath(DATA,p)||'');
  b.disabled=true; var old=b.textContent; b.textContent='⏳';
  api('/admin/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:task,path:p,value:cur})})
    .then(function(j){
      if(j&&j.text){setPath(DATA,p,j.text);setDirty(true);refreshField(p,j.text);toast('AI ('+j.provider+'): готово')}
      else toast('AI: '+((j&&j.error)||'пустой ответ'),true);
    })
    .catch(function(e){toast('AI ошибка: '+e.message,true)})
    .then(function(){b.disabled=false;b.textContent=old});
}

function openMedia(p){
  mediaTarget=p;
  q('#mediaGrid').innerHTML='<p class="hint" style="padding:16px">Загружаю список…</p>';
  q('#modal').classList.add('open');
  api('/admin/api/media').then(function(j){
    if(!j||!j.items||!j.items.length){q('#mediaGrid').innerHTML='<p class="hint" style="padding:16px">В хранилище пока нет файлов. Загрузите первый через кнопку 📁.</p>';return}
    q('#mediaGrid').innerHTML=j.items.map(function(it){
      return '<button data-pick="'+esc(it.url)+'"><img src="'+esc(it.url)+'" loading="lazy"><div class="nm">'+esc(it.name)+'</div></button>';
    }).join('');
    qa('[data-pick]').forEach(function(b){b.addEventListener('click',function(){
      setPath(DATA,mediaTarget,b.dataset.pick);setDirty(true);refreshField(mediaTarget,b.dataset.pick);
      q('#modal').classList.remove('open');toast('Картинка выбрана');
    })});
  }).catch(function(e){q('#mediaGrid').innerHTML='<p class="hint" style="padding:16px">Ошибка: '+esc(e.message)+'</p>'});
}

function doAction(act){
  if(act==='open'){window.open('/','_blank');return}
  if(act==='reload'){if(!confirm('Отменить несохранённые изменения?'))return;load();return}
  if(act==='export'){location.href='/admin/api/export';return}
  if(act==='import'){q('#importFile').click();return}
  if(act==='status'){showStatus();return}
  if(act==='ai-seo'){aiSeo();return}
}

function out(html){var el=q('#toolsOut'); if(el)el.innerHTML=html; else toast('Откройте вкладку «Инструменты»')}

function showStatus(){
  out('Проверяю…');
  api('/admin/api/status').then(function(j){
    function row(ok,txt){return '<div>'+(ok?'✅':'❌')+' '+txt+'</div>'}
    var size=Math.round((j.size||0)/1024);
    var html='<b>Состояние</b>\n'
      +row(j.db_read,'Чтение Supabase: '+(j.db_read?'OK':'ошибка'))
      +row(j.db_write!==false,'Запись Supabase: '+(j.db_write===false?'была ошибка':'OK'))
      +row(j.storage,'Хранилище картинок: '+(j.storage?('бакет '+j.bucket):'недоступно (картинки будут data-URL)'))
      +row(j.ai.yandex||j.ai.gigachat,'AI: '+(j.ai.yandex?'YandexGPT готов':'YandexGPT нет ключа')+', '+(j.ai.gigachat?'GigaChat готов':'GigaChat нет ключа'))
      +'\n<b>Контент</b>\n'
      +'<div>Размер данных: '+size+' КБ · работ: '+(j.counts.works||0)+' · отзывов: '+(j.counts.reviews||0)+' · услуг: '+(j.counts.services||0)+'</div>'
      +'<div>Домен: '+esc(j.domain)+' · страниц в sitemap: '+j.sitemap_urls+'</div>';
    if(j.ai_error)html+='\n<div>AI: '+esc(j.ai_error)+'</div>';
    out(html);
  }).catch(function(e){out('Ошибка проверки: '+esc(e.message))});
}

function aiSeo(){
  var tasks=[['seo.title','seo_title'],['seo.description','seo_description'],['seo.keywords','seo_keywords']];
  out('Генерирую SEO… (может занять 10-30 секунд)');
  var i=0,done=[];
  (function next(){
    if(i>=tasks.length){out('<b>SEO обновлён</b>\n'+done.join('\n')+'\n\nНе забудьте нажать «Сохранить».');return}
    var p=tasks[i][0],t=tasks[i][1];
    api('/admin/api/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:t,path:p,value:String(getPath(DATA,p)||'')})})
      .then(function(j){
        if(j&&j.text){setPath(DATA,p,j.text);setDirty(true);done.push('• '+p+': '+esc(j.text.slice(0,90)))}
        else done.push('• '+p+': ошибка '+esc((j&&j.error)||''));
      }).catch(function(e){done.push('• '+p+': '+esc(e.message))})
      .then(function(){i++;next()});
  })();
}

function save(){
  if(!DATA){toast('Данные ещё не загрузились',true);return}
  setStatus('Сохранение…','saving');
  fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)})
    .then(function(r){return r.json()})
    .then(function(j){
      if(j&&j.ok){setStatus('✅ Сохранено','ok');setDirty(false);toast('Сохранено в Supabase')}
      else{setStatus('❌ Не сохранилось','bad');toast('Ошибка записи! Проверьте SUPABASE_SERVICE_KEY',true)}
    }).catch(function(e){setStatus('Ошибка','bad');toast('Ошибка: '+e.message,true)});
}

function load(){
  api('/admin/api/data').then(function(j){
    if(!j||typeof j!=='object'){throw new Error('пустой ответ')}
    DATA=j;setDirty(false);render();setStatus('Готово','ok');
  }).catch(function(e){
    setStatus('Ошибка загрузки','bad');
    q('#main').innerHTML='<h2>Не удалось загрузить данные</h2><p class="hint">'+esc(e.message)+'</p><p class="hint">Проверьте SUPABASE_URL и SUPABASE_SERVICE_KEY на хостинге, затем обновите страницу.</p>';
  });
}

document.addEventListener('click',function(e){
  var tab=e.target.closest('nav.side a[data-tab]');
  if(tab){TAB=tab.dataset.tab;render();return}
  if(e.target.closest('#saveBtn')){save();return}
  if(e.target.closest('#reloadBtn')){doAction('reload');return}
  if(e.target.closest('#mClose')||e.target.id==='modal'){q('#modal').classList.remove('open');return}
});
q('#importFile').addEventListener('change',function(){
  var f=this.files[0]; if(!f)return;
  var r=new FileReader();
  r.onload=function(){
    try{
      var obj=JSON.parse(r.result);
      if(!obj||typeof obj!=='object')throw new Error('это не объект');
      DATA=obj;setDirty(true);render();toast('Бэкап загружен — нажмите «Сохранить»');
    }catch(err){toast('Не разобрал JSON: '+err.message,true)}
  };
  r.readAsText(f,'utf-8');
  this.value='';
});
document.addEventListener('keydown',function(e){
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();save()}
  if(e.key==='Escape')q('#modal').classList.remove('open');
});
window.addEventListener('beforeunload',function(e){if(dirty){e.preventDefault();e.returnValue=''}});
load();
</script></body></html>"""

ADMIN_HTML = ADMIN_HTML.replace("__SCHEMA__", _SCHEMA_JSON)

STATIC_EXT = {".html", ".htm", ".txt", ".xml", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico",
              ".css", ".js", ".json", ".webmanifest", ".woff", ".woff2", ".pdf", ".mp4"}
STATIC_BLOCK = {"mebel.py", "requirements.txt", "Dockerfile", "robots.txt", "sitemap.xml", "page.html"}
MIME = {".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".txt": "text/plain; charset=utf-8",
        ".xml": "application/xml; charset=utf-8", ".svg": "image/svg+xml", ".png": "image/png",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
        ".ico": "image/x-icon", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8", ".webmanifest": "application/manifest+json; charset=utf-8",
        ".woff": "font/woff", ".woff2": "font/woff2", ".pdf": "application/pdf", ".mp4": "video/mp4"}


# ============================================================
#  HTTP
# ============================================================
def _parse_multipart(body, boundary):
    if not body or not boundary:
        return None, None
    parts = body.split(b"--" + boundary)
    for p in parts:
        if b"Content-Disposition" not in p:
            continue
        head, _, data = p.partition(b"\r\n\r\n")
        if not data:
            continue
        data = data.rstrip(b"\r\n")
        if data.endswith(b"--"):
            data = data[:-2].rstrip(b"\r\n")
        name = ""
        m = re.search(rb'filename="([^"]*)"', head)
        if m:
            name = m.group(1).decode("utf-8", "ignore")
        return name, data
    return None, None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "OstrovskyCMS/3.0"
    _head_only = False

    def _tok(self):
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

    def _admin(self):
        return _check_session(self._tok())

    def _ip(self):
        fwd = self.headers.get("X-Forwarded-For", "")
        return (fwd.split(",")[0].strip() if fwd else self.client_address[0])

    def _is_https(self):
        return self.headers.get("X-Forwarded-Proto", "").lower() == "https"

    def _send(self, code, body, ctype="text/plain; charset=utf-8", cache="no-cache", gzip_ok=True):
        data = body.encode("utf-8") if isinstance(body, str) else body
        etag = '"' + hashlib.sha256(data).hexdigest()[:20] + '"'
        if code == 200 and self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache)
            self.end_headers()
            return
        ae = self.headers.get("Accept-Encoding", "") or ""
        gzipped = False
        if gzip_ok and isinstance(body, str) and "gzip" in ae and len(data) > 700:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz:
                gz.write(data)
            data = buf.getvalue()
            gzipped = True
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if gzipped:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag)
        self.send_header("X-Robots-Tag", "noindex" if self.path.startswith("/admin") else "all")
        self.end_headers()
        if not self._head_only:
            try:
                self.wfile.write(data)
            except Exception:
                pass

    def _redir(self, loc, cookie=None):
        self.send_response(302)
        self.send_header("Location", loc)
        self.send_header("Cache-Control", "no-cache")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", "0") or 0)
        except Exception:
            n = 0
        if n <= 0 or n > MAX_UPLOAD * 4:
            return b""
        return self.rfile.read(n)

    def _cookie(self, token):
        c = "admin_session={}; Path=/; Max-Age={}; HttpOnly; SameSite=Lax".format(token, SESSION_TTL)
        if self._is_https():
            c += "; Secure"
        return c

    def do_HEAD(self):
        self._head_only = True
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/img":
            self._route_img()
            return
        if path == "/healthz":
            self._send(200, "ok", "text/plain; charset=utf-8")
            return
        if path == "/admin/login":
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", ""), "text/html; charset=utf-8")
            return
        if path == "/admin/logout":
            _drop_session(self._tok())
            self._redir("/admin/login", "admin_session=; Path=/; Max-Age=0; HttpOnly")
            return
        if path == "/admin/api/data":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            self._json(load_fresh())
            return
        if path == "/admin/api/export":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            blob = json.dumps(load_fresh(), ensure_ascii=False, indent=1).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition",
                             'attachment; filename="mebel-backup-{}.json"'.format(date.today().isoformat()))
            self.send_header("Content-Length", str(len(blob)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            if not self._head_only:
                self.wfile.write(blob)
            return
        if path == "/admin/api/media":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            self._json({"items": _storage_list(), "bucket": BUCKET})
            return
        if path == "/admin/api/status":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            self._json(self._status_payload())
            return
        if path == "/admin":
            if not self._admin():
                self._redir("/admin/login")
                return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8")
            return

        if path in ("/", "/index.html"):
            self._send(200, render_site(), "text/html; charset=utf-8", "no-cache")
            return
        if path == "/robots.txt":
            self._send(200, build_robots(load_data()), "text/plain; charset=utf-8", "public, max-age=3600")
            return
        if path == "/sitemap.xml":
            self._send(200, build_sitemap(load_data()), "application/xml; charset=utf-8", "public, max-age=3600")
            return
        if path == "/manifest.webmanifest":
            self._send(200, build_manifest(load_data()), "application/manifest+json; charset=utf-8", "public, max-age=86400")
            return
        if path in ("/favicon.ico", "/favicon-16x16.png", "/favicon-32x32.png",
                    "/apple-touch-icon.png", "/favicon-192x192.png"):
            self._route_favicon(path)
            return
        if self._serve_static(path):
            return
        self._send(404, build_404(load_data()), "text/html; charset=utf-8")

    def do_POST(self):
        path = self.path.split("?", 1)[0]

        if path == "/admin/login":
            ip = self._ip()
            if _login_blocked(ip):
                self._send(200, ADMIN_LOGIN_HTML.replace(
                    "__ERROR__", '<div class="err">Слишком много попыток. Подождите 10 минут.</div>'),
                           "text/html; charset=utf-8")
                return
            raw = self._body().decode("utf-8", "ignore")
            p = parse_qs(raw)
            login = (p.get("login") or [""])[0].strip()
            pw = (p.get("password") or [""])[0]
            if (hmac.compare_digest(login.encode("utf-8"), ADMIN_LOGIN_ENV.encode("utf-8"))
                    and hmac.compare_digest(pw.encode("utf-8"), ADMIN_PASSWORD_ENV.encode("utf-8"))):
                _login_note(ip, True)
                self._redir("/admin", self._cookie(_new_session()))
            else:
                _login_note(ip, False)
                self._send(200, ADMIN_LOGIN_HTML.replace(
                    "__ERROR__", '<div class="err">Неверный логин или пароль</div>'),
                           "text/html; charset=utf-8")
            return

        if path == "/admin/api/save":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            try:
                obj = json.loads(self._body().decode("utf-8"))
            except Exception:
                self._json({"error": "bad json"}, 400)
                return
            if not isinstance(obj, dict):
                self._json({"error": "not an object"}, 400)
                return
            self._json({"ok": bool(save_data(obj))})
            return

        if path == "/admin/api/upload":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            body = self._body()
            if not body:
                self._json({"error": "пустой файл"}, 400)
                return
            if len(body) > MAX_UPLOAD:
                self._json({"error": "файл больше 8 МБ"}, 413)
                return
            ctype = self.headers.get("Content-Type", "")
            blob, fname = None, "upload"
            if "multipart/form-data" in ctype:
                m = re.search(r"boundary=([^;]+)", ctype)
                if m:
                    fname, blob = _parse_multipart(body, m.group(1).strip().strip('"').encode())
            if not blob:
                blob, fname = body, "upload.jpg"
            mime = "image/jpeg"
            if blob[:8] == b"\x89PNG\r\n\x1a\n":
                mime = "image/png"
            elif blob[:6] in (b"GIF87a", b"GIF89a"):
                mime = "image/gif"
            elif blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
                mime = "image/webp"
            elif blob[:5] == b"<?xml" or blob[:4] == b"<svg":
                mime = "image/svg+xml"
            url = _storage_upload(fname, blob, mime)
            if url:
                self._json({"url": url, "storage": True, "bucket": BUCKET})
            else:
                self._json({"url": "data:{};base64,{}".format(mime, base64.b64encode(blob).decode("ascii")),
                            "storage": False, "warning": "Storage недоступен — картинка сохранена как data-URL"})
            return

        if path == "/admin/api/ai":
            if not self._admin():
                self._json({"error": "no auth"}, 401)
                return
            try:
                req = json.loads(self._body().decode("utf-8") or "{}")
            except Exception:
                req = {}
            task = str(req.get("task") or "improve")
            value = str(req.get("value") or "")
            data = load_data()
            system, user = _ai_ask(data, task, req.get("path"), value)
            text, provider, err = _ai_generate(system, user, 700)
            if text:
                self._json({"text": text, "provider": provider})
            else:
                self._json({"error": err or "AI недоступен"}, 200)
            return

        self._json({"error": "not found"}, 404)

    def _route_img(self):
        qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
        u = (qs.get("u") or [""])[0]
        if not u:
            self._send(404, "no url")
            return
        try:
            pad = "=" * (-len(u) % 4)
            url = base64.urlsafe_b64decode(u + pad).decode("utf-8")
        except Exception:
            self._send(400, "bad")
            return
        host = urllib.parse.urlparse(url).hostname or ""
        if not url.startswith("https://") or not host.endswith("vkuserphoto.ru"):
            self._send(403, "forbidden")
            return
        blob, ct = _fetch_image(url)
        if blob is None:
            self._redir(url)
            return
        self._send(200, blob, ct, "public, max-age=604800", gzip_ok=False)

    def _route_favicon(self, path):
        if path == "/favicon.ico":
            d = get_favicon()
            if _ic["ico"]:
                self._send(200, _ic["ico"], "image/x-icon", "public, max-age=86400", gzip_ok=False)
            elif d:
                self._send(200, d, "image/x-icon", "public, max-age=86400", gzip_ok=False)
            else:
                self._redir(FAVICON_URL)
            return
        key = {"/favicon-16x16.png": "png16", "/favicon-32x32.png": "png32",
               "/apple-touch-icon.png": "png180", "/favicon-192x192.png": "png192"}[path]
        if _ic.get(key) is None:
            get_favicon()
        if _ic.get(key):
            self._send(200, _ic[key], "image/png", "public, max-age=86400", gzip_ok=False)
        else:
            self._redir(FAVICON_URL)

    def _serve_static(self, path):
        rel = urllib.parse.unquote(path).lstrip("/")
        if not rel or rel.startswith(".") or ".." in rel.split("/"):
            return False
        if rel in STATIC_BLOCK:
            return False
        ext = os.path.splitext(rel)[1].lower()
        if ext not in STATIC_EXT:
            return False
        fp = os.path.join(ROOT, *rel.split("/"))
        if not os.path.isfile(fp):
            return False
        try:
            with open(fp, "rb") as f:
                blob = f.read()
        except Exception:
            return False
        self._send(200, blob, MIME.get(ext, "application/octet-stream"), "public, max-age=86400", gzip_ok=False)
        return True

    def _status_payload(self):
        data = load_data()
        counts = {}
        for key in ("works", "reviews", "services", "process", "guarantees", "cities"):
            items = (data.get(key) or {}).get("items")
            counts[key] = len(items) if isinstance(items, list) else 0
        return {
            "db_read": bool(_db_state.get("read")),
            "db_write": _db_state.get("write"),
            "storage": _bucket_ensure(),
            "bucket": BUCKET,
            "ai": {"yandex": bool(YANDEX_API_KEY and FOLDER_ID), "gigachat": bool(GIGACHAT_AUTH_KEY)},
            "counts": counts,
            "size": len(json.dumps(data, ensure_ascii=False).encode("utf-8")),
            "domain": _domain(data),
            "sitemap_urls": build_sitemap(data).count("<url>"),
        }

    def log_message(self, fmt, *args):
        if os.environ.get("VERBOSE"):
            print("[http] " + (fmt % args), flush=True)


# ============================================================
#  ЗАПУСК
# ============================================================
def main():
    print("BOOT: Кухни Островский CMS (single-file)", flush=True)
    print("BOOT: PORT = {}".format(PORT), flush=True)
    print("BOOT: DOMAIN = {} ({})".format(_domain(), _host()), flush=True)
    print("BOOT: Supabase = {} / таблица {}".format(SUPABASE_URL or "НЕ ЗАДАН", DATA_TABLE), flush=True)
    print("BOOT: Storage bucket = {}".format(BUCKET), flush=True)
    print("BOOT: AI = yandex:{} gigachat:{}".format(
        bool(YANDEX_API_KEY and FOLDER_ID), bool(GIGACHAT_AUTH_KEY)), flush=True)
    if not os.environ.get("SUPABASE_SERVICE_KEY"):
        print("BOOT: ВНИМАНИЕ! SUPABASE_SERVICE_KEY берётся из кода — задайте её в переменных хостинга", flush=True)
    try:
        load_fresh()
    except Exception as e:
        print("BOOT: первичная загрузка не удалась: {}".format(e), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
