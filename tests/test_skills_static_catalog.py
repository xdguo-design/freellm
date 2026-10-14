"""Regression checks for FreeLLM Skill catalog and individual guide pages.

Only standard-library XML/HTML and static file checks are used; no network calls.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "skills.json"
GUIDES = ROOT / "skills"
EXPECTED_CATEGORIES = {
    "development": 22, "seo-content": 16, "planning-office": 15,
    "product-design": 10, "writing": 9, "presentations": 8,
    "documents": 7, "data-office": 3, "resume": 3,
    "file-office": 2, "ecommerce": 2, "email-office": 1,
}


def _skills():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_skill_catalog_source_count_and_categories():
    skills = _skills()
    ids = [item["id"] for item in skills]
    assert len(ids) == len(set(ids)) == 98
    assert {
        key: sum(item["category"] == key for item in skills)
        for key in EXPECTED_CATEGORIES
    } == EXPECTED_CATEGORIES
    assert {item["category"] for item in skills} == set(EXPECTED_CATEGORIES)


def test_all_skills_have_unique_indexable_detail_card():
    for skill in _skills():
        path = GUIDES / skill["id"] / "index.html"
        assert path.is_file(), f"Missing detail page: {path}"
        content = path.read_text(encoding="utf-8")
        expected_url = f"https://freellm.top/skills/{quote(skill['id'])}/"
        assert f'<link rel="canonical" href="{expected_url}">' in content
        assert "<h1>" in content and "</h1>" in content
        assert "<title>" in content and "</title>" in content
        assert 'class="detail-grid"' in content
        assert "本站核验与实测记录" in content
        assert "来源、兼容环境与原始说明" in content
        assert "阅读原始 SKILL.md" in content or "打开上游仓库" in content
        assert "</html>" in content


def test_catalog_cards_cover_every_skill():
    catalog = (GUIDES / "catalog" / "index.html").read_text(encoding="utf-8")
    assert 'id="skill-search"' in catalog
    for skill in _skills():
        assert f'href="/skills/{quote(skill["id"])}/"' in catalog
    assert catalog.count('class="card skill"') == 98
    for category in EXPECTED_CATEGORIES:
        assert f'id="{category}"' in catalog
    old_market = (GUIDES / "index.html").read_text(encoding="utf-8")
    assert 'href="/skills/catalog/"' in old_market
    assert 'href="/skills/${encodeURIComponent(skill.id)}/"' in old_market


def test_skill_sitemap_contains_all_detail_urls():
    xml = ET.parse(ROOT / "sitemap-skills.xml").getroot()
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    actual = {entry.text for entry in xml.findall(".//s:loc", ns)}
    expected = {
        "https://freellm.top/skills/catalog/",
        *(f"https://freellm.top/skills/{quote(item['id'])}/" for item in _skills()),
    }
    assert actual == expected
    main_sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    assert "https://freellm.top/sitemap-skills.xml" in main_sitemap
