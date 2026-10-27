"""Run: python -m unittest discover -v tests   (stdlib only; numpy required by the program)"""
import copy, json, math, tempfile, unittest
from pathlib import Path
import numpy as np
from muse_gm import engine as m

DATA = Path(m.__file__).resolve().parent / "data"
VARS = json.loads((DATA / "variables.json").read_text())
RUB = json.loads((DATA / "rubric.json").read_text())


class Surface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = m.Spec(VARS, RUB)
        cls.comps = cls.spec.component_arrays()
        cls.S = cls.spec.score(cls.comps, cls.spec.profiles["master"])

    def test_size(self):
        self.assertEqual(self.spec.total, 4_445_280)
        self.assertTrue(np.isfinite(self.S).all())

    def test_golden_winners(self):  # values from the first independent script run
        gold = {0: (0.9157, "Harlem", "ethical rebel loner"),
                1: (0.9160, "Kingston JA", "enforcer"),
                2: (0.8981, "Harlem", "heir")}
        for e, (score, node, arch) in gold.items():
            rows, _ = self.spec.top(self.S, self.comps, e, 1)
            self.assertAlmostEqual(rows[0]["score"], score, delta=6e-4)
            self.assertEqual(rows[0]["config"]["node"], node)
            self.assertEqual(rows[0]["config"]["archetype"], arch)

    def test_deterministic(self):
        a, _ = self.spec.top(self.S, self.comps, 0, 5)
        b, _ = self.spec.top(self.S, self.comps, 0, 5)
        self.assertEqual(a, b)

    def test_distinct_cores_are_distinct(self):
        rows, _ = self.spec.top(self.S, self.comps, 0, 5, ["node", "era", "economy"])
        cores = {(r["codes"]["node"], r["codes"]["era"], r["codes"]["economy"]) for r in rows}
        self.assertEqual(len(cores), 5)

    def test_selection_is_exhaustive_subspace(self):
        v, r = VARS, RUB
        sel = m.resolve_selection(v, ["node=Harlem", "era=3"])
        small = m.Spec(*m.restrict(v, r, sel))
        self.assertEqual(small.total, 1 * 1 * 9 * 7 * 5 * 6 * 7 * 3)
        sc = small.component_arrays()
        full_rows, _ = self.spec.top(np.where(self._mask(sel), self.S, -1.0), self.comps, 0, 1)
        sub_rows, _ = small.top(small.score(sc, small.profiles["master"]), sc, 0, 1)
        self.assertAlmostEqual(full_rows[0]["score"], sub_rows[0]["score"], places=12)

    def _mask(self, sel):
        mask = np.ones(self.spec.shape, bool)
        for n, ix in sel.items():
            ax = self.spec.names.index(n)
            keep = np.zeros(self.spec.shape[ax], bool); keep[ix] = True
            shp = [1] * 8; shp[ax] = -1
            mask &= keep.reshape(shp)
        return mask


class FailClosed(unittest.TestCase):
    def bad(self, mutate, msg):
        v, r = copy.deepcopy(VARS), copy.deepcopy(RUB)
        mutate(v, r)
        with self.assertRaises(m.ConfigError, msg=msg):
            m.Spec(v, r)

    def test_nan_value(self):
        self.bad(lambda v, r: r["tables"]["node_era"]["values"][0].__setitem__(0, float("nan")), "nan")

    def test_out_of_range(self):
        self.bad(lambda v, r: r["tables"]["node_era"]["values"][0].__setitem__(0, 1.5), "range")

    def test_wrong_shape(self):
        self.bad(lambda v, r: r["tables"]["node_era"]["values"].pop(), "shape")

    def test_component_weights_not_one(self):
        self.bad(lambda v, r: r["components"]["Empathy_Structure"]["terms"][0].__setitem__("w", 0.9), "weights")

    def test_profile_weights_not_one(self):
        self.bad(lambda v, r: r["profiles"]["master"].__setitem__("Empathy_Structure", 0.5), "profile sum")

    def test_profile_missing_component(self):
        self.bad(lambda v, r: r["profiles"]["master"].pop("Empathy_Structure"), "missing component")

    def test_unknown_table(self):
        self.bad(lambda v, r: r["components"]["Empathy_Structure"]["terms"][0].__setitem__("table", "nope"), "unknown table")

    def test_unknown_key(self):
        self.bad(lambda v, r: r.__setitem__("surprise", 1), "unknown key")

    def test_combination_cap(self):
        def blow(v, r):
            pass
        v, r = copy.deepcopy(VARS), copy.deepcopy(RUB)
        old = m.MAX_COMBINATIONS
        m.MAX_COMBINATIONS = 1000
        try:
            with self.assertRaises(m.ConfigError):
                m.Spec(v, r)
        finally:
            m.MAX_COMBINATIONS = old

    def test_ambiguous_selection(self):
        with self.assertRaises(m.ConfigError):
            m.resolve_selection(VARS, ["era=19"])  # matches several era labels


class Exports(unittest.TestCase):
    def test_run_writes_auditable_files(self):
        with tempfile.TemporaryDirectory() as d:
            rc = m.main(["run", "--effect", "pivot", "--top", "2", "--export-top", "3", "--out", d,
                         "--select", "node=Harlem", "--select", "era=3", "--select", "economy=policy"])
            self.assertEqual(rc, 0)
            man = json.loads((Path(d) / "manifest.json").read_text())
            self.assertEqual(man["evidence_status"], m.EVIDENCE_STATUS)
            self.assertEqual(len(man["rubric_sha256"]), 64)
            self.assertEqual(man["full_space"], 4_445_280)
            self.assertTrue((Path(d) / "surface_top.sps").read_text().startswith("GET DATA"))
            lines = (Path(d) / "results.jsonl").read_text().strip().splitlines()
            self.assertEqual(len(lines), 3)


if __name__ == "__main__":
    unittest.main()
