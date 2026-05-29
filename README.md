# Bottleneck Research CLI

Agent research context CLI for Bottleneck Research.

This tool exports Bottleneck Research public research data into JSON or Markdown so you can use it inside Codex, Claude Code, Cursor, notebooks, shell workflows, or your own agents.

It is a research interface, not a trading terminal. It does not provide buy/sell instructions, position sizing, return promises, or personalized investment advice.

## Install

Run directly:

```bash
python br_research_cli.py context --format markdown
```

Or install locally:

```bash
pipx install .
br context --format markdown
```

The CLI reads the public feed from `https://bottleneckresearch.com/data.json` by default. For offline testing:

```bash
python br_research_cli.py --data-file tests/fixtures/sample_data.json context
```

## Common Commands

```bash
br context --format markdown
br signals
br candidates --chain optical
br chain storage --format markdown
br decision-check 06088.HK --format markdown
br compare 06088.HK 00894.HK 01888.HK --format markdown
br freshness
br macro --format markdown
br graph --chain optical
```

## Decision Checks

`decision-check` converts a buy/sell style question into a research checklist:

- research bucket
- evidence completeness
- missing orders/capacity/ASP/EPS/management disclosure evidence
- price-volume status
- crowding risk
- freshness status
- next research action

Example:

```bash
br decision-check 06088.HK --format markdown
```

Output shape:

```markdown
# Decision Check: 06088.HK

- research_bucket: `evidence_incomplete_continue_diligence`
- not_buy_sell_instruction: `true`
- evidence_score: 0.0
- price_volume_status: `unconfirmed`
- crowding_risk: `unknown`

## Next Research Action
Verify customer revenue split, orders, capacity, margin and management disclosure.
```

## Agent Usage

In Codex or another coding agent:

```bash
br context --format markdown
br decision-check 06088.HK --format markdown
br chain optical --format markdown
```

Then ask your agent:

> Based on this Bottleneck Research context, convert "can I buy 06088.HK?" into an evidence, valuation, freshness, crowding and counter-evidence review. Do not provide personalized trading advice.

## Public vs Private Data

The public CLI does not require an API key. Future private workspaces or higher-frequency endpoints may use `BR_API_KEY`, but the open-source CLI only depends on the public research feed.

## Boundary

Bottleneck Research is for public information organization, research lead generation and risk identification. It is not investment advice, a recommendation, an offer to buy/sell securities, or a substitute for independent diligence.
