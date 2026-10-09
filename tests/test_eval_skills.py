"""Offline tests for scripts/eval_skills.py (no network: model calls are mocked)."""
import io
import json
import os
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from scripts import eval_skills as es

ROOT = Path(__file__).resolve().parents[1]


class TaskCoverageTests(unittest.TestCase):
    def test_every_skill_has_a_task_with_checks(self):
        tasks = es.load_tasks()
        ids = {s["id"] for s in es.load_skills()}
        self.assertEqual(ids, set(tasks))
        for sid, task in tasks.items():
            self.assertTrue(task["task"].strip(), sid)
            self.assertGreaterEqual(len(task["checks"]), 2, sid)
            for check in task["checks"]:
                self.assertTrue(check["label"], sid)
                es.run_check(check, "")  # every check type is known

    def test_system_prompt_injects_skill_md(self):
        messages, truncated = es.build_messages("obra-brainstorming", "hi")
        self.assertFalse(truncated)
        skill = (ROOT / "data/skill-content/obra-brainstorming.md").read_text(encoding="utf-8")
        self.assertIn(skill, messages[0]["content"])
        self.assertEqual(messages[1], {"role": "user", "content": "hi"})


class CheckTests(unittest.TestCase):
    def test_python_code_compiles_uses_longest_block(self):
        check = {"type": "code_compiles", "langs": ["python"], "label": "x"}
        self.assertTrue(es.run_check(check, "```python\ndef f():\n    return 1\n```")[0])
        self.assertFalse(es.run_check(check, "```python\ndef f(:\n```")[0])
        self.assertFalse(es.run_check(check, "no code")[0])

    def test_html_doc(self):
        check = {"type": "html_doc", "label": "x", "min_chars": 10}
        self.assertTrue(es.run_check(check, "```html\n<!doctype html><html><body>hi</body></html>\n```")[0])
        self.assertFalse(es.run_check(check, "<div>only</div>")[0])

    def test_count_and_not_regex(self):
        self.assertTrue(es.run_check({"type": "count_regex", "pattern": "[?？]", "min": 1, "max": 3, "label": "q"}, "a？b?")[0])
        self.assertFalse(es.run_check({"type": "count_regex", "pattern": "[?？]", "max": 1, "label": "q"}, "a？b?")[0])
        self.assertFalse(es.run_check({"type": "not_regex", "pattern": "delve", "label": "n"}, "let's delve")[0])

    def test_frontmatter_and_order(self):
        self.assertTrue(es.run_check({"type": "frontmatter", "keys": ["name", "description"], "label": "f"},
                                     "---\nname: a\ndescription: b\n---\n# A")[0])
        self.assertTrue(es.run_check({"type": "order", "first": "def test_", "second": "def slug", "label": "o"},
                                     "def test_x(): pass\ndef slugify(): pass")[0])

    def test_grade_verdicts(self):
        task = {"checks": [{"type": "regex", "pattern": "a", "label": "a"}, {"type": "regex", "pattern": "b", "label": "b"},
                           {"type": "regex", "pattern": "c", "label": "c"}]}
        self.assertEqual(es.grade(task, "abc")["verdict"], "通过")
        self.assertEqual(es.grade(task, "ab")["verdict"], "部分通过")
        self.assertEqual(es.grade(task, "x")["verdict"], "未通过")
        self.assertEqual(es.grade(task, "<think>abc</think>x")["verdict"], "未通过")  # reasoning is not graded


class ScrubTests(unittest.TestCase):
    def test_scrub_removes_env_keys_and_bearer(self):
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "gsk_supersecretvalue123"}):
            text = es.scrub("err gsk_supersecretvalue123 Authorization: Bearer abcdefghijkl sk-abcdefghijklmnop")
        self.assertNotIn("supersecret", text)
        self.assertNotIn("abcdefghijkl", text)
        self.assertNotIn("abcdefghijklmnop", text)


