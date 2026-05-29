# Bottleneck Research CLI

[![License: MIT](https://img.shields.io/badge/license-MIT-black.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Research only](https://img.shields.io/badge/boundary-research%20only-111111.svg)](#research-boundary)

**Bottleneck Research CLI** exports public Bottleneck Research data into
agent-readable JSON or Markdown. Use it inside Codex, Claude Code, Cursor,
notebooks, shell workflows, or your own research agents.

English | [中文](README.zh-CN.md)

Website: [bottleneckresearch.com](https://bottleneckresearch.com)  
Public data feed: [bottleneckresearch.com/data.json](https://bottleneckresearch.com/data.json)

## What It Does

The CLI turns AI supply-chain bottleneck research into structured context:

- current research view and market regime
- AI infrastructure and application-layer candidate pools
- chain-level views for optical, storage, power, PCB/CCL, passive components, packaging and testing
- evidence freshness, missing proof and source quality checks
- decision-check context for a single ticker
- compact context blocks for external agents

It is designed for research workflows where a user asks an agent a question such
as:

> Can I buy 06088.HK?

The CLI does **not** answer with buy/sell instructions. It converts that question
into an evidence, valuation, freshness, crowding and counter-evidence review.

## Install

Recommended:

```bash
pipx install git+https://github.com/chatjesus/bottleneck-research-cli.git
```

Alternative:

```bash
uv tool install git+https://github.com/chatjesus/bottleneck-research-cli.git
```

Or install with pip:

```bash
python -m pip install git+https://github.com/chatjesus/bottleneck-research-cli.git
```

Run from a local clone:

```bash
git clone https://github.com/chatjesus/bottleneck-research-cli.git
cd bottleneck-research-cli
python br_research_cli.py context --format markdown
```

After installation, the command is:

```bash
br
```

## Quick Start

The public feed is used by default. No API key is required.

```bash
br context --format markdown
br decision-check 06088.HK --format markdown
br candidates --chain optical --limit 10 --format markdown
br freshness --format markdown
```

If you want to specify the public endpoint explicitly:

```bash
br --base-url https://bottleneckresearch.com context --format markdown
```

For offline testing:

```bash
br --data-file tests/fixtures/sample_data.json context --format markdown
```

## Common Commands

### Agent Context

```bash
br agent-context --format markdown
```

Emits a compact research context that can be pasted into Codex, Claude Code, or
another agent.

### Decision Check

```bash
br decision-check 06088.HK --format markdown
```

Returns:

- research bucket
- evidence completeness
- missing orders, capacity, ASP, EPS/revenue expectation or management disclosure evidence
- price-volume status
- crowding risk
- freshness status
- next research action

Example output shape:

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

### Chain View

```bash
br chain storage --format markdown
br candidates --chain optical --limit 10 --format markdown
br graph --chain power --format json
```

### Freshness and Risk Checks

```bash
br freshness --format markdown
br macro --format markdown
br signals --format markdown
```

### Compare Tickers

```bash
br compare 06088.HK 00894.HK 01888.HK --format markdown
```

## Agent Usage Pattern

Run:

```bash
br decision-check 06088.HK --format markdown
```

Then ask your agent:

```text
Based on this Bottleneck Research context, convert "can I buy 06088.HK?"
into an evidence, valuation, freshness, crowding and counter-evidence review.
Do not provide personalized trading advice.
```

## Public Data and API Keys

The open-source CLI reads:

```bash
https://bottleneckresearch.com/data.json
```

No API key is required for the public endpoint.

The CLI supports `--api-key` and `BR_API_KEY` for future protected endpoints,
but they are not needed for the current public feed.

## Research Boundary

Bottleneck Research CLI is a **research context tool**. It helps organize public
market data, supply-chain evidence, candidate pools, freshness checks and risk
signals for further diligence.

It is **not**:

- investment advice
- a buy/sell recommendation engine
- a trading signal service
- a portfolio or position-sizing tool
- a substitute for independent diligence

All outputs should be reviewed against primary sources, valuation, liquidity,
risk tolerance and personal suitability.

## Development

```bash
git clone https://github.com/chatjesus/bottleneck-research-cli.git
cd bottleneck-research-cli
python -m unittest discover -s tests
python br_research_cli.py --data-file tests/fixtures/sample_data.json schema
```

## Contributing

Issues and pull requests are welcome when they improve research context quality,
data provenance, agent interoperability, documentation or test coverage. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Please do not open public issues for sensitive data exposure or security
problems. See [SECURITY.md](SECURITY.md).

## License

MIT License. See [LICENSE](LICENSE).
