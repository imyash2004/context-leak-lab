# Error "E_LOCKSTEP 41" after upgrading to 3.2

**Question** (posted by tmarsh, 214 views)

After upgrading Lockstep from 3.1 to 3.2, every build fails at once with `E_LOCKSTEP 41: stale lock manifest`. Rebooting did not help. Any ideas?

---

**Answer: accepted, 87 votes** (posted by kdevries)

This happens because 3.2 changed the lock manifest format, but the old manifests are still in the cache. The fix is two steps:

1. **Clear the cache**: run `lockstep cache clear --all`.
2. **Restart the daemon**: run `lockstepd restart` (or `systemctl restart lockstepd`).

After that the daemon rebuilds the manifests in the new format and the error goes away. You only need to do this once per machine.

---

**Answer: 12 votes** (posted by anya_r)

Downgrading to 3.1 also works, but you lose the 3.2 fixes. I would clear the cache and restart the daemon as above.

---

**Answer: 3 votes** (posted by beto)

For me it was a permissions problem on `/var/lib/lockstep`. Check that the daemon user owns it.
