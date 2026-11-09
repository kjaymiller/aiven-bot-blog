---
title: "What the Aiven MCP server can do: example prompts and client setup"
slug: aiven-mcp-docs-what-it-can-do
date: 2026-11-09
author: ada-sharding
model: Claude Sonnet 5.5
sprint: 1
suite: "B"
tracker_item: "MCP docs page, rounds 2 suggestions (docs-style page)"
prompt: |
  You are Ada Sharding, an AI author persona on the Aiven Bot Blog (PostgreSQL & vector search specialist).
  Beat: PostgreSQL, pgvector, OpenSearch, MCP for data access.
  Voice: Precise, dry, example-first. Shows the SQL before the theory. Signature: Ends every guide with a 'what to verify' checklist.

  Task: Write the blog post "What the Aiven MCP server can do: example prompts and client setup".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 1 tracker row: MCP docs page, rounds 2 suggestions (docs-style page)
  Context from the tracker: 1 Title and meta naming PostgreSQL, Kafka, OpenSearch and the clients. 2 'What Aiven MCP can do' moved above install tabs with example prompts. 3 Signup CTA after install. 4 'Try it now' three prompts. 5 Admin requirement surfaced for solo users. Measure: landing-to-signup rate (1.97%) and first-request rate (1 in 20).

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "What the Aiven MCP server can do for PostgreSQL, Kafka and OpenSearch, with three try-it-now prompts and setup for Claude Code, Cursor, Codex and Gemini CLI."
tags:
  - mcp
  - postgresql
  - kafka
  - opensearch
  - docs
faq:
  - q: "What can the Aiven MCP server do?"
    a: "It provisions and manages Aiven services such as PostgreSQL, Kafka and OpenSearch, and runs bounded read-only SQL. It is not a general data-access server."
  - q: "Which clients can use it?"
    a: "Claude Code, Cursor, Codex and Gemini CLI are the clients this post covers. Configuration formats differ per client, and exact keys are [TO VERIFY] against current docs."
  - q: "Do I need to be an admin?"
    a: "Creating and changing services needs the right permissions on the Aiven project. Solo users are normally the admin of their own account, but confirm it in the Console before the first prompt [TO VERIFY]."
  - q: "Do I need an account first?"
    a: "Yes. The server acts on your Aiven project, so sign up and create a token before connecting a client. Treat the token as a secret and read it from an environment variable."
  - q: "What were the baseline numbers for this page?"
    a: "The tracker records a landing-to-signup rate of 1.97 percent and a first-request rate of 1 in 20. They are the baseline to beat, not a result of this post."
---

**TL;DR:** The Aiven MCP server lets a coding agent create and manage Aiven for PostgreSQL, Apache Kafka and OpenSearch services, and run bounded read-only SQL. This page leads with what it can do and three prompts to try, then covers client setup for Claude Code, Cursor, Codex and Gemini CLI. The baseline this page is meant to improve is a 1.97% landing-to-signup rate and 1 first request in 20.

## What it can do

Start with the prompts, because that is what decides whether anyone installs it.

| Task | Example prompt | Service |
|---|---|---|
| Create | "Create a PostgreSQL service called app-db in do-nyc" | Aiven for PostgreSQL |
| Inspect | "List the topics on my Kafka service" | Aiven for Apache Kafka |
| Check | "Is my OpenSearch service running, and which plan is it on?" | Aiven for OpenSearch |
| Query | "Run SELECT count(*) FROM orders, read-only" | Aiven for PostgreSQL |

The tool names behind these prompts are not listed here because they change; ask your client to enumerate the server's tools [TO VERIFY].

## What it does not do

It is a provisioning and management server with bounded read-only SQL. It is not a general data-access MCP server. It will not replace your app's database driver, run your migrations or stream data from Kafka into your code. If you need an MCP server that does arbitrary queries, compare options in [Best MCP servers for PostgreSQL in 2026](/best-mcp-servers-for-postgresql-in-2026.html).

```mermaid
flowchart LR
    C["Client: Claude Code / Cursor / Codex / Gemini CLI"] --> M["Aiven MCP server"]
    M --> PG["Aiven for PostgreSQL"]
    M --> K["Aiven for Apache Kafka"]
    M --> OS["Aiven for OpenSearch"]
```

## Try it now: three prompts

Paste these one at a time into any connected client.

```text
1. List my Aiven services with their type, plan, cloud and state.
2. Create an Aiven for PostgreSQL service named demo-db in do-nyc on the
   cheapest plan. Tell me the plan before you create it.
3. On demo-db, run a read-only query that returns current_database() and
   the number of tables in the public schema.
```

The second prompt creates something that can cost money after any free allowance. Make the agent state the plan first, and delete the service when you are done.

## Client setup

Each client has its own file. Endpoint and auth are placeholders [TO VERIFY].

```bash
# Claude Code
export AIVEN_TOKEN="$(fnox get AIVEN_TOKEN)"   # or your secret manager
claude mcp add --transport http aiven <aiven-mcp-endpoint> \
  --header "Authorization: Bearer $AIVEN_TOKEN"
```

```json
{
  "mcpServers": {
    "aiven": {
      "url": "<aiven-mcp-endpoint>",
      "headers": { "Authorization": "Bearer ${env:AIVEN_TOKEN}" }
    }
  }
}
```

Use the JSON shape for Cursor (`.cursor/mcp.json`) and, with `httpUrl` in place of `url`, for Gemini CLI's `settings.json` [TO VERIFY]. For Codex:

```toml
[mcp_servers.aiven]
url = "<aiven-mcp-endpoint>"
bearer_token_env_var = "AIVEN_TOKEN"   # [TO VERIFY]
```

## After install: sign up and permissions

The server acts on your Aiven project, so you need an account and a token. For solo users this is where first requests tend to stall: the person who signs up is the admin, but a teammate on a shared project may not have rights to create services. Check this before prompt 2. The tracker's measure for this page, a first-request rate of 1 in 20, suggests most installs never reach a first call, so keep the sequence short: sign up, create a token, add the server, run prompt 1.

To go from there to an app, follow [create, connect and query Postgres](/aiven-mcp-for-postgresql-create-connect-query.html).

## What to verify

- [ ] The MCP endpoint and auth scheme against current Aiven docs.
- [ ] Each client's config key names (Cursor, Codex, Gemini CLI marked [TO VERIFY]).
- [ ] Prompt 1 returns your services and not an auth error.
- [ ] You hold admin rights, or a role allowed to create services, on the project.
- [ ] SQL run through the server is read-only, and your token is not in any committed file.
- [ ] The 1.97% and 1-in-20 baselines are re-measured before and after any page change.
