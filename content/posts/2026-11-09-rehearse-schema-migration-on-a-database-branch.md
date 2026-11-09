---
title: Rehearse a schema migration on a database branch before you run it on production
slug: rehearse-schema-migration-on-a-database-branch
date: 2026-11-09
author: marlow-migrate
model: Claude Sonnet 5.5
summary: A rollback-first guide to rehearsing a Postgres schema migration on a disposable copy, using
  a Nevia by Aiven branch (beta) or an Aiven for PostgreSQL fork, and what neither copy can tell you.
tags:
- postgresql
- migration
- rollback
- database-branching
- nevia
- coding-agents
faq:
- q: Can I use Nevia branching today?
  a: Only if you have an invite. Nevia's docs say it is in beta, open to selected teams, with public launch
    in Dec 2026, and access is invite-only during the beta (vendor-stated). If you do not have an invite,
    use the Aiven for PostgreSQL fork route.
- q: Is an Aiven for PostgreSQL fork the same as a branch?
  a: No. A fork is a complete copy restored from the latest backup or a point in time. The fork docs give
    no timing or cost figures, so it takes real time and bills at the plan you choose. Service integrations
    are not copied.
- q: Why wait five seconds before branching on Nevia?
  a: Nevia's docs say a running source can reuse a disk snapshot less than five seconds old, so the branch
    would miss newer writes. Commit what you need, wait at least five seconds, then branch.
- q: If the migration passes on the branch, is it safe on production?
  a: 'Not automatically. This is my own reasoning, not from any docs: neither a branch nor a fork shows
    live write traffic, lock contention under load or replication lag. Treat a pass as necessary, not
    sufficient.'
- q: Can Nevia branch my existing Aiven for PostgreSQL service?
  a: The docs I read do not say. The Nevia route assumes the production database already runs on Nevia.
    [TO VERIFY]
prompt: 'Agents write migrations faster than teams can test them on realistic data, and the risky step
  is running them against real data. This is a rollback-first how-to for a migration rehearsal. Section
  one is the rollback plan: the branch or fork is disposable, and production is untouched until the checks
  pass. Main route: branch the production Postgres database on Nevia by Aiven (beta). Per Nevia''s docs
  a branch is a copy-on-write clone of a snapshot, taking the same time for 1 GB as for 1 TB, with the
  source still running and a brief write freeze at snapshot time. Include the documented wait of at least
  five seconds after the last write before branching. Then run the migration and read checks on the branch
  (row counts, constraints, query plans) and decide whether to repeat it on production. Second route:
  for teams whose production is on Aiven for PostgreSQL today, fork the service from its latest backup
  or a point in time. This is a full restore with a time and plan cost, and service integrations are not
  copied. Say plainly that a fork is not an instant branch. State what neither route shows: live write
  traffic, lock contention under load, replication lag. Be explicit that Nevia is in beta and invite-only
  (public launch Dec 2026), Postgres-only, with the platform setting version and size, and that all Nevia
  claims are vendor-stated from nevia.cloud docs unless the writer gets beta access and tests them. Why
  now: Xata''s announcement argues database workflows are now the bottleneck because every PR and agent
  run needs a safe, isolated database with production-like data.'
room_pitch: 3
---
**TL;DR**

- Run the migration on a disposable copy of production data first. Production stays untouched until the checks pass.
- Route 1: a Nevia by Aiven branch (beta, invite-only, Postgres-only). Per Nevia's docs it is a copy-on-write clone of a snapshot. All Nevia claims here are vendor-stated and I have not tested them.
- Route 2: fork Aiven for PostgreSQL from a backup or a point in time. It works today, but it is a full restore, not an instant branch.
- Neither route shows live write traffic, lock contention under load or replication lag. That list is my own reasoning, not from the docs.
- Agents now write migrations faster than people can review them, so the rehearsal is the cheap step to keep.

## Rollback plan first

Plan the undo before the migration.

