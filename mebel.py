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
            try:
                _sb_read = create_client(SUPABASE_URL, SUPABASE_ANON)
            except Exception as e:
                print(f"[supabase read] {e}")
        return _sb_read


def _sb_write_client():
    global _sb_write
    with _sb_lock:
        if _sb_write is None and _SUPABASE_LIB and SUPABASE_URL and SUPABASE_SERVICE:
            try:
                _sb_write = create_client(SUPABASE_URL, SUPABASE_SERVICE)
            except Exception as e:
                print(f"[supabase write] {e}")
        return _sb_write


# ---------- Сессии ----------
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


# ---------- Данные ----------
_data_cache = None
_cache_ts = 0.0
_data_lock = threading.Lock()
_initialized_db = False


def _deep_fill(target, source):
    """Дополняет target недостающими полями из source."""
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
                if res.data:
                    raw = res.data[0].get("data") or {}
            except Exception as e:
                print(f"[load_data] {e}")

        # Если в БД пусто — берём DEFAULT_DATA и записываем в БД
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
            sb.table("site_content").upsert({
                "id": DATA_ROW_ID,
                "data": data,
            }).execute()
            _data_cache = data
            _cache_ts = time.time()
            return True
        except Exception as e:
            print(f"[save_data] {e}")
            return False


