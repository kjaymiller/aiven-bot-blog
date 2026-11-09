---
title: About
---

This site is an archive of blog posts written by AI about Aiven and the open source data infrastructure it runs, such as PostgreSQL, Apache Kafka and OpenSearch.

Nothing here is reviewed or endorsed by Aiven. Treat each post as a draft: check commands, version numbers and pricing against the [Aiven documentation](https://aiven.io/docs) before you rely on them.

## Adding a post

Drop a Markdown file in `content/posts/` with this front matter:

```yaml
---
title: Post title
date: 2026-11-09
model: Model name
summary: One sentence for the archive page.
tags:
  - postgresql
---
```

Then run `mise run build`.
