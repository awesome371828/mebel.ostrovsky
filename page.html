# -*- coding: utf-8 -*-
"""
mebel.py — Кухни Островский: сайт + /admin
Читает page.html, вставляет анимации, проксирует VK-картинки, синхронит с Supabase.
"""
import base64, concurrent.futures, gzip, hashlib, io, json, os, re, secrets, threading, time, urllib.request
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

SESSION_TTL = 604800
MAX_UPLOAD = 8 * 1024 * 1024
DATA_ROW_ID = 1
CACHE_TTL = 15

FAVICON_URL = "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&cs=1254x0"

ROBOTS = "User-agent: *\nAllow: /\n\nHost: кухниостровский.рф\n\nSitemap: {}/sitemap.xml\n".format(DOMAIN)
SITEMAP = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           '  <url>\n    <loc>' + DOMAIN + '/</loc>\n    <lastmod>' + date.today().isoformat() +
           '</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>1.0</priority>\n  </url>\n</urlset>\n')
MANIFEST = '{"name":"Кухни Островский","short_name":"Кухни Островский","start_url":"/","display":"standalone","background_color":"#0e0c09","theme_color":"#0e0c09","lang":"ru-RU"}'
PAGE_404 = '<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><title>404</title></head><body style="background:#0e0c09;color:#f5efe3;font-family:system-ui;text-align:center;padding:80px"><h1>404</h1><p><a style="color:#eccfa0" href="/">На главную</a></p></body></html>'

DEFAULT_DATA = {}  # заполняется ниже

# ============ АНИМАЦИИ (вставляются в page.html) ============
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


def _read_page():
    """Читает page.html и вставляет анимации."""
    try:
        p = os.path.join(ROOT, "page.html")
        with open(p, "r", encoding="utf-8") as f:
            html = f.read()
        print("[page] OK: прочитано " + str(len(html)) + " байт из " + p, flush=True)
    except Exception as e:
        print("[page] ОШИБКА: " + str(e), flush=True)
        return "<!DOCTYPE html><html><body><h1>page.html не найден: " + str(e) + "</h1></body></html>"
    # Вставляем анимации
    if "</head>" in html and "goldAnimations" not in html:
        html = html.replace("</head>", ANIM_STYLE + "\n</head>", 1)
    if "</body>" in html and "goldAnimationScript" not in html:
        html = html.replace("</body>", ANIM_SCRIPT + "\n</body>", 1)
    return html


# ============ ПРОКСИ VK-КАРТИНОК ============
_img_cache = {}
_img_lock = threading.Lock()
_IMG_TTL = 604800


def _fetch_image(url):
    now = time.time()
    with _img_lock:
        c = _img_cache.get(url)
        if c and now - c[1] < _IMG_TTL:
            return c[0], c[2]
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
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
        print("[img] " + str(e), flush=True)
        return None, None


def _proxify_urls(html):
    pat = re.compile(r'https://sun9-\d+\.vkuserphoto\.ru/[^\s"\')<>]+')

    def repl(m):
        u = m.group(0)
        return "/img?u=" + base64.urlsafe_b64encode(u.encode()).decode().rstrip("=")
    return pat.sub(repl, html)


# ============ SUPABASE ============
_sb_read = None
_sb_write = None
_sb_lock = threading.Lock()


def _sb_read_client():
    global _sb_read
    with _sb_lock:
        if _sb_read is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_ANON:
            try: _sb_read = create_client(SUPABASE_URL, SUPABASE_ANON)
            except Exception as e: print("[sb read] " + str(e), flush=True)
        return _sb_read


def _sb_write_client():
    global _sb_write
    with _sb_lock:
        if _sb_write is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_SERVICE:
            try: _sb_write = create_client(SUPABASE_URL, SUPABASE_SERVICE)
            except Exception as e: print("[sb write] " + str(e), flush=True)
        return _sb_write


def _sb_exec(fn, timeout=5):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(fn).result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        print("[sb] TIMEOUT " + str(timeout) + "s", flush=True); return None
    except Exception as e:
        print("[sb] " + str(e), flush=True); return None


