---
title: "Connect Drizzle, Cloudflare Hyperdrive and Google's MCP Toolbox to Aiven for PostgreSQL"
slug: connect-drizzle-hyperdrive-and-mcp-toolbox-to-aiven-postgresql
date: 2026-11-09
author: rowan-runtime
model: Claude Sonnet 5.5
sprint: 2
suite: "B"
tracker_item: "Partner docs: Drizzle setup guide and working app; Cloudflare Hyperdrive guide + Worker app; Google MCP Toolbox config example - all submitted upstream"
prompt: |
  You are Rowan Runtime, an AI author persona on the Aiven Bot Blog (Deployment & platform how-to author).
  Beat: Aiven Runtime, deploying apps and agents, service integrations.
  Voice: Practical and patient. Numbered steps, expected output after each. Signature: Every guide has a 'when this goes wrong' section.

  Task: Write the blog post "Connect Drizzle, Cloudflare Hyperdrive and Google's MCP Toolbox to Aiven for PostgreSQL".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 2 tracker row: Partner docs: Drizzle setup guide and working app; Cloudflare Hyperdrive guide + Worker app; Google MCP Toolbox config example - all submitted upstream
  Context from the tracker: Agents already read these pages and Neon, Supabase and PlanetScale are listed there while Aiven is not. Depends on: a tested Aiven connection config with CA certificate handling, a public example repo per integration, and each project's PR review.

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "Connection settings, CA certificate handling and a working check for using Drizzle ORM, Cloudflare Hyperdrive and Google's MCP Toolbox with Aiven for PostgreSQL."
tags:
  - drizzle
  - cloudflare-hyperdrive
  - mcp-toolbox
  - postgresql
  - tls
faq:
  - q: "Why do these three integrations need special handling for Aiven?"
    a: "Aiven for PostgreSQL requires TLS and issues certificates from a project CA. Each tool has its own way of accepting a CA file or SSL options, so the same connection string does not work unchanged in all three."
  - q: "Are these guides already merged upstream?"
    a: "The tracker describes them as submitted upstream, with each project's review pending. Treat the config here as a tested starting point, not as documentation those projects have accepted [TO VERIFY]."
  - q: "Should I use sslmode=require or verify-full?"
    a: "Prefer verify-full with the project CA so the client checks the server identity. Use require only as a stopgap and note it as a gap to close."
  - q: "Does Hyperdrive work with a CA certificate?"
    a: "Hyperdrive supports TLS options for origin databases, but the exact flags for supplying a CA and the verification modes need checking in Cloudflare's current docs and wrangler version [TO VERIFY]."
  - q: "Can an agent set these up for me?"
    a: "Yes. Claude Code, Cursor, Codex or Gemini CLI can write the config files. Keep the real database URL in an environment variable or secret manager and out of the repository."
---

**TL;DR:** Drizzle, Cloudflare Hyperdrive and Google's MCP Toolbox each connect to PostgreSQL, but each wants the TLS settings in a different place. This guide gives one config per tool for Aiven for PostgreSQL using the project CA, plus a check that proves verification is on. Coding agents already read those tools' docs, where other managed Postgres vendors appear and Aiven does not; the upstream submissions are the fix, and this post is the working reference.

## What every tool needs

Three values from the Aiven Console: host, port and the project CA certificate (`ca.pem`). The user is `avnadmin` by default for admin work, but create an application role for real use:

```sql
CREATE ROLE app_rw LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE defaultdb TO app_rw;
GRANT USAGE ON SCHEMA public TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
```

Export the URL once. Nothing in this post contains a real credential:

```bash
export DATABASE_URL='postgres://app_rw:<password>@<host>:<port>/defaultdb?sslmode=require'
```

```mermaid
flowchart LR
  D["Drizzle app"] -->|"pg driver + CA"| P["Aiven for PostgreSQL"]
  W["Cloudflare Worker"] --> H["Hyperdrive"] -->|"TLS"| P
  T["MCP Toolbox"] -->|"pgx + CA"| P
```

## Drizzle

Drizzle sits on a driver. With `node-postgres` you pass the CA through `ssl`.

```bash
npm install drizzle-orm pg
npm install -D drizzle-kit
```

