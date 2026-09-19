import tempfile
import unittest
from pathlib import Path

from scripts.check_adsense import (
    EXEMPT_PAGES,
    build_report,
    load_rewrites,
    read_ads_txt_publishers,
    sitemap_page_paths,
    url_path_to_file,
)


ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = "pub-2461062743308239"
LOADER = (
    '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
    f'?client=ca-{PUBLISHER}" crossorigin="anonymous"></script>'
)


def write_tree(root: Path, pages: dict[str, str], sitemap: list[str], ads: str | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if ads is not None:
        (root / "ads.txt").write_text(ads, encoding="utf-8")
    locs = "".join(f"<loc>https://freellm.top{path}</loc>" for path in sitemap)
    (root / "sitemap-pages.xml").write_text(f"<urlset>{locs}</urlset>", encoding="utf-8")
    for path, body in pages.items():
        target = url_path_to_file(root, path, load_rewrites(root))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")


VALID_ADS = f"google.com, {PUBLISHER}, DIRECT, f08c47fec0942fa0\n"


class AdsenseGateTests(unittest.TestCase):
    def test_current_tree_passes_the_gate(self):
        report = build_report(ROOT)
        self.assertTrue(report["ok"], report["issues"])
        self.assertEqual(report["ads_txt_publishers"], [PUBLISHER])
        self.assertEqual(report["missing_loader"], [])
        self.assertEqual(report["client_mismatches"], [])
        self.assertEqual(report["noindex_with_loader"], [])

    def test_ads_txt_publisher_is_parsed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ads.txt").write_text(VALID_ADS, encoding="utf-8")
            publishers, problems = read_ads_txt_publishers(root)
            self.assertEqual(publishers, {PUBLISHER})
            self.assertEqual(problems, [])

    def test_ads_txt_missing_is_an_issue(self):
        with tempfile.TemporaryDirectory() as directory:
            publishers, problems = read_ads_txt_publishers(Path(directory))
            self.assertEqual(publishers, set())
            self.assertTrue(any("missing" in problem for problem in problems))

    def test_root_rewrite_resolves_to_the_design_page(self):
        self.assertEqual(
            url_path_to_file(ROOT, "/", load_rewrites(ROOT)),
            ROOT / "design" / "free-china-ai-index.html",
        )

    def test_sitemap_paths_come_from_the_section_sitemaps(self):
        paths = sitemap_page_paths(ROOT)
        self.assertIn("/", paths)
        self.assertIn("/logs/", paths)
        self.assertIn("/skills/", paths)
        self.assertIn("/skills/lab/", paths)

    def test_page_without_loader_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tree(root, {"/about/": "<html></html>"}, ["/about/"], ads=VALID_ADS)
            report = build_report(root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["missing_loader"], ["/about/"])

    def test_page_with_loader_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tree(root, {"/about/": f"<html>{LOADER}</html>"}, ["/about/"], ads=VALID_ADS)
            report = build_report(root)
            self.assertTrue(report["ok"], report["issues"])

    def test_client_outside_ads_txt_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other = LOADER.replace(PUBLISHER, "9999999999999999")
            write_tree(root, {"/about/": f"<html>{other}</html>"}, ["/about/"], ads=VALID_ADS)
            report = build_report(root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["client_mismatches"][0]["path"], "/about/")

    def test_noindex_page_carrying_the_loader_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = f'<html><head><meta name="robots" content="noindex,follow">{LOADER}</head></html>'
            write_tree(root, {"/about/": body}, ["/about/"], ads=VALID_ADS)
            report = build_report(root)
            self.assertFalse(report["ok"])
            self.assertEqual(report["noindex_with_loader"], ["about/index.html"])

    def test_exempt_page_is_skipped_with_its_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exempt_path = sorted(EXEMPT_PAGES)[0]
            write_tree(root, {exempt_path: "<html></html>"}, [exempt_path], ads=VALID_ADS)
            report = build_report(root)
            self.assertTrue(report["ok"], report["issues"])
            self.assertEqual([entry["path"] for entry in report["exempt_pages"]], [exempt_path])

    def test_sitemap_url_without_a_file_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tree(root, {}, ["/missing/"], ads=VALID_ADS)
            report = build_report(root)
            self.assertFalse(report["ok"])
            self.assertTrue(any("/missing/" in issue for issue in report["issues"]))

    def test_slot_flag_reflects_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_tree(root, {"/about/": f"<html>{LOADER}</html>"}, ["/about/"], ads=VALID_ADS)
            self.assertFalse(build_report(root, slot="")["slot_configured"])
            self.assertFalse(build_report(root, slot="not-a-slot")["slot_configured"])
            self.assertTrue(build_report(root, slot="1234567890")["slot_configured"])


if __name__ == "__main__":
    unittest.main()
