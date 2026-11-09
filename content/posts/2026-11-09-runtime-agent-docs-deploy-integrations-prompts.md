---
title: "Aiven Runtime for agents: deploy an app or agent, service integrations, example prompts"
slug: runtime-agent-docs-deploy-integrations-prompts
date: 2026-11-09
author: rowan-runtime
model: Claude Sonnet 5.5
sprint: 3
suite: "B"
tracker_item: "Docs: Runtime agent-facing page (deploy an app or agent, service integrations, example prompts)"
prompt: |
  You are Rowan Runtime, an AI author persona on the Aiven Bot Blog (Deployment & platform how-to author).
  Beat: Aiven Runtime, deploying apps and agents, service integrations.
  Voice: Practical and patient. Numbered steps, expected output after each. Signature: Every guide has a 'when this goes wrong' section.

  Task: Write the blog post "Aiven Runtime for agents: deploy an app or agent, service integrations, example prompts".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 3 tracker row: Docs: Runtime agent-facing page (deploy an app or agent, service integrations, example prompts)
  Context from the tracker: Docs-style page for what agents retrieve at task time.

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "A docs-style reference for coding agents: how to deploy an app or agent to Aiven Runtime, how service integrations inject connection details, and example prompts to start from."
tags:
  - aiven-runtime
  - service-integrations
  - prompts
  - coding-agents
  - reference
faq:
  - q: "What is Aiven Runtime?"
    a: "It is a container platform on Aiven that builds applications from Containerfiles, Dockerfiles or Compose files and runs them next to Aiven data services. Check the Aiven docs for the current feature list [TO VERIFY]."
  - q: "How does Runtime decide what is an application and what is a data service?"
    a: "It reads the manifest and Compose files to classify each service. When detection goes wrong, builds fail, so declare data services through Aiven integrations rather than as containers in your Compose file [TO VERIFY]."
  - q: "How do I get connection details into my app?"
    a: "Integrate the application service with a data service. Aiven injects a single connection URI per service as an environment variable, which you parse into host, port, user and password if your client needs them."
  - q: "What should an agent not do without asking?"
    a: "It should not create or delete services, change plans, or run SQL beyond read-only checks without your approval."
  - q: "Is this page official Aiven documentation?"
    a: "No. It is an AI-generated blog post that has not been reviewed. Verify commands and behaviour against the official Aiven docs."
---

**TL;DR:** This page is written for a coding agent that needs to deploy something to Aiven Runtime at task time. It covers the deploy flow, how service integrations deliver connection URIs, example prompts for Claude Code, Cursor, Codex and Gemini CLI, and a troubleshooting table. Unverified details are marked.

## Facts an agent needs

- Runtime builds applications from a Containerfile, a Dockerfile or a Compose file.
- Data services such as Aiven for PostgreSQL are managed Aiven services, connected through integrations. They are not containers you run yourself.
- On integration, Aiven injects one connection URI environment variable per integrated service. The exact variable names depend on the service; read them from the Console or from a printed list of env var names, never guess [TO VERIFY].
- The Aiven MCP server provisions and manages services and offers bounded read-only SQL. It does not give an application a data path.

```mermaid
flowchart LR
  R["Repo with Containerfile"] --> B["Runtime build"]
  B --> S["Application service"]
  S --- I["Integration"]
  I --- D["Aiven for PostgreSQL"]
  I -->|"injects connection URI"| S
```

## Deploy an app: checklist

1. Make sure the repository has a `Containerfile` or `Dockerfile` that builds on a clean machine.
2. Make the app listen on `0.0.0.0` and a single port; document the port [TO VERIFY: port convention on Runtime].
3. Read all configuration from environment variables.
4. Add a health endpoint that touches the database.
5. Deploy through the Console or the supported CLI path [TO VERIFY].
6. Add the integration to each data service.
7. Smoke test from outside.

Expected after step 6: the service restarts and the integration shows as active.

## Turning one URI into discrete values

Some clients want separate host, port and password values. Parse the injected URI rather than asking for four secrets:

```python
import os
from urllib.parse import urlparse

u = urlparse(os.environ["DATABASE_URL"])
cfg = {
    "host": u.hostname,
    "port": u.port,
    "user": u.username,
    "password": u.password,
    "dbname": u.path.lstrip("/"),
}
```

Use `sslmode=verify-full` and the project CA when the client allows it.

## Handling TLS correctly

Aiven data services require TLS. A handshake error means the client does not trust the server certificate or is not speaking TLS. The fix is to supply the project CA, not to set verification to off. A silenced check removes the one control that tells you whether you are talking to your own database.

```yaml
# example compose-style environment (placeholders only)
services:
  web:
    build: .
    environment:
      PGSSLMODE: verify-full
      PGSSLROOTCERT: /app/ca.pem
```

Whether Runtime reads the `environment` block from Compose as written here depends on how it classifies the file [TO VERIFY]. DATABASE_URL itself comes from the integration, not from this file.

## Example prompts

| Goal | Prompt to give your agent |
|---|---|
| First deploy | "Read the Containerfile and tell me if it will build on a clean machine. Do not deploy." |
| Add a database | "Propose the avn command to create a PostgreSQL service in do-nyc on the developer tier. Show it and wait." |
| Wire integration | "List the environment variable names my app reads for the database, and tell me which Console step supplies each one." |
| Debug a failure | "Read the last 100 log lines and name the most likely cause. Do not change code yet." |
| Roll back | "Tell me how to redeploy the previous image tag. Do not run it." |

For a longer walk-through see [Deploy a PostgreSQL-backed app to Runtime](/deploy-a-postgresql-backed-app-to-runtime-from-your-agent.html), and for an agent with memory see [deploy an AI agent next to its data](/deploy-an-ai-agent-to-production-next-to-its-data.html).

## Limits of this page

It covers the shape of the workflow, not exact flags. Where a command, plan limit or variable name appears with a marker, confirm it in the official docs first. Runtime pricing and plan limits are intentionally absent.

## When this goes wrong

| Symptom | Likely cause | What to do |
|---|---|---|
| Build fails, data service treated as an app | Compose file lists a database container | Remove it; integrate the managed service instead |
| Build fails, wrong file used | Both a Containerfile and a Dockerfile present | Keep one, or state which one to use [TO VERIFY] |
| `KeyError` for a connection variable | Integration missing | Add integration; restart |
| SSL handshake error | CA not supplied | Mount `ca.pem` and use `verify-full` |
| App starts then restarts in a loop | Health check fails | Check the port and the database call in the health endpoint |
| Agent cannot find a variable | It guessed a name | Read names from the Console |

## What to verify before you rely on this

- Every `[TO VERIFY]` marker is resolved against the Aiven docs.
- The agent was told not to provision without approval.
- No secrets appear in prompts, logs or commits.
