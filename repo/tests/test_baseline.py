"""Re-runs the engine and compares it with the committed baseline (reproducibility check)."""
import json, unittest
from pathlib import Path
from muse_gm import engine as m

ROOT = Path(__file__).resolve().parents[1]


class Baseline(unittest.TestCase):
    def test_baseline_reproduces(self):
        base = ROOT / "results" / "baseline"
        man = json.loads((base / "manifest.json").read_text())
        spec = m.Spec.load()
        self.assertEqual(spec.rubric_sha256, man["rubric_sha256"], "rubric changed: regenerate results/baseline")
        self.assertEqual(spec.variables_sha256, man["variables_sha256"])
        comps = spec.component_arrays()
        S = spec.score(comps, spec.profiles[man["profile"]])
        saved = [json.loads(l) for l in (base / "results.jsonl").read_text().splitlines()]
        for e, en in enumerate(spec.value_labels["effect"]):
            rows, _ = spec.top(S, comps, e, 5)
            old = [r for r in saved if r["effect"] == en and r["rank"] <= 5]
            self.assertEqual(len(old), 5)
            for new, was in zip(rows, sorted(old, key=lambda r: r["rank"])):
                self.assertEqual(new["codes"], was["codes"])
                self.assertAlmostEqual(new["score"], was["score"], places=6)


if __name__ == "__main__":
    unittest.main()
