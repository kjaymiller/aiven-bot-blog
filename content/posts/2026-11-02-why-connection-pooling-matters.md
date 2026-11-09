---
title: Why Connection Pooling Matters for PostgreSQL
date: 2026-11-02
model: Sample content
summary: Placeholder post showing the archive layout. Replace with real AI-generated content.
tags:
  - postgresql
  - performance
---

This is a **sample post** that exists so the archive has something to show. Delete it once real posts are in place.

PostgreSQL starts one backend process per client connection, so hundreds of short-lived connections get expensive. A pooler sits between your app and the database and reuses a small set of server connections.

```sql
SHOW max_connections;
```

| Mode        | Connection is returned to the pool... |
|-------------|----------------------------------------|
| session     | when the client disconnects            |
| transaction | at the end of each transaction         |
