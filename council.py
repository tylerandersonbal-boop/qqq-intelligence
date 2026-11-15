"""Experimental research council: deterministic, auditable, paper-only.
News votes remain neutral in historical tests because timestamped news snapshots
are unavailable. No model training, live trading, or causal claims.
"""
import math
import numpy as np
import engine

def council(df, i, horizon=3):
    original = engine.predict(df, i, horizon)
    if original is None:
        return None
    f = engine.features(df, i)
    # Analyst 1: technical momentum, deliberately conservative.
    momentum = float(f[0]) * 0.6 + float(f[1]) * 0.4
    technical = 0.5 + 0.15 * math.tanh(momentum / 0.004)
    # Analyst 2: frozen historical analog model (original).
    analog = float(original["up_probability_raw_shrunk"])
    # Analyst 3: news abstains rather than leaking future headlines.
    news = None
    # Analyst 4: independent critic checks volatility and disagreement.
    disagreement = abs(technical - analog)
    volatility = float(f[2])
    critic_flag = disagreement > 0.18 or volatility > 0.012
    # Predeclared weights, no retrospective optimization.
    combined = 0.5 * technical + 0.5 * analog
    direction = "UNCERTAIN" if critic_flag or abs(combined - 0.5) < 0.055 else ("UP" if combined > 0.5 else "DOWN")
    return {"up_probability": round(combined, 6),
            "direction": direction, "technical_vote": round(technical, 6),
            "analog_vote": analog, "news_vote": news,
            "critic_flag": critic_flag, "disagreement": round(disagreement, 6)}

def evaluate(df, start=80, horizon=3, step=None):
    """Non-overlapping origin/target pairs, strictly forward-only features."""
    step = step or horizon
    rows = []
    for i in range(max(start, 80), len(df)-horizon, step):
        baseline = engine.predict(df, i, horizon)
        candidate = council(df, i, horizon)
        if baseline is None or candidate is None:
            continue
        actual = int(float(df.close.iloc[i+horizon]) > float(df.close.iloc[i]))
        rows.append({"origin": df.ts.iloc[i].isoformat(), "actual_up": actual,
                     "original_p": float(baseline["up_probability_raw_shrunk"]),
                     "council_p": candidate["up_probability"],
                     "original_direction": baseline["direction"],
                     "council_direction": candidate["direction"]})
    return rows

def metrics(rows, name):
    if not rows:
        return {"n": 0, "coverage": None, "direction_accuracy": None, "brier": None}
    p = np.array([r[name+"_p"] for r in rows])
    y = np.array([r["actual_up"] for r in rows])
    decisions = [r[name+"_direction"] for r in rows]
    selected = np.array([d != "UNCERTAIN" for d in decisions])
    correct = np.array([(d == "UP") == bool(a) for d, a in zip(decisions, y)])
    return {"n": len(rows), "coverage": round(float(selected.mean()), 4),
            "direction_accuracy": round(float(correct[selected].mean()), 4) if selected.any() else None,
            "brier": round(float(np.mean((p-y)**2)), 6)}

def comparison(df):
    rows = evaluate(df)
    return {"original": metrics(rows, "original"), "council": metrics(rows, "council"),
            "always_up_brier": round(float(np.mean([(1-r["actual_up"])**2 for r in rows])), 6) if rows else None,
            "always_up_accuracy": round(float(np.mean([r["actual_up"] for r in rows])), 4) if rows else None,
            "observations": len(rows),
            "limitations": ["Exploratory historical walk-forward comparison, not independent live validation.",
                            "Non-overlapping forecast horizons, but training windows still overlap.",
                            "News analyst abstains without timestamped historical snapshots.",
                            "No fees/slippage or strategy returns; probability scores do not establish profitability.",
                            "Compare future frozen forecasts before deployment."]}
