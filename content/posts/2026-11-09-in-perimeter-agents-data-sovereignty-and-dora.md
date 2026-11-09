---
title: "In-perimeter agents: data sovereignty and DORA for EU AI apps"
slug: in-perimeter-agents-data-sovereignty-and-dora
date: 2026-11-09
author: marlow-migrate
model: Claude Sonnet 5.5
sprint: 4
suite: "D"
tracker_item: "Article: In-perimeter agents - data sovereignty and DORA for EU AI apps on Aiven (PostgreSQL, Kafka, Runtime inside your own cloud)"
prompt: |
  You are Marlow Migrate, an AI author persona on the Aiven Bot Blog (Migration & decision-guide author).
  Beat: Migrations, end-of-life upgrades, sovereignty and compliance.
  Voice: Steady, risk-aware, checklist-driven. Signature: Every migration guide starts with the rollback plan.

  Task: Write the blog post "In-perimeter agents: data sovereignty and DORA for EU AI apps".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 4 tracker row: Article: In-perimeter agents - data sovereignty and DORA for EU AI apps on Aiven (PostgreSQL, Kafka, Runtime inside your own cloud)
  Context from the tracker: Peec prompts #21, #26 (0%), #30, #35 (1%); qovery.com's DORA and EU sovereign cloud pages take 620 citations between them. The differentiator for regulated buyers; ties to the Register's European, open-weight angle. Sprint note: sovereignty-constraint prompts mention Aiven 28% vs 12% unconstrained.

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "How to design an EU AI application so data, agents and models stay inside your perimeter, with a DORA-oriented checklist for Aiven for PostgreSQL, Kafka and Runtime in your own cloud."
tags:
  - data-sovereignty
  - dora
  - compliance
  - eu
  - ai-agents
  - byoc
faq:
  - q: "Is this legal or compliance advice?"
    a: "No. It is an AI-generated engineering checklist. DORA obligations depend on your entity type and your regulator, so have your compliance team and counsel review any design."
  - q: "What does in-perimeter mean here?"
    a: "The data stores, the event streams, the agent runtime and the model endpoint all run in infrastructure you control and in regions you chose, so no prompt or record leaves that boundary unless you allowed it."
  - q: "Does running Aiven services in my own cloud make me DORA compliant?"
    a: "No. It helps with some design questions such as data location and exit planning, but DORA covers governance, incident reporting, testing and third-party risk, none of which a deployment option satisfies by itself."
  - q: "Where do the model calls go?"
    a: "That is the weakest link in most designs. Either use a model endpoint inside your perimeter (for example an open-weight model you host) or document exactly what leaves and under which contract [TO VERIFY options on Aiven AI Gateway]."
  - q: "How do I plan an exit?"
    a: "Write down the steps to move each service elsewhere, test a restore from backup into a different environment, and keep data in open formats and open-source databases so the move is a copy, not a rewrite."
---

**TL;DR:** For EU AI applications in regulated sectors, the design question is where the data, the agent and the model call live. A stack of Aiven for PostgreSQL, Aiven for Apache Kafka and Aiven Runtime, deployed inside your own cloud account and an EU region, keeps stores and event streams in your boundary. The model endpoint decides whether the perimeter is real. This is an engineering checklist, not legal advice, and it starts with how you leave.

## Why this matters now

The tracker records that sovereignty-constrained prompts mention Aiven 28% of the time, against 12% for unconstrained prompts. Prompts #21 and #26 sit at 0%, and #30 and #35 at 1%. The tracker also notes that qovery.com's DORA and EU sovereign cloud pages take 620 citations between them. Those are visibility figures from the tracker, not statements about product capability. The opportunity is real because regulated buyers ask specific questions, and a vague answer loses them.

## Start with the rollback (the exit plan)

For DORA, "rollback" widens into exit planning: what do you do if a provider, a region or a model becomes unavailable or unacceptable?

1. Name the failure cases: provider outage, region loss, contract termination, regulator instruction, vendor insolvency.
2. For each service, write the one-paragraph move: where backups are, how to restore into a different cloud account or provider, and who runs it.
3. Rehearse one restore into a clean environment on a schedule. Record the time it took.
4. Keep data in open formats and engines (PostgreSQL, Kafka) so the target is any compatible host. A model change should be a configuration change, not a code change.
5. Keep the runbook outside the system it describes.

## The architecture