# =====================================================================
# АНИМАЦИИ — вставляются в PAGE
# =====================================================================
ANIM_STYLE = r"""
<style id="goldAnimations">
/* ==================== Общие настройки анимаций ==================== */
@keyframes fadeUp{from{opacity:0;transform:translateY(40px)}to{opacity:1;transform:none}}
@keyframes fadeLeft{from{opacity:0;transform:translateX(-50px)}to{opacity:1;transform:none}}
@keyframes fadeRight{from{opacity:0;transform:translateX(50px)}to{opacity:1;transform:none}}
@keyframes fadeZoom{from{opacity:0;transform:scale(.85)}to{opacity:1;transform:scale(1)}}
@keyframes blurIn{from{opacity:0;filter:blur(20px)}to{opacity:1;filter:blur(0)}}
@keyframes goldLine{from{width:0;opacity:0}to{width:80px;opacity:1}}
@keyframes shimmerX{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes pulseGold{0%,100%{box-shadow:0 0 0 0 rgba(212,175,106,.4)}50%{box-shadow:0 0 0 14px rgba(212,175,106,0)}}
@keyframes rotateSlow{from{transform:rotate(0)}to{transform:rotate(360deg)}}
@keyframes floatY{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
@keyframes goldGradient{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}

/* ==================== Применение к элементам ==================== */
.anim-hidden{opacity:0}
.anim-up{animation:fadeUp 1s cubic-bezier(.22,.61,.36,1) forwards}
.anim-left{animation:fadeLeft 1s cubic-bezier(.22,.61,.36,1) forwards}
.anim-right{animation:fadeRight 1s cubic-bezier(.22,.61,.36,1) forwards}
.anim-zoom{animation:fadeZoom .9s cubic-bezier(.22,.61,.36,1) forwards}
.anim-blur{animation:blurIn 1.1s ease forwards}

/* ==================== Заголовок с золотой заливкой ==================== */
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
.js .anim-visible h1, .js h1.anim-visible,
.js .anim-visible h2, .js h2.anim-visible{
  background-position:0% 0;
}

/* ==================== Карточки — готовятся к появлению ==================== */
.js .stat,.js .svc,.js .step,.js .guar,.js .city,.js .car-slide,.js .rev-card,.js .about-card,.js .about-body,.js .call-block,.js .contact-info,.js .sec-head{
  opacity:0;
  transform:translateY(30px);
  transition:opacity .9s cubic-bezier(.22,.61,.36,1),transform .9s cubic-bezier(.22,.61,.36,1),box-shadow .4s,border-color .4s;
}
.js .stat.anim-in,.js .svc.anim-in,.js .step.anim-in,.js .guar.anim-in,.js .city.anim-in,
.js .car-slide.anim-in,.js .rev-card.anim-in,.js .about-card.anim-in,.js .about-body.anim-in,
.js .call-block.anim-in,.js .contact-info.anim-in,.js .sec-head.anim-in{
  opacity:1;
  transform:translateY(0);
}

/* Стаггер — по индексу внутри контейнера */
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

/* ==================== Золотая линия под заголовками секций ==================== */
.sec-head h2,.about-body h2,.contact-info h2,.cta h2{
  position:relative;
}
.sec-head h2::after,.about-body h2::after,.contact-info h2::after,.cta h2::after{
  content:"";
  position:absolute;
  left:50%;
  bottom:-12px;
  height:2px;
  width:0;
  background:linear-gradient(90deg,transparent,var(--gold),transparent);
  transform:translateX(-50%);
  transition:width 1.4s cubic-bezier(.22,.61,.36,1) .3s;
  border-radius:2px;
}
.about-body h2::after,.contact-info h2::after{left:0;transform:none}
.js .sec-head.anim-in h2::after{width:80px}
.js .about-body.anim-in h2::after{width:100px}
.js .contact-info.anim-in h2::after{width:100px}

/* ==================== Кнопки — ripple и магнитный эффект ==================== */
.btn{position:relative;overflow:hidden;transform:translateZ(0);will-change:transform}
.btn .ripple-el{
  position:absolute;
  border-radius:50%;
  background:radial-gradient(circle,rgba(255,255,255,.55),transparent 70%);
  transform:scale(0);
  animation:rippleAnim .8s ease-out forwards;
  pointer-events:none;
}
@keyframes rippleAnim{to{transform:scale(4);opacity:0}}
.btn-solid{
  background-size:200% 200%;
  animation:btnGlow 3.6s ease-in-out infinite, goldGradient 6s ease infinite;
}
.c-action{position:relative;overflow:hidden}
.c-action .ripple-el{background:radial-gradient(circle,rgba(255,255,255,.35),transparent 70%)}

/* ==================== Золотые частицы на фоне ==================== */
#goldParticles{
  position:fixed;
  inset:0;
  z-index:-1;
  pointer-events:none;
  overflow:hidden;
}
#goldParticles span{
  position:absolute;
  width:6px;height:6px;
  border-radius:50%;
  background:radial-gradient(circle,rgba(236,207,160,.9),rgba(212,175,106,.4) 40%,transparent 70%);
  box-shadow:0 0 12px rgba(236,207,160,.55);
  animation:particleFloat linear infinite;
  will-change:transform,opacity;
}
@keyframes particleFloat{
  0%{transform:translateY(100vh) scale(.5);opacity:0}
  10%{opacity:1}
  90%{opacity:.85}
  100%{transform:translateY(-100px) scale(1.1);opacity:0}
}

/* ==================== Вращающиеся орбы ==================== */
.orb{
  animation:orbFloat 22s ease-in-out infinite alternate, rotateSlow 60s linear infinite;
  will-change:transform;
}
.orb-1{animation-duration:22s,80s}
.orb-2{animation-duration:28s,100s}
.orb-3{animation-duration:34s,120s}

/* ==================== Фоновые изображения — плавный kenburns ==================== */
.panel .bg{
  transition:transform 1.2s cubic-bezier(.22,.61,.36,1);
}

/* ==================== Иконки в карточках — bounce ==================== */
.svc svg,.guar .ico,.c-ico,.vb-play{
  transition:transform .55s cubic-bezier(.34,1.56,.64,1),background .35s,color .35s,box-shadow .35s;
}
.svc:hover svg{transform:scale(1.18) rotate(-8deg)}
.guar:hover .ico{transform:scale(1.18) rotate(8deg)}
.c-line:hover .c-ico{transform:scale(1.16) rotate(-6deg)}

/* ==================== Звёзды отзыва — переливаются ==================== */
.rev-stars{
  background:linear-gradient(90deg,#eccfa0,#fff 50%,#eccfa0 100%);
  background-size:200% auto;
  -webkit-background-clip:text;
  background-clip:text;
  -webkit-text-fill-color:transparent;
  animation:shimmerX 3s linear infinite;
}

/* ==================== Счётчики — масштаб при появлении ==================== */
.stat .num{
  display:inline-block;
  transition:transform .8s cubic-bezier(.34,1.56,.64,1);
}
.js .stat.anim-in .num{animation:countPop .9s cubic-bezier(.34,1.56,.64,1)}
@keyframes countPop{
  0%{transform:scale(.3);opacity:0}
  60%{transform:scale(1.15)}
  100%{transform:scale(1);opacity:1}
}

/* ==================== Телефон в консультации — пульс ==================== */
.consult .phone,.call-block .cb-num{
  transition:transform .4s,filter .4s;
  display:inline-block;
}
.consult .phone:hover,.call-block .cb-num:hover{
  transform:scale(1.04);
  filter:drop-shadow(0 10px 30px rgba(212,175,106,.6));
}

/* ==================== Бейджи/плашки — пульсирующее золото ==================== */
.eyebrow,.kicker,.sec-head .kicker{
  background:linear-gradient(90deg,rgba(236,207,160,.85),#fff 50%,rgba(236,207,160,.85));
  background-size:220% auto;
  -webkit-background-clip:text;
  background-clip:text;
  -webkit-text-fill-color:transparent;
  animation:shimmerX 4.5s linear infinite;
}

/* ==================== Логотип — пульс кольца ==================== */
.brand-ava-w::before{
  animation:ringPulse 3.2s ease-in-out infinite, rotateSlow 24s linear infinite;
}
.brand-ava{
  transition:transform .5s cubic-bezier(.34,1.56,.64,1),filter .4s;
}
.logo:hover .brand-ava{transform:scale(1.08) rotate(-6deg);filter:brightness(1.15)}

/* ==================== Дивайдер — золотая линия дышит ==================== */
.gold-divider b{
  animation:pulseGold 2.8s ease-in-out infinite;
}
.gold-divider i{
  animation:dividerLine 3s ease-in-out infinite alternate;
}
@keyframes dividerLine{0%{opacity:.35;transform:scaleX(.8)}100%{opacity:1;transform:scaleX(1.15)}}

/* ==================== Прогресс-бар сверху — мягкое свечение ==================== */
.progress{
  background-size:200% 100%;
  animation:goldGradient 4s ease infinite;
  box-shadow:0 0 22px rgba(236,207,160,.85);
}

/* ==================== Карточки — при ховере золотое свечение ==================== */
.stat:hover,.svc:hover,.step:hover,.guar:hover,.city:hover,.rev-card:hover{
  box-shadow:0 30px 80px rgba(0,0,0,.6),0 0 60px rgba(212,175,106,.15);
}

/* ==================== Фото работ — мягкий зум ==================== */
.car-slide img{
  transition:transform 1.1s cubic-bezier(.22,.61,.36,1),filter .8s;
}
.car-slide:hover img{transform:scale(1.12)}

/* ==================== Плавный скролл по всему сайту ==================== */
html{scroll-behavior:smooth}

/* ==================== Уважение к prefers-reduced-motion ==================== */
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{
    animation-duration:.01ms !important;
    animation-iteration-count:1 !important;
    transition-duration:.01ms !important;
  }
  .js .stat,.js .svc,.js .step,.js .guar,.js .city,.js .car-slide,.js .rev-card,
  .js .about-card,.js .about-body,.js .call-block,.js .contact-info,.js .sec-head{
    opacity:1 !important;transform:none !important;
  }
}
</style>
"""