def _fetch_from_supabase(timeout=5):
    sb = _sb_read_client()
    if sb is None: return None
    res = _sb_exec(lambda: sb.table("site_content").select("data").eq("id", DATA_ROW_ID).execute(), timeout=timeout)
    if res is not None and getattr(res, "data", None):
        raw = res.data[0].get("data") or {}
        if raw and isinstance(raw, dict) and len(raw) >= 3:
            return raw
    return None


def _save_to_supabase(data):
    sb = _sb_write_client()
    if sb is None:
        print("[save] НЕТ КЛИЕНТА (проверь SUPABASE_SERVICE_KEY)", flush=True); return False
    res = _sb_exec(lambda: sb.table("site_content").upsert({"id": DATA_ROW_ID, "data": data}).execute(), timeout=10)
    if res is not None:
        print("[save] OK: записано в Supabase", flush=True); return True
    print("[save] FAIL: запись не прошла", flush=True); return False


# ============ КЭШ ============
_auth_lock = threading.Lock()
_sessions = {}
_data_cache = None
_cache_ts = 0.0
_data_lock = threading.Lock()


def _new_session():
    t = secrets.token_urlsafe(32)
    with _auth_lock: _sessions[t] = time.time() + SESSION_TTL
    return t


def _check_session(token):
    if not token: return False
    with _auth_lock:
        exp = _sessions.get(token)
        if not exp: return False
        if exp < time.time(): _sessions.pop(token, None); return False
    return True


def _drop_session(token):
    if token:
        with _auth_lock: _sessions.pop(token, None)


def _merge_deep(base, over):
    if not isinstance(base, dict) or not isinstance(over, dict): return over
    r = dict(base)
    for k, v in over.items():
        if k in r and isinstance(r[k], dict) and isinstance(v, dict):
            r[k] = _merge_deep(r[k], v)
        else:
            r[k] = json.loads(json.dumps(v))
    return r


def load_fresh():
    """СИНХРОННО читает из БД. Для сайта и админки."""
    global _data_cache, _cache_ts
    raw = _fetch_from_supabase(timeout=6)
    if raw is None:
        with _data_lock:
            _data_cache = json.loads(json.dumps(DEFAULT_DATA))
            _cache_ts = time.time()
        print("[load] БД пуста — дефолты", flush=True)
        return _data_cache
    data = _merge_deep(json.loads(json.dumps(DEFAULT_DATA)), raw)
    with _data_lock:
        _data_cache = data
        _cache_ts = time.time()
    print("[load] свежие данные: " + str(len(raw)) + " полей", flush=True)
    return data


def load_data():
    """Быстрая версия — отдаёт кэш, если свежий."""
    global _data_cache, _cache_ts
    now = time.time()
    with _data_lock:
        if _data_cache is not None and now - _cache_ts < CACHE_TTL:
            return _data_cache
    return load_fresh()


def save_data(data):
    """Синхронная запись. Возвращает True только при успехе."""
    global _data_cache, _cache_ts
    ok = _save_to_supabase(data)
    if ok:
        with _data_lock:
            _data_cache = data
            _cache_ts = time.time()
    return ok


# ============ FAVICON ============
_fc = {"data": None, "ts": 0.0}
_ic = {"ico": None, "png16": None, "png32": None, "png180": None}


def _make_icons(data):
    try:
        from PIL import Image
    except Exception: return
    try:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
        _ic["ico"] = buf.getvalue()
        def png(s):
            c = img.copy(); c.thumbnail((s, s))
            b = io.BytesIO(); c.save(b, format="PNG"); return b.getvalue()
        _ic["png16"] = png(16); _ic["png32"] = png(32); _ic["png180"] = png(180)
    except Exception: pass


