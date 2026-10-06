import unittest

from scripts.audit_all_pages import AuditParser


class AuditAllPagesParserTests(unittest.TestCase):
    def test_metadata_attribute_order_is_irrelevant(self):
        parser = AuditParser()
        parser.feed(
            '<html><head>'
            '<meta content="index,follow" name="robots">'
            '<meta content="Useful page" name="description">'
            '<link href="https://freellm.top/example/" rel="canonical">'
            '</head><body><h1 id="hero">Hello</h1></body></html>'
        )
        self.assertEqual(parser.robots, "index,follow")
        self.assertEqual(parser.description, "Useful page")
        self.assertEqual(parser.canonical, "https://freellm.top/example/")
        self.assertEqual(parser.h1_count, 1)
        self.assertEqual(parser.ids, ["hero"])

    def test_noindex_page_does_not_need_index_metadata(self):
        parser = AuditParser()
        parser.feed('<meta content="noindex,nofollow" name="robots"><div id="tool"></div>')
        self.assertIn("noindex", parser.robots)
        self.assertEqual(parser.description, "")
        self.assertEqual(parser.canonical, "")


if __name__ == "__main__":
    unittest.main()
