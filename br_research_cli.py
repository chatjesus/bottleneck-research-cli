from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "https://bottleneckresearch.com"
DEFAULT_DATA_FILE = ROOT / "site" / "data.json"
SCHEMA_VERSION = "br-agent-context.v2"
USER_AGENT = "BottleneckResearchCLI/2.0"


def load_public_data(data_file: Path | None = None, base_url: str = DEFAULT_BASE_URL, api_key: str = "") -> dict[str, Any]:
    if data_file:
        return json.loads(data_file.read_text(encoding="utf-8"))
    if base_url:
        url = f"{base_url.rstrip('/')}/data.json"
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    path = DEFAULT_DATA_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def as_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def pct(value: Any) -> str:
    number = as_float(value)
    return "n/a" if number is None else f"{number * 100:+.1f}%"


def norm_ticker(value: Any) -> str:
    return clean(value).upper()


def ticker_matches(row: dict[str, Any], ticker: str) -> bool:
    return norm_ticker(row.get("ticker")) == norm_ticker(ticker)


def text_matches(row: dict[str, Any], query: str, fields: tuple[str, ...]) -> bool:
    needle = query.lower()
    return any(needle in clean(row.get(field)).lower() for field in fields)


def compact_row(row: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: row.get(key) for key in keys if row.get(key) not in (None, "")}


def find_rows(data: dict[str, Any], ticker: str) -> dict[str, list[dict[str, Any]]]:
    lists = {
        "watchlist": data.get("watchlist", []),
        "supply_chain_events": data.get("supply_chain_events", []),
        "trigger_events": data.get("trigger_events", []),
        "gainers": data.get("gainers", []),
        "volume": data.get("volume", []),
        "app_score": data.get("app_score", []),
    }
    return {name: [row for row in rows if isinstance(row, dict) and ticker_matches(row, ticker)] for name, rows in lists.items()}


