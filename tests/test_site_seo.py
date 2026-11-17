import pathlib
import unittest
import xml.etree.ElementTree as ET

import mebel


class SiteRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = pathlib.Path(__file__).resolve().parents[1]
        cls.css = (cls.root / "site-theme.css").read_text(encoding="utf-8")
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
        self.assertIn('/site-theme.css?v=20261117-r10', self.page)
        self.assertIn('--ostr-bg:#f4f2ed', self.css)
        self.assertIn('--ostr-ink:#242621', self.css)
        self.assertIn('color-scheme:light', self.css)
        self.assertIn('#top.panel--hero', self.css)
        self.assertIn('#works .car-slide img', self.css)
        self.assertIn('#contacts .contact-grid', self.css)
        self.assertIn('--q-bg:#f5f2ec', self.css)
        self.assertIn('--q-teal:#4d9ca8', self.css)
        self.assertIn('#top>.bg{background-image:url(', self.css)
        self.assertIn('@media(max-width:380px)', self.css)
        self.assertIn('54RqB_cEOPzF_Xj9-FdI8pIegVBTKXk1KqQ7UYCmZ6CO7lzkigXLPoiQurkUnKJRXvN60EnbppdZ61nbnwiuVh6I.jpg', self.css)

    def test_about_and_process_do_not_have_inline_dark_backgrounds(self):
        self.assertIn('<section class="panel panel--dark" id="about">', self.page)
        self.assertIn('<section class="panel panel--dark" id="process">', self.page)
        self.assertIn("{{{about.bg}}}", self.page)
        self.assertIn("{{{process.bg}}}", self.page)
        self.assertNotIn('id="about" style="background:#191a17', self.page)
        self.assertNotIn('id="process" style="background:#191a17', self.page)
        self.assertIn('#about>.bg,#process>.bg{display:block!important;opacity:1!important;visibility:visible!important}', self.css)

    def test_responsive_navigation_and_reduced_motion_rules_exist(self):
        self.assertIn('@media(max-width:860px)', self.css)
        self.assertIn('#menu.open', self.css)
        self.assertIn('max-height:calc(100dvh - 72px)', self.css)
        self.assertIn('@media(prefers-reduced-motion:reduce)', self.css)

    def test_legal_pages_and_404_load_the_shared_theme(self):
        for path in ("/ip", "/privacy", "/personal-data-consent"):
            page = mebel._legal_page(path, mebel.DEFAULT_DATA)
            self.assertIn('/site-theme.css?v=20261117-r10', page)
            self.assertIn('class="legal-card"', page)
        self.assertIn('/site-theme.css?v=20261117-r10', mebel.build_404(mebel.DEFAULT_DATA))

    def test_client_portal_loads_shared_theme(self):
        source = pathlib.Path(mebel.__file__).read_text(encoding="utf-8")
        self.assertIn("site-theme.css?v=20261117-r10", source)
        self.assertIn("Личный кабинет клиента", source)


if __name__ == "__main__":
    unittest.main()
