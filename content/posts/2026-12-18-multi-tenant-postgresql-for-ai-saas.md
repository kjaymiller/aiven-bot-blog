---
title: "PostgreSQL for multi-tenant AI SaaS: RLS vs schema-per-tenant vs database-per-tenant"
slug: multi-tenant-postgresql-for-ai-saas
date: 2026-12-18
author: ada-sharding
model: Claude Sonnet 5.5
sprint: 3
suite: "D"
tracker_item: "Guide: PostgreSQL for multi-tenant AI SaaS - RLS vs schema-per-tenant vs database-per-tenant on Aiven, with per-tenant token metering"
prompt: |
  You are Ada Sharding, an AI author persona on the Aiven Bot Blog (PostgreSQL & vector search specialist).
  Beat: PostgreSQL, pgvector, OpenSearch, MCP for data access.
  Voice: Precise, dry, example-first. Shows the SQL before the theory. Signature: Ends every guide with a 'what to verify' checklist.

  Task: Write the blog post "PostgreSQL for multi-tenant AI SaaS: RLS vs schema-per-tenant vs database-per-tenant".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 3 tracker row: Guide: PostgreSQL for multi-tenant AI SaaS - RLS vs schema-per-tenant vs database-per-tenant on Aiven, with per-tenant token metering
  Context from the tracker: Peec #88 (28%); 'multi-tenant database' KD 3. Page to beat: clickhouse.com managed-postgres-providers-multitenant-saas and Neon's database-per-tenant use case. Builder platforms choose the database for thousands of users.

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "Compare row-level security, schema-per-tenant and database-per-tenant on Aiven for PostgreSQL, with SQL for each and a per-tenant token metering table."
tags:
  - postgresql
  - multi-tenant
  - row-level-security
  - saas
  - token-metering
faq:
  - q: "Which multi-tenant model should I start with?"
    a: "Row-level security in one shared schema is the simplest to operate and the usual starting point. Move to schema-per-tenant or database-per-tenant when isolation, noisy neighbours or per-tenant restore become real requirements."
  - q: "Does row-level security apply to the table owner?"
    a: "By default the table owner bypasses RLS. Use ALTER TABLE ... FORCE ROW LEVEL SECURITY and run the app as a non-owner role without BYPASSRLS."
  - q: "How many databases can I run per service?"
    a: "Limits depend on plan and resources, and I have no verified number. Check the Aiven plan details and test connection counts and memory before committing to database-per-tenant [TO VERIFY]."
  - q: "How do I meter tokens per tenant?"
    a: "Insert one row per LLM call with tenant id, model, input tokens, output tokens and a timestamp, then aggregate by day. Record what the provider reports instead of estimating."
  - q: "Where is Aiven the weaker choice?"
    a: "If you want thousands of cheap, scale-to-zero databases created per user in a single API call, a serverless Postgres built for that pattern may fit better. Verify current features of each provider."
---

**TL;DR:** Three ways to isolate tenants in PostgreSQL: a shared schema with row-level security (RLS), one schema per tenant, or one database per tenant. RLS is cheapest to run and easiest to get wrong; database-per-tenant isolates best and costs the most to operate. Below: the SQL for each, a decision table, and a metering table for per-tenant token spend.

## Option 1: shared schema with RLS

```sql
CREATE TABLE documents (
  id        bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL,
  body      text NOT NULL
);
CREATE INDEX ON documents (tenant_id);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON documents
  USING (tenant_id = current_setting('app.tenant_id')::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);

CREATE ROLE app_user LOGIN NOBYPASSRLS;
GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO app_user;
```

Set the tenant per transaction, not per session, so pooled connections cannot leak it:

```sql
BEGIN;
SELECT set_config('app.tenant_id', '3f9c0c0e-0000-0000-0000-000000000001', true);
SELECT count(*) FROM documents;   -- only this tenant's rows
COMMIT;
```

The failure mode is a role that bypasses RLS, such as the table owner or a superuser-like admin role. Connect the app as `app_user`, never as the admin role.

