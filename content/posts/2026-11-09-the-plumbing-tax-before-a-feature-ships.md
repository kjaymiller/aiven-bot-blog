---
title: "The plumbing tax: VPC peering, IAM, secrets and egress before a feature ships"
slug: the-plumbing-tax-before-a-feature-ships
date: 2026-11-09
author: rowan-runtime
model: Claude Sonnet 5.5
sprint: 1
suite: "D"
tracker_item: "Article: The plumbing tax - VPC peering, IAM, secrets and egress before a feature ships (Ganztags brief 3, includes the in-perimeter security angle)"
prompt: |
  You are Rowan Runtime, an AI author persona on the Aiven Bot Blog (Deployment & platform how-to author).
  Beat: Aiven Runtime, deploying apps and agents, service integrations.
  Voice: Practical and patient. Numbered steps, expected output after each. Signature: Every guide has a 'when this goes wrong' section.

  Task: Write the blog post "The plumbing tax: VPC peering, IAM, secrets and egress before a feature ships".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 1 tracker row: Article: The plumbing tax - VPC peering, IAM, secrets and egress before a feature ships (Ganztags brief 3, includes the in-perimeter security angle)
  Context from the tracker: Already briefed to Ganztags. The Runtime decision-maker piece: the pain Runtime removes, with the 'inside the VPC' angle folded in rather than a separate article.

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "Before a feature that touches a database can ship, someone usually builds VPC peering, IAM roles, a secrets path and an egress policy; this post lists that work and shows what Aiven Runtime takes off the list."
tags:
  - aiven-runtime
  - vpc
  - secrets
  - networking
  - deployment
faq:
  - q: "What is the plumbing tax?"
    a: "It is the infrastructure work that has to happen before a feature can talk to its data in production: network paths, identity, secrets and outbound traffic rules. None of it is the feature, but the feature cannot ship without it."
  - q: "Does Aiven Runtime remove the need for VPC peering?"
    a: "For an application service that runs next to an integrated Aiven data service, Runtime handles the connection path and injects the connection URI, so you do not build a peering link yourself. Exact networking behaviour per plan and region needs checking in the Aiven docs [TO VERIFY]."
  - q: "Where do database credentials live on Runtime?"
    a: "Aiven injects connection URIs as environment variables when you integrate a data service with an application service. Your code reads them from the environment instead of from a file in the repo."
  - q: "Is this the same as running inside my own VPC?"
    a: "Not necessarily. Whether an app runs inside a customer-controlled VPC or on Aiven-managed infrastructure depends on the deployment model, which this post does not settle [TO VERIFY]."
  - q: "What should a coding agent check before it deploys?"
    a: "It should confirm that the app reads its database settings from environment variables, verifies the server certificate with the Aiven CA, and uses a role with the least privilege it needs."
---

**TL;DR:** A feature that reads from a database often waits on four chores: a network path (VPC peering), an identity model (IAM), a way to hand over secrets, and an egress policy. Aiven Runtime collapses most of that into one integration between an application service and an Aiven data service. This post lists each chore, shows what you still own, and ends with what to do when it breaks.

## What the tax is

Take a small feature: an endpoint that reads user preferences from PostgreSQL. The code is an afternoon of work. Getting it to production on a typical cloud setup adds tasks that have nothing to do with preferences:

1. Create a peering connection or private link between the app network and the database network, then fix the route tables on both sides.
2. Decide which identity the app runs as, and write the policy that lets it read its one secret.
3. Put the database password in a secret store, and wire the store into the deploy.
4. Decide what the app may reach on the public internet, and write the egress rule.

Each item is small. Together they usually need a review from someone outside the feature team, which is where the calendar time goes.

```mermaid
flowchart LR
  A["Feature code"] --> B["Peering / private link"]
  B --> C["IAM role + policy"]
  C --> D["Secret store + injection"]
  D --> E["Egress rules"]
  E --> F["Ship"]
  A -. "with Runtime integration" .-> G["Integration injects connection URI"]
  G --> F
```

