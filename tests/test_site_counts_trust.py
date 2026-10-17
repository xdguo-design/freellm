"""Series 1 (2026-10-10 audit): one count source across pages, no unsourced marketing numbers."""
import json
import re
from pathlib import Path

import pytest

from scripts.site_counts import COUNT_DEFINITIONS, compute_site_counts, is_active_offer, reference_date_for

ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _json(relative: str):
    return json.loads(_read(relative))


@pytest.fixture(scope="module")
def summary() -> dict:
    return _json("data/scan-summary.json")


@pytest.fixture(scope="module")
def expected_counts(summary) -> dict:
    offers = _json("data/offers.json")
    models = _json("data/models.json")
    return compute_site_counts(offers, models, reference_date_for(summary["date"]))


def test_count_helper_definitions():
    offers = [
        {"id": "a", "status": "verified"},
        {"id": "b", "status": "expired"},
        {"id": "c", "status": "verified", "expires_at": "2026-10-01"},
        {"id": "d", "status": "needs_review", "expires_at": "2026-12-31"},
    ]
    counts = compute_site_counts(offers, [{"id": "m1"}, {"id": "m2"}], "2026-10-10")
    assert counts == {"offers": 2, "offersTotal": 4, "offersExpired": 2, "models": 2}
    assert is_active_offer(offers[3], "2026-10-10")
    assert reference_date_for("2026-10-10") == "2026-10-10"
    for key in ("offers", "offersTotal", "offersExpired", "models", "scannedModels", "scannedOffers"):
        assert COUNT_DEFINITIONS[key]


def test_scan_summary_carries_the_shared_counts(summary, expected_counts):
    for key, value in expected_counts.items():
        assert summary[key] == value, key
    assert summary["offersTotal"] == summary["offers"] + summary["offersExpired"]
    assert summary["countDefinitions"] == COUNT_DEFINITIONS
    # Scan coverage stays available but under its own, explicit keys.
    assert isinstance(summary["scannedModels"], int)
    assert isinstance(summary["scannedOffers"], int)


def test_homepage_counts_agree(summary):
    home = _read("design/free-china-ai-index.html")
    offers, total, expired = summary["offers"], summary["offersTotal"], summary["offersExpired"]
    assert f'<b id="heroCount">{offers}</b>' in home
    assert f'<b data-category-count="all">{offers}</b>' in home
    assert re.search(rf'data-filter="all"[^>]*>全部 <em>{offers}</em>', home)
    assert re.search(rf'data-filter="expired"[^>]*>已结束 <em>{expired}</em>', home)
    assert re.search(rf'id="catalog-result-count"[^>]*>{offers} 个当前有效资源（存档共 {total} 条，{expired} 条已结束）<', home)
    assert f'data-scan-stat="offers">{offers}</strong>' in home
    assert f'data-scan-stat="models">{summary["models"]}</strong>' in home
    # The old competing definitions must be gone from the homepage.
    for stale in ("条最近扫描资源记录", "个当前有效入口（共存档", "口径不同"):
        assert stale not in home


def test_about_logs_models_and_english_hubs_agree(summary):
    models, offers = summary["models"], summary["offers"]
    about = _read("about/index.html")
    for key in ("models", "offers", "offersTotal", "offersExpired", "newCount"):
        assert f'data-scan-stat="{key}">{summary[key]}</strong>' in about, key
    assert f'<time data-scan-date>{summary["snapshotDate"]}</time>' in about

    logs = _read("logs/index.html")
    assert f"<span>模型目录</span><strong>{models}</strong>" in logs
    assert f"<span>当前有效资源</span><strong>{offers}</strong>" in logs

    models_page = _read("models/index.html")
    assert f"完整目录共 {models} 条模型记录" in models_page
    assert f"完整模型目录（{models} 条）" in models_page
    assert f"{models}+" not in models_page
    all_models = _read("models/all/index.html")
    assert f"共 {models} 条记录" in all_models

    for relative in ("en/index.html", "en/about/index.html", "en/logs/index.html", "en/models/index.html",
                     "en/models/all/index.html", "en/providers/index.html"):
        page = _read(relative)
        assert f'data-en-stat="models">{models}</strong>' in page, relative
        assert f'data-en-stat="offers">{offers}</strong>' in page, relative
        assert "Observed offers" not in page