ANIM_SCRIPT = r"""
<script id="goldAnimationScript">
(function(){
  if (!('IntersectionObserver' in window)) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head').forEach(el=>el.classList.add('anim-in'));
    document.documentElement.classList.remove('js');
    return;
  }

  // ---------- 1. Появление карточек ----------
  const io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting){
        e.target.classList.add('anim-in');
        io.unobserve(e.target);
      }
    });
  }, {threshold:0.12, rootMargin:'0px 0px -50px 0px'});

  document.querySelectorAll('.stat,.svc,.step,.guar,.city,.car-slide,.rev-card,.about-card,.about-body,.call-block,.contact-info,.sec-head').forEach(function(el){
    io.observe(el);
  });

  // ---------- 2. Заголовки — золотая заливка слева направо ----------
  const headIo = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if (e.isIntersecting){
        e.target.classList.add('anim-visible');
        headIo.unobserve(e.target);
      }
    });
  }, {threshold:0.5});
  document.querySelectorAll('h1,h2.k,.sec-head h2,.about-body h2,.contact-info h2,.cta h2').forEach(function(el){
    headIo.observe(el);
  });

  // ---------- 3. Золотые частицы на фоне ----------
  (function(){
    var container = document.createElement('div');
    container.id = 'goldParticles';
    document.body.appendChild(container);
    var count = window.innerWidth < 700 ? 12 : 24;
    for (var i=0;i<count;i++){
      var s = document.createElement('span');
      var size = 3 + Math.random()*5;
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      s.style.left = (Math.random()*100) + '%';
      s.style.animationDuration = (14 + Math.random()*18) + 's';
      s.style.animationDelay = (-Math.random()*20) + 's';
      s.style.opacity = (0.35 + Math.random()*0.55);
      container.appendChild(s);
    }
  })();

  // ---------- 4. Ripple на кнопках ----------
  document.addEventListener('click', function(e){
    var btn = e.target.closest('.btn, .c-action, .car-dot, .soc');
    if (!btn) return;
    var rect = btn.getBoundingClientRect();
    var ripple = document.createElement('span');
    ripple.className = 'ripple-el';
    var size = Math.max(rect.width, rect.height);
    ripple.style.width = size + 'px';
    ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
    ripple.style.top  = (e.clientY - rect.top  - size/2) + 'px';
    btn.appendChild(ripple);
    setTimeout(function(){ ripple.remove(); }, 850);
  }, {passive:true});

  // ---------- 5. Магнитный эффект для кнопок ----------
  var fine = matchMedia('(hover:hover) and (pointer:fine)').matches;
  if (fine) {
    document.querySelectorAll('.btn-solid, .c-action.c-call').forEach(function(btn){
      btn.addEventListener('mousemove', function(e){
        var r = btn.getBoundingClientRect();
        var dx = (e.clientX - r.left - r.width/2) / r.width;
        var dy = (e.clientY - r.top  - r.height/2) / r.height;
        btn.style.transform = 'translate(' + (dx*6) + 'px,' + (dy*6 - 4) + 'px)';
      });
      btn.addEventListener('mouseleave', function(){
        btn.style.transform = '';
      });
    });
  }

  // ---------- 6. Микро-параллакс фото в работах ----------
  if (fine) {
    document.querySelectorAll('.car-slide').forEach(function(slide){
      var img = slide.querySelector('img');
      if (!img) return;
      slide.addEventListener('mousemove', function(e){
        var r = slide.getBoundingClientRect();
        var dx = (e.clientX - r.left) / r.width - .5;
        var dy = (e.clientY - r.top ) / r.height - .5;
        img.style.transform = 'scale(1.12) translate(' + (dx*10) + 'px,' + (dy*10) + 'px)';
      });
      slide.addEventListener('mouseleave', function(){
        img.style.transform = '';
      });
    });
  }

  // ---------- 7. Фоны секций — мягкий zoom при скролле ----------
  if (fine) {
    var bgs = document.querySelectorAll('.panel .bg');
    var ticking = false;
    function updateBgs(){
      if (ticking) return;
      ticking = true;
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
    window.addEventListener('scroll', updateBgs, {passive:true});
    updateBgs();
  }

  // ---------- 8. Каскадное появление первых элементов hero ----------
  document.querySelectorAll('#top .eyebrow, #top h1, #top .sub, #top .btn-row').forEach(function(el,i){
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 1s cubic-bezier(.22,.61,.36,1), transform 1s cubic-bezier(.22,.61,.36,1)';
    setTimeout(function(){
      el.style.opacity = '1';
      el.style.transform = 'none';
    }, 200 + i*180);
  });

})();
</script>
"""


def _inject_animations(html):
    """Вставляет стили перед </head> и скрипт перед </body>."""
    if "</head>" in html and "goldAnimations" not in html:
        html = html.replace("</head>", ANIM_STYLE + "\n</head>", 1)
    if "</body>" in html and "goldAnimationScript" not in html:
        html = html.replace("</body>", ANIM_SCRIPT + "\n</body>", 1)
    return html


# =====================================================================
# ЗАМЕНЫ В PAGE
# =====================================================================
def _sub_exact(html, anchor, replacement):
    if anchor and anchor in html:
        return html.replace(anchor, replacement, 1)
    return html


