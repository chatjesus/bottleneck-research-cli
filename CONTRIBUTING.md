# Contributing

Thank you for considering a contribution to Bottleneck Research CLI.

This project is intentionally small: it exposes public Bottleneck Research data
as structured research context for humans and agents. Contributions should keep
that boundary clear.

## Good Contributions

Useful pull requests typically improve one of these areas:

- clearer command output for agent workflows
- better handling of missing, stale or ambiguous data
- stronger data provenance and source metadata
- additional tests for command behavior
- documentation in English or Chinese
- compatibility with common shells, notebooks and coding agents

## Out of Scope

Please do not add:

- buy/sell recommendations
- position sizing or portfolio allocation advice
- return promises or ranking language that implies a trade instruction
- scraping of private, paywalled or permissioned data
- credentials, API keys, private endpoints or personal portfolio data

## Local Development

```bash
git clone https://github.com/chatjesus/bottleneck-research-cli.git
cd bottleneck-research-cli
python -m unittest discover -s tests
python br_research_cli.py --data-file tests/fixtures/sample_data.json schema
```

For manual command checks:

```bash
python br_research_cli.py --data-file tests/fixtures/sample_data.json decision-check 06088.HK --format markdown
python br_research_cli.py --data-file tests/fixtures/sample_data.json agent-context --format markdown
```

## Pull Request Checklist

Before opening a PR, please check:

- tests pass
- examples in the README still run
- no credentials or personal data are included
- output remains research-only and does not issue trading instructions
- English and Chinese docs stay consistent if public behavior changes

## Financial Content Boundary

All contributions must preserve the research-only boundary. The CLI can help
identify evidence gaps, freshness problems, crowding risk and next research
actions. It must not tell users what to buy, sell or size.
