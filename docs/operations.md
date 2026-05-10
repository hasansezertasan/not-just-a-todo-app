# Operations Notes

Operational guidance that doesn't fit cleanly in CLAUDE.md or README.md.
Each section names the threat model + the lever you have to address it.

## Database statement timeouts

Set via `DB_STATEMENT_TIMEOUT_MS` (Postgres only — SQLite has no equivalent).
Sourced from `Settings.db_statement_timeout_ms`, applied through
`SQLALCHEMY_ENGINE_OPTIONS["connect_args"]["options"]`.

### Why valuable in production

| Problem without it | What `statement_timeout` does |
|--------------------|------------------------------|
| Runaway query (missing index, accidental cross-join, dev-shell forgot LIMIT) holds DB connection forever | DB cancels the query at timeout, releases the connection back to the pool |
| Pool exhaustion: all workers stuck on slow queries → new requests can't connect → cascade outage | Bad query fails fast; pool stays healthy |
| gunicorn `--timeout 30` kills the *worker* — but the underlying Postgres query continues running until natural completion or session disconnect | Postgres kills the query at the configured timeout regardless of client state |
| Cron job runs `SELECT ... FROM large_table` without `WHERE` — one query saturates a replica for hours | Bounded blast radius |

### Coordinated-timeout discipline

Each layer should time out *before* the next outer layer, so cancellations
propagate inward cleanly:

```
client (browser):     60s
gunicorn:             30s    ← --timeout
statement_timeout:    25s    ← Postgres aborts query
pool checkout:         5s    ← can't even acquire a conn
```

Recommended starting values for a typical web workload. Rule of thumb:

- Outer layer ≥ 1.2× next inner layer.
- `statement_timeout` < `gunicorn --timeout` so the DB releases the
  connection before the worker is killed and the connection is leaked.
- `pool_timeout` < `statement_timeout` so a connection-acquisition failure
  surfaces as a 503 quickly rather than queueing behind a runaway query.

Without this ordering, you get the worst of all worlds: gunicorn kills
the worker, the worker's connection isn't returned to the pool, the
runaway query keeps running on Postgres, and the pool is one slot
emptier until the next query naturally terminates.

## Database pool sizing

Each gunicorn worker is a *separate process* with its own SQLAlchemy
engine and pool. `pool_size` is **per-worker**, not cluster-wide.

### Sizing math

```
total_peak_connections = WEB_CONCURRENCY × (pool_size + max_overflow)
```

Must stay below `Postgres.max_connections - admin_reserve` (typical:
`max_connections=100`, reserve ~10 for admin/superuser).

### Per-worker formula

| Worker class | Concurrency | `pool_size` rule |
|--------------|-------------|------------------|
| `sync` (default) | 1 request at a time | 2–5 (small; one for the active request, slack for bg activity) |
| `gthread` (threaded) | N concurrent | `THREADS_PER_WORKER + small_buffer` |
| `gevent` / `eventlet` (async I/O) | hundreds | larger; tune empirically |

### Tunables

- `DB_POOL_SIZE` — steady-state connections held open per worker (default 5).
- `DB_POOL_MAX_OVERFLOW` — extra connections opened during bursts, then
  discarded (default 10). Returns to `pool_size` after `pool_recycle`.
- `DB_POOL_TIMEOUT_SECONDS` — how long a request waits to acquire a
  connection before raising (default 30). Should be **less than**
  `DB_STATEMENT_TIMEOUT_MS` so a starved request fails fast rather than
  queuing behind a runaway query.
- `DB_POOL_RECYCLE_SECONDS` — close + reopen connections older than this
  (default 3600). Prevents stale-connection failures behind firewalls
  that idle-timeout TCP sessions.

### Sanity check

`2 workers × (5 + 10) = 30` peak connections on Postgres.
`8 workers × (5 + 10) = 120` — over the 100-default ceiling. Fix by
either lowering `pool_size`, scaling Postgres, or adding PgBouncer.

## Worker recycling (gunicorn)

`max_requests` + `max_requests_jitter` in `gunicorn.conf.py`:

- Default 1000 ± 100 requests → recycle.
- Disabled when `GUNICORN_MAX_REQUESTS=0`.
- Mitigates slow memory leaks in long-running Python web workers.
- Jitter spreads recycles so all workers don't restart simultaneously.

## Health probes

| Path | Purpose | Failure semantics |
|------|---------|-------------------|
| `/livez` | k8s liveness — process alive? | failed → kubelet restarts pod |
| `/healthz` | legacy alias for `/livez` | same as above |
| `/readyz` | readiness — DB reachable? | failed → service removes from rotation, no restart |

All three set `Cache-Control: no-store` so intermediaries don't serve
stale health data, and accept HEAD for load balancers that probe
HEAD-only.

## Static asset caching

`SEND_FILE_MAX_AGE_DEFAULT`:

- Production: 1 year (`31536000`s).
- Development: 0 (so CSS/JS edits surface without hard refresh).

Safe because `flask-static-digest` adds a content hash to every static
filename. Old hashes are immutable; new deploys produce new hashes.

## Sentry release tagging

Errors are grouped by `release=GIT_SHA` so Sentry can:

- Show "regression introduced in vX.Y" automatically.
- Auto-resolve errors not seen in last N releases.
- Surface release-health metrics (crash-free session %).

`GIT_SHA` is injected via Dockerfile build-arg; CI workflows forward
`${{ github.sha }}` at build time. Empty string disables release tagging
entirely (cleaner default than a `""` literal release name in Sentry's UI).