def render_page():
    """PAGE с подстановками из БД + анимациями."""
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
    process = d.get("process", {}) or {}
    guarantees = d.get("guarantees", {}) or {}
    cities = d.get("cities", {}) or {}
    cta = d.get("cta", {}) or {}
    contacts = d.get("contacts", {}) or {}
    footer = d.get("footer", {}) or {}

    # SEO
    if seo.get("title"):
        html = re.sub(r"<title>.*?</title>", f"<title>{seo['title']}</title>", html, count=1, flags=re.S)
    if seo.get("description"):
        html = re.sub(r'<meta name="description" content="[^"]*">',
                      f'<meta name="description" content="{seo["description"]}">', html, count=1)
    if seo.get("keywords"):
        html = re.sub(r'<meta name="keywords" content="[^"]*">',
                      f'<meta name="keywords" content="{seo["keywords"]}">', html, count=1)
    if seo.get("og_image"):
        html = re.sub(r'<meta property="og:image" content="[^"]*">',
                      f'<meta property="og:image" content="{seo["og_image"]}">', html, count=1)

    # Brand
    if b.get("name"):
        html = _sub_exact(html, '<span class="name">Кухни Островский</span>',
                          f'<span class="name">{b["name"]}</span>')
        html = _sub_exact(html, '<meta property="og:site_name" content="Кухни Островский">',
                          f'<meta property="og:site_name" content="{b["name"]}">')
    if b.get("sub"):
        html = _sub_exact(html, '<span class="sub">Ростов · Батайск · Азов</span>',
                          f'<span class="sub">{b["sub"]}</span>')
    if b.get("logo_url"):
        old = "https://sun9-20.vkuserphoto.ru/s/v1/ig2/2sp8pX_XIyDNZzghUeFMvYeHfkg4Kp7SVOVYhov8iLwAn3vAprbtUJPdXPi5IYkhMH-BR1LanCX8B0gH5rM8NC6c.jpg?quality=95&as=32x32,48x48,72x72,108x108,160x160,240x240,360x360,480x480,540x540,640x640,720x720,1080x1080,1254x1254&from=bu&u=8vUcv8YxPcmfEmzVcjy5cNrPtcWeOIJmbKMc6vln3Q8&cs=1254x0"
        html = html.replace(old, b["logo_url"])
    if b.get("phone"):
        html = html.replace("+7 (950) 846-53-97", b["phone"])
    if b.get("phone_raw"):
        html = html.replace("tel:+79508465397", f'tel:{b["phone_raw"]}')
        html = html.replace("+79508465397", b["phone_raw"])
    if b.get("telegram"):
        html = html.replace("https://t.me/fanny161", b["telegram"])
    if b.get("vk"):
        html = html.replace("https://vk.com/mebel.ostrovsky", b["vk"])

    # Hero
    if hero.get("eyebrow"):
        html = _sub_exact(html, '<span class="eyebrow">Мебель и кухни на заказ</span>',
                          f'<span class="eyebrow">{hero["eyebrow"]}</span>')
    if hero.get("title_before") or hero.get("title_em"):
        t_before = hero.get("title_before", "Мебель, которая ")
        t_em = hero.get("title_em", "создаёт настроение")
        new_h1 = f'<h1 id="heroTitle">{t_before}<em class="shimmer">{t_em}</em></h1>'
        html = re.sub(r'<h1 id="heroTitle">.*?</h1>', new_h1, html, count=1, flags=re.S)
    if hero.get("sub"):
        html = re.sub(r'<p class="sub">[^<]*</p>',
                      f'<p class="sub">{hero["sub"]}</p>', html, count=1)
    if hero.get("btn1"):
        html = _sub_exact(html, '>Получить консультацию<', f'>{hero["btn1"]}<')
    if hero.get("btn2"):
        html = _sub_exact(html, '>Смотреть работы<', f'>{hero["btn2"]}<')

    # About
    if about.get("photo"):
        html = _sub_exact(html, 'src="https://i.ibb.co/mVchNnp1/photo-2026-09-10-18-48-37.jpg"',
                          f'src="{about["photo"]}"')
    if about.get("name"):
        html = _sub_exact(html, '<h3>Роман Островский</h3>', f'<h3>{about["name"]}</h3>')
    if about.get("role"):
        html = _sub_exact(html, '<div class="role">Руководитель мебельной мастерской Островского</div>',
                          f'<div class="role">{about["role"]}</div>')
    if about.get("text"):
        html = _sub_exact(html, '<p>С командой изготавливаем кухни и корпусную мебель по индивидуальным проектам — с учётом ваших идей, размеров и задач.</p>',
                          f'<p>{about["text"]}</p>')
    if about.get("kicker"):
        html = _sub_exact(html, '<div class="kicker">О руководителе</div>',
                          f'<div class="kicker">{about["kicker"]}</div>')
    if about.get("title"):
        html = _sub_exact(html, '<h2>Кухни и мебель под ключ — с заботой о деталях</h2>',
                          f'<h2>{about["title"]}</h2>')
    if about.get("body"):
        html = _sub_exact(html, '<p>Мы помогаем с планировкой и подбором материалов, предлагаем решения даже для сложных задач — когда другие разводят руками. Ведём вас от консультации и замера до сборки и установки.</p>',
                          f'<p>{about["body"]}</p>')
    feats = about.get("features")
    if isinstance(feats, list) and feats:
        block = "<ul class=\"features\">\n" + "\n".join(f"          <li>{x}</li>" for x in feats) + "\n        </ul>"
        html = re.sub(r'<ul class="features">.*?</ul>', block, html, count=1, flags=re.S)

    # Фоны
    bg_map = {
        "hero": hero.get("bg"),
        "stats": (d.get("stats") or {}).get("bg"),
        "about": about.get("bg"),
        "consult": consult.get("bg"),
        "works": works.get("bg"),
        "reviews": reviews.get("bg"),
        "services": services.get("bg"),
        "process": process.get("bg"),
        "guarantees": guarantees.get("bg"),
        "cities": cities.get("bg"),
        "cta": cta.get("bg"),
        "contacts": contacts.get("bg"),
    }
    old_bgs = {
        "hero": "https://sun9-70.vkuserphoto.ru/s/v1/ig2/s4A0AFD1sjqbbnq-mAfS6e6lCbOTfaw6skzD08T04rMk8FkgYcORaFyMLFJIPcR9EamDGrZ3fDDamkpzifiUnmkO.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x241,480x321,540x361,640x428,720x481,1080x722,1280x855,1440x962,2560x1711&from=bu&u=udyioV6Vl_ghNhYbFZ9zjc-ZU_IjlhkVV114xfpUZJs&cs=1280x0",
        "stats": "https://sun9-20.vkuserphoto.ru/s/v1/ig2/9W8TzKo3y8t8-s63NRmlys3yJtHJAKPBOp2QIyuqMSTinG9q-UFuD5sYkz4wbd7QZDv7wQxsZlldmCrAM-PzPlDJ.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,1800x1200&from=bu&u=kySpH3qK1oaqlWr8kbrP_y7iDDbASMEGWuJ5dgxf5MU&cs=1280x0",
        "about": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/_uJbJ-Gw0zJ3jVPyc4QJRGUErYM5zju63UDQM6FFDezILgQ54i5ycLVvhgSHl5hHPVIKikt0AL9V6DrmqDH7G5C6.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2208x1656&from=bu&u=9_d3vo4cDIif_5OxDZbDgMLFC1xuAQSKRY1zAPscIwM&cs=1280x0",
        "consult": "https://sun9-41.vkuserphoto.ru/s/v1/ig2/qi7m_VnJPio2P4oKJhNr6X-9HJD2kCt6f98XGtveyiAxhJ4ru17yVoibjERFJ4-ZWDOm8Lr7xGMwRP6dSudvgPnG.jpg?quality=95&as=32x43,48x64,72x96,108x144,160x213,240x320,360x480,480x640,540x720,640x853,720x960,1080x1440,1280x1707,1440x1920,1920x2560&from=bu&u=myRGe7iEVeLqDstzbpBsld7P0jp7l04_xCLynpcz4So&cs=1280x0",
        "works": "https://sun9-32.vkuserphoto.ru/s/v1/ig2/ipQDYrxkEiu9wFqxHUIJNhf4YERP29pOrzOhJ2hTcO6Z-fqWBrPA9D1vCltHlp9RltkldMRefKPMMkB8aD8jhZfR.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=q3wKCscaGbBU8n3umOUNA0wOvLkQBDAVXIkzDrivHgk&cs=1280x0",
        "reviews": "https://sun9-64.vkuserphoto.ru/s/v1/ig2/wllk0NJeZqqGu0oNhLoLS7k3FJSugAEpIBElk8HeWwp_EqOH7dKCix844jHZRQwXWkISHmdmXW9hWEaFuC-CCB84.jpg?quality=95&as=32x21,48x32,72x48,108x72,160x107,240x160,360x240,480x320,540x360,640x427,720x480,1080x720,1280x853,1440x960,2560x1707&from=bu&u=T5NJHPubDiY9E_IwXkmzI6uExoeA0QSNz39xjf4UD5M&cs=1280x0",
        "services": "https://sun9-88.vkuserphoto.ru/s/v1/ig2/vCipZmkZdy5Ix0cFh98i0yhNAYynqzh2gm00rWx5Qr019O4RHjwcs7pN6iKT4L_d1vanDAbUJ9JRrHj_uw13YVhg.jpg?quality=95&as=32x44,48x66,72x99,108x149,160x220,240x331,360x496,480x661,540x744,640x882,720x992,1080x1488,1280x1764,1440x1984,1858x2560&from=bu&u=lrbIDUwRUQKMEvaw12w2pRXFBLE0sHCmc6AYF8H7CIA&cs=1280x0",
        "process": "https://sun9-39.vkuserphoto.ru/s/v1/ig2/xiwu_WFFyjmJc4_VAOD1BHikAdMqBy9N-SuKyiWu7xC8OYE-pfhtW5GkOyO5No0KjOrNQUwcgOW3Gr2bCnjvFp2H.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=VpmAnVyzkXcBCcJLy2DSlVkJJG2zYnSPbLzk7-TXGGk&cs=1280x0",
        "guarantees": "https://sun9-50.vkuserphoto.ru/s/v1/ig2/C_b5sF8D1xkYdXe0s1BPq0c52G5b_U0r8MpWIaYYJzh9CXIE4qk0Q3rnZh2FuNZhpnp78BBveTceOk2Js-tECU_z.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=YCey971XM2nuNjhkwSaIOfPMTMneMAyHLaPyHT4mLyY&cs=1280x0",
        "cities": "https://sun9-87.vkuserphoto.ru/s/v1/ig2/WHkPw7TZze6TV4t2q6Yr2pw61S1zWDeDyp8Dbe2IFm31aAuhXVSQ2DUTnM6AIt5u3cLTp9mh-YN2b_Lb0q5iHCFu.jpg?quality=95&as=32x40,48x60,72x90,108x134,160x199,240x298,360x448,480x597,540x671,640x796,720x895,1080x1343,1280x1591,1440x1790,2059x2560&from=bu&u=bQW477ZK7yLopHDa2oCbH-uA483cvDm58BTlNs29AoE&cs=1280x0",
        "contacts": "https://sun9-52.vkuserphoto.ru/s/v1/ig2/iD_ZIKN3aW1Ml52LPM3C65Qa7raIjG1CUC-fRrbHZEdxtU9hrsvTAh80W9sM3wI2hBUlsHc86fnHiG43aAOPlRuP.jpg?quality=95&as=32x24,48x36,72x54,108x81,160x120,240x180,360x270,480x360,540x405,640x480,720x540,1080x810,1280x960,1440x1080,2560x1920&from=bu&u=mdGpdzTBkRhwLQzuIJS1nz6l-_CWqdnxhW1cwsXNCx8&cs=1080x0",
    }
    for key, new_bg in bg_map.items():
        if new_bg and key in old_bgs:
            html = html.replace(old_bgs[key], new_bg)

    # Works
    items = works.get("items")
    if isinstance(items, list) and items:
        block = ""
        for it in items:
            it = it or {}
            url = it.get("url", "")
            alt = it.get("alt", "")
            if not url:
                continue
            block += (f'<div class="car-slide"><img loading="lazy" decoding="async" '
                      f'src="{url}" alt="{alt}"></div>\n        ')
        if block:
            html = re.sub(
                r'<div class="car-track" id="carTrack">.*?</div>\s*<button class="car-nav car-next" id="carNext">',
                '<div class="car-track" id="carTrack">\n        ' + block.strip() +
                '\n      </div>\n      <button class="car-nav car-next" id="carNext">',
                html, count=1, flags=re.S)

    # Reviews
    rev_items = reviews.get("items")
    if isinstance(rev_items, list) and rev_items:
        block = ""
        for r in rev_items:
            r = r or {}
            name = r.get("name", "")
            sub = r.get("sub", "")
            stars = "★" * int(r.get("stars", 5))
            avatar = r.get("avatar", "")
            text = r.get("text", "")
            video = r.get("video", "")
            video_poster = r.get("video_poster", "") or VIDEO_POSTER
            ava_html = (f'<img class="rev-ava" loading="lazy" decoding="async" width="50" height="50" '
                        f'src="{avatar}" alt="Отзыв: {name}">') if avatar else ""
            video_html = ""
            if video:
                video_html = (f'<div class="rev-video"><div class="video-box" data-src="{video}" '
                              f'style="background-image:url(\'{video_poster}\')" role="button">'
                              f'<span class="vb-play"><svg viewBox="0 0 24 24">'
                              f'<path d="M8 5v14l11-7z"/></svg></span></div></div>')
            block += (f'<div class="rev-card"><div class="rev-head">{ava_html}'
                      f'<div><div class="rev-name">{name}</div>'
                      f'<div class="rev-sub">{sub}</div></div>'
                      f'<div class="rev-stars">{stars}</div></div>'
                      f'{video_html}<p class="rev-text">{text}</p></div>\n        ')
        if block:
            html = re.sub(
                r'<div class="car-track rev-track" id="revTrack">.*?</div>\s*<button class="car-nav car-next" id="revNext">',
                '<div class="car-track rev-track" id="revTrack">\n        ' + block.strip() +
                '\n      </div>\n      <button class="car-nav car-next" id="revNext">',
                html, count=1, flags=re.S)

    # Services
    svc_items = services.get("items")
    if isinstance(svc_items, list) and svc_items:
        block = ""
        for s in svc_items:
            s = s or {}
            icon = s.get("icon", "")
            title = s.get("title", "")
            text = s.get("text", "")
            block += (f'<div class="svc reveal"><svg viewBox="0 0 24 24"><path d="{icon}"/></svg>'
                      f'<h3>{title}</h3><p>{text}</p></div>\n      ')
        if block:
            html = re.sub(
                r'<div class="svc-grid">.*?</div>\s*</div></div>\s*</section>\s*<section class="panel" id="process">',
                '<div class="svc-grid">\n      ' + block.strip() +
                '\n    </div>\n  </div></div>\n</section>\n\n<section class="panel" id="process">',
                html, count=1, flags=re.S)

    # Process
    st_items = process.get("items")
    if isinstance(st_items, list) and st_items:
        block = ""
        for s in st_items:
            s = s or {}
            n = s.get("n", "")
            title = s.get("title", "")
            text = s.get("text", "")
            block += (f'<div class="step reveal"><div class="n">{n}</div>'
                      f'<h3>{title}</h3><p>{text}</p></div>\n      ')
        if block:
            html = re.sub(
                r'<div class="steps">.*?</div>\s*</div></div>\s*</section>\s*<section class="panel panel--dark">',
                '<div class="steps">\n      ' + block.strip() +
                '\n    </div>\n  </div></div>\n</section>\n\n<section class="panel panel--dark">',
                html, count=1, flags=re.S)

    # Guarantees
    g_items = guarantees.get("items")
    if isinstance(g_items, list) and g_items:
        block = ""
        for g in g_items:
            g = g or {}
            icon = g.get("icon", "")
            title = g.get("title", "")
            text = g.get("text", "")
            block += (f'<div class="guar reveal"><div class="ico"><svg viewBox="0 0 24 24">'
                      f'<path d="{icon}"/></svg></div><h3>{title}</h3><p>{text}</p></div>\n      ')
        if block:
            html = re.sub(
                r'<div class="guar-grid">.*?</div>\s*</div></div>\s*</section>\s*<section class="panel panel--center panel--dark" id="cities">',
                '<div class="guar-grid">\n      ' + block.strip() +
                '\n    </div>\n  </div></div>\n</section>\n\n<section class="panel panel--center panel--dark" id="cities">',
                html, count=1, flags=re.S)

    # Cities
    c_items = cities.get("items")
    if isinstance(c_items, list) and c_items:
        block = ""
        for c in c_items:
            c = c or {}
            name = c.get("name", "")
            text = c.get("text", "")
            block += (f'<div class="city reveal"><div class="city-name">{name}</div>'
                      f'<div class="city-line"></div><p>{text}</p></div>\n      ')
        if block:
            html = re.sub(
                r'<div class="city-grid">.*?</div>\s*</div></div>\s*</section>\s*<section class="panel panel--center panel--dark">\s*<div class="bg"',
                '<div class="city-grid">\n      ' + block.strip() +
                '\n    </div>\n  </div></div>\n</section>\n\n<section class="panel panel--center panel--dark">\n  <div class="bg"',
                html, count=1, flags=re.S)

    # CTA
    if cta.get("title"):
        html = _sub_exact(html, '<h2 class="reveal shimmer">Готовы обсудить вашу мебель?</h2>',
                          f'<h2 class="reveal shimmer">{cta["title"]}</h2>')
    if cta.get("text"):
        html = _sub_exact(html, '<p class="reveal">Позвоните нам — бесплатно проконсультируем, посчитаем и запишем на замер.</p>',
                          f'<p class="reveal">{cta["text"]}</p>')
    if cta.get("button"):
        html = _sub_exact(html, '>📞 Позвонить специалисту<', f'>{cta["button"]}<')

    # Contacts
    if contacts.get("kicker"):
        html = _sub_exact(html, '<div class="kicker">Контакты</div>',
                          f'<div class="kicker">{contacts["kicker"]}</div>')
    if contacts.get("title"):
        html = _sub_exact(html, '<h2>Создадим мебель, о которой вы мечтали</h2>',
                          f'<h2>{contacts["title"]}</h2>')
    if contacts.get("subtitle"):
        html = _sub_exact(html, '<p>Позвоните или напишите — ответим быстро и подскажем по всем вопросам.</p>',
                          f'<p>{contacts["subtitle"]}</p>')
    if contacts.get("regions"):
        html = _sub_exact(html, '<div class="val">Ростов-на-Дону, Батайск, Азов</div>',
                          f'<div class="val">{contacts["regions"]}</div>')

    # Footer
    if footer.get("line"):
        html = _sub_exact(html, '<p>Кухни и корпусная мебель на заказ — Ростов, Батайск, Азов</p>',
                          f'<p>{footer["line"]}</p>')
    if footer.get("copyright"):
        html = re.sub(r'© <span id="year"></span>[^<]*',
                      f'© <span id="year"></span> {footer["copyright"]}',
                      html, count=1)

    # Вставляем анимации
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