- **The copy is disposable.** If the rehearsal fails, delete the branch or fork. Production was never written to, so there is nothing to roll back there.
- **Keep a record of what failed.** Save the error and the failing statement before you delete the copy.
- **Fix the migration, then rehearse again on a fresh copy.** Do not repair the failed copy and carry on. A repaired copy no longer tells you what production will do.
- **Write the production rollback before you pass the rehearsal.** For each migration step, write the reverse step (a `DROP COLUMN` for an `ADD COLUMN`, for example). Note which steps cannot be reversed, such as a dropped column with data. For those, the rollback is a restore, so confirm a recent backup exists.
- **Stop rule.** If any check in the checklist below fails, you do not run on production.

## Status and limits up front

Everything about Nevia below comes from nevia.cloud docs ([branch page](https://nevia.cloud/docs/databases/branch.md), [why page](https://nevia.cloud/why.md)). I have no beta access and tested none of it. Read each Nevia claim as [TO VERIFY].

- Nevia is in beta and open to selected teams. Public launch is Dec 2026.
- Access is invite-only during the beta. A person signs in in the browser.
- Postgres is the only engine. During the beta the platform sets version, size and storage.
- Nevia is built by Aiven, per its own page.
- Whether a branch copies extensions, roles or settings beyond version, size and storage is not documented. [TO VERIFY]
- Whether Nevia can import or branch an existing Aiven for PostgreSQL service is not documented. [TO VERIFY]

Xata, a competing Postgres branching product, also claims fast branches, and says it is joining ClickHouse ([announcement](https://xata.io/blog/xata-is-joining-clickhouse)). I have not tested Xata either.

## Route 1: branch on Nevia

What the docs say:

- A branch is a snapshot plus a clone. It takes the same time for 1 GB as for 1 TB and uses new space only as it diverges from its parent (vendor-stated).
- The branch has its own host, data disks and password. It inherits the source's Postgres version, size and storage.
- The source keeps running. A fresh snapshot briefly freezes its disk writes. The docs give no duration, so I do not quote one.
- You can branch a `ready` or `sleeping` database with no pending transition or running operation.
- You need the CLI installed and signed in, `psql`, and a workspace where you have the admin or editor role.

Commit the writes you need, wait at least five seconds, then branch. The command comes from the docs example:

```bash
sleep 5
nevia pg branch orders -b orders-staging --wait
```

Get the connection string for `orders-staging` from the Nevia CLI or console (see the [branch docs](https://nevia.cloud/docs/databases/branch.md); I did not verify the exact command) and export it as `BRANCH_URL`.

Mutations on the branch do not affect the source. The docs example shows the source count unchanged while the branch has one more row.

Cleanup:

```bash
nevia pg rm orders-staging --yes --wait
```

If you enabled protection on the branch, clear that first. Deleting the source leaves its branches running with their own data. The docs do not describe what deleting a branch does to its parent; mutations on a branch do not reach the source, so I expect nothing, but that is inference.

## Run the migration and check it

Run the same migration file you plan for production against the branch, then run the checks. Take the "before" numbers on the branch first, since it matches production at snapshot time.

```bash
psql "$BRANCH_URL" -f checks_before.sql > before.txt
psql "$BRANCH_URL" -v ON_ERROR_STOP=1 -1 -f migration.sql
psql "$BRANCH_URL" -f checks_after.sql > after.txt
diff before.txt after.txt
```

`-1` runs the file in one transaction and `ON_ERROR_STOP=1` stops at the first error. Some statements (such as `CREATE INDEX CONCURRENTLY`) cannot run in a transaction; split those into their own file.

`checks_before.sql` and `checks_after.sql` can share this content:

```sql
-- Row counts for the tables the migration touches
SELECT 'orders' AS tbl, count(*) FROM orders
UNION ALL SELECT 'order_items', count(*) FROM order_items;

-- Constraints present, and validated
SELECT conrelid::regclass AS tbl, conname, contype, convalidated
FROM pg_constraint
WHERE conrelid IN ('orders'::regclass, 'order_items'::regclass)
ORDER BY 1, 2;

-- Query plan for the hot query the migration might affect
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE customer_id = 42 ORDER BY created_at DESC LIMIT 20;
```

Replace the table and query names with yours. Read the results like this:

- Row counts should match unless the migration is meant to change them.
- Every constraint you expect should be there with `convalidated = true`. A `NOT VALID` constraint that you meant to validate is a finding.
- The plan should still use the index you expect. Timings on a copy are only a rough guide, because caches and load differ from production.

## Route 2: fork Aiven for PostgreSQL

Use this if production is on Aiven for PostgreSQL today. Per the [fork docs](https://aiven.io/docs/products/postgresql/howto/fork-service), a fork is a complete copy from the latest backup, independent of the original. Be clear about the cost of that:

- It is a full restore, not an instant branch. The docs give no timing or cost figures, and you choose a plan for the fork. How long it takes and what it costs are [TO VERIFY] for your data size.
- The source needs at least one backup.
- Configuration, databases, service users and connection pools are copied. Service integrations are not.
- The fork might initially have only one node while backups are taken.
- For a point in time, choose a time between the first and latest available backups.
- The Aiven docs list testing upgrades before applying them to production as a fork use case.

Setup: you need an Aiven account, a project and an API token, and the CLI signed in (`avn user login`, or a token; see the [CLI docs](https://aiven.io/docs/tools/cli) [TO VERIFY] for the current auth flow). The console route is also available: open the service, choose fork, then pick a name, cloud and plan.

CLI, using the flag the fork page documents:

```bash
avn service create orders-rehearsal \
  --service-type pg \
  --cloud <cloud-region> \
  --plan <plan> \
  --service-to-fork-from orders
```

Only `--service-to-fork-from` is quoted from the fork page. The `--service-type`, `--cloud` and `--plan` flags are [TO VERIFY]: run `avn service create --help`. For a point in time, add `--recovery-target-time` with a timestamp between the first and latest backups.

When the fork is running, get its URI from the console, export it as `FORK_URL`, and run the same checks as above against it. Then delete the fork in the console (or with the `avn service terminate` command [TO VERIFY]) so it stops billing. Fork rehearsal is the subject of a separate post on this blog, "test a migration on a forked copy"; I will link it once it is published rather than repeat it here.

## What neither route shows

This section is my own reasoning, not from Nevia's or Aiven's docs. Neither docs set says what a copy cannot tell you.

- **Live write traffic.** The copy sits idle apart from your checks. A migration that is fine on a quiet database can behave differently under concurrent writes.
- **Lock contention under load.** An `ALTER TABLE` that takes a lock instantly on a quiet copy can queue behind long transactions in production, and block everything behind it. Check with `lock_timeout` set, and read the Postgres docs for the lock level each statement takes.
- **Replication lag.** Neither copy has your production replicas. A large rewrite that is fast on the primary can leave replicas behind.

Mitigations are yours to design: set `lock_timeout` and `statement_timeout` in the production migration, run during a low-traffic window, and prefer additive, backward-compatible steps.

## Decision checklist

Run on production only if all of these are true:

1. The migration ran to completion on a fresh copy with no errors.
2. Before/after row counts match what you intended.
3. Expected constraints exist and are validated.
4. Query plans for your hot queries still look right.
5. You wrote the reverse step for each statement, and you know which steps cannot be reversed.
6. A recent backup of production exists.
7. The production run has `lock_timeout` set, and you know which statements take heavy locks.
8. For Nevia: you waited at least five seconds after your last write before branching, so the copy has the data you meant to test.

Stop if any item fails. Delete the copy, fix the migration, and rehearse again on a new one.

## Why now

Xata's announcement argues that for many companies database workflows are now the bottleneck: every pull request and every agent run needs a safe, isolated database with production-like data. That matches the problem here. A coding agent can produce a migration in seconds, and the slow part is trusting it. A disposable copy is how you get that trust without risking production.

Trade-offs, plainly: a Nevia branch is the faster route in the vendor's own account, but it is beta, invite-only and Postgres-only, with the platform setting version and size, so most readers cannot use it yet. An Aiven fork is available today but is slower and costs plan time. Pick on what you can reach, then run the checklist.
