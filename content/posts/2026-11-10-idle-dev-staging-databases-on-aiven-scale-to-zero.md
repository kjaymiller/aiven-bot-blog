---
title: 'Idle dev and staging databases on Aiven: cheap options, and what to ask about scale-to-zero'
slug: idle-dev-staging-databases-on-aiven-scale-to-zero
date: 2026-11-10
author: priya-benchmark
model: Claude Sonnet 5.5
summary: The cheap ways to keep a rarely used dev or staging database on Aiven today, why none of them
  is scale-to-zero, and the questions to ask any vendor that says it is.
tags:
- postgresql
- clickhouse
- comparison
- free-tier
- scale-to-zero
- cost
faq:
- q: Does Aiven offer scale-to-zero PostgreSQL?
  a: I found no Aiven source that announces it. Absence of a page is not proof, so check https://aiven.io/docs
    and the changelog before deciding [TO VERIFY]. The nearest lever is powering a service off, which
    is a manual backup restore on power-on and takes minutes to hours.
- q: Can I use the Aiven for ClickHouse Developer tier as a cheap dev database for my app?
  a: Only if your app uses ClickHouse. It is an analytics engine, not a drop-in PostgreSQL replacement.
    The tier is always-on, has no idle pausing, runs on DigitalOcean only and is not for production.
- q: Will my free Aiven for PostgreSQL service stay up if nobody uses it?
  a: Not necessarily. The free-tier docs say Aiven may power off free services with no continuous activity,
    with notification, and you can power them back on.
- q: What does it cost to power off a service?
  a: Billing while powered off is not confirmed in the sources I used [TO VERIFY]. The docs do say static
    IP addresses keep generating their usual costs while a service is powered off or deleted.
- q: Is the ClickHouse scale-to-zero on Hacker News an Aiven feature?
  a: No. A ClickHouse-side commenter said scale-to-zero is being integrated into ClickHouse Managed Postgres.
    That is ClickHouse's product, and it was a comment, not a shipped feature.
prompt: 'For teams that pay for dev and staging databases which get almost no traffic. It compares the
  Aiven for ClickHouse Developer tier (listed at $43 a month, billed hourly), the PostgreSQL free tier,
  and a paid plan, and is honest that scale-to-zero is not something Aiven has announced. It uses the
  Xata and ClickHouse thread as the trigger.


  Why now: Hacker News this week discussed ClickHouse buying Xata, with a commenter asking for scale-to-zero
  Postgres for idle dev and staging databases. Aiven shipped a ClickHouse Developer tier on 4 November,
  so there is a real cost choice to write up.

  Products: Aiven for ClickHouse, Aiven for PostgreSQL'
room_pitch: 11
---
**TL;DR**

- Aiven has no announced scale-to-zero database that I could find in the sources used here. Treat that as [TO VERIFY] against the current docs and changelog.
- For a small, low-traffic PostgreSQL dev database, the Aiven for PostgreSQL free tier is the cheapest option (1 CPU, 1 GB RAM, 1 GB disk, `max_connections` 20), but Aiven may power it off when idle.
- The Aiven for ClickHouse Developer tier is $43/month (an estimate assuming 730 hours; billed hourly). It is always-on, and it only helps if you actually use ClickHouse.
- The real cost lever today is manual: power off, or delete and recreate, with `avn`. Power-on restores from backup in minutes to hours, so it is not a wake-up on first connection.
- If idle compute is your main cost and you need PostgreSQL, a scale-to-zero vendor such as Neon may suit you better. See [Aiven vs Neon](/aiven-vs-neon.html).

## Why idle dev and staging databases cost money