# =====================================================================
# АДМИНКА
# =====================================================================
ADMIN_LOGIN_HTML = """<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Вход в админку</title>
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
  <label>Логин</label><input type="text" name="login" required autofocus>
  <label>Пароль</label><input type="password" name="password" required>
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
    <button class="btn btn-gold" onclick="saveAll()">💾 Сохранить</button>
    <a class="btn btn-red" href="/admin/logout">Выйти</a>
  </div>
</header>
<div class="layout">
  <nav class="side">
    <a data-tab="seo">🔍 SEO</a>
    <a data-tab="brand">🏷 Бренд</a>
    <a data-tab="hero" class="active">🏠 Главный</a>
    <a data-tab="about">👤 О специалисте</a>
    <a data-tab="consult">💬 Консультация</a>
    <a data-tab="works">🖼 Работы</a>
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
async function loadData(){const r=await fetch('/admin/api/data',{credentials:'same-origin'});if(r.status===401){location.href='/admin/login';return;}DATA=await r.json();render();checkStatus();}
async function saveAll(){const r=await fetch('/admin/api/save',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(DATA)});if(r.ok){toast('✅ Сохранено');}else{toast('❌ Ошибка',1);}}
function getPath(o,p){return p.split('.').reduce((a,k)=>a==null?undefined:a[k],o);}
function setPath(o,p,v){const a=p.split('.');let c=o;for(let i=0;i<a.length-1;i++){const k=a[i],n=a[i+1];if(c[k]==null)c[k]=/^\d+$/.test(n)?[]:{};c=c[k];}c[a[a.length-1]]=v;}
function field(l,p,o){o=o||{};const v=getPath(DATA,p);const i=o.rows?`<textarea data-path="${p}" rows="${o.rows}">${esc(v)}</textarea>`:`<input type="text" data-path="${p}" value="${esc(v)}">`;return `<div class="field"><label>${l}</label>${i}</div>`;}
function imgField(l,p){const v=getPath(DATA,p);return `<div class="field"><label>${l}</label><input type="text" data-path="${p}" value="${esc(v)}"><label class="drop">📁 загрузить файл<input type="file" accept="image/*" style="display:none" onchange="uploadImg(this,'${p}')"></label>${v?`<img class="img-preview" src="${esc(v)}" onerror="this.style.display='none'">`:''}</div>`;}
function bindInputs(){document.querySelectorAll('[data-path]').forEach(el=>{el.addEventListener('input',()=>{setPath(DATA,el.dataset.path,el.value);});});}
async function uploadImg(inp,p){const f=inp.files[0];if(!f)return;if(f.size>8*1024*1024){toast('>8МБ',1);return;}const fd=new FormData();fd.append('file',f);toast('Загрузка...');const r=await fetch('/admin/api/upload',{method:'POST',body:fd,credentials:'same-origin'});if(!r.ok){toast('Ошибка',1);return;}const j=await r.json();setPath(DATA,p,j.url);toast('✅');render();}
function addItem(p,v){getPath(DATA,p).push(v);render();}
function delItem(p,i){if(!confirm('Удалить?'))return;getPath(DATA,p).splice(i,1);render();}
function moveItem(p,i,d){const a=getPath(DATA,p),j=i+d;if(j<0||j>=a.length)return;[a[i],a[j]]=[a[j],a[i]];render();}

const TABS={};
TABS.seo=()=>`<h2>SEO</h2><p class="hint">Пустые поля оставят оригинал из HTML.</p>${field('Title','seo.title',{rows:2})}${field('Description','seo.description',{rows:3})}${field('Keywords','seo.keywords',{rows:3})}${field('OG-картинка','seo.og_image')}`;
TABS.brand=()=>`<h2>Бренд</h2><div class="row">${field('Название','brand.name')}${field('Подзаголовок','brand.sub')}</div>${imgField('Логотип','brand.logo_url')}<div class="row">${field('Телефон (визуал)','brand.phone')}${field('Телефон (tel:)','brand.phone_raw')}</div><div class="row">${field('Telegram','brand.telegram')}${field('VK','brand.vk')}</div>`;
TABS.hero=()=>`<h2>Главный экран</h2>${field('Надзаголовок','hero.eyebrow')}${field('Заголовок до','hero.title_before')}${field('Заголовок выделенный','hero.title_em')}${field('Подзаголовок','hero.sub',{rows:3})}<div class="row">${field('Кнопка 1','hero.btn1')}${field('Кнопка 2','hero.btn2')}</div>${imgField('Фон','hero.bg')}`;
TABS.about=()=>`<h2>О специалисте</h2>${imgField('Фото','about.photo')}<div class="row">${field('Имя','about.name')}${field('Должность','about.role')}</div>${field('Описание','about.text',{rows:3})}${field('Надзаголовок','about.kicker')}${field('Заголовок','about.title')}${field('Текст','about.body',{rows:4})}${imgField('Фон','about.bg')}`;
TABS.consult=()=>`<h2>Консультация</h2>${field('Надзаголовок','consult.kicker')}${field('Заголовок','consult.title')}${field('Текст (HTML)','consult.text',{rows:4})}${imgField('Фон','consult.bg')}`;
TABS.works=()=>`<h2>Работы</h2>${field('Надзаголовок','works.kicker')}${field('Заголовок','works.title')}${field('Подзаголовок','works.subtitle')}${imgField('Фон','works.bg')}<div class="item-head" style="margin-top:20px"><strong>Фото</strong></div>${(DATA.works&&DATA.works.items||[]).map((it,i)=>`<div class="item"><div class="item-head"><strong>#${i+1}</strong><div><button class="btn mini" onclick="moveItem('works.items',${i},-1)">↑</button> <button class="btn mini" onclick="moveItem('works.items',${i},1)">↓</button> <button class="btn btn-red mini" onclick="delItem('works.items',${i})">Удалить</button></div></div>${imgField('Картинка',`works.items.${i}.url`)}${field('Alt',`works.items.${i}.alt`)}</div>`).join('')}<button class="btn" onclick="addItem('works.items',{url:'',alt:''})">+ Добавить фото</button>`;
TABS.reviews=()=>`<h2>Отзывы</h2>${field('Надзаголовок','reviews.kicker')}${field('Заголовок','reviews.title')}${field('Подзаголовок','reviews.subtitle')}${imgField('Фон','reviews.bg')}<div class="item-head" style="margin-top:20px"><strong>Отзывы</strong></div>${(DATA.reviews&&DATA.reviews.items||[]).map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.name||'')}</strong><div><button class="btn mini" onclick="moveItem('reviews.items',${i},-1)">↑</button> <button class="btn mini" onclick="moveItem('reviews.items',${i},1)">↓</button> <button class="btn btn-red mini" onclick="delItem('reviews.items',${i})">Удалить</button></div></div><div class="row">${field('Имя',`reviews.items.${i}.name`)}${field('Подпись',`reviews.items.${i}.sub`)}</div>${field('Звёзд (1-5)',`reviews.items.${i}.stars`)}${imgField('Аватар',`reviews.items.${i}.avatar`)}${field('Текст',`reviews.items.${i}.text`,{rows:4})}<div class="row">${field('Видео (URL)',`reviews.items.${i}.video`)}${field('Постер видео',`reviews.items.${i}.video_poster`)}</div></div>`).join('')}<button class="btn" onclick="addItem('reviews.items',{name:'',sub:'',stars:5,avatar:'',text:'',video:'',video_poster:''})">+ Добавить отзыв</button>`;
TABS.services=()=>`<h2>Услуги</h2>${field('Надзаголовок','services.kicker')}${field('Заголовок','services.title')}${field('Подзаголовок','services.subtitle')}${imgField('Фон','services.bg')}${(DATA.services&&DATA.services.items||[]).map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.title||'')}</strong><button class="btn btn-red mini" onclick="delItem('services.items',${i})">Удалить</button></div>${field('Название',`services.items.${i}.title`)}${field('Описание',`services.items.${i}.text`,{rows:2})}${field('SVG-иконка (path)',`services.items.${i}.icon`)}</div>`).join('')}<button class="btn" onclick="addItem('services.items',{title:'',text:'',icon:''})">+ Добавить</button>`;
TABS.process=()=>`<h2>Этапы</h2>${field('Надзаголовок','process.kicker')}${field('Заголовок','process.title')}${imgField('Фон','process.bg')}${(DATA.process&&DATA.process.items||[]).map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.n||'')} ${esc(it.title||'')}</strong><button class="btn btn-red mini" onclick="delItem('process.items',${i})">Удалить</button></div><div class="row">${field('Номер',`process.items.${i}.n`)}${field('Заголовок',`process.items.${i}.title`)}</div>${field('Текст',`process.items.${i}.text`,{rows:2})}</div>`).join('')}<button class="btn" onclick="addItem('process.items',{n:'',title:'',text:''})">+ Добавить</button>`;
TABS.guarantees=()=>`<h2>Гарантии</h2>${field('Надзаголовок','guarantees.kicker')}${field('Заголовок','guarantees.title')}${imgField('Фон','guarantees.bg')}${(DATA.guarantees&&DATA.guarantees.items||[]).map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.title||'')}</strong><button class="btn btn-red mini" onclick="delItem('guarantees.items',${i})">Удалить</button></div>${field('Заголовок',`guarantees.items.${i}.title`)}${field('Текст',`guarantees.items.${i}.text`,{rows:2})}${field('SVG path',`guarantees.items.${i}.icon`)}</div>`).join('')}<button class="btn" onclick="addItem('guarantees.items',{title:'',text:'',icon:''})">+ Добавить</button>`;
TABS.cities=()=>`<h2>Города</h2>${field('Надзаголовок','cities.kicker')}${field('Заголовок','cities.title')}${field('Подзаголовок','cities.subtitle')}${imgField('Фон','cities.bg')}${(DATA.cities&&DATA.cities.items||[]).map((it,i)=>`<div class="item"><div class="item-head"><strong>${esc(it.name||'')}</strong><button class="btn btn-red mini" onclick="delItem('cities.items',${i})">Удалить</button></div>${field('Название',`cities.items.${i}.name`)}${field('Описание',`cities.items.${i}.text`,{rows:2})}</div>`).join('')}<button class="btn" onclick="addItem('cities.items',{name:'',text:''})">+ Добавить</button>`;
TABS.cta=()=>`<h2>CTA</h2>${field('Заголовок','cta.title')}${field('Текст','cta.text',{rows:3})}${field('Кнопка','cta.button')}${imgField('Фон','cta.bg')}`;
TABS.contacts=()=>`<h2>Контакты</h2>${field('Надзаголовок','contacts.kicker')}${field('Заголовок','contacts.title')}${field('Подзаголовок','contacts.subtitle',{rows:2})}${field('Регионы','contacts.regions')}${imgField('Фон','contacts.bg')}`;
TABS.footer=()=>`<h2>Подвал</h2>${field('Строка','footer.line')}${field('Копирайт','footer.copyright')}`;

function render(){const a=document.querySelector('nav.side a.active')?.dataset.tab||'hero';document.getElementById('main').innerHTML=(TABS[a]||(()=>'<h2>?</h2>'))();bindInputs();}
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
</script></body></html>"""