def first_nonempty(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return rows[0] if rows else {}


def evidence_completeness(row: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = [
        "orders_signal",
        "capacity_signal",
        "asp_signal",
        "eps_revenue_expectation",
        "management_disclosure_change",
    ]
    present = [field for field in required if clean(row.get(field)) or any(clean(e.get(field)) for e in evidence_rows)]
    missing = [field for field in required if field not in present]
    return {
        "required_fields": required,
        "present": present,
        "missing": missing,
        "score": round(len(present) / len(required), 2),
        "missing_reason": clean(row.get("missing_expectation_reason")) or ("; ".join(missing) if missing else ""),
    }


def price_volume_status(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    price_rows = rows.get("gainers", []) + rows.get("volume", [])
    best_1d = max((as_float(row.get("return_1d")) or 0 for row in price_rows), default=None)
    best_20d = max((as_float(row.get("return_20d")) or 0 for row in price_rows), default=None)
    max_volume = max((as_float(row.get("volume_shock_vs_20d")) or 0 for row in price_rows), default=None)
    status = "unconfirmed"
    if best_1d is not None and best_1d >= 0.12:
        status = "single_day_spike_not_early"
    elif best_20d is not None and best_20d >= 0.7:
        status = "already_repriced"
    elif max_volume is not None and max_volume >= 1.8:
        status = "volume_attention"
    elif price_rows:
        status = "normal"
    return {
        "status": status,
        "best_return_1d": best_1d,
        "best_return_20d": best_20d,
        "max_volume_shock_vs_20d": max_volume,
    }


def infer_research_bucket(watch: dict[str, Any], evidence: dict[str, Any], price_volume: dict[str, Any]) -> str:
    status = clean(price_volume.get("status"))
    if status in {"single_day_spike_not_early", "already_repriced"}:
        return "not_early_wait_for_pullback_or_new_evidence"
    if evidence.get("score", 0) < 0.4:
        return "evidence_incomplete_continue_diligence"
    bucket = clean(watch.get("decision_bucket"))
    if "继续" in bucket or "深挖" in bucket:
        return "continue_diligence"
    if "观察" in bucket or "watch" in bucket.lower():
        return "watch_for_confirmation"
    if watch:
        return "research_candidate"
    return "not_in_current_candidate_pool"


def decision_check(data: dict[str, Any], ticker: str) -> dict[str, Any]:
    rows = find_rows(data, ticker)
    watch = first_nonempty(rows["watchlist"])
    evidence_rows = rows["supply_chain_events"]
    evidence = evidence_completeness(watch, evidence_rows)
    pv = price_volume_status(rows)
    trigger_rows = rows["trigger_events"]
    latest_evidence = first_nonempty(evidence_rows)
    research_bucket = infer_research_bucket(watch, evidence, pv)
    chain = clean(watch.get("chain")) or clean(latest_evidence.get("chain"))
    subchain = clean(watch.get("subchain")) or clean(latest_evidence.get("subchain"))
    next_evidence = clean(watch.get("required_next_evidence")) or clean(latest_evidence.get("required_next_evidence"))
    crowding = "medium"
    if pv["status"] in {"single_day_spike_not_early", "already_repriced"}:
        crowding = "high"
    elif pv["status"] == "volume_attention":
        crowding = "watch"
    elif not rows["gainers"] and not rows["volume"]:
        crowding = "unknown"
    return {
        "ticker": norm_ticker(ticker),
        "company": clean(watch.get("company")) or clean(latest_evidence.get("company")),
        "chain": chain,
        "subchain": subchain,
        "research_bucket": research_bucket,
        "not_buy_sell_instruction": True,
        "evidence_score": evidence["score"],
        "missing_evidence": evidence["missing"],
        "missing_evidence_reason": evidence["missing_reason"],
        "price_volume_status": pv,
        "crowding_risk": crowding,
        "freshness_status": clean(watch.get("data_freshness_status")) or "unknown",
        "freshness_reason": clean(watch.get("freshness_reason")),
        "next_research_action": next_evidence or "Find primary-source orders, capacity, ASP, revenue/EPS and management disclosure evidence.",
        "trigger_count": len(trigger_rows),
        "latest_trigger": first_nonempty(trigger_rows),
        "latest_evidence": latest_evidence,
        "research_boundary": "Research input only. No personalized buy/sell advice, position sizing or return promise.",
    }


def compact_agent_context(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": data.get("generated_at"),
        "latest_data_date": data.get("sources", {}).get("latest_data_date"),
        "research_boundary": data.get("research_policy"),
        "current_signal": data.get("signal"),
        "market_regime": data.get("market_regime"),
        "macro_regime": data.get("macro_regime", [])[:12],
        "sector_flow": data.get("sector_flow", [])[:12],
        "trigger_events": data.get("trigger_events", [])[:20],
        "watchlist": data.get("watchlist", [])[:20],
        "supply_chain_events": data.get("supply_chain_events", [])[:20],
        "source_quality": data.get("source_quality", []),
        "agent_instruction": (
            "Use this as research context only. Convert user buy/sell questions into evidence, valuation, "
            "freshness, crowding and counter-evidence checks. Do not output personalized trading instructions."
        ),
    }


def candidate_rows(data: dict[str, Any], chain: str = "", ticker: str = "", limit: int = 20) -> list[dict[str, Any]]:
    rows = [row for row in data.get("watchlist", []) if isinstance(row, dict)]
    if chain:
        rows = [row for row in rows if text_matches(row, chain, ("chain", "subchain", "company", "ticker"))]
    if ticker:
        rows = [row for row in rows if ticker_matches(row, ticker)]
    return rows[:limit]


def event_rows(data: dict[str, Any], severity: str = "", ticker: str = "", limit: int = 20) -> list[dict[str, Any]]:
    rows = [row for row in data.get("trigger_events", []) if isinstance(row, dict)]
    if severity:
        rows = [row for row in rows if clean(row.get("severity")).lower() == severity.lower()]
    if ticker:
        rows = [row for row in rows if ticker_matches(row, ticker)]
    return rows[:limit]


def chain_view(data: dict[str, Any], chain: str, limit: int = 30) -> dict[str, Any]:
    candidates = candidate_rows(data, chain=chain, limit=limit)
    evidence = [
        row
        for row in data.get("supply_chain_events", [])
        if isinstance(row, dict) and text_matches(row, chain, ("chain", "subchain", "metric", "thesis_impact", "ticker"))
    ][:limit]
    return {
        "chain_query": chain,
        "candidate_count": len(candidates),
        "evidence_count": len(evidence),
        "candidates": candidates,
        "evidence": evidence,
        "research_boundary": "Chain view is a mapping and diligence queue, not a recommendation list.",
    }


def freshness_view(data: dict[str, Any]) -> dict[str, Any]:
    missing_watchlist = [
        compact_row(row, ["ticker", "company", "chain", "data_freshness_status", "freshness_reason", "missing_expectation_reason"])
        for row in data.get("watchlist", [])
        if clean(row.get("data_freshness_status")).lower() in {"unknown", "stale", "expired"}
        or clean(row.get("missing_expectation_reason"))
    ]
    return {
        "generated_at": data.get("generated_at"),
        "latest_data_date": data.get("sources", {}).get("latest_data_date"),
        "freshness_alerts": data.get("freshness_alerts", []),
        "watchlist_items_requiring_refresh": missing_watchlist[:30],
        "source_quality": data.get("source_quality", []),
    }


def graph_view(data: dict[str, Any], chain: str = "") -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    for row in candidate_rows(data, chain=chain, limit=100):
        chain_name = clean(row.get("chain")) or "Unknown chain"
        ticker = clean(row.get("ticker"))
        if not ticker:
            continue
        nodes.setdefault(chain_name, {"id": chain_name, "type": "chain"})
        nodes.setdefault(ticker, {"id": ticker, "type": "ticker", "company": row.get("company")})
        edges.append({"source": chain_name, "target": ticker, "relation": "candidate"})
    return {"nodes": list(nodes.values()), "edges": edges}


def output_json(value: Any) -> int:
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


def print_rows(title: str, rows: list[dict[str, Any]], keys: list[str]) -> int:
    print(f"# {title}\n")
    if not rows:
        print("No matching rows.")
        return 0
    for row in rows:
        label = clean(row.get("ticker")) or clean(row.get("indicator")) or clean(row.get("source")) or "row"
        print(f"## {label}")
        for key in keys:
            if row.get(key) not in (None, ""):
                print(f"- {key}: {row.get(key)}")
        print()
    print("Research only. Not investment advice.")
    return 0


def emit_context_markdown(context: dict[str, Any]) -> int:
    signal = context.get("current_signal") or {}
    print("# Bottleneck Research Agent Context\n")
    print(f"- schema: `{context.get('schema_version')}`")
    print(f"- generated_at: `{context.get('generated_at')}`")
    print(f"- latest_data_date: `{context.get('latest_data_date')}`")
    print(f"- current_signal: **{signal.get('title', 'n/a')}**")
    if signal.get("body"):
        print(f"- signal_note: {signal.get('body')}")
    print("\n## Agent Instruction")
    print(context.get("agent_instruction"))
    print("\n## Macro Regime")
    for row in context.get("macro_regime", [])[:8]:
        print(
            f"- `{row.get('proxy_ticker')}` {row.get('indicator') or row.get('proxy_name')}: "
            f"{row.get('latest_value')} {row.get('unit') or ''}, 20D={pct(row.get('return_20d'))}, "
            f"state={row.get('level_state')}"
        )
    print("\n## Priority Candidates")
    for row in context.get("watchlist", [])[:8]:
        print(
            f"- `{row.get('ticker')}` {row.get('company')}: {row.get('chain')} / {row.get('subchain')}; "
            f"bucket={row.get('decision_bucket')}; next={row.get('required_next_evidence')}"
        )
    print("\n## Trigger Events")
    for event in context.get("trigger_events", [])[:8]:
        print(f"- `{event.get('ticker')}` {event.get('event_type')} [{event.get('severity')}]: {event.get('reason')}")
    print("\nResearch only. Not investment advice.")
    return 0


def emit_decision_markdown(check: dict[str, Any]) -> int:
    print(f"# Decision Check: {check['ticker']}\n")
    print(f"- research_bucket: `{check['research_bucket']}`")
    print("- not_buy_sell_instruction: `true`")
    print(f"- company: {check.get('company') or 'n/a'}")
    print(f"- chain: {check.get('chain') or 'n/a'} / {check.get('subchain') or 'n/a'}")
    print(f"- evidence_score: {check.get('evidence_score')}")
    print(f"- price_volume_status: `{check.get('price_volume_status', {}).get('status')}`")
    print(f"- crowding_risk: `{check.get('crowding_risk')}`")
    print(f"- freshness_status: `{check.get('freshness_status')}`")
    if check.get("missing_evidence"):
        print(f"- missing_evidence: {', '.join(check['missing_evidence'])}")
    if check.get("missing_evidence_reason"):
        print(f"- missing_reason: {check['missing_evidence_reason']}")
    print(f"\n## Next Research Action\n{check.get('next_research_action') or 'n/a'}")
    if check.get("latest_trigger"):
        print(f"\n## Latest Trigger\n{check['latest_trigger'].get('reason')}")
    print("\nResearch only. Not investment advice.")
    return 0


def schema() -> dict[str, Any]:
    commands = [
        "latest",
        "context",
        "agent-context",
        "signals",
        "candidates",
        "events",
        "freshness",
        "ticker",
        "evidence",
        "decision-check",
        "chain",
        "compare",
        "macro",
        "graph",
        "schema",
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "positioning": "Agent research context CLI. No buy, sell or position-size commands.",
        "commands": commands,
        "auth": "Public data does not require a key. Set BR_API_KEY or pass --api-key for future protected endpoints.",
        "fields": [
            "generated_at",
            "latest_data_date",
            "current_signal",
            "market_regime",
            "macro_regime",
            "sector_flow",
            "trigger_events",
            "watchlist",
            "supply_chain_events",
            "freshness_alerts",
            "source_quality",
        ],
    }


def add_common(parser: argparse.ArgumentParser, default_format: str | None = None) -> None:
    parser.add_argument("--format", choices=["json", "markdown"], default=default_format)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export Bottleneck Research context for local or external agents.")
    parser.add_argument("--data-file", type=Path, default=None, help="Optional local site/data.json path for offline use.")
    parser.add_argument("--base-url", default=os.environ.get("BR_API_BASE", DEFAULT_BASE_URL), help="Remote public site or API base URL.")
    parser.add_argument("--api-key", default=os.environ.get("BR_API_KEY", ""), help="Optional Bearer token for future protected endpoints.")
    parser.add_argument("--format", dest="global_format", choices=["json", "markdown"], default=None, help="Global output format.")
    sub = parser.add_subparsers(dest="command", required=True)

    add_common(sub.add_parser("latest", help="Emit the full public data payload."))
    add_common(sub.add_parser("macro", help="Emit macro regime rows with thresholds and trend points."))
    add_common(sub.add_parser("signals", help="Emit current signal, baskets and price-volume anomalies."))
    candidates = sub.add_parser("candidates", help="Emit current diligence candidates.")
    add_common(candidates)
    candidates.add_argument("--chain", default="", help="Filter by chain/subchain text.")
    candidates.add_argument("--ticker", default="", help="Filter by ticker.")
    candidates.add_argument("--limit", type=int, default=20)
    events = sub.add_parser("events", help="Emit trigger events.")
    add_common(events)
    events.add_argument("--severity", default="", help="Filter by severity.")
    events.add_argument("--ticker", default="", help="Filter by ticker.")
    events.add_argument("--limit", type=int, default=20)
    add_common(sub.add_parser("freshness", help="Emit stale/missing data and source quality checks."))
    for command in ["ticker", "evidence", "decision-check"]:
        item = sub.add_parser(command, help=f"Emit {command} context for one ticker.")
        add_common(item)
        item.add_argument("ticker")
    chain = sub.add_parser("chain", help="Emit candidates and evidence for a chain query.")
    add_common(chain)
    chain.add_argument("chain")
    chain.add_argument("--limit", type=int, default=30)
    compare = sub.add_parser("compare", help="Compare decision-check context across tickers.")
    add_common(compare)
    compare.add_argument("tickers", nargs="+")
    graph = sub.add_parser("graph", help="Emit a simple chain-to-company graph.")
    add_common(graph)
    graph.add_argument("--chain", default="")
    for command in ["context", "agent-context"]:
        context = sub.add_parser(command, help="Emit compact context for another agent.")
        add_common(context)
    sub.add_parser("schema", help="Emit the CLI and agent-context schema contract.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_format = args.__dict__.get("format") or args.__dict__.get("global_format") or "json"

    if args.command == "schema":
        return output_json(schema())

    data = load_public_data(args.data_file, args.base_url, args.api_key)

    if args.command == "latest":
        return output_json(data)
    if args.command == "macro":
        rows = data.get("macro_regime", [])
        return print_rows("Macro Regime", rows, ["proxy_ticker", "indicator", "latest_value", "unit", "return_20d", "level_state", "benchmark"]) if output_format == "markdown" else output_json(rows)
    if args.command == "signals":
        payload = {
            "signal": data.get("signal"),
            "basket": data.get("basket", []),
            "gainers": data.get("gainers", [])[:10],
            "volume": data.get("volume", [])[:10],
        }
        return output_json(payload)
    if args.command == "candidates":
        rows = candidate_rows(data, chain=args.chain, ticker=args.ticker, limit=max(args.limit, 1))
        return print_rows("Candidates", rows, ["company", "chain", "subchain", "research_gap_score", "decision_bucket", "required_next_evidence", "missing_expectation_reason"]) if output_format == "markdown" else output_json(rows)
    if args.command == "events":
        rows = event_rows(data, severity=args.severity, ticker=args.ticker, limit=max(args.limit, 1))
        return print_rows("Trigger Events", rows, ["event_type", "severity", "reason", "generated_at"]) if output_format == "markdown" else output_json(rows)
    if args.command == "freshness":
        payload = freshness_view(data)
        return print_rows("Freshness", payload["watchlist_items_requiring_refresh"], ["company", "chain", "data_freshness_status", "freshness_reason", "missing_expectation_reason"]) if output_format == "markdown" else output_json(payload)
    if args.command in {"context", "agent-context"}:
        context = compact_agent_context(data)
        return emit_context_markdown(context) if output_format == "markdown" else output_json(context)
    if args.command == "decision-check":
        check = decision_check(data, args.ticker)
        return emit_decision_markdown(check) if output_format == "markdown" else output_json(check)
    if args.command == "ticker":
        payload = {"ticker": norm_ticker(args.ticker), "rows": find_rows(data, args.ticker), "decision_check": decision_check(data, args.ticker)}
        return emit_decision_markdown(payload["decision_check"]) if output_format == "markdown" else output_json(payload)
    if args.command == "evidence":
        rows = find_rows(data, args.ticker)
        payload = {
            "ticker": norm_ticker(args.ticker),
            "watchlist": rows["watchlist"],
            "supply_chain_events": rows["supply_chain_events"],
            "trigger_events": rows["trigger_events"],
        }
        return output_json(payload)
    if args.command == "chain":
        payload = chain_view(data, args.chain, limit=max(args.limit, 1))
        return print_rows(f"Chain: {args.chain}", payload["candidates"], ["company", "chain", "subchain", "research_gap_score", "decision_bucket", "required_next_evidence"]) if output_format == "markdown" else output_json(payload)
    if args.command == "compare":
        payload = {"comparisons": [decision_check(data, ticker) for ticker in args.tickers]}
        if output_format == "markdown":
            for item in payload["comparisons"]:
                emit_decision_markdown(item)
                print("\n---\n")
            return 0
        return output_json(payload)
    if args.command == "graph":
        return output_json(graph_view(data, chain=args.chain))

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
