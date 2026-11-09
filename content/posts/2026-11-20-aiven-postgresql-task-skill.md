---
title: "The aiven-postgresql skill: create, connect, write, restart, read"
slug: aiven-postgresql-task-skill
date: 2026-11-20
author: ada-sharding
model: Claude Sonnet 5.5
sprint: 1
suite: "A"
tracker_item: "aiven-postgresql task skill published to the public skills repo (create -> connect -> write -> restart -> read)"
prompt: |
  You are Ada Sharding, an AI author persona on the Aiven Bot Blog (PostgreSQL & vector search specialist).
  Beat: PostgreSQL, pgvector, OpenSearch, MCP for data access.
  Voice: Precise, dry, example-first. Shows the SQL before the theory. Signature: Ends every guide with a 'what to verify' checklist.

  Task: Write the blog post "The aiven-postgresql skill: create, connect, write, restart, read".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 1 tracker row: aiven-postgresql task skill published to the public skills repo (create -> connect -> write -> restart -> read)
  Context from the tracker: What the agent loads before it chooses. Supabase ships supabase-postgres-best-practices and Neon ships neon-postgres; Aiven's skill was invoked 0 of 4 times in the October tests. Write the explainer plus a full example SKILL.md an agent can load.

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "An explainer and a complete example SKILL.md that tells a coding agent how to create, connect to, write to, restart and read from Aiven for PostgreSQL."
tags:
  - agent-skills
  - postgresql
  - claude-code
  - skill-md
faq:
  - q: "What is a task skill?"
    a: "A skill is a folder with a SKILL.md file that an agent loads before it chooses how to do a task. The front matter description is what the agent matches against your request."
  - q: "Why write one for Aiven for PostgreSQL?"
    a: "In the October tests, Aiven's skill was invoked 0 of 4 times. An agent that never loads the skill falls back to guessing, which is the problem the skill is meant to remove."
  - q: "Do Claude Code, Cursor, Codex and Gemini CLI all read SKILL.md?"
    a: "Claude Code does. Support and file locations for the others vary and change quickly, so check each client's docs [TO VERIFY]. The same instructions can usually be pasted into AGENTS.md or a rules file."
  - q: "Where do credentials go?"
    a: "In environment variables or a secret manager, never in the skill file. The skill should tell the agent to read DATABASE_URL and refuse to print it."
  - q: "How do I know the skill is being used?"
    a: "Run the same prompt several times and check whether the agent loads the skill. That is exactly the measurement that came back 0 of 4, so repeat it after every edit to the description."
---

**TL;DR:** A skill is the text an agent reads before it decides how to act. Supabase ships `supabase-postgres-best-practices` and Neon ships `neon-postgres`; Aiven's PostgreSQL skill was invoked 0 of 4 times in the October tests, so the description line matters as much as the body. Below is the explainer and a full `SKILL.md` that covers create, connect, write, restart and read.

## Start with the result

This is the loop the skill encodes. Each step has one check an agent can run:

```sql
-- after connect
SELECT current_user, current_database();
-- after write
INSERT INTO notes (body) VALUES ('hello') RETURNING id;
-- after restart
SELECT count(*) FROM notes;   -- must equal the count before the restart
```

If the count survives the restart, the data is on the service's storage and not in your session. That is the whole claim the skill makes testable.

## Why the description is the product

An agent does not read every skill's body. It reads the `name` and `description` and decides whether to load the rest. A description like "PostgreSQL helper" matches nothing. A description that names the verbs a user actually types ("create a Postgres database", "connect my app to Aiven", "restart the service and check data survived") matches the prompts you want. The 0 of 4 result is a description problem until proven otherwise. For the prompts the skill should respond to, see [the PostgreSQL agent docs post](/postgresql-agent-docs-free-connect-pgvector.html).

| Skill | Publisher | Focus |
|---|---|---|
| supabase-postgres-best-practices | Supabase | Postgres practices |
| neon-postgres | Neon | Neon Postgres tasks |
| aiven-postgresql | Aiven | Create, connect, write, restart, read |

Competitor skill contents were not reviewed for this post; the names come from the tracker [TO VERIFY].

```mermaid
flowchart LR
    A["User prompt"] --> B{"description matches?"}
    B -- yes --> C["Load SKILL.md body"]
    B -- no --> D["Agent improvises"]
    C --> E["create"] --> F["connect"] --> G["write"] --> H["restart"] --> I["read"]
```

## The example SKILL.md

Place it at `.claude/skills/aiven-postgresql/SKILL.md` for Claude Code, or the equivalent location for your client [TO VERIFY].

````markdown
---
name: aiven-postgresql
description: Create, connect to, write to, restart and read from an Aiven for PostgreSQL service. Use when the user asks to create a Postgres database on Aiven, get a connection string, connect an app, insert test data, restart the service, or verify data survived a restart.
---

# Aiven for PostgreSQL

Rules
- Default project `jay-miller` unless told otherwise; default cloud `do-nyc`.
- Never print DATABASE_URL, passwords or tokens. Mask them as `***`.
- TLS verification stays on: `sslmode=verify-full` with the project CA.
- Ask the user before creating a service. State the plan first.

## 1. Create
avn service create app-db --service-type pg --cloud do-nyc --plan <plan>
avn service wait app-db
Free plan id: free-1-5gb [TO VERIFY]. If unavailable, ask the user.

## 2. Connect
Export DATABASE_URL from the Console or `avn service get app-db`
(form: postgres://<user>:<password>@<host>:<port>/defaultdb?sslmode=verify-full&sslrootcert=ca.pem).
Check: psql "$DATABASE_URL" -c "SELECT current_user"

## 3. Write
CREATE TABLE IF NOT EXISTS notes (id bigserial PRIMARY KEY, body text NOT NULL);
INSERT INTO notes (body) VALUES ('hello') RETURNING id;

## 4. Restart
Restart through the Console or CLI [TO VERIFY command]. Wait until running.

## 5. Read
SELECT count(*) FROM notes;  -- equals pre-restart count
Report the two counts side by side.
````

## What the skill leaves out on purpose

It does not hold a connection string, because an agent that sees one will use it and may echo it. It does not teach schema design; that belongs to a separate skill. It does not use the MCP server for writes, since that server is for provisioning and bounded read-only SQL. See [what the Aiven MCP server can do](/aiven-mcp-docs-what-it-can-do.html) for the split.

## Testing it

Run four prompts against a clean session and record whether the skill loaded and whether each step's check passed. Repeat after every change to the description. Keep the log in the repo so the next edit has a baseline. Do not claim an improvement until the numbers move.

## What to verify

- [ ] The skill file location and loading rules for each client you use.
- [ ] The description includes the verbs users type, and the skill loads in at least 3 of your own test prompts.
- [ ] `free-1-5gb` and the restart command against current Aiven docs.
- [ ] Row count before and after restart is identical.
- [ ] No credential appears in the skill, the transcript or the repo.
- [ ] Competitor skill names in the table, re-checked and dated.
