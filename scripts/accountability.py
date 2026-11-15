"""Auditable paper-only scorecard for frozen QQQ forecasts.

Only forecasts recorded before their target candle are eligible. Historical
reconstructions must never be presented as forward-tested predictions.
"""
import datetime as dt
import json
from pathlib import Path

UTC = dt.timezone.utc


def timestamp(value):
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(UTC) if parsed.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def score(forecasts):
    eligible = []
    excluded = {}
    seen = set()
    for rec in forecasts:
        key = rec.get("id")
        reason = None
        if not key or key in seen:
            reason = "missing_or_duplicate_id"
        else:
            seen.add(key)
            origin = timestamp(rec.get("origin_utc"))
            recorded = timestamp(rec.get("recorded_utc"))
            target = timestamp(rec.get("target_utc"))
            outcome = rec.get("outcome") or {}
            probability = (rec.get("prediction") or {}).get("up_probability_raw_shrunk")
            direction = (rec.get("prediction") or {}).get("direction")
            if not origin or not recorded:
                reason = "no_verifiable_recording_time"
            elif not target or not outcome or "actual_return" not in outcome:
                reason = "unresolved"
            elif not (recorded <= origin + dt.timedelta(minutes=5) and recorded < target and origin < target):
                reason = "not_proven_forward"
            elif direction not in ("UP", "DOWN", "UNCERTAIN"):
                reason = "invalid_direction"
            elif isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
                reason = "invalid_probability"
            elif not isinstance(outcome["actual_return"], (int, float)) or isinstance(outcome["actual_return"], bool):
                reason = "invalid_return"
            else:
                eligible.append((rec, float(probability), float(outcome["actual_return"])))
        if reason:
            excluded[reason] = excluded.get(reason, 0) + 1
    decisive = [(r, p, ret) for r, p, ret in eligible if r["prediction"]["direction"] != "UNCERTAIN" and ret != 0]
    correct = sum((ret > 0) == (r["prediction"]["direction"] == "UP") for r, _, ret in decisive)
    brier = sum((p - float(ret > 0)) ** 2 for _, p, ret in eligible) / len(eligible) if eligible else None
    always_up = sum(ret > 0 for _, _, ret in decisive) / len(decisive) if decisive else None
    return {
        "status": "forward_observations_only" if eligible else "insufficient_verified_forward_data",
        "eligible_forecasts": len(eligible),
        "excluded": excluded,
        "directional_predictions": len(decisive),
        "directional_accuracy": round(correct / len(decisive), 4) if decisive else None,
        "always_up_accuracy_same_subset": round(always_up, 4) if decisive else None,
        "brier_score": round(brier, 4) if brier is not None else None,
        "coverage": round(len(decisive) / len(eligible), 4) if eligible else None,
        "warning": "Overlapping horizons are correlated. This is descriptive paper research, not an independent backtest or evidence of trading profitability.",
    }


def main():
    root = Path(__file__).resolve().parents[1]
    state = json.loads((root / "data/state.json").read_text())
    report = score(state.get("forecasts", []))
    destination = root / "docs/accountability.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