def test_models_page_does_not_show_empty_featured_filter_as_all_models():
    page = _read("models/index.html")
    featured_match = re.search(r'id="featured-model-title">.*?<small>\((\d+)\)</small>', page, re.S)
    featured = int(featured_match.group(1)) if featured_match else 0
    chip = re.search(r'data-model-filter="all"[^>]*>(.*?)</button>', page, re.S).group(1)
    assert "全部模型" not in chip and "全部精选" in chip
    if featured == 0:
        assert "团队复核精选模型" in page
        assert '<div class="model-filter-toolbar" hidden>' in page
        assert '<div class="featured-evidence-filters" hidden>' in page


def test_models_navigation_uses_active_offer_count_and_no_empty_pick_count(summary):
    page = _read("models/index.html")
    assert f"当前有效资源（{summary['offers']}）" in page
    assert f"Active offers ({summary['offers']})" in page
    assert "已核验资源（80+）" not in page
    assert "Verified offers (80+)" not in page
    if 'id="featured-model-title">' in page:
        assert '(0)</small>' not in re.search(r'id="featured-model-title">(.*?)</h2>', page, re.S).group(1)
    assert 'href="#real-evaluation"' in page


def test_homepage_uses_current_footer_year():
    home = _read("design/free-china-ai-index.html")
    assert "© 2026 FreeLLM. All rights reserved." in home
    assert "© 2024 FreeLLM" not in home


FORBIDDEN_MARKETING = (
    "10,000+", "50万+", "300万+", "4.9/5", "用户满意度", "累计使用次数", "精选 AI 技能",
    "开发者与创作者", "12.4k", "1.2k 评价", "论文写作助手", "FreeLLM 官方", "持续创作收益", "🔥",
)


@pytest.mark.parametrize("relative", ["skills/index.html", "js/reference-shell.js", "scripts/build_seo_pages.py"])
def test_no_unsourced_skill_marketing_numbers(relative):
    text = _read(relative)
    for needle in FORBIDDEN_MARKETING:
        assert needle not in text, f"{needle!r} in {relative}"
    assert "4.8 - index" not in text
    for fake in ("usage:'", "rating:'", "reviews:'("):
        assert fake not in text


def test_skill_stars_are_labelled_as_repository_stars():
    page = _read("skills/index.html")
    body = re.sub(r"<script.*?</script>", "", page, flags=re.S)
    assert "★ 10.0" not in body
    # Every rendered star count is explicitly a repository figure.
    for match in re.finditer(r"★ ?[\d.]+k?", body):
        prefix = body[max(0, match.start() - 3):match.start()]
        assert prefix.endswith("仓库 "), body[max(0, match.start() - 40):match.end() + 10]
    # Popular strip shows one Skill per source repository, so repo stars never repeat as if per-Skill.
    popular = re.search(r'<div class="skills-popular-grid">(.*?)</section>', page, re.S).group(1)
    repos = re.findall(r"来源仓库 ([^ <]+) ·", popular)
    assert repos and len(repos) == len(set(repos))


def test_skill_hero_stats_come_from_repo_data():
    page = _read("skills/index.html")
    skills = _json("data/skills.json")
    latest = _json("data/evaluations/skills-latest.json")
    order = ["通过", "部分通过", "未通过", "调用失败"]
    best = []
    for entry in latest["skills"]:
        verdicts = [run.get("verdict") for run in entry.get("runs") or [] if run.get("verdict") in order]
        if verdicts:
            best.append(min(verdicts, key=order.index))
    assert f'data-skill-stat="skills">{len(skills)}</strong>' in page
    assert f'data-skill-stat="freeModelPassed">{best.count("通过")}/{len(best)}</strong>' in page
    tests = _json("data/skill-tests.json")["entries"]
    blocked = sum(1 for entry in tests.values() if entry.get("testLevel") == "blocked")
    assert f'data-skill-stat="sandboxBlocked">{blocked}</strong>' in page
    assert f"显示 {len(skills)} / {len(skills)}" in page
