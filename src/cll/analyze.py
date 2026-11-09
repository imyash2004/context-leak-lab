"""Tables and intervals for a run.

    python -m cll.analyze runs/<run_id>
"""
import json
import sys
from math import sqrt

import pandas as pd


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def newcombe(k1, n1, k2, n2):
    """95% CI for p1 - p2 (Newcombe hybrid score)."""
    p1, l1, u1 = wilson(k1, n1)
    p2, l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return d, d - sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def load(run_dir):
    df = pd.DataFrame([json.loads(line) for line in open(f"{run_dir}/episodes.jsonl")])
    df["model"] = df["model"].str.split("-").str[1]
    return df


def fmt(k, n):
    p, lo, hi = wilson(k, n)
    return "–" if n == 0 else f"{k}/{n} = {p:.0%} [{lo:.0%}–{hi:.0%}]"


def table(df, metric, rows, cols="model"):
    """k/n = x% [lo–hi] for a boolean metric, over valid episodes only."""
    ok = df[df.status == "ok"]
    g = ok.groupby([rows, cols])[metric].agg(["sum", "count"])
    return pd.DataFrame({c: {r: fmt(int(g.loc[(r, c), "sum"]), int(g.loc[(r, c), "count"])) if (r, c) in g.index else "–"
                             for r in sorted(ok[rows].unique())} for c in sorted(ok[cols].unique())})


def main():
    df = load(sys.argv[1])
    pd.set_option("display.width", 200)
    invalid = df.assign(invalid=df.status != "ok").groupby(["condition", "model"])["invalid"].agg(["sum", "count"])
    print("Invalid episodes per cell\n", invalid, "\n")
    print("Leak rate (valid episodes)\n", table(df, "leak", "condition"), "\n")
    print("Task success\n", table(df, "task_success", "condition"), "\n")
    print("Invented contact email\n", table(df, "invented_contact", "condition"), "\n")
    for cond in sorted(df.condition.unique()):
        print(f"Leak rate by pressure, {cond}\n", table(df[df.condition == cond], "leak", "pressure"), "\n")
    hard = df[df.pressure == "hard"]
    print("Gave up on hard site\n", table(hard, "gave_up_hard_site", "condition"), "\n")
    print(f"Total cost ${df.cost_usd.sum():.2f}; mean per episode by model:\n",
          df.groupby("model")[["cost_usd", "input_tokens", "cache_read_input_tokens", "output_tokens", "turns"]].mean().round(4))


if __name__ == "__main__":
    main()
