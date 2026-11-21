import pathlib
import unittest
import xml.etree.ElementTree as ET

import mebel


class SiteRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(__file__).resolve().parents[1]
        cls.css = mebel.THEME_CSS
        cls.premium = mebel.THEME_CSS
        cls.redesign = mebel.THEME_CSS
        cls.page = mebel.PAGE

    def test_robots_advertises_sitemap_and_hides_admin(self):
        robots = mebel.build_robots(mebel.DEFAULT_DATA)
        self.assertIn("Sitemap: https://www.кухниостровский.рф/sitemap.xml", robots)
        self.assertIn("Disallow: /admin", robots)

    def test_sitemap_is_valid_and_contains_city_pages(self):
        root = ET.fromstring(mebel.build_sitemap(mebel.DEFAULT_DATA))
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [node.text for node in root.findall("sm:url/sm:loc", ns)]
        self.assertIn("https://www.кухниостровский.рф/", urls)
        for slug in ("rostov-na-donu", "bataysk", "azov"):
            self.assertIn("https://www.кухниостровский.рф/" + slug + "/", urls)

    def test_canonical_redirect_domain_is_idna_safe(self):
        self.assertEqual(
            mebel._domain_ascii(),
            "https://www.xn--b1albebcsjatkdjj4a.xn--p1ai",
        )

    def test_logo_and_favicon_are_preserved(self):
        source = "https://hliafkrpvmntpctmqwfu.supabase.co/storage/v1/object/public/site-images/logo/logo-256.jpg"
        self.assertIn(source, self.page)
        self.assertIn(source, mebel.build_manifest(mebel.DEFAULT_DATA))
        self.assertIn(source, mebel.favicon_source(mebel.DEFAULT_DATA))

    def test_max_is_kept_as_one_supplied_image_per_control(self):
        self.assertIn('class="max-mark" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSMjcyn3EjLZQPbqynA3RI8DJKygMgRWxAB_a3Jzl1mlA&amp;s=10"', self.page)
        self.assertNotIn('class="max-mark"><svg', self.page)
        self.assertIn('aria-label="Написать в MAX"', self.page)
        self.assertIn("quiz-max", self.page)
        self.assertIn("footer-max", self.page)
        self.assertIn("content:none!important", self.css)

    def test_all_primary_navigation_and_sections_are_present(self):
        for fragment in (
            'href="#about">Руководитель</a>',
            'href="#works">Работы</a>',
            'href="#reviews">Отзывы</a>',
            'href="#services">Услуги</a>',
            'href="#process">Как работаем</a>',
            'href="#cities">Города</a>',
            'href="#contacts">Контакты</a>',
            'href="#consult">Консультация</a>',
            'href="#quiz">Рассчитать проект</a>',
        ):
            self.assertIn(fragment, self.page)
        for section_id in ("top", "about", "consult", "works", "quiz", "reviews", "services", "process", "cities", "contacts"):
            self.assertIn('id="' + section_id + '"', self.page)

    def test_latest_theme_is_linked_and_uses_editorial_palette(self):
        self.assertIn('/site-theme.css?v=20261117-r11', self.page)
        self.assertIn('--ostr-bg:#f4f2ed', self.css)
        self.assertIn('--ostr-ink:#242621', self.css)
        self.assertIn('color-scheme:light', self.css)
        self.assertIn('#top.panel--hero', self.css)
        self.assertIn('#works .car-slide img', self.css)
        self.assertIn('#contacts .contact-grid', self.css)
        self.assertIn('--q-bg:#ded7cb', self.css)
        self.assertIn('--q-teal:#4f9aa2', self.css)
        self.assertIn('@media(max-width:380px)', self.css)
        self.assertIn('@media(max-width:900px)', self.css)
        self.assertIn('#menu li a{display:flex', self.css)

    def test_hero_uses_real_full_bleed_photo_and_fact_panel(self):
        self.assertIn('class="hero-photo"', self.page)
        self.assertIn('{{#if hero.bg}}<img src="{{hero.bg}}"', self.page)
        self.assertIn('class="hero-proof"', self.page)
        self.assertIn("site-premium.css?v=20261117-r14", self.page)
        self.assertIn("54RqB_cEOPzF_Xj9-FdI8pIegVBTKXk1KqQ7UYCmZ6CO7lzkigXLPoiQurkUnKJRXvN60EnbppdZ61nbnwiuVh6I.jpg", self.page)
        self.assertIn("#top .hero-photo img{display:block!important;width:100%!important;height:100%!important;object-fit:cover!important", self.premium)
        self.assertIn("#top .hero-layout{display:grid!important;grid-template-columns:minmax(0,1.15fr) minmax(280px,.85fr)!important", self.premium)
        self.assertIn("@media(max-width:600px)", self.premium)
        self.assertIn("@media(max-width:380px)", self.premium)
        self.assertIn("prefers-reduced-motion:reduce", self.premium)
        self.assertNotIn("Фотографии работ скоро появятся", self.page)
        self.assertNotIn("Отзывы появятся здесь совсем скоро", self.page)
        self.assertNotIn(".img-failed::after", self.page)
        self.assertIn('data-fallback="https://sun9-49.vkuserphoto.ru', self.page)

    def test_about_and_process_do_not_have_inline_dark_backgrounds(self):
        self.assertIn('<section class="panel panel--dark" id="about">', self.page)
        self.assertIn('<section class="panel panel--dark" id="process">', self.page)
        self.assertIn("{{{about.bg}}}", self.page)
        self.assertIn("{{{process.bg}}}", self.page)
        self.assertNotIn('id="about" style="background:#191a17', self.page)
        self.assertNotIn('id="process" style="background:#191a17', self.page)
        self.assertIn('#about>.bg,#process>.bg{display:block!important;opacity:1!important;visibility:visible!important}', self.css)

    def test_final_responsive_photo_design(self):
        premium = mebel.THEME_CSS
        self.assertIn("#about .about{display:grid!important;grid-template-columns:minmax(280px,.72fr)", premium)
        self.assertIn("#about .about-body{display:block!important;align-self:center!important", premium)
        self.assertIn("#contacts .c-ico{display:none!important}", premium)
        self.assertIn("#contacts .c-action svg{display:none!important}", premium)
        for breakpoint in ("max-width:1280px", "max-width:1100px", "max-width:760px", "max-width:540px", "max-width:360px"):
            self.assertIn("@media(" + breakpoint + ")", premium)
        self.assertIn("prefers-reduced-motion:reduce", premium)
        self.assertIn("site-premium.css?v=20261117-r14", self.page)


    def test_hero_is_raised_and_scroll_cue_is_always_visible(self):
        self.assertIn('aria-label="Листайте вниз"', self.page)
        self.assertIn('else}}Листайте', self.page)
        self.assertIn('#top.panel--hero{\n  align-items:center!important;', self.premium)
        self.assertIn('#top .scroll-cue{\n  display:flex!important;', self.premium)

    def test_review_cards_keep_text_visible_and_do_not_expand_blank(self):
        self.assertIn('#reviews .rev-card{\n  display:flex!important;', self.premium)
        self.assertIn('#reviews .rev-text.rv.in{', self.premium)
        self.assertIn('opacity:1!important;', self.premium)
        self.assertIn('aspect-ratio:16/9!important;', self.premium)

    def test_responsive_navigation_and_reduced_motion_rules_exist(self):
        self.assertIn('@media(max-width:860px)', self.css)
        self.assertIn('#menu.open', self.css)
        self.assertIn('max-height:calc(100dvh - 72px)', self.css)
        self.assertIn('@media(prefers-reduced-motion:reduce)', self.css)

    def test_legal_pages_and_404_load_the_shared_theme(self):
        for path in ("/ip", "/privacy", "/personal-data-consent"):
            page = mebel._legal_page(path, mebel.DEFAULT_DATA)
            self.assertIn('/site-theme.css?v=20261117-r11', page)
            self.assertIn('class="legal-card"', page)
            self.assertIn("site-premium.css?v=20261117-r14", page)
        self.assertIn('/site-theme.css?v=20261117-r11', mebel.build_404(mebel.DEFAULT_DATA))
        self.assertIn("site-premium.css?v=20261117-r14", mebel.build_404(mebel.DEFAULT_DATA))

    def test_client_portal_loads_shared_theme(self):
        source = pathlib.Path(mebel.__file__).read_text(encoding="utf-8")
        self.assertIn("site-theme.css?v=20261117-r11", source)
        self.assertIn("site-premium.css?v=20261117-r14", source)
        self.assertIn("Личный кабинет клиента", source)


    def test_unified_redesign_is_loaded_last_and_keeps_content_legible(self):
        self.assertIn('site-redesign.css?v=20261117-r1', self.page)
        self.assertGreater(self.page.index('site-redesign.css?v=20261117-r1'), self.page.index('site-premium.css?v=20261117-r14'))
        for selector in ('#heroTitle{', '#top .scroll-cue{', '#menu li a,#menu li a:visited',
                         '#about .about{display:grid!important;', '#reviews .rev-card{',
                         '#contacts .c-ico svg', '@media(max-width:560px)'):
            self.assertIn(selector, self.redesign)
        self.assertIn('visibility:visible!important', self.redesign)
        self.assertIn('overflow-wrap:normal!important', self.redesign)
        self.assertIn('height:auto!important', self.redesign)
        self.assertIn('prefers-reduced-motion:reduce', self.redesign)


    def test_all_visual_styles_are_embedded_in_mebel_py(self):
        source = pathlib.Path(mebel.__file__).read_text(encoding="utf-8")
        self.assertIn("THEME_CSS =", source)
        self.assertIn("OSTROVSKY_SINGLE_FILE_THEME_V1", mebel.THEME_CSS)
        self.assertIn("#contacts .c-ico{display:flex!important", mebel.THEME_CSS)
        self.assertIn("#process .step *{color:#f5f3ed!important", mebel.THEME_CSS)

    def test_theme_links_are_inlined_before_html_is_sent(self):
        html = '<html><head><link rel="stylesheet" href="/site-theme.css?v=1"><link rel="stylesheet" href="/site-premium.css?v=2"><link rel="stylesheet" href="/site-redesign.css?v=3"></head></html>'
        rendered = mebel._inline_theme_styles(html)
        self.assertIn('id="ostUnifiedTheme"', rendered)
        self.assertEqual(rendered.count('<style id="ostUnifiedTheme">'), 1)
        self.assertNotIn('href="/site-theme.css', rendered)
        self.assertNotIn('href="/site-premium.css', rendered)
        self.assertNotIn('href="/site-redesign.css', rendered)



    def test_public_pages_apply_embedded_theme_and_animations_are_default_on(self):
        source = pathlib.Path(mebel.__file__).read_text(encoding="utf-8")
        self.assertIn("html = _inline_theme_styles(html)", source)
        self.assertIn("html=_inline_theme_styles(html)", source)
        self.assertIn("OSTROVSKY_CONTRAST_HOTFIX_20261121", source)
        self.assertIn("var reduced=OFF;", source)
        self.assertNotIn("var reduced=OFF||prefersReduced", source)
        self.assertIn("#contacts .contact-info *", mebel.THEME_CSS)
        self.assertIn("#about .about-body *", mebel.THEME_CSS)


    def test_quhni_inspired_theme_is_the_final_embedded_public_theme(self):
        source = pathlib.Path(mebel.__file__).read_text(encoding="utf-8")
        self.assertIn("OSTROVSKY_QUHNI_INSPIRED_SYSTEM_20261121", source)
        self.assertIn("THEME_CSS += r\"\"\"", source)
        self.assertIn("--q-bg:#f4f2ed", mebel.THEME_CSS)
        self.assertIn("--q-paper:#fffefa", mebel.THEME_CSS)
        self.assertIn("--q-teal:#4f9aa2", mebel.THEME_CSS)
        self.assertIn("#top .hero-photo img", mebel.THEME_CSS)
        self.assertIn("#about .about-body", mebel.THEME_CSS)
        self.assertIn("#contacts .contact-info", mebel.THEME_CSS)
        self.assertIn("@media(max-width:600px)", mebel.THEME_CSS)

    def test_embedded_theme_is_applied_to_every_html_response(self):
        html = '<!doctype html><html><head><link rel="stylesheet" href="/site-theme.css"></head><body></body></html>'
        rendered = mebel._inline_theme_styles(html)
        self.assertIn("OSTROVSKY_QUHNI_INSPIRED_SYSTEM_20261121", rendered)
        self.assertIn("--q-bg:#f4f2ed", rendered)
        self.assertNotIn('href="/site-theme.css"', rendered)
        self.assertEqual(rendered.count('id="ostUnifiedTheme"'), 1)


    def test_public_site_copy_is_consistent_and_polished(self):
        ctx = mebel._normalize_context(mebel.DEFAULT_DATA)
        self.assertEqual(ctx["hero"]["title_before"], "Кухни и мебель ")
        self.assertEqual(ctx["hero"]["title_em"], "под ваши задачи")
        self.assertIn("от замера до установки", ctx["hero"]["sub"])
        self.assertEqual(ctx["about"]["kicker"], "О мастерской")
        self.assertEqual(ctx["works"]["title"], "Мебель в реальных интерьерах")
        self.assertEqual(ctx["contacts"]["title"], "Давайте обсудим вашу мебель")
        self.assertEqual(ctx["quiz"]["submit_label"], "Отправить заявку")
        self.assertEqual(ctx["stats"]["items"][1]["label"], "города работы")
        self.assertEqual(ctx["local_seo"]["cities"][2]["title"], "Кухни и мебель на заказ в Азове — Кухни Островский")
        self.assertIn("Я согласен(на)", mebel.PAGE)
        self.assertIn("Пожалуйста, подтвердите согласие", mebel.PAGE)
        self.assertNotIn("Удобнее напрямую?", mebel.PAGE)

    def test_editorial_copy_does_not_rewrite_customer_testimonials(self):
        ctx = mebel._normalize_context(mebel.DEFAULT_DATA)
        self.assertEqual(ctx["reviews"]["items"][0]["name"], mebel.DEFAULT_DATA["reviews"]["items"][0]["name"])
        self.assertEqual(ctx["reviews"]["items"][0]["text"], mebel.DEFAULT_DATA["reviews"]["items"][0]["text"])



if __name__ == "__main__":
    unittest.main()
