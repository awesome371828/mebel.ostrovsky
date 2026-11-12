import pathlib
import unittest
import xml.etree.ElementTree as ET

import mebel


class SiteSeoTests(unittest.TestCase):
    def test_robots_advertises_sitemap(self):
        robots = mebel.build_robots(mebel.DEFAULT_DATA)
        self.assertIn("Sitemap: https://www.кухниостровский.рф/sitemap.xml", robots)
        self.assertIn("Disallow: /admin", robots)

    def test_sitemap_is_valid_xml_and_contains_city_pages(self):
        sitemap = mebel.build_sitemap(mebel.DEFAULT_DATA)
        root = ET.fromstring(sitemap)
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

    def test_requested_favicon_is_used_everywhere(self):
        source = "https://hliafkrpvmntpctmqwfu.supabase.co/storage/v1/object/public/site-images/logo/logo-256.jpg"
        self.assertIn(source, mebel.PAGE)
        self.assertIn(source, mebel.build_manifest(mebel.DEFAULT_DATA))
        self.assertIn(source, mebel.favicon_source(mebel.DEFAULT_DATA))

    def test_max_links_are_preserved_in_public_context(self):
        ctx = mebel._normalize_context(mebel.DEFAULT_DATA)
        self.assertEqual(ctx.get("brand", {}).get("max"), "https://max.ru/")
        self.assertTrue(any("max.ru" in str(x.get("href", "")) for x in (ctx.get("footer", {}).get("socials") or []) if isinstance(x, dict)))
        self.assertIn('aria-label="Написать в MAX"', mebel.PAGE)
        self.assertIn("quiz-max", mebel.PAGE)

    def test_theme_has_final_dark_palette(self):
        css_path = pathlib.Path(__file__).resolve().parents[1] / "site-theme.css"
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("color-scheme:dark!important", css)
        self.assertIn("--ostr-bg:#151613", css)
        self.assertIn(".panel .svc", css)
        self.assertIn("body.admin-shell", css)
        self.assertIn("--studio-teal:#86b9b7", css)
        self.assertIn(".section-rail{display:none!important}", css)
        self.assertIn("r3 — coherent dark editorial system", css)
        self.assertIn("#quiz .quiz-options", css)
        self.assertNotIn("max-brand-icon", mebel.PAGE)


    def test_header_and_contact_layout_regressions_are_guarded(self):
        css_path = pathlib.Path(__file__).resolve().parents[1] / "site-theme.css"
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("actual DOM corrections", css)
        self.assertIn("#contacts .contact-grid", css)
        self.assertIn("#about>.bg:after", css)
        self.assertIn("#menu.open", css)
        self.assertIn("font-family:var(--studio-font-body)", css)

    def test_footer_has_max_with_requested_brand_icon(self):
        self.assertIn('class="footer-max"', mebel.PAGE)
        self.assertIn('aria-label="Написать в MAX"', mebel.PAGE)
        self.assertIn("SMjcyn3EjLZQPbqynA3RI8DJKygMgRWxAB_a3Jzl1mlA", mebel.PAGE)


    def test_max_uses_one_real_image_and_consultation_points_to_max(self):
        self.assertIn('class="max-mark" src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSMjcyn3EjLZQPbqynA3RI8DJKygMgRWxAB_a3Jzl1mlA&amp;s=10"', mebel.PAGE)
        self.assertNotIn('class="max-mark"><svg', mebel.PAGE)
        self.assertIn('class="consult-inline-link" href="{{#if brand.max}}', mebel.PAGE)
        self.assertIn('aria-label="Написать в MAX">MAX</a> — расскажем про кухни', mebel.PAGE)
        self.assertNotIn('aria-label="Написать в Telegram">Telegram</a> — расскажем про кухни', mebel.PAGE)

    def test_theme_forces_leader_section_dark_and_disables_duplicate_max_pseudos(self):
        css_path = pathlib.Path(__file__).resolve().parents[1] / "site-theme.css"
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("#about>.bg{display:none!important", css)
        self.assertIn(".quiz-max:before", css)
        self.assertIn("content:none!important", css)
        self.assertIn("OSTR r5 — deterministic dark leader panel", css)


    def test_navigation_restores_all_primary_sections_and_consultation(self):
        self.assertIn('href="#about"', mebel.PAGE)
        self.assertIn('href="#works"', mebel.PAGE)
        self.assertIn('href="#reviews"', mebel.PAGE)
        self.assertIn('href="#services"', mebel.PAGE)
        self.assertIn('href="#process"', mebel.PAGE)
        self.assertIn('href="#cities"', mebel.PAGE)
        self.assertIn('href="#contacts"', mebel.PAGE)
        self.assertIn('href="#consult">Консультация</a>', mebel.PAGE)

    def test_leader_and_process_backgrounds_are_forced_dark(self):
        css_path = pathlib.Path(__file__).resolve().parents[1] / "site-theme.css"
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("#about>.bg,#process>.bg{display:none!important", css)
        self.assertIn("#process .step{background:linear-gradient", css)
        self.assertIn("img.max-mark{", css)
        self.assertIn("background-image:none!important", css)
        self.assertIn("visibility:visible!important", css)



if __name__ == "__main__":
    unittest.main()
