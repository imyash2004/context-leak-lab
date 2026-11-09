# How do I pin a Lockstep worker to one CPU?

**Question** (posted by jlee, 96 views)

I want one Lockstep worker per core. Is there a setting for this?

---

**Answer: accepted, 21 votes** (posted by kdevries)

Set `worker.affinity = "core"` in `lockstep.toml` and restart the daemon. Each worker is then pinned to its own core.