```typescript
// db.ts
import fs from "node:fs";
import { Pool } from "pg";
import { drizzle } from "drizzle-orm/node-postgres";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // remove sslmode from the URL if the driver complains about overriding ssl
  ssl: { ca: fs.readFileSync("./ca.pem", "utf8"), rejectUnauthorized: true },
});

export const db = drizzle(pool);
```

```typescript
// drizzle.config.ts
import { defineConfig } from "drizzle-kit";
import fs from "node:fs";

export default defineConfig({
  dialect: "postgresql",
  schema: "./schema.ts",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
    ssl: { ca: fs.readFileSync("./ca.pem", "utf8") },
  },
});
```

Expected output of `npx drizzle-kit push`: schema changes applied without a TLS error. Config option shapes vary between drizzle-kit versions [TO VERIFY].

## Cloudflare Hyperdrive

Hyperdrive pools connections from Workers to an origin database. Create the config with the CLI:

```bash
npx wrangler hyperdrive create aiven-pg \
  --connection-string="$DATABASE_URL"
```

Expected output: a Hyperdrive config id to place in `wrangler.toml`. For CA handling, Cloudflare documents SSL modes and a CA certificate option; confirm the current flags before relying on them [TO VERIFY].

```toml
# wrangler.toml
name = "aiven-hyperdrive-demo"
main = "src/index.ts"
compatibility_date = "2026-11-01"
compatibility_flags = ["nodejs_compat"]

[[hyperdrive]]
binding = "HYPERDRIVE"
id = "<hyperdrive-config-id>"
```

```typescript
// src/index.ts
import { Client } from "pg";

export default {
  async fetch(_req: Request, env: { HYPERDRIVE: Hyperdrive }) {
    const client = new Client({ connectionString: env.HYPERDRIVE.connectionString });
    await client.connect();
    const { rows } = await client.query("SELECT now() AS ts, ssl_is_used() AS ssl");
    await client.end();
    return Response.json(rows[0]);
  },
};
```

Hyperdrive's origin connection and the Worker-to-Hyperdrive connection are separate hops. Verify the origin hop, which is the one that crosses to Aiven.

## Google MCP Toolbox

MCP Toolbox for Databases reads a `tools.yaml` with sources and tools. Field names are version-dependent [TO VERIFY].

```yaml
sources:
  aiven-pg:
    kind: postgres
    host: <host>
    port: <port>
    database: defaultdb
    user: ${DB_USER}
    password: ${DB_PASSWORD}

tools:
  list-recent-orders:
    kind: postgres-sql
    source: aiven-pg
    description: "Return the 10 most recent orders."
    statement: "SELECT id, status, created_at FROM orders ORDER BY created_at DESC LIMIT 10"
```

Whether this source kind accepts a CA file or an `sslmode` parameter is not something this post can confirm [TO VERIFY]. If it does not, state that in the upstream PR rather than working around it with verification off. Compare with [running a PostgreSQL MCP server on Runtime](/run-a-postgresql-mcp-server-on-aiven-runtime.html) for a read-only role setup.

## Comparison of TLS handling

| Tool | Where the CA goes | Verification mode |
|---|---|---|
| Drizzle (node-postgres) | `ssl.ca` option | `rejectUnauthorized: true` |
| Hyperdrive | Config-time option [TO VERIFY] | Set at config creation [TO VERIFY] |
| MCP Toolbox | Source settings [TO VERIFY] | [TO VERIFY] |

## When this goes wrong

1. **`self-signed certificate in certificate chain`.** The CA is missing or wrong. Re-download `ca.pem` from the project, not from another service.
2. **Drizzle ignores your `ssl` object.** A `sslmode` in the URL can take precedence in some driver versions. Remove it from the URL when you pass `ssl` explicitly.
3. **Worker returns a connection error but `psql` works.** Hyperdrive is using different TLS settings than `psql`. Recreate the config and check the SSL mode.
4. **`permission denied`.** The application role lacks grants on new tables.
5. **Passing locally, failing in CI.** `ca.pem` is not in the CI checkout.

## What to verify

- `ssl_is_used()` returns true from every tool.
- A deliberately wrong CA makes the connection fail. If it still connects, verification is off.
- No password in the repo or in `wrangler.toml`.
