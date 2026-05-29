import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "br_research_cli.py"
FIXTURE = ROOT / "tests" / "fixtures" / "sample_data.json"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(CLI), "--data-file", str(FIXTURE), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class BottleneckResearchCliTests(unittest.TestCase):
    def test_schema_exposes_research_commands_without_trading_commands(self):
        result = run_cli("schema")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "br-agent-context.v2")
        self.assertIn("decision-check", payload["commands"])
        self.assertIn("candidates", payload["commands"])
        self.assertIn("freshness", payload["commands"])
        self.assertNotIn("buy", payload["commands"])
        self.assertNotIn("sell", payload["commands"])

    def test_decision_check_marks_single_day_spike_as_not_early(self):
        result = run_cli("decision-check", "06088.HK")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIs(payload["not_buy_sell_instruction"], True)
        self.assertEqual(payload["research_bucket"], "not_early_wait_for_pullback_or_new_evidence")
        self.assertEqual(payload["price_volume_status"]["status"], "single_day_spike_not_early")
        self.assertIn("orders_signal", payload["missing_evidence"])

    def test_context_markdown_includes_agent_instruction(self):
        result = run_cli("context", "--format", "markdown")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Agent Instruction", result.stdout)
        self.assertIn("Do not output personalized trading instructions", result.stdout)

    def test_chain_filter_returns_optical_candidate(self):
        result = run_cli("chain", "optical")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["candidate_count"], 1)
        self.assertEqual(payload["candidates"][0]["ticker"], "06088.HK")


if __name__ == "__main__":
    unittest.main()