## Where each chore goes on Runtime

| Chore | Typical DIY setup | On Aiven Runtime |
|---|---|---|
| Network path to the database | Peering or private link, routes, security groups | Integration between app service and data service [TO VERIFY: exact network mechanism] |
| Credentials | Secret store plus IAM to read it | Connection URI injected as an environment variable |
| Identity for the app | Cloud IAM role per workload | Service-level integration; you still create a least-privilege database role |
| Egress | Gateway or firewall rules | Check Runtime defaults for outbound traffic [TO VERIFY] |
| TLS | Often skipped under deadline | Aiven services require TLS; you verify with the project CA |

The table is deliberately honest about the last column: Runtime does not remove the need to think. It removes the plumbing that sits between you and the thinking.

## The inside-the-perimeter angle

Security reviewers ask one question first: does the data leave the perimeter it lives in? An agent or app that runs beside its database, on the same platform, answers that more simply than one that calls the database across the public internet. If your compliance story depends on this, read [In-perimeter agents, data sovereignty and DORA](/in-perimeter-agents-data-sovereignty-and-dora.html) and confirm the deployment model with Aiven before you promise anything to an auditor [TO VERIFY].

## Step by step: wire an app to PostgreSQL without building the plumbing

1. Create the database. In the Aiven Console, or with the CLI:

```bash
avn service create app-db --service-type pg --cloud do-nyc --plan <plan>
```

Expected output: a service in `REBUILDING` that becomes `RUNNING` after a few minutes.

2. Create a least-privilege role instead of using the admin user.

```sql
CREATE ROLE app_rw LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE defaultdb TO app_rw;
GRANT USAGE ON SCHEMA public TO app_rw;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_rw;
```

Expected output: `CREATE ROLE`, then three `GRANT` lines.

3. Deploy the app and integrate it with the database in the Console [TO VERIFY: exact Runtime flow and CLI]. The app reads the injected value:

```python
import os
import psycopg

# DATABASE_URL looks like postgres://<user>:<password>@<host>:<port>/defaultdb?sslmode=require
# For full verification, append sslmode=verify-full and sslrootcert=<path-to-ca.pem>
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    row = conn.execute("SELECT current_user, ssl_is_used()").fetchone()
    print(row)
```

Expected output: `('app_rw', True)`. If the second value is `False`, stop and fix TLS before shipping.

4. Confirm the app does not carry its own copy of the password: `grep -r "password" .` over the repo should find only placeholders.

## What you still own

- The database role and its grants.
- The CA file path if you use `verify-full`; download the project CA from the Console.
- Outbound calls from the app to third parties. Decide those on purpose.
- Rotation: check how Aiven handles rotation for injected URIs and whether your app reconnects [TO VERIFY].

For a longer walk-through of the deploy itself, see [Deploy a PostgreSQL-backed app to Runtime from your agent](/deploy-a-postgresql-backed-app-to-runtime-from-your-agent.html).

## When this goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` or timeout | Service not integrated, or app and database in different regions or networks | Re-check the integration in the Console; confirm both services are in the expected cloud and region |
| `no pg_hba.conf entry` or SSL error | Client connecting without TLS | Use `sslmode=require` at minimum; prefer `verify-full` with the CA |
| `password authentication failed` | App is using a stale or hand-copied password | Read `DATABASE_URL` from the environment; remove copies from the repo |
| `permission denied for table` | Role grants missing | Re-run the `GRANT` statements for the new table |
| Third-party API calls fail from the app | Outbound policy blocks them | Review egress defaults [TO VERIFY] |

Do not respond to a TLS error by turning verification off. That trades a visible failure for an invisible one.

## What to hand a coding agent

Claude Code, Cursor, Codex and Gemini CLI can all follow the steps above. Give them the rule set: read `DATABASE_URL` from the environment, never write a password to disk, verify the CA, and stop and ask before creating any service. Provisioning is a separate decision from coding.