# =====================================================================
# HTTP-СЕРВЕР
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
            m = re.search(rb'filename="([^"]*)"', head)
            ctype = b"application/octet-stream"
            for line in head.split(b"\r\n"):
                if line.lower().startswith(b"content-type:"):
                    ctype = line.split(b":", 1)[1].strip()
            return data, ctype, (m.group(1).decode("utf-8", "ignore") if m else "file")
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
            self.send_response(304); self.send_header("ETag", etag)
            self.send_header("Cache-Control", cache); self.end_headers(); return
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
        else:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            if isinstance(body, str):
                self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.send_header("ETag", etag)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location, cache="no-cache", set_cookie=None):
        self.send_response(302); self.send_header("Location", location)
        self.send_header("Cache-Control", cache)
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", "0"); self.end_headers()

    def _read_body(self):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n <= 0 or n > MAX_UPLOAD * 3:
            return b""
        return self.rfile.read(n)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False),
                   "application/json; charset=utf-8")

    def _serve_static(self, path):
        import mimetypes
        safe = path.lstrip("/")
        if not safe or ".." in safe or safe.startswith("."):
            return False
        allowed = {".html", ".txt", ".svg", ".png", ".jpg", ".jpeg", ".ico",
                   ".xml", ".webmanifest", ".json", ".css", ".js", ".webp", ".gif"}
        ext = os.path.splitext(safe)[1].lower()
        if ext not in allowed:
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

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/admin/login":
            self._send(200, ADMIN_LOGIN_HTML.replace("__ERROR__", ""), "text/html; charset=utf-8")
            return
        if path == "/admin/logout":
            _drop_session(self._cookie_token())
            self._redirect("/admin/login",
                           set_cookie="admin_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            return
        if path == "/admin/api/data":
            if not self._is_admin():
                self._json({"error": "unauthorized"}, 401); return
            self._json(load_data(force=True))
            return
        if path == "/admin":
            if not self._is_admin():
                self._redirect("/admin/login"); return
            self._send(200, ADMIN_HTML, "text/html; charset=utf-8")
            return

        if path not in ("/", "/index.html"):
            if self._serve_static(path):
                return

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
            body = self._read_body().decode("utf-8", "ignore")
            p = parse_qs(body)
            login = (p.get("login") or [""])[0]
            password = (p.get("password") or [""])[0]
            if login == ADMIN_LOGIN_ENV and password == ADMIN_PASSWORD_ENV:
                token = _new_session()
                self._redirect("/admin",
                               set_cookie=f"admin_session={token}; Path=/; Max-Age={SESSION_TTL}; HttpOnly; SameSite=Lax")
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
        print("⚠️  supabase не установлен: pip install supabase")
    # Пробуем сразу засеять БД при старте
    try:
        load_data(force=True)
        print("✅ Supabase подключён, данные загружены")
    except Exception as e:
        print(f"⚠️ Supabase: {e}")
    print(f"🚀 Сервер: http://0.0.0.0:{PORT}")
    print(f"🔐 Админка: http://0.0.0.0:{PORT}/admin  (логин: {ADMIN_LOGIN_ENV})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