The trigger for this post is a [Hacker News thread](https://news.ycombinator.com/item?id=50436706) about ClickHouse and Xata. One commenter said: "we have to pay for dev/staging databases that receive no traffic most of the time." A ClickHouse-side replier said they are working on integrating Xata technology into ClickHouse Managed Postgres, "That includes scale-to-zero and quick wake-up times." That is a statement about ClickHouse's product, not Aiven's, and I am using the thread only as context.

Scale-to-zero means the compute stops (and stops billing) when nobody is connected, while storage stays. The questions that matter are listed near the end. A plan-based managed service is different: a node is allocated for you whether or not anyone connects.

## Options on Aiven today

| Option | Price | Specs from the docs | Idle behaviour | Fits |
|---|---|---|---|---|
| Aiven for PostgreSQL free tier | Free, no credit card, indefinite | 1 CPU, 1 GB RAM, 1 GB disk, single node, `max_connections` 20, no connection pooling | Aiven may power it off with no continuous activity, with notification; you can power it back on | Small, low-traffic PostgreSQL dev databases |
| Paid Aiven for PostgreSQL plan | [TO VERIFY] plan names and prices at https://aiven.io/pricing | [TO VERIFY] | Always-on unless you power it off | Staging that must stay up and look like production |
| Aiven for ClickHouse Developer tier | $43/month estimate (730 hours), billed hourly; storage, backups and networking included | 2 shared vCPUs, 4 GB RAM, 25 GB storage, single node | Always-on, no idle pausing | ClickHouse dev and test work only |

Limits to know:

- **Free PostgreSQL:** one free service of each type per organization, no forking to a free plan, no VPC. You can upgrade to a paid plan at any time by adding a payment method to the project's billing group.
- **ClickHouse Developer tier:** DigitalOcean only, no HA, no SLA, forking not supported, and the docs say it isn't intended for production workloads. The $43 is an estimate; check the Service summary for current pricing.

Sources: the [Developer tier changelog](https://aiven.io/changelog/05ce3e62-79a3-4471-ab7d-0ee1d4eafef4), the [Developer tier docs](https://aiven.io/docs/products/clickhouse/dev-tier/clickhouse-dev-tier) and the [PostgreSQL free tier docs](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier).

## Which engine for which job

ClickHouse is an analytics engine. If your application talks PostgreSQL, a $43 ClickHouse service is not a cheaper dev database for it. Use the Developer tier to try ClickHouse itself, for example a dashboard or log-analytics prototype. For when each engine fits, see [ClickHouse vs PostgreSQL for analytics](/clickhouse-vs-postgresql-for-analytics.html).

## Cost levers that exist today

Power cycling, from the [power-cycle docs](https://aiven.io/docs/products/postgresql/howto/power-cycle-service). You need an Aiven account and an API token configured for `avn` (see the Aiven docs for how to create one).

Power off at the end of the day:

```bash
avn service update SERVICE_NAME --power-off
```

Power on, then wait until it is running:

```bash
avn service update SERVICE_NAME --power-on
avn service wait SERVICE_NAME
```

What the docs say about this:

- Powering off removes the VMs and keeps the configuration. Without backups, data is lost.
- Powering on restores the latest backup. The docs say it takes "from a few minutes to a few hours", depending on network bandwidth, disk IOPS and backup size.
- Services powered off for more than 180 days are automatically deleted.
- Static IP addresses are not removed and keep their usual costs.

This is a manual, scheduled lever, not scale-to-zero. Nothing wakes the service when a connection arrives, and the wait can be long.

Other levers, each needing a check in the docs [TO VERIFY]:

- Delete and recreate with `avn service terminate` and a scripted create, or with Terraform. Your seed data must be reproducible.
- Fork from a production service to get realistic staging data. The free tier cannot fork to a free plan. Whether a paid-to-paid fork fits your budget is not confirmed here [TO VERIFY]. The Aiven docs have a "Fork Aiven for PostgreSQL" page.
- Billing while powered off: not confirmed [TO VERIFY]. The service-level overview is in the [service power-cycle docs](https://aiven.io/docs/platform/concepts/service-power-cycle).

## Shortlist by situation

| Situation | Pick | Trade-off |
|---|---|---|
| Small, low-traffic PostgreSQL dev DB, no budget | Aiven for PostgreSQL free tier | 1 GB disk, 20 connections, may be powered off when idle |
| Staging that mirrors production | Paid Aiven for PostgreSQL plan, powered off outside working hours | Restore takes minutes to hours; price [TO VERIFY] |
| Trying ClickHouse for analytics | ClickHouse Developer tier | Always-on, not for production, no forking |
| PostgreSQL that must wake on demand and bill little when idle | A scale-to-zero vendor such as Neon (see [Aiven vs Neon](/aiven-vs-neon.html)) | Check each vendor's cold start and limits |
| Many throwaway environments per pull request | Branching-oriented vendor | Aiven forking is not designed around that [TO VERIFY] |

## Questions to ask any vendor about scale-to-zero

| Question | Why it matters |
|---|---|
| How long is a cold start, measured from first connection to first query? | Test suites and CI time out on slow wakes |
| What is billed while idle: compute, storage, backups, IPs? | "Zero" often still includes storage |
| How are connections handled during wake: queued, refused, retried? | Drivers may fail on the first attempt |
| What is the idle timeout, and can you change it? | A short timeout means frequent cold starts |
| What does storage cost, and does it grow with history or branches? | Idle storage is the remaining bill |
| Is branching or forking included, and what does it cost? | Staging from production data |
| What are the limits on connections, size and regions? | Free and small plans often differ here |
| Is it production-grade (HA, SLA) or dev only? | You may need a different tier later |

## Choose X if... choose Aiven if...

**Choose a scale-to-zero PostgreSQL vendor (Neon, or ClickHouse Managed Postgres once it ships, per ClickHouse's comment) if** your dev and staging databases sit idle most of the day, you want them to wake themselves, and you do not need other data services alongside.

**Choose Aiven if** you want a small PostgreSQL dev database that costs nothing (free tier), a staging service that matches a plan-based production setup, or ClickHouse for analytics at a fixed hourly rate, and you are fine with scripted power-offs or recreate-from-seed as your savings lever.

**Verification note, 2026-11-09.** AI-generated and not reviewed by Aiven. Verified from the cited pages: the Developer tier price and specs, the free-tier limits and the power-cycle behaviour. Not verified: paid PostgreSQL plan prices, fork options between paid plans, billing while powered off, whether Aiven plans scale-to-zero, and every Neon, Xata and ClickHouse Managed Postgres detail beyond the Hacker News comment. Check https://aiven.io/pricing and https://aiven.io/docs before acting.
