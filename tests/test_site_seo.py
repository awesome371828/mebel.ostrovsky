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

    def test_theme_has_final_dark_palette(self):
        css_path = pathlib.Path(__file__).resolve().parents[1] / "site-theme.css"
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("color-scheme:dark!important", css)
        self.assertIn("--ostr-bg:#151613", css)
        self.assertIn(".panel .svc", css)
        self.assertIn("body.admin-shell", css)


if __name__ == "__main__":
    unittest.main()