class RunOneTests(unittest.TestCase):
    cfg = {"provider": "Mock", "model": "mock-1", "base": "http://x"}

    def task(self):
        return {"task": "t", "checks": [{"type": "regex", "pattern": "OK", "label": "ok"}]}

    def test_success_records_timing_and_excerpt(self):
        caller = lambda cfg, key, msgs: {"ok": True, "output": "OK " + "x" * 2000, "ttftMs": 10, "totalMs": 99, "usage": {}}
        r = es.run_one({"id": "obra-brainstorming"}, self.task(), "m", self.cfg, "k", caller=caller)
        self.assertTrue(r["callOk"])
        self.assertEqual(r["verdict"], "通过")
        self.assertEqual(r["totalMs"], 99)
        self.assertLessEqual(len(r["excerpt"]), es.EXCERPT_CHARS + 1)

    def test_failure_is_labeled_call_failed_and_scrubbed(self):
        with mock.patch.dict(os.environ, {"NVIDIA_API_KEY": "nvapi-secretsecret"}):
            caller = lambda cfg, key, msgs: {"ok": False, "error": "HTTP 401: bad key nvapi-secretsecret"}
            r = es.run_one({"id": "obra-brainstorming"}, self.task(), "m", self.cfg, "k", caller=caller)
        self.assertFalse(r["callOk"])
        self.assertEqual(r["verdict"], "调用失败")
        self.assertIsNone(r["score"])
        self.assertNotIn("secretsecret", r["error"])

    def test_empty_output_is_call_failure(self):
        caller = lambda cfg, key, msgs: {"ok": True, "output": "<think>long</think>", "ttftMs": 1, "totalMs": 2, "usage": {}}
        r = es.run_one({"id": "obra-brainstorming"}, self.task(), "m", self.cfg, "k", caller=caller)
        self.assertEqual(r["verdict"], "调用失败")

    def test_retry_at_most_twice(self):
        calls = []

        def boom(cfg, key, msgs):
            calls.append(1)
            raise urllib.error.HTTPError("u", 429, "rate", {}, io.BytesIO(b"too many"))

        with mock.patch.object(es, "stream_chat", boom):
            r = es.call_with_retry(self.cfg, "k", [], sleep=lambda s: None)
        self.assertFalse(r["ok"])
        self.assertEqual(len(calls), 2)
        self.assertIn("429", r["error"])

    def test_call_too_long_is_not_retried(self):
        calls = []

        def slow(cfg, key, msgs):
            calls.append(1)
            raise es.CallTooLong("超过单次调用上限 420s 被中止")

        with mock.patch.object(es, "stream_chat", slow):
            r = es.call_with_retry(self.cfg, "k", [], sleep=lambda s: None)
        self.assertFalse(r["ok"])
        self.assertEqual(len(calls), 1)
        self.assertIn("上限", r["error"])

    def test_no_retry_after_deadline(self):
        calls = []

        def boom(cfg, key, msgs):
            calls.append(1)
            raise urllib.error.HTTPError("u", 503, "down", {}, io.BytesIO(b"x"))

        with mock.patch.object(es, "stream_chat", boom), mock.patch.object(es, "DEADLINE", [0.0]):
            r = es.call_with_retry(self.cfg, "k", [], sleep=lambda s: None)
        self.assertEqual(len(calls), 1)
        self.assertIn("503", r["error"])

    def test_not_executed_pairs_are_labeled_call_failed(self):
        tasks = es.load_tasks()
        skills = [{"id": sid} for sid in list(tasks)[:2]]
        runs = [{"skillId": skills[0]["id"], "modelId": "modelscope"}]
        missing = es.not_executed(runs, skills, ["modelscope", "nvidia"], tasks)
        self.assertEqual(len(missing), 3)
        for r in missing:
            self.assertEqual(r["verdict"], "调用失败")
            self.assertIsNone(r["score"])
            self.assertIn("未执行", r["error"])

    def test_merge_runs_replaces_only_rerun_pairs(self):
        old = [{"skillId": "a", "modelId": "modelscope", "verdict": "调用失败"},
               {"skillId": "b", "modelId": "modelscope", "verdict": "通过"}]
        new = [{"skillId": "a", "modelId": "zhipu", "verdict": "通过"}]
        merged = es.merge_runs(old, new)
        self.assertEqual(len(merged), 3)  # failed attempt on a stays recorded
        self.assertIn({"skillId": "a", "modelId": "modelscope", "verdict": "调用失败"}, merged)

    def test_followup_models_registered_with_own_limits(self):
        self.assertNotIn("zhipu", es.DEFAULT_MODELS)
        self.assertEqual(es.MODELS["zhipu"]["env"], "ZHIPU_API_KEY")
        self.assertEqual(es.MODELS["zhipu"]["max_tokens"], 4095)
        self.assertEqual(es.MODELS["nvidia_oss"]["model"], "openai/gpt-oss-20b")


class ReviewAndApplyTests(unittest.TestCase):
    def test_manual_review_override_is_marked(self):
        runs = [{"skillId": "a", "modelId": "m", "callOk": True, "verdict": "通过"}]
        out = es.apply_review(runs, {"a": {"m": {"verdict": "未通过", "note": "编造"}}})
        self.assertEqual(out[0]["verdict"], "未通过")
        self.assertEqual(out[0]["judgedBy"], "manual")
        self.assertEqual(out[0]["autoVerdict"], "通过")

    def test_apply_promotes_pending_only(self):
        import tempfile
        tests = {"entries": {
            "a": {"status": "待执行", "testLevel": "blocked", "score": None},
            "b": {"status": "端到端通过", "testLevel": "e2e", "score": 9},
            "c": {"status": "待执行", "testLevel": "blocked", "score": None}}}
        run_ok = {"provider": "P", "model": "M", "callOk": True, "verdict": "部分通过", "score": 7.5,
                  "passedChecks": 3, "totalChecks": 4, "totalMs": 1000}
        run_fail = {"provider": "P", "model": "M", "callOk": False, "verdict": "调用失败", "score": None, "error": "HTTP 500"}
        latest = {"suite": "s", "runAt": "2026-10-09 10:00 CST", "vantage": "GA", "skills": [
            {"id": "a", "task": "ta", "bestVerdict": "部分通过", "runs": [run_ok]},
            {"id": "b", "task": "tb", "bestVerdict": "部分通过", "runs": [run_ok]},
            {"id": "c", "task": "tc", "bestVerdict": "调用失败", "runs": [run_fail]}]}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.json"
            p.write_text(json.dumps(tests), encoding="utf-8")
            es.apply_to_site(latest, p)
            e = json.loads(p.read_text(encoding="utf-8"))["entries"]
        self.assertEqual(e["a"]["testLevel"], "task")
        self.assertEqual(e["a"]["score"], 7.5)
        self.assertEqual(e["b"]["testLevel"], "e2e")
        self.assertEqual(e["b"]["score"], 9)
        self.assertEqual(e["c"]["testLevel"], "blocked")
        self.assertIsNone(e["c"]["score"])
        self.assertEqual(e["c"]["status"], "调用失败")
        for k in "abc":
            self.assertIn("freeModelRun", e[k])


if __name__ == "__main__":
    unittest.main()
