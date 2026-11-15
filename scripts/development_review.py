"""Daily audit: no AI API key, network, or paid service required."""
import datetime as dt
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
now = dt.datetime.now(dt.timezone.utc)
report = ["# QQQ Intelligence — daily development review", "",
          f"Generated: {now.isoformat()}", "",
          "This is an automated diagnostic, not an AI coding agent or trading advice.", ""]
try:
    state = json.loads((root / "data/state.json").read_text())
    status = state.get("status", {})
    forecasts = state.get("forecasts", [])
    metrics = state.get("metrics", {})
    stamp = status.get("updated_utc")
    age = None
    if stamp:
        age = (now - dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds() / 3600
    report += [
        "## Data freshness",
        f"- Last saved update: {stamp or 'missing'}",
        f"- Hours since update: {round(age, 1) if age is not None else 'unknown'}",
        f"- Market fetch status: {status.get('market', 'unknown')}",
        f"- News fetch status: {status.get('news', 'unknown')}",
        f"- Forecast records: {len(forecasts)}",
        f"- Scored directional forecasts: {metrics.get('evaluated_directional', 0)}",
        "",
        "## Suggested next work",
    ]
    if age is None or age > 2:
        report.append("- HIGH: Investigate stalled monitor workflow or data source.")
    if status.get("market") != "ok":
        report.append("- HIGH: Investigate QQQ data availability.")
    if status.get("news") != "ok":
        report.append("- MEDIUM: Investigate RSS source reliability.")
    if metrics.get("evaluated_directional", 0) < 100:
        report.append("- Collect more forward forecasts before interpreting accuracy.")
    report += [
        "- Add walk-forward calibration and a benchmark (always-up and random).",
        "- Track costs, slippage, drawdown and uncertainty before paper-trading strategies.",
        "- Keep AI-suggested changes in reviewed pull requests; never auto-merge.",
    ]
except Exception as exc:
    report += ["## ERROR", f"Could not read saved state: {type(exc).__name__}: {exc}"]
(root / "development-review.md").write_text("\n".join(report) + "\n")
print("\n".join(report))
