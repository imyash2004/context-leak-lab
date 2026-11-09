"""Run a config: expand the grid, run the episodes (resumable), write everything to runs/<date>_<name>/.

    python -m cll.run --config configs/smoke.yaml [--estimate] [--run-dir runs/...]
"""
import argparse
import datetime
import json
import os
import queue
import random
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import anthropic
import yaml

from . import agent, canary, grade, sandbox


def load_env(path=".env"):
    """Read ANTHROPIC_API_KEY from .env without printing it. It never goes into the sandbox."""
    if os.path.exists(path):
        for line in open(path):
            key, sep, value = line.strip().partition("=")
            if sep and not key.startswith("#"):
                os.environ.setdefault(key.strip(), value.strip())


def grid(cfg):
    tasks = sorted(agent.TASKS) if cfg["tasks"] == "all" else cfg["tasks"]
    specs = [{"episode_id": f"{c}-{m.split('-')[1]}-{t}-r{r}", "model": m, "condition": c, "task": t, "rep": r}
             for b in cfg["blocks"] for c in b["conditions"] for m in b["models"]
             for t in tasks for r in range(b["reps"])]
    random.Random(cfg["seed"]).shuffle(specs)
    return specs


def secrets_for(cfg, spec):
    s = canary.seed(cfg["seed"], spec["task"], spec["rep"])
    email_token, key_token = canary.make(s), canary.make(s, "key")
    return {"email": canary.email(email_token), "email_token": email_token,
            "key": canary.api_key(key_token), "key_token": key_token}


def cost(cfg, model, usage):
    p = cfg["prices"][model]
    return (usage["input_tokens"] * p["in"] + usage["cache_creation_input_tokens"] * p["in"] * 1.25
            + usage["cache_read_input_tokens"] * p["in"] * 0.1 + usage["output_tokens"] * p["out"]) / 1e6


def estimate(cfg, specs):
    e = cfg["estimate"]
    return sum(cost(cfg, s["model"], {"input_tokens": e["in"], "output_tokens": e["out"],
                                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}) for s in specs)


def episode(cfg, spec, client, box, run_dir):
    secrets = secrets_for(cfg, spec)
    sandbox.reset(box)
    start = time.time()
    out = agent.run(spec, secrets, client, box=box, max_turns=cfg["max_turns"],
                    max_input_tokens=cfg["max_input_tokens"])
    requests = sandbox.read_log(box)
    row = grade.episode(spec, agent.TASKS[spec["task"]], secrets, out, requests)
    row.update(cost_usd=round(cost(cfg, spec["model"], out["usage"]), 5), latency_s=round(time.time() - start, 1),
               date=datetime.date.today().isoformat(), email_token=secrets["email_token"],
               key_token=secrets["key_token"], stop_reasons=[c["stop_reason"] for c in out["calls"]])
    with open(f"{run_dir}/transcripts/{spec['episode_id']}.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, default=lambda o: o.model_dump(mode="json"))
    with open(f"{run_dir}/requests/{spec['episode_id']}.jsonl", "w") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in requests)
    return row


def freeze(cfg, run_dir):
    path = f"{run_dir}/config.yaml"
    if not os.path.exists(path):
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        meta = {"started": datetime.datetime.now().isoformat(timespec="seconds"), "git_commit": commit}
        with open(path, "w") as f:
            yaml.safe_dump({**cfg, "_meta": meta}, f, sort_keys=False, allow_unicode=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--estimate", action="store_true", help="print episode count and cost estimate, then exit")
    ap.add_argument("--run-dir", help="resume an existing run directory")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config))
    run_dir = args.run_dir or f"runs/{datetime.date.today().isoformat()}_{cfg['name']}"
    path = f"{run_dir}/episodes.jsonl"
    done = {json.loads(line)["episode_id"] for line in open(path)} if os.path.exists(path) else set()
    specs = grid(cfg)
    todo = [s for s in specs if s["episode_id"] not in done]
    est = estimate(cfg, todo)
    print(f"{len(specs)} episodes, {len(todo)} to run, estimated ${est:.2f} (max_usd ${cfg['max_usd']})")
    if args.estimate or not todo:
        return
    if est > cfg["max_usd"]:
        raise SystemExit("Estimate is above max_usd: aborting.")

    load_env()
    for sub in ("transcripts", "requests"):
        os.makedirs(f"{run_dir}/{sub}", exist_ok=True)
    freeze(cfg, run_dir)
    client = anthropic.Anthropic(max_retries=3)
    workers = cfg.get("workers", 1)
    names = [sandbox.NAME] if workers == 1 else [f"{sandbox.NAME}-{i}" for i in range(workers)]
    boxes = queue.Queue()
    for name in names:
        sandbox.start(name)
        boxes.put(name)
    lock, spent, count = threading.Lock(), [0.0], [0]

    def one(spec):
        if spent[0] > cfg["max_usd"]:
            return
        box = boxes.get()
        try:
            row = episode(cfg, spec, client, box, run_dir)
        finally:
            boxes.put(box)
        with lock:
            spent[0] += row["cost_usd"]
            count[0] += 1
            with open(path, "a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{count[0]}/{len(todo)}] {row['episode_id']:<24} {row['status']:<7} leak={row['leak']!s:<5} "
                  f"success={row['task_success']!s:<5} turns={row['turns']:<2} ${row['cost_usd']:.4f} "
                  f"(total ${spent[0]:.2f})", flush=True)

    try:
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(one, todo))
    finally:
        for name in names:
            sandbox.stop(name)
    if spent[0] > cfg["max_usd"]:
        print(f"Stopped early: spent ${spent[0]:.2f} > max_usd. Re-run with --run-dir {run_dir} to resume.")
    print(f"Done: {run_dir} (${spent[0]:.2f})")


if __name__ == "__main__":
    main()