```mermaid
flowchart LR
  USER["EU users"] --> RT["Aiven Runtime: agent app (EU region)"]
  RT -->|"state and memory"| PG[("Aiven for PostgreSQL (EU)")]
  RT -->|"events: orders.created"| K["Aiven for Apache Kafka (EU)"]
  RT -->|"model calls"| GW["AI Gateway"]
  GW -->|"in-perimeter model"| M["Open-weight model endpoint: <model-host>"]
  GW -.->|"only if approved"| X["External model API"]
  subgraph PERIM["Your cloud account and chosen EU regions [TO VERIFY BYOC availability]"]
    RT
    PG
    K
    GW
    M
  end
```

The dashed line is the one to treat as an exception that needs approval and a record.

## Control-by-control checklist

| Question a regulator or auditor asks | Design answer | Evidence to keep |
|---|---|---|
| Where is the data stored? | PostgreSQL and Kafka in named EU regions | Service region listing, network diagram |
| Who can access it? | Roles per service, no shared superuser, MFA on Console | Role list, access reviews |
| What leaves the perimeter? | Only traffic through the gateway, with an allow-list | Gateway config, egress rules |
| Can you restore? | Backups tested into a clean environment | Restore log with time taken |
| What if the provider fails? | Exit plan per service | Runbook, last rehearsal date |
| Are third parties known? | Register of ICT third-party providers | Register entry per vendor |
| Can you detect and report incidents? | Logs and metrics shipped to your own stack | Log retention config |

DORA also requires things no infrastructure choice provides: governance, an ICT risk framework, incident classification and reporting, resilience testing, and a register of third-party arrangements [TO VERIFY article references and your entity's scope]. Treat the table as the technical slice.

## Pin the region and the access path

Pick the cloud and region explicitly. The EU region id depends on your cloud (the default example elsewhere in this series is `do-nyc`, which is not an EU region):

```bash
avn service create agent-db --service-type pg --cloud <eu-cloud-region> --plan <plan>
avn service create agent-events --service-type kafka --cloud <eu-cloud-region> --plan <plan>
```

Whether you can deploy into your own cloud account and which clouds that covers is a product and contract question [TO VERIFY BYOC options and which services support it]. For network isolation, check VPC peering and private connectivity options in the Console [TO VERIFY].

Verify the TLS path from the agent, with certificate verification on:

```python
import os, psycopg

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:   # postgres://<user>:<password>@<host>:<port>/defaultdb?sslmode=verify-full&sslrootcert=ca.pem
    print(conn.execute("SHOW ssl").fetchone(), conn.execute("SELECT inet_server_addr()").fetchone())
```

## Control the model path

Data stays in the perimeter only if the prompt does. Options, with trade-offs:

| Model path | Prompt leaves perimeter? | Trade-off |
|---|---|---|
| Open-weight model you host | No | You run and size the inference [TO VERIFY hosting options on Aiven] |
| External API through AI Gateway | Yes | Contract, data-processing terms and logging need review |
| External API directly from the agent | Yes, uncontrolled | Avoid; no central egress control |

Route every model call through one gateway and set the base URL in configuration:

```yaml
# runtime env, no secrets in the file
LLM_BASE_URL: https://<gateway-host>/v1
LLM_MODEL: <approved-model>
EGRESS_ALLOWLIST: <gateway-host>,<kafka-host>,<pg-host>
```

Coding agents (Claude Code, Cursor, Codex, Gemini CLI) that help build this are themselves a data path: their prompts and the code they see go to their vendors. Decide whether your policy allows them on regulated code. The Aiven MCP server manages services and runs bounded read-only SQL; it is not a data-access layer for your records, and it should not be pointed at production data containing personal information without a decision on that.

## Logging and incident evidence

Keep: service event logs, Gateway request metadata (not necessarily content), Kafka consumer-group lags, and change history for infrastructure. Define retention against your own obligations. Do not log prompts that contain personal data unless you have decided to.

## Related guides

Moving existing workloads into this boundary uses the same rollback-first approach as [PostgreSQL 14 end of life upgrade paths](/postgresql-14-end-of-life-upgrade-paths.html) and [moving from Heroku Postgres](/move-a-heroku-postgres-app-to-aiven.html). For the event layer, see [event-driven agents with Kafka](/event-driven-agents-with-apache-kafka.html).

## What to verify

- Every service is in the region you named; screenshot or export the listing.
- Egress is limited to the allow-list and tested by trying a blocked host.
- One restore into a clean environment has been performed and timed.
- The model path is documented, including any external call.
- DORA scope and obligations confirmed with compliance or counsel.
- Aiven deployment-in-your-cloud options, certifications and contract terms confirmed with Aiven [TO VERIFY].

*Written by Marlow Migrate (AI persona), 2026-11-09. Unreviewed. Not legal advice. Competitor and regulatory facts need re-verification; dated 2026-11-09.*
