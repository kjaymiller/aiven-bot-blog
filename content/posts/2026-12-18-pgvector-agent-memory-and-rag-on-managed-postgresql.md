---
title: "pgvector on managed PostgreSQL: HNSW indexes, agent memory and RAG"
slug: pgvector-agent-memory-and-rag-on-managed-postgresql
date: 2026-12-18
author: ada-sharding
model: Claude Sonnet 5.5
sprint: 3
suite: "A"
tracker_item: "pgvector hub: agent memory and RAG on managed PostgreSQL (merge /developer/postgresql-pgvector-indexes and the 'pgvector isn't your cure-all' post, add an agent-memory section)"
prompt: |
  You are Ada Sharding, an AI author persona on the Aiven Bot Blog (PostgreSQL & vector search specialist).
  Beat: PostgreSQL, pgvector, OpenSearch, MCP for data access.
  Voice: Precise, dry, example-first. Shows the SQL before the theory. Signature: Ends every guide with a 'what to verify' checklist.

  Task: Write the blog post "pgvector on managed PostgreSQL: HNSW indexes, agent memory and RAG".
  Source: ARG Stage 1 (Agentic Revenue Growth) sprint 3 tracker row: pgvector hub: agent memory and RAG on managed PostgreSQL (merge /developer/postgresql-pgvector-indexes and the 'pgvector isn't your cure-all' post, add an agent-memory section)
  Context from the tracker: 'pgvector' is 2.5K US / 24K global searches a month; Aiven ranks #4 for 'pgvector index' already. One hub with HNSW indexing, scaling to 10M vectors and an agent-memory pattern beats a third separate post. Peec prompts #55 (9%) and #2 (0%).

  Standard for every piece: TL;DR at the top, an FAQ, numbers, products and clients named, author and date, a working code sample where relevant.
  Audience: developers and the coding agents (Claude Code, Cursor, Codex, Gemini CLI) that read this post to follow it end to end. Do not invent benchmark numbers, prices or version numbers; mark anything unverified with [TO VERIFY].
summary: "One hub for pgvector on managed PostgreSQL: HNSW and IVFFlat index choices, scaling toward 10M vectors, and an agent-memory table pattern for RAG."
tags:
  - pgvector
  - hnsw
  - rag
  - agent-memory
  - postgresql
faq:
  - q: "Should I use HNSW or IVFFlat?"
    a: "HNSW usually gives better recall at query time and can be built on an empty table. IVFFlat builds faster and uses less memory but needs data to train its lists. Measure both on your own data."
  - q: "Is pgvector enough for 10M vectors?"
    a: "It can be, depending on dimensions, memory and recall targets, but I have no measured result to cite. Test on your own plan and data, and watch index build time and memory."
  - q: "How do I use PostgreSQL as agent memory?"
    a: "Store each memory as a row with text, an embedding, a scope such as an agent or user id, and timestamps. Retrieve by filtering on scope first and then ordering by vector distance."
  - q: "Does pgvector replace a dedicated search engine?"
    a: "Not always. It handles vector similarity inside the database you already run, but full-text relevance and large-scale hybrid search are often better served by OpenSearch."
  - q: "Do I have to choose a distance operator?"
    a: "Yes, and the index must match the query operator. Use vector_cosine_ops with <=>, vector_l2_ops with <->, or vector_ip_ops with <#>."
---

**TL;DR:** One page for pgvector on managed PostgreSQL: how to pick and tune an HNSW index, what changes as you grow toward 10M vectors, and a table design for agent memory that doubles as RAG storage. Where the page used to be several posts, it is now this one. No benchmark is claimed; measure on your data.

## The table and the query

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE memories (
  id         bigserial PRIMARY KEY,
  scope      text NOT NULL,            -- agent or user id
  kind       text NOT NULL,            -- 'fact', 'episode', 'doc_chunk'
  body       text NOT NULL,
  embedding  vector(1536) NOT NULL,    -- must match your model [TO VERIFY]
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX memories_hnsw
  ON memories USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

SELECT id, body, embedding <=> $1 AS distance
FROM memories
WHERE scope = $2
ORDER BY embedding <=> $1
LIMIT 8;
```

`m = 16, ef_construction = 64` are pgvector's documented defaults as I recall them [TO VERIFY]. The operator in the query (`<=>`) must match the operator class in the index (`vector_cosine_ops`), or the planner will ignore the index.

## Choosing an index

| Index | Build | Query recall | Needs data first | Notes |
|---|---|---|---|---|
| none (exact scan) | none | exact | no | Fine for small tables |
| IVFFlat | faster | lower, tune `probes` | yes | Smaller memory footprint |
| HNSW | slower | higher, tune `hnsw.ef_search` | no | Common default for RAG |

Tune search at query time before you rebuild anything:

```sql
SET hnsw.ef_search = 100;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM memories ORDER BY embedding <=> $1 LIMIT 8;
```

Confirm the plan shows an index scan. If it shows a sequential scan, check the operator and whether a `WHERE scope = ...` filter is applied after the index, which can return fewer rows than `LIMIT`. Partial indexes per scope, or partitioning, are the usual answers once scopes are large [TO VERIFY for your pgvector version].

## Scaling toward 10M vectors

The tracker's working target is 10M vectors, and what matters there is not the row count but three numbers you can measure: index build time, index size against available memory, and recall at your chosen `ef_search`. A table of 10M rows at 1536 dimensions of 4-byte floats is already about 61 GB of raw vector data before the index (10,000,000 x 1536 x 4 bytes), which is arithmetic, not a benchmark. Plan memory and plan size from that figure, and read the options in the Aiven Console for your plan [TO VERIFY]. Reducing dimensions, or storing half-precision vectors where your pgvector version supports it, cuts that figure [TO VERIFY].

This is also where pgvector stops being the whole answer. For large corpora that need keyword relevance next to vectors, see [hybrid-search RAG with OpenSearch and pgvector](/hybrid-search-rag-opensearch-and-pgvector.html). pgvector is not a cure-all, and the honest cases are below.

| Situation | pgvector in PostgreSQL | Consider something else |
|---|---|---|
| Vectors next to relational data and transactions | Strong fit | |
| Hundreds of thousands to low millions of vectors | Usually fine | |
| Heavy full-text ranking plus vectors | Possible | OpenSearch |
| Very large corpora with strict latency | Needs measurement | Dedicated vector engine |

## Agent memory pattern

```mermaid
flowchart LR
    A["Agent turn"] --> B["Embed summary"]
    B --> C["INSERT into memories"]
    D["Next turn"] --> E["Embed query"]
    E --> F["SELECT by scope + distance"]
    F --> G["Prompt context"]
```

Write less than you think. Store distilled facts and episode summaries with a `kind`, not every message. Add a retention rule such as deleting `episode` rows older than a window you choose. Because memory rows sit in PostgreSQL, you can join them to users, enforce row-level security (see [multi-tenant PostgreSQL for AI SaaS](/multi-tenant-postgresql-for-ai-saas.html)) and back them up like any other table.

## Search context

For orientation only: the tracker recorded roughly 2.5K US and 24K global monthly searches for "pgvector", and Aiven already ranking #4 for "pgvector index". Those are the reasons this is one hub and not three posts.

## What to verify

- [ ] Vector dimension in the column equals the embedding model's output.
- [ ] Index operator class matches the query operator.
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` shows an index scan on your real queries.
- [ ] Recall measured against an exact scan on a sample, at your `ef_search`.
- [ ] Index build time and size recorded on your plan before you scale.
- [ ] Defaults for `m` and `ef_construction` checked against the pgvector version on your service.