def get_favicon():
    now = time.time()
    if _fc["data"] is None or now - _fc["ts"] > 3600:
        try:
            req = urllib.request.Request(FAVICON_URL, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://vk.com/"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                _fc["data"] = data; _fc["ts"] = now; _make_icons(data)
        except Exception: return None
    return _fc["data"]


# ============ АДМИНКА (краткая версия) ============
ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Вход</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:linear-gradient(135deg,#0e0c09,#1a1611);color:#f5efe3;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(236,207,160,.2);border-radius:20px;padding:42px 38px;width:100%;max-width:420px}
h1{font-family:Georgia,serif;font-size:28px;color:#fff;margin-bottom:8px;text-align:center}
p.sub{color:#b9ad9a;font-size:13.5px;text-align:center;margin-bottom:28px}
label{display:block;color:#eccfa0;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:600}
input{width:100%;padding:14px 16px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);border-radius:12px;color:#fff;font-size:15px;margin-bottom:18px}
button{width:100%;padding:15px;background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;font-weight:700;border:none;border-radius:12px;cursor:pointer;text-transform:uppercase;letter-spacing:1px}
.err{background:rgba(220,60,60,.14);border:1px solid rgba(220,60,60,.4);color:#ff9a9a;padding:12px;border-radius:10px;font-size:13px;margin-bottom:18px;text-align:center}
</style></head><body>
<form class="card" method="POST" action="/admin/login">
<h1>Кухни Островский</h1><p class="sub">Вход в панель</p>__ERROR__
<label>Логин</label><input type="text" name="login" required autofocus>
<label>Пароль</label><input type="password" name="password" required>
<button>Войти</button></form></body></html>"""


ADMIN_HTML = r"""<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Админка</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:system-ui;background:#0e0c09;color:#f5efe3;line-height:1.5}
header{background:rgba(14,12,9,.95);border-bottom:1px solid rgba(236,207,160,.16);padding:14px 20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;position:sticky;top:0;z-index:10}
.brand{font-family:Georgia,serif;font-size:20px;color:#eccfa0}.brand span{font-size:12px;margin-left:6px;opacity:.7}
.actions{display:flex;gap:8px;flex-wrap:wrap}
.btn{padding:9px 16px;border-radius:9px;border:1px solid rgba(236,207,160,.16);background:rgba(255,255,255,.04);color:#f5efe3;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;font-family:inherit}
.btn:hover{border-color:#d4af6a}
.btn-gold{background:linear-gradient(135deg,#eccfa0,#d4af6a 55%,#a37c3f);color:#17120b;border:none}
.btn-red{background:rgba(220,60,60,.14);border-color:rgba(220,60,60,.35);color:#ff9a9a}
.layout{display:flex;min-height:calc(100vh - 60px)}
nav.side{width:220px;background:rgba(0,0,0,.28);border-right:1px solid rgba(236,207,160,.16);padding:12px 0;flex-shrink:0}
nav.side a{display:block;padding:11px 20px;color:#b9ad9a;font-size:14px;cursor:pointer;border-left:3px solid transparent}
nav.side a:hover{color:#fff;background:rgba(255,255,255,.04)}
nav.side a.active{color:#eccfa0;border-left-color:#d4af6a;background:rgba(212,175,106,.08)}
main{flex:1;padding:24px 30px;max-width:1100px;overflow-x:hidden}
h2{font-family:Georgia,serif;font-size:24px;color:#fff;margin-bottom:6px}
p.hint{color:#b9ad9a;font-size:13px;margin-bottom:20px}
.field{margin-bottom:14px}.field label{display:block;color:#eccfa0;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:6px;font-weight:600}
.field input,.field textarea{width:100%;padding:10px 13px;background:rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.12);border-radius:9px;color:#fff;font-size:14px;font-family:inherit}
.field textarea{resize:vertical;min-height:70px}
.field input:focus,.field textarea:focus{outline:none;border-color:#d4af6a}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.item{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:16px;margin-bottom:12px}
.item-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:8px;flex-wrap:wrap}
.item-head strong{color:#eccfa0;font-size:13px}
.mini{padding:5px 10px;font-size:12px;border-radius:7px}
.img-preview{max-width:200px;border-radius:8px;margin-top:6px;display:block}
.toast{position:fixed;bottom:20px;left:50%;transform:translate(-50%,140%);background:linear-gradient(135deg,#eccfa0,#d4af6a);color:#17120b;padding:12px 24px;border-radius:11px;font-weight:700;font-size:14px;z-index:9999;transition:transform .4s}
.toast.show{transform:translate(-50%,0)}.toast.err{background:linear-gradient(135deg,#ff8a8a,#e04a4a);color:#fff}
.drop{display:block;border:2px dashed rgba(236,207,160,.16);border-radius:11px;padding:18px;text-align:center;color:#b9ad9a;font-size:13px;cursor:pointer;margin-top:6px}
.drop:hover{border-color:#d4af6a}
.status{font-size:12px;padding:5px 10px;border-radius:7px;display:inline-block}
.status.ok{background:rgba(80,200,120,.15);color:#7ee0a0;border:1px solid rgba(80,200,120,.4)}
.status.bad{background:rgba(220,60,60,.15);color:#ff9a9a;border:1px solid rgba(220,60,60,.4)}
.status.saving{background:rgba(212,175,106,.2);color:#eccfa0;border:1px solid rgba(212,175,106,.5)}
</style></head><body>
<header>
<div style="display:flex;gap:12px;align-items:center"><div class="brand">Кухни Островский<span>CMS</span></div><span class="status" id="status">Загрузка...</span></div>
<div class="actions"><a class="btn" href="/" target="_blank">Сайт</a><button class="btn btn-gold" id="saveBtn">💾 Сохранить</button><a class="btn btn-red" href="/admin/logout">Выйти</a></div>
</header>
<div class="layout">
<nav class="side">
<a data-tab="seo">SEO</a><a data-tab="brand">Бренд</a><a data-tab="hero" class="active">Главный</a>
<a data-tab="about">О специалисте</a><a data-tab="consult">Консультация</a>
<a data-tab="works">Работы</a><a data-tab="reviews">Отзывы</a><a data-tab="services">Услуги</a>
<a data-tab="process">Этапы</a><a data-tab="guarantees">Гарантии</a><a data-tab="cities">Города</a>
<a data-tab="cta">CTA</a><a data-tab="contacts">Контакты</a><a data-tab="footer">Подвал</a>
</nav>
<main id="main"><p class="hint">Загрузка...</p></main>
</div>
<div class="toast" id="toast"></div>
<script>
var DATA=null,currentTab='hero';
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}
function toast(m,e){var t=document.getElementById('toast');t.textContent=m;t.classList.toggle('err',!!e);t.classList.add('show');setTimeout(function(){t.classList.remove('show')},2500)}
function setStatus(text,cls){var el=document.getElementById('status');el.className='status '+(cls||'ok');el.textContent=text}
function getPath(o,p){return p.split('.').reduce(function(a,k){return a==null?undefined:a[k]},o)}
function setPath(o,p,v){var a=p.split('.');var c=o;for(var i=0;i<a.length-1;i++){var k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k]}c[a[a.length-1]]=v}
function loadData(){fetch('/admin/api/data',{credentials:'same-origin'}).then(function(r){if(r.status===401){location.href='/admin/login';return null}return r.json()}).then(function(j){if(!j)return;DATA=j;setStatus('Готово','ok');render()}).catch(function(e){setStatus('Ошибка загрузки','bad');document.getElementById('main').innerHTML='<h2>Ошибка</h2><p class="hint">'+esc(e.message)+'</p>'})}
function saveAll(){if(!DATA){toast('Нет данных',true);return}setStatus('Сохранение...','saving');fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)}).then(function(r){return r.json()}).then(function(j){if(j&&j.ok===true){setStatus('✅ Сохранено','ok');toast('Сохранено в Supabase')}else{setStatus('❌ НЕ сохранилось','bad');toast('Ошибка записи!',true)}}).catch(function(e){setStatus('Ошибка','bad');toast('Ошибка: '+e.message,true)})}
function field(l,p,o){o=o||{};var v=getPath(DATA,p);var i=o.rows?'<textarea data-path="'+p+'" rows="'+o.rows+'">'+esc(v)+'</textarea>':'<input type="text" data-path="'+p+'" value="'+esc(v)+'">';return '<div class="field"><label>'+l+'</label>'+i+'</div>'}
function imgField(l,p){var v=getPath(DATA,p);return '<div class="field"><label>'+l+'</label><input type="text" data-path="'+p+'" value="'+esc(v)+'"><label class="drop" data-upload-path="'+p+'">загрузить файл<input type="file" accept="image/*" style="display:none"></label>'+(v?'<img class="img-preview" src="'+esc(v)+'">':'')+'</div>'}
function render(){if(!DATA)return;var map={seo:rSeo,brand:rBrand,hero:rHero,about:rAbout,consult:rConsult,works:rWorks,reviews:rReviews,services:rServices,process:rProcess,guarantees:rGuarantees,cities:rCities,cta:rCta,contacts:rContacts,footer:rFooter};var fn=map[currentTab];document.getElementById('main').innerHTML=fn?fn():'<h2>?</h2>';bindInputs()}
function bindInputs(){document.querySelectorAll('[data-path]').forEach(function(el){el.addEventListener('input',function(){setPath(DATA,el.dataset.path,el.value)})});document.querySelectorAll('[data-upload-path]').forEach(function(lbl){var fi=lbl.querySelector('input[type="file"]');if(!fi)return;fi.addEventListener('change',function(){uploadImage(fi,lbl.dataset.uploadPath)})})}
function uploadImage(input,path){var f=input.files[0];if(!f)return;if(f.size>8*1024*1024){toast('Файл > 8 МБ',true);return}var fd=new FormData();fd.append('file',f);toast('Загрузка...');fetch('/admin/api/upload',{method:'POST',body:fd,credentials:'same-origin'}).then(function(r){return r.json()}).then(function(j){if(j.url){setPath(DATA,path,j.url);render();toast('Загружено')}else{toast('Ошибка',true)}})}
function rSeo(){return '<h2>SEO</h2>'+field('Title','seo.title',{rows:2})+field('Description','seo.description',{rows:3})+field('Keywords','seo.keywords',{rows:3})+field('OG-картинка','seo.og_image')}
function rBrand(){return '<h2>Бренд</h2>'+field('Название','brand.name')+field('Подзаголовок','brand.sub')+imgField('Логотип','brand.logo_url')+field('Телефон (визуал)','brand.phone')+field('Телефон (tel:)','brand.phone_raw')+field('Telegram','brand.telegram')+field('VK','brand.vk')}
function rHero(){return '<h2>Главный экран</h2>'+field('Надзаголовок','hero.eyebrow')+field('Заголовок до','hero.title_before')+field('Заголовок выделенный','hero.title_em')+field('Подзаголовок','hero.sub',{rows:3})+field('Кнопка 1','hero.btn1')+field('Кнопка 2','hero.btn2')+imgField('Фон','hero.bg')}
function rAbout(){return '<h2>О специалисте</h2>'+imgField('Фото','about.photo')+field('Имя','about.name')+field('Должность','about.role')+field('Описание','about.text',{rows:3})+field('Заголовок','about.title')+field('Текст','about.body',{rows:4})+imgField('Фон','about.bg')}
function rConsult(){return '<h2>Консультация</h2>'+field('Надзаголовок','consult.kicker')+field('Заголовок','consult.title')+field('Текст','consult.text',{rows:4})+imgField('Фон','consult.bg')}
function rWorks(){var a=(DATA.works&&DATA.works.items)||[];var h='<h2>Работы</h2>'+field('Надзаголовок','works.kicker')+field('Заголовок','works.title')+field('Подзаголовок','works.subtitle')+imgField('Фон','works.bg')+'<div class="item-head"><strong>Фото ('+a.length+')</strong></div>';a.forEach(function(it,i){h+='<div class="item"><div class="item-head"><strong>#'+(i+1)+'</strong><div><button class="btn mini" data-action="mv" data-list="works.items" data-i="'+i+'" data-d="-1">↑</button> <button class="btn mini" data-action="mv" data-list="works.items" data-i="'+i+'" data-d="1">↓</button> <button class="btn btn-red mini" data-action="del" data-list="works.items" data-i="'+i+'">Удалить</button></div></div>'+imgField('Картинка','works.items.'+i+'.url')+field('Alt','works.items.'+i+'.alt')+'</div>'});h+='<button class="btn" data-action="add" data-list="works.items" data-tpl=\'{"url":"","alt":""}\'>+ Добавить</button>';return h}
function rReviews(){var a=(DATA.reviews&&DATA.reviews.items)||[];var h='<h2>Отзывы</h2>'+field('Надзаголовок','reviews.kicker')+field('Заголовок','reviews.title')+field('Подзаголовок','reviews.subtitle')+imgField('Фон','reviews.bg')+'<div class="item-head"><strong>Отзывы ('+a.length+')</strong></div>';a.forEach(function(it,i){h+='<div class="item"><div class="item-head"><strong>'+esc(it.name||'#'+(i+1))+'</strong><div><button class="btn mini" data-action="mv" data-list="reviews.items" data-i="'+i+'" data-d="-1">↑</button> <button class="btn mini" data-action="mv" data-list="reviews.items" data-i="'+i+'" data-d="1">↓</button> <button class="btn btn-red mini" data-action="del" data-list="reviews.items" data-i="'+i+'">Удалить</button></div></div><div class="row">'+field('Имя','reviews.items.'+i+'.name')+field('Подпись','reviews.items.'+i+'.sub')+'</div>'+field('Звёзд','reviews.items.'+i+'.stars')+imgField('Аватар','reviews.items.'+i+'.avatar')+field('Текст','reviews.items.'+i+'.text',{rows:5})+field('Видео URL','reviews.items.'+i+'.video')+'</div>'});h+='<button class="btn" data-action="add" data-list="reviews.items" data-tpl=\'{"name":"","sub":"","stars":5,"avatar":"","text":"","video":""}\'>+ Добавить</button>';return h}
function rServices(){var a=(DATA.services&&DATA.services.items)||[];var h='<h2>Услуги</h2>'+field('Надзаголовок','services.kicker')+field('Заголовок','services.title')+field('Подзаголовок','services.subtitle')+imgField('Фон','services.bg');a.forEach(function(it,i){h+='<div class="item"><div class="item-head"><strong>'+esc(it.title||'#'+(i+1))+'</strong><button class="btn btn-red mini" data-action="del" data-list="services.items" data-i="'+i+'">Удалить</button></div>'+field('Название','services.items.'+i+'.title')+field('Описание','services.items.'+i+'.text',{rows:2})+field('SVG','services.items.'+i+'.icon')+'</div>'});h+='<button class="btn" data-action="add" data-list="services.items" data-tpl=\'{"title":"","text":"","icon":""}\'>+ Добавить</button>';return h}
function rProcess(){var a=(DATA.process&&DATA.process.items)||[];var h='<h2>Этапы</h2>'+field('Надзаголовок','process.kicker')+field('Заголовок','process.title')+imgField('Фон','process.bg');a.forEach(function(it,i){h+='<div class="item"><div class="item-head"><strong>'+esc((it.n||'')+' '+(it.title||''))+'</strong><button class="btn btn-red mini" data-action="del" data-list="process.items" data-i="'+i+'">Удалить</button></div><div class="row">'+field('Номер','process.items.'+i+'.n')+field('Заголовок','process.items.'+i+'.title')+'</div>'+field('Текст','process.items.'+i+'.text',{rows:2})+'</div>'});h+='<button class="btn" data-action="add" data-list="process.items" data-tpl=\'{"n":"","title":"","text":""}\'>+ Добавить</button>';return h}
function rGuarantees(){var a=(DATA.guarantees&&DATA.guarantees.items)||[];var h='<h2>Гарантии</h2>'+field('Надзаголовок','guarantees.kicker')+field('Заголовок','guarantees.title')+imgField('Фон','guarantees.bg');a.forEach(function(it,i){h+='<div class="item"><div class="item-head"><strong>'+esc(it.title||'#'+(i+1))+'</strong><button class="btn btn-red mini" data-action="del" data-list="guarantees.items" data-i="'+i+'">Удалить</button></div>'+field('Заголовок','guarantees.items.'+i+'.title')+field('Текст','guarantees.items.'+i+'.text',{rows:2})+field('SVG','guarantees.items.'+i+'.icon')+'</div>'});h+='<button class="btn" data-action="add" data-list="guarantees.items" data-tpl=\'{"title":"","text":"","icon":""}\'>+ Добавить</button>';return h}
function rCities(){var a=(DATA.cities&&DATA.cities.items)||[];var h='<h2>Города</h2>'+field('Надзаголовок','cities.kicker')+field('Заголовок','cities.title')+field('Подзаголовок','cities.subtitle')+imgField('Фон','cities.bg');a.forEach(function(it,i){h+='<div class="item"><div class="item-head"><strong>'+esc(it.name||'#'+(i+1))+'</strong><button class="btn btn-red mini" data-action="del" data-list="cities.items" data-i="'+i+'">Удалить</button></div>'+field('Название','cities.items.'+i+'.name')+field('Описание','cities.items.'+i+'.text',{rows:2})+'</div>'});h+='<button class="btn" data-action="add" data-list="cities.items" data-tpl=\'{"name":"","text":""}\'>+ Добавить</button>';return h}
function rCta(){return '<h2>CTA</h2>'+field('Заголовок','cta.title')+field('Текст','cta.text',{rows:3})+field('Кнопка','cta.button')+imgField('Фон','cta.bg')}
function rContacts(){return '<h2>Контакты</h2>'+field('Надзаголовок','contacts.kicker')+field('Заголовок','contacts.title')+field('Подзаголовок','contacts.subtitle',{rows:2})+field('Регионы','contacts.regions')+imgField('Фон','contacts.bg')}
function rFooter(){return '<h2>Подвал</h2>'+field('Строка','footer.line')+field('Копирайт','footer.copyright')}
document.addEventListener('click',function(e){
  var t=e.target;
  var tab=t.closest('nav.side a[data-tab]');
  if(tab){document.querySelectorAll('nav.side a').forEach(function(y){y.classList.remove('active')});tab.classList.add('active');currentTab=tab.dataset.tab;render();return}
  if(t.closest('#saveBtn')){e.preventDefault();saveAll();return}
  var b=t.closest('[data-action]');
  if(b){
    var a=b.dataset.action,list=b.dataset.list,i=parseInt(b.dataset.i||'0',10),d=parseInt(b.dataset.d||'0',10),tpl=b.dataset.tpl;
    if(a==='add'){var arr=getPath(DATA,list)||[];arr.push(JSON.parse(tpl));setPath(DATA,list,arr);render();toast('Добавлено')}
    else if(a==='del'){if(!confirm('Удалить?'))return;var arr=getPath(DATA,list);arr.splice(i,1);setPath(DATA,list,arr);render()}
    else if(a==='mv'){var arr=getPath(DATA,list);var j=i+d;if(j<0||j>=arr.length)return;var x=arr[i];arr[i]=arr[j];arr[j]=x;render()}
  }
});
loadData();
</script></body></html>"""


# ============ HTTP ============
def _parse_multipart(body, boundary):
    parts = body.split(b"--" + boundary)
    for p in parts:
        if b"Content-Disposition" not in p: continue
        head, _, data = p.partition(b"\r\n\r\n")
        if not data: continue
        data = data.rstrip(b"\r\n--")
        if b'name="file"' in head:
            return data
    return None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _tok(self):
        raw = self.headers.get("Cookie", "")
        if not raw: return None
        try:
            c = SimpleCookie(); c.load(raw)
            m = c.get("admin_session")
            return m.value if m else None
        except Exception: return None

    def _admin(self):
        return _check_session(self._tok())

    def _send(self, code, body, ctype="text/plain; charset=utf-8", cache="no-cache", gzip_ok=True):
        data = body.encode("utf-8") if isinstance(body, str) else body
        etag = '"' + hashlib.sha256(data).hexdigest()[:20] + '"'
        if code == 200 and self.headers.get("If-None-Match") == etag:
            self.send_response(304); self.send_header("ETag", etag); self.send_header("Cache-Control", cache); self.end_headers(); return
        ae = self.headers.get("Accept-Encoding", "")
        if gzip_ok and isinstance(body, str) and "gzip" in ae and len(data) > 700:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=6) as gz: gz.write(data)
            data = buf.getvalue()
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Encoding", "gzip"); self.send_header("Vary", "Accept-Encoding")
        else:
            self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag); self.end_headers(); self.wfile.write(data)

    def _redir(self, loc, cookie=None):
        self.send_response(302); self.send_header("Location", loc); self.send_header("Cache-Control", "no-cache")
        if cookie: self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0"); self.end_headers()

    def _body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n <= 0 or n > MAX_UPLOAD * 3: return b""
        return self.rfile.read(n)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/img":
            qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            u = (qs.get("u") or [""])[0]
            if not u: self._send(404, "no url"); return
            try:
                pad = "=" * (-len(u) % 4)
                url = base64.urlsafe_b64decode(u + pad).decode()
            except Exception: self._send(400, "bad"); return
            if not url.startswith("https://") or "vkuserphoto.ru" not in url:
                self._send(403, "forbidden"); return
            data, ct = _fetch_image(url)
            if data is None: self._redir(url); return
            self._send(200, data, ct, "public, max-age=604800", gzip_ok=False)
            return

        if path == "/admin/login":
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", ""), "text/html; charset=utf-8"); return
        if path == "/admin/logout":
            _drop_session(self._tok())
            self._redir("/admin/login", "admin_session=; Path=/; Max-Age=0; HttpOnly"); return
        if path == "/admin/api/data":
            if not self._admin(): self._json({"error": "no"}, 401); return
            self._json(load_fresh()); return
        if path == "/admin":
            if not self._admin(): self._redir("/admin/login"); return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8"); return
        if path in ("/", "/index.html"):
            html = _read_page()
            html = _proxify_urls(html)
            self._send(200, html, "text/html; charset=utf-8", "no-cache")
        elif path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8", "public, max-age=86400")
        elif path == "/sitemap.xml":
            self._send(200, SITEMAP, "application/xml; charset=utf-8", "public, max-age=3600")
        elif path == "/favicon.ico":
            d = get_favicon()
            if not d: self._redir(FAVICON_URL)
            elif _ic["ico"]: self._send(200, _ic["ico"], "image/x-icon", "public, max-age=86400", gzip_ok=False)
            else: self._send(200, d, "image/x-icon", "public, max-age=86400", gzip_ok=False)
        elif path == "/favicon-16x16.png":
            if _ic["png16"]: self._send(200, _ic["png16"], "image/png", "public, max-age=86400", gzip_ok=False)
            else: self._redir(FAVICON_URL)
        elif path == "/favicon-32x32.png":
            if _ic["png32"]: self._send(200, _ic["png32"], "image/png", "public, max-age=86400", gzip_ok=False)
            else: self._redir(FAVICON_URL)
        elif path == "/apple-touch-icon.png":
            if _ic["png180"]: self._send(200, _ic["png180"], "image/png", "public, max-age=86400", gzip_ok=False)
            else: self._redir(FAVICON_URL)
        elif path == "/manifest.webmanifest":
            self._send(200, MANIFEST, "application/manifest+json; charset=utf-8")
        else:
            self._send(404, PAGE_404, "text/html; charset=utf-8")

    def do_POST(self):
        path = self.path.split("?")[0]
        if path == "/admin/login":
            b = self._body().decode("utf-8", "ignore")
            p = parse_qs(b)
            login = (p.get("login") or [""])[0]
            pw = (p.get("password") or [""])[0]
            if login == ADMIN_LOGIN_ENV and pw == ADMIN_PASSWORD_ENV:
                t = _new_session()
                self._redir("/admin", "admin_session=" + t + "; Path=/; Max-Age=" + str(SESSION_TTL) + "; HttpOnly; SameSite=Lax")
            else:
                self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", '<div class="err">Неверный логин или пароль</div>'), "text/html; charset=utf-8")
            return
        if path == "/admin/api/save":
            if not self._admin(): self._json({"error": "no"}, 401); return
            try: obj = json.loads(self._body().decode("utf-8"))
            except Exception: self._json({"error": "bad json"}, 400); return
            ok = save_data(obj)
            self._json({"ok": ok})
            return
        if path == "/admin/api/upload":
            if not self._admin(): self._json({"error": "no"}, 401); return
            body = self._body()
            ct = self.headers.get("Content-Type", "")
            fb = None
            if "multipart/form-data" in ct:
                m = re.search(r'boundary=([^;]+)', ct)
                if m: fb = _parse_multipart(body, m.group(1).strip().strip('"').encode())
            if not fb: self._json({"error": "no file"}, 400); return
            if len(fb) > MAX_UPLOAD: self._json({"error": "too big"}, 413); return
            mime = "image/jpeg"
            if fb[:8] == b"\x89PNG\r\n\x1a\n": mime = "image/png"
            elif fb[:6] in (b"GIF87a", b"GIF89a"): mime = "image/gif"
            elif fb[:4] == b"RIFF" and fb[8:12] == b"WEBP": mime = "image/webp"
            self._json({"url": "data:" + mime + ";base64," + base64.b64encode(fb).decode()})
            return
        self._json({"error": "not found"}, 404)

    def log_message(self, *args): pass


if __name__ == "__main__":
    print("BOOT: старт", flush=True)
    print("BOOT: PORT = " + str(PORT), flush=True)
    # Проверка page.html при старте
    p = os.path.join(ROOT, "page.html")
    if os.path.exists(p):
        print("BOOT: page.html найден (" + str(os.path.getsize(p)) + " байт)", flush=True)
    else:
        print("BOOT: ⚠️  page.html НЕ НАЙДЕН в " + ROOT, flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
