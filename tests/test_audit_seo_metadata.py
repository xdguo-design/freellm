import unittest

from scripts.audit_seo_metadata import (
    _normalize_internal_href,
    _public_path,
    _related_link_issues,
)


class SeoAuditQualityGateTests(unittest.TestCase):
    def test_public_path_maps_generated_index_pages(self):
        self.assertEqual(_public_path("design/free-china-ai-index.html"), "/")
        self.assertEqual(
            _public_path("guides/free-ai-coding-tools/index.html"),
            "/guides/free-ai-coding-tools/",
        )

    def test_internal_href_normalization_ignores_fragments_and_external_hosts(self):
        current = "/guides/free-ai-coding-tools/"
        self.assertEqual(
            _normalize_internal_href(current, "#comparison"),
            "/guides/free-ai-coding-tools/",
        )
        self.assertEqual(
            _normalize_internal_href(current, "https://freellm.top/guides/china-free-ai-api/?x=1#top"),
            "/guides/china-free-ai-api/",
        )
        self.assertIsNone(
            _normalize_internal_href(current, "https://example.com/guides/free-ai-coding-tools/")
        )

    def test_related_link_gate_catches_self_duplicate_url_and_duplicate_anchor(self):
        page = """
        <ul class="link-list">
          <li><a href="/guides/free-ai-coding-tools/">免费 AI 编程工具</a></li>
          <li><a href="/guides/china-free-ai-api/">国内免费 AI API</a></li>
          <li><a href="/guides/china-free-ai-api/#top">国内免费 AI API</a></li>
          <li><a href="/guides/free-openai-compatible-apis/">国内免费 AI API</a></li>
        </ul>
        """
        issues = _related_link_issues(page, "guides/free-ai-coding-tools/index.html")
        self.assertEqual(len(issues["related_self_link"]), 1)
        self.assertEqual(len(issues["related_duplicate_link"]), 1)
        self.assertEqual(len(issues["related_duplicate_anchor"]), 2)

    def test_related_link_gate_accepts_clean_unique_list(self):
        page = """
        <ul class="link-list">
          <li><a href="/models/">模型目录</a></li>
          <li><a href="/guides/china-free-ai-api/">国内免费 AI API</a></li>
          <li><a href="/guides/free-openai-compatible-apis/">免费 OpenAI 兼容 API</a></li>
        </ul>
        """
        issues = _related_link_issues(page, "guides/free-ai-coding-tools/index.html")
        self.assertTrue(all(not rows for rows in issues.values()))


if __name__ == "__main__":
    unittest.main()