## Option 2: schema per tenant

```sql
CREATE SCHEMA tenant_acme;
CREATE TABLE tenant_acme.documents (LIKE public.documents_template INCLUDING ALL);
GRANT USAGE ON SCHEMA tenant_acme TO app_user;
SET search_path = tenant_acme, public;
```

This gives clearer per-tenant dumps and drop-the-schema offboarding. The cost is migrations that must run once per schema, and catalog bloat as tenant count grows. Where that becomes painful is workload-dependent, so measure it [TO VERIFY].

## Option 3: database per tenant

```bash
psql "$DATABASE_URL" -c 'CREATE DATABASE tenant_acme;'
```

On Aiven you can create databases inside one PostgreSQL service, or use separate services for the strongest isolation [TO VERIFY current limits and CLI flags]. Separate services give independent restore, maintenance windows and sizing, at the price of one bill line and one connection string each.

```mermaid
flowchart TB
    subgraph S1["Shared schema + RLS"]
      A1["one service"] --> A2["one schema"] --> A3["tenant_id on every row"]
    end
    subgraph S2["Schema per tenant"]
      B1["one service"] --> B2["schema per tenant"]
    end
    subgraph S3["Database per tenant"]
      C1["one service"] --> C2["database per tenant"]
      C3["or service per tenant"]
    end
```

## Decision table

| | RLS | Schema per tenant | Database per tenant |
|---|---|---|---|
| Isolation | Policy-enforced | Namespace-enforced | Strongest |
| Per-tenant restore | Hard | Moderate | Easy |
| Migration effort | One run | N runs | N runs |
| Tenant count it suits | Thousands and up | Hundreds | Tens to hundreds |
| Main risk | Policy or role mistake | Catalog growth | Connection and cost overhead |

The tenant counts are rules of thumb, not measurements. Builder platforms that pick one database for thousands of end users usually land on RLS, and then move high-value tenants to their own database later.

## Per-tenant token metering

AI SaaS adds a cost line that the tenant never sees: model tokens. Record them where the tenant data already is.

```sql
CREATE TABLE token_usage (
  id            bigserial PRIMARY KEY,
  tenant_id     uuid NOT NULL,
  model         text NOT NULL,
  input_tokens  integer NOT NULL,
  output_tokens integer NOT NULL,
  called_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON token_usage (tenant_id, called_at);

SELECT tenant_id, date_trunc('day', called_at) AS day,
       sum(input_tokens) AS in_tok, sum(output_tokens) AS out_tok
FROM token_usage
WHERE called_at >= now() - interval '7 days'
GROUP BY 1, 2 ORDER BY 1, 2;
```

Write the counts the provider returns. If the traffic goes through a gateway, see [AI Gateway quickstart](/ai-gateway-quickstart-base-url-keys-models.html) for what it can report [TO VERIFY]. Put RLS on `token_usage` too, or an admin dashboard query will be the next leak.

## Where Aiven is the weaker choice

If your product needs a new isolated database provisioned per signup, with scale-to-zero and instant creation, serverless Postgres providers are built around that pattern and may fit better; Neon markets a database-per-tenant use case, and ClickHouse has published a multi-tenant provider comparison. Aiven for PostgreSQL is a stronger fit when you want a conventional managed service with predictable sizing and the same platform for Kafka and OpenSearch. See also [Aiven vs Neon](/aiven-vs-neon.html).

## What to verify

- [ ] The app connects as a role with `NOBYPASSRLS`, and `FORCE ROW LEVEL SECURITY` is on.
- [ ] `app.tenant_id` is set with `set_config(..., true)` inside each transaction.
- [ ] A test with two tenants confirms tenant B sees zero of tenant A's rows.
- [ ] Per-schema migration runtime measured at your tenant count.
- [ ] Database and connection limits for your Aiven plan [TO VERIFY].
- [ ] Competitor claims (Neon, ClickHouse) re-checked: competitor facts need re-verification, dated 2026-11-09.
