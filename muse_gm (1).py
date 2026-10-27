#!/usr/bin/env python3
"""MUSE-GM Decision Surface: exhaustive enumeration of a factorial story space.

Variables (factors + value labels) live in config/variables.json, like an SPSS Variable View.
Rubric tables, component formulas and weight profiles live in config/rubric.json.
Every combination is scored; nothing is sampled. The rubric values are encoded judgments,
not measured data, and every run manifest says so.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import json
import math
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

VERSION = "0.1.0"
MAX_COMBINATIONS = 10**9
HERE = Path(__file__).resolve().parent
EVIDENCE_STATUS = "rubric_encoded_judgments_not_measured_data"


class ConfigError(ValueError):
    """Raised when configuration is incomplete or invalid. The program fails closed."""


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _only_keys(obj, allowed, where):
    extra = set(obj) - set(allowed)
    if extra:
        raise ConfigError(f"{where}: unknown keys {sorted(extra)}")
    missing = set(allowed) - set(obj)
    if missing:
        raise ConfigError(f"{where}: missing keys {sorted(missing)}")


def _weights_ok(weights, where):
    vals = list(weights)
    if not vals or any((not isinstance(v, (int, float))) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in vals):
        raise ConfigError(f"{where}: weights must be finite, non-negative numbers")
    if not math.isclose(sum(vals), 1.0, rel_tol=0, abs_tol=1e-8):
        raise ConfigError(f"{where}: weights must sum to 1.0 (got {sum(vals):.10f})")


class Spec:
    """Validated variables + rubric. Axis order of the surface is the order of variables."""

    def __init__(self, variables: dict, rubric: dict):
        try:
            self.variables_sha256 = sha256_text(canonical(variables))
            self.rubric_sha256 = sha256_text(canonical(rubric))
        except (ValueError, TypeError) as err:  # NaN/Infinity or non-JSON values
            raise ConfigError(f"configuration is not valid JSON data: {err}") from err
        _only_keys(variables, ["schema_version", "variables"], "variables.json")
        self.names, self.var_labels, self.value_labels = [], {}, {}
        for v in variables["variables"]:
            _only_keys(v, ["name", "label", "type", "values"], "variable")
            name = v["name"]
            if not isinstance(name, str) or not name.isidentifier() or name in self.names:
                raise ConfigError(f"variable name invalid or duplicated: {name!r}")
            codes = list(v["values"])
            if codes != [str(i) for i in range(1, len(codes) + 1)] or not codes:
                raise ConfigError(f"{name}: value codes must be '1'..'n' in order")
            self.names.append(name)
            self.var_labels[name] = v["label"]
            self.value_labels[name] = [v["values"][c] for c in codes]
        if "effect" not in self.names:
            raise ConfigError("a variable named 'effect' is required")
        self.shape = tuple(len(self.value_labels[n]) for n in self.names)
        self.total = int(np.prod(self.shape, dtype=object))
        self.full_total = self.total
        self.code_map = {n: list(range(1, len(self.value_labels[n]) + 1)) for n in self.names}
        self.selection_desc = None
        if self.total > MAX_COMBINATIONS:
            raise ConfigError(f"{self.total:,} combinations exceeds the cap of {MAX_COMBINATIONS:,}")

        _only_keys(rubric, ["schema_version", "evidence_status", "tables", "components", "profiles"], "rubric.json")
        self.tables = {}
        for tname, t in rubric["tables"].items():
            _only_keys(t, ["axes", "note", "values"], f"table {tname}")
            axes = t["axes"]
            if len(set(axes)) != len(axes) or any(a not in self.names for a in axes):
                raise ConfigError(f"table {tname}: axes must be distinct known variables")
            arr = np.array(t["values"], dtype=float)
            want = tuple(len(self.value_labels[a]) for a in axes)
            if arr.shape != want:
                raise ConfigError(f"table {tname}: shape {arr.shape} != {want} for axes {axes}")
            if not np.isfinite(arr).all() or arr.min() < 0 or arr.max() > 1:
                raise ConfigError(f"table {tname}: values must be finite and within [0, 1]")
            self.tables[tname] = (axes, arr)
        self.components = {}
        for cname, c in rubric["components"].items():
            _only_keys(c, ["op", "terms"], f"component {cname}")
            if c["op"] not in ("linear", "geomean"):
                raise ConfigError(f"component {cname}: op must be 'linear' or 'geomean'")
            for term in c["terms"]:
                _only_keys(term, ["table", "w"], f"component {cname} term")
                if term["table"] not in self.tables:
                    raise ConfigError(f"component {cname}: unknown table {term['table']!r}")
            _weights_ok([x["w"] for x in c["terms"]], f"component {cname}")
            self.components[cname] = c
        self.profiles = {}
        for pname, p in rubric["profiles"].items():
            if set(p) != set(self.components):
                raise ConfigError(f"profile {pname}: must weight exactly the components {sorted(self.components)}")
            _weights_ok(p.values(), f"profile {pname}")
            self.profiles[pname] = dict(p)

    # ---- loading -------------------------------------------------------------------------
    @classmethod
    def load(cls, variables_path=None, rubric_path=None):
        vp = Path(variables_path or HERE / "config" / "variables.json")
        rp = Path(rubric_path or HERE / "config" / "rubric.json")
        return cls(json.loads(vp.read_text(encoding="utf-8")), json.loads(rp.read_text(encoding="utf-8")))

    # ---- computation ---------------------------------------------------------------------
    def _expand(self, tname):
        axes, arr = self.tables[tname]
        pos = [self.names.index(a) for a in axes]
        arr = np.transpose(arr, np.argsort(pos))
        shape = [1] * len(self.names)
        for p, s in zip(sorted(pos), arr.shape):
            shape[p] = s
        return arr.reshape(shape)

    def component_arrays(self):
        out = {}
        for cname, c in self.components.items():
            if c["op"] == "linear":
                val = sum(t["w"] * self._expand(t["table"]) for t in c["terms"])
            else:
                val = np.ones((1,) * len(self.names))
                for t in c["terms"]:
                    val = val * self._expand(t["table"]) ** t["w"]
            out[cname] = np.broadcast_to(val, self.shape)
        return out

    def score(self, comps, weights):
        total = np.zeros(self.shape)
        for cname, w in weights.items():
            total = total + w * comps[cname]
        if not np.isfinite(total).all():
            raise ConfigError("non-finite score produced")
        return total

    # ---- ranking -------------------------------------------------------------------------
    def effect_slice(self, S, e):
        ax = self.names.index("effect")
        rest = [n for n in self.names if n != "effect"]
        return np.take(S, e, axis=ax), rest

    def _row(self, rank, score, idx, comps):
        full = tuple(idx[n] for n in self.names)
        return {
            "rank": rank,
            "score": round(float(score), 6),
            "config": {n: self.value_labels[n][idx[n]] for n in self.names},
            "codes": {n: self.code_map[n][idx[n]] for n in self.names},
            "components": {c: round(float(a[full]), 4) for c, a in comps.items()},
        }

    def top(self, S, comps, e, k=5, distinct=None):
        sl, rest = self.effect_slice(S, e)
        if not distinct:
            flat = sl.ravel()
            order = np.lexsort((np.arange(flat.size), -flat))[:k]
            top_score = flat[order[0]]
            tied = int(np.isclose(flat, top_score, rtol=0, atol=1e-12).sum())
            rows = []
            for r, o in enumerate(order, 1):
                idx = dict(zip(rest, np.unravel_index(o, sl.shape)))
                idx["effect"] = e
                rows.append(self._row(r, flat[o], idx, comps))
            return rows, tied
        for d in distinct:
            if d not in rest:
                raise ConfigError(f"--distinct: unknown variable {d!r}")
        gpos = [rest.index(d) for d in distinct]
        moved = np.moveaxis(sl, gpos, range(len(gpos)))
        gshape = moved.shape[:len(gpos)]
        flat2 = moved.reshape(int(np.prod(gshape)), -1)
        gmax, garg = flat2.max(axis=1), flat2.argmax(axis=1)
        order = np.argsort(-gmax, kind="stable")[:k]
        others = [n for i, n in enumerate(rest) if i not in gpos]
        oshape = [sl.shape[rest.index(n)] for n in others]
        rows = []
        for r, g in enumerate(order, 1):
            idx = dict(zip(distinct, np.unravel_index(g, gshape)))
            idx.update(dict(zip(others, np.unravel_index(garg[g], oshape))))
            idx["effect"] = e
            rows.append(self._row(r, gmax[g], idx, comps))
        return rows, None

    def sensitivity(self, comps, profile, against, k=5, step=0.05):
        base = self.profiles[profile]
        S0 = self.score(comps, base)
        report = {"profile": profile, "against": against, "by_effect": {}}
        alt_S = self.score(comps, self.profiles[against])
        variants = []
        for c in base:
            for sign in (+1, -1):
                w = dict(base)
                w[c] = max(0.0, w[c] + sign * step)
                tot = sum(w.values())
                variants.append((f"{c} {'+' if sign > 0 else '-'}{step}", {a: b / tot for a, b in w.items()}))
        for e, en in enumerate(self.value_labels["effect"]):
            r0, _ = self.top(S0, comps, e, k)
            r1, _ = self.top(alt_S, comps, e, k)
            key = lambda r: tuple(r["codes"][n] for n in self.names)
            base_set, alt_set = {key(r) for r in r0}, {key(r) for r in r1}
            flips = []
            for label, w in variants:
                rv, _ = self.top(self.score(comps, w), comps, e, 1)
                if key(rv[0]) != key(r0[0]):
                    flips.append(label)
            report["by_effect"][en] = {
                "top_k_overlap_with_" + against: len(base_set & alt_set),
                "winner_same_under_" + against: key(r0[0]) == key(r1[0]),
                "winner_changes_under_weight_shifts": flips,
                "weight_shifts_tested": len(variants),
            }
        return report


# ---- subspace selection (SPSS SELECT IF) ---------------------------------------------------
def resolve_selection(variables, items):
    """items like ['node=Harlem', 'era=3|4']. Values: a code number or a unique label substring."""
    byname = {v["name"]: v for v in variables["variables"]}
    sel = {}
    for item in items:
        if "=" not in item:
            raise ConfigError(f"--select expects name=value, got {item!r}")
        name, vals = item.split("=", 1)
        if name not in byname:
            raise ConfigError(f"--select: unknown variable {name!r}")
        labels = list(byname[name]["values"].values())
        picked = []
        for tok in vals.split("|"):
            tok = tok.strip()
            if tok.isdigit() and 1 <= int(tok) <= len(labels):
                picked.append(int(tok) - 1)
                continue
            hits = [i for i, l in enumerate(labels) if tok.lower() in l.lower()]
            if len(hits) != 1:
                raise ConfigError(f"--select {name}={tok!r}: matches {len(hits)} values (use the code number)")
            picked.append(hits[0])
        sel[name] = sorted(set(sel.get(name, []) + picked))
    return sel


def restrict(variables, rubric, sel):
    nv, nr = copy.deepcopy(variables), copy.deepcopy(rubric)
    for v in nv["variables"]:
        if v["name"] in sel:
            labs = [v["values"][str(i + 1)] for i in sel[v["name"]]]
            v["values"] = {str(k + 1): l for k, l in enumerate(labs)}
    for t in nr["tables"].values():
        arr = np.array(t["values"], dtype=float)
        for ax, a in enumerate(t["axes"]):
            if a in sel:
                arr = np.take(arr, sel[a], axis=ax)
        t["values"] = arr.tolist()
    return nv, nr


def load_spec(a):
    vp = Path(a.variables or HERE / "config" / "variables.json")
    rp = Path(a.rubric or HERE / "config" / "rubric.json")
    variables, rubric = json.loads(vp.read_text(encoding="utf-8")), json.loads(rp.read_text(encoding="utf-8"))
    full = Spec(variables, rubric)
    if not getattr(a, "select", None):
        return full
    sel = resolve_selection(variables, a.select)
    spec = Spec(*restrict(variables, rubric, sel))
    spec.variables_sha256, spec.rubric_sha256 = full.variables_sha256, full.rubric_sha256
    spec.full_total = full.total
    spec.code_map = {n: [i + 1 for i in sel.get(n, range(len(full.value_labels[n])))] for n in full.names}
    spec.selection_desc = {n: [full.value_labels[n][i] for i in ix] for n, ix in sel.items()}
    return spec


# ---- reporting helpers -------------------------------------------------------------------
def git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True, timeout=2, check=True)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def print_rows(spec, rows, header):
    print(f"\n== {header}")
    cols = [n for n in spec.names if n != "effect"]
    for r in rows:
        print(f"#{r['rank']}  {r['score']:.4f}  " + " | ".join(r["config"][c] for c in cols))
        print("      " + "  ".join(f"{k.split('_')[0][:5]}={v:.2f}" for k, v in r["components"].items()))


def write_exports(spec, results, outdir, n):
    """CSV with numeric codes (SPSS-ready), labeled CSV, and SPSS syntax with VALUE LABELS."""
    comp_names = list(spec.components)
    head = ["effect", "rank", "score"] + comp_names + [x for x in spec.names if x != "effect"]
    coded, labeled = [], []
    for en, rows in results.items():
        for r in rows[:n]:
            base = [spec.value_labels["effect"].index(en) + 1, r["rank"], r["score"]] + [r["components"][c] for c in comp_names]
            coded.append(base + [r["codes"][x] for x in head[3 + len(comp_names):]])
            labeled.append([en, r["rank"], r["score"]] + [r["components"][c] for c in comp_names] + [r["config"][x] for x in head[3 + len(comp_names):]])
    for name, data in (("surface_top.csv", coded), ("surface_top_labeled.csv", labeled)):
        with (outdir / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows(data)
    q = lambda s: "'" + str(s).replace("'", "''") + "'"
    fmt = {"effect": "F2.0", "rank": "F5.0", "score": "F8.5"}
    for c in comp_names:
        fmt[c] = "F8.5"
    for v in spec.names:
        fmt.setdefault(v, "F3.0")
    lines = ["GET DATA /TYPE=TXT /FILE='surface_top.csv' /ENCODING='UTF8' /DELIMITERS=\",\" /QUALIFIER='\"'",
             "  /ARRANGEMENT=DELIMITED /FIRSTCASE=2 /VARIABLES="]
    lines += [f"  {h} {fmt[h]}" for h in head] + ["  ."]
    lines.append("VARIABLE LABELS " + " ".join(f"{v} {q(spec.var_labels[v])}" for v in spec.names) + " .")
    vl = ["VALUE LABELS"]
    for i, v in enumerate(spec.names):
        pairs = " ".join(f"{k + 1} {q(lab)}" for k, lab in enumerate(spec.value_labels[v]))
        vl.append(("  /" if i else "  ") + f"{v} {pairs}")
    lines += vl + ["  .", "EXECUTE."]
    (outdir / "surface_top.sps").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_variables(spec, a):
    print(f"{'#':<3}{'name':<11}{'type':<9}{'n':<4}label")
    for i, n in enumerate(spec.names, 1):
        print(f"{i:<3}{n:<11}{'nominal':<9}{len(spec.value_labels[n]):<4}{spec.var_labels[n]}")
        if a.values:
            for k, lab in enumerate(spec.value_labels[n], 1):
                print(f"      {k:>2} = {lab}")
    print(f"\ncases (full factorial): {spec.total:,}   cap: {MAX_COMBINATIONS:,}")


def cmd_check(spec, a):
    print(f"OK  variables={len(spec.names)}  tables={len(spec.tables)}  components={len(spec.components)}  profiles={sorted(spec.profiles)}")
    print(f"combinations: {spec.total:,} of full space {spec.full_total:,} (cap {MAX_COMBINATIONS:,})  est. memory ~{spec.total * 8 * 8 / 1e6:,.0f} MB")
    if spec.selection_desc:
        print("selection:", json.dumps(spec.selection_desc, ensure_ascii=False))
    print(f"variables sha256: {spec.variables_sha256}\nrubric sha256:    {spec.rubric_sha256}")


def cmd_run(spec, a):
    if a.profile not in spec.profiles:
        raise ConfigError(f"unknown profile {a.profile!r}; have {sorted(spec.profiles)}")
    weights = spec.profiles[a.profile]
    comps = spec.component_arrays()
    S = spec.score(comps, weights)
    effects = spec.value_labels["effect"]
    if a.effect != "all":
        if a.effect not in effects:
            raise ConfigError(f"unknown effect {a.effect!r}; have {effects}")
        effects = [a.effect]
    distinct = [d for d in a.distinct.split(",") if d] if a.distinct else None
    results, ties = {}, {}
    for en in effects:
        e = spec.value_labels["effect"].index(en)
        rows, tied = spec.top(S, comps, e, max(a.top, a.export_top), distinct)
        results[en], ties[en] = rows, tied
        print_rows(spec, rows[:a.top], f"{en}" + (f"  (distinct by {','.join(distinct)})" if distinct else "") + f"   profile={a.profile}")
        if tied and tied > 1:
            print(f"      NOTE: {tied} combinations tie for first place")
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "results.jsonl").open("w", encoding="utf-8") as f:
            for en, rows in results.items():
                for r in rows:
                    f.write(canonical({"effect": en, **r}) + "\n")
        manifest = {
            "schema_version": 1, "program": "muse-gm decision surface", "version": VERSION,
            "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "command": sys.argv, "profile": a.profile, "weights": weights,
            "combinations": spec.total, "full_space": spec.full_total, "selection": spec.selection_desc,
            "max_combinations": MAX_COMBINATIONS, "distinct": distinct,
            "variables_sha256": spec.variables_sha256, "rubric_sha256": spec.rubric_sha256,
            "git_commit": git_commit(), "python": sys.version.split()[0], "numpy": np.__version__,
            "platform": platform.platform(), "ties_at_first_place": ties, "evidence_status": EVIDENCE_STATUS,
        }
        (out / "manifest.json").write_text(canonical(manifest) + "\n", encoding="utf-8")
        write_exports(spec, results, out, a.export_top)
        print(f"\nwrote results.jsonl, manifest.json, surface_top.csv, surface_top_labeled.csv, surface_top.sps -> {out}")


def cmd_sensitivity(spec, a):
    comps = spec.component_arrays()
    rep = spec.sensitivity(comps, a.profile, a.against, a.top)
    print(json.dumps(rep, indent=1))


def main(argv=None):
    p = argparse.ArgumentParser(prog="muse_gm", description=__doc__.split("\n")[0])
    p.add_argument("--variables"); p.add_argument("--rubric")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--select", action="append", default=[], metavar="VAR=VAL[|VAL]",
                        help="restrict to a subspace (exhaustive within it); repeatable")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("variables", help="SPSS-style Variable View"); s.add_argument("--values", action="store_true")
    sub.add_parser("check", help="validate config and report size", parents=[common])
    s = sub.add_parser("run", help="enumerate every combination and rank", parents=[common])
    s.add_argument("--profile", default="master"); s.add_argument("--effect", default="all")
    s.add_argument("--top", type=int, default=5); s.add_argument("--distinct", help="comma list, e.g. node,era,economy")
    s.add_argument("--out"); s.add_argument("--export-top", type=int, default=1000)
    s = sub.add_parser("sensitivity", help="compare profiles and test weight shifts", parents=[common])
    s.add_argument("--profile", default="master"); s.add_argument("--against", default="equal"); s.add_argument("--top", type=int, default=5)
    a = p.parse_args(argv)
    try:
        spec = load_spec(a)
        {"variables": cmd_variables, "check": cmd_check, "run": cmd_run, "sensitivity": cmd_sensitivity}[a.cmd](spec, a)
    except ConfigError as err:
        print(f"CONFIG ERROR: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
