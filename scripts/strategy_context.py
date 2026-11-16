"""Observational strategy context, frozen at forecast creation. Not model inputs.

Data contains only five-minute close and volume. True VWAP requires typical
price (high/low/close) or trade-level data and is deliberately not fabricated.
"""
import numpy as np

def snapshot(df, i):
    if i < 30:
        return {"status": "insufficient_history"}
    c = df.close.iloc[:i+1].to_numpy(dtype=float)
    v = df.volume.iloc[:i+1].fillna(0).to_numpy(dtype=float)
    if not np.all(np.isfinite(c)) or np.any(c <= 0):
        return {"status": "invalid_prices"}
    delta = np.diff(c[-15:])
    gains = np.maximum(delta, 0).mean()
    losses = np.maximum(-delta, 0).mean()
    rsi = 100.0 if losses == 0 and gains > 0 else 50.0 if losses == 0 else 100 - 100 / (1 + gains / losses)
    sma_10 = float(c[-10:].mean())
    sma_20 = float(c[-20:].mean())
    # Previous 20 completed bars, excluding the current bar to avoid self-comparison.
    prior = c[-21:-1]
    resistance = float(prior.max())
    support = float(prior.min())
    avg_vol = float(v[-21:-1].mean())
    relative_vol = float(v[-1] / avg_vol) if avg_vol > 0 else None
    return {
        "status": "observed_not_predictive",
        "rsi_14_close": round(float(rsi), 2),
        "sma_10_close": round(sma_10, 4),
        "sma_20_close": round(sma_20, 4),
        "short_sma_above_long": bool(sma_10 > sma_20),
        "support_20_prior_closes": round(support, 4),
        "resistance_20_prior_closes": round(resistance, 4),
        "close_breakout_above_prior_resistance": bool(c[-1] > resistance),
        "close_breakdown_below_prior_support": bool(c[-1] < support),
        "relative_volume_20": round(relative_vol, 3) if relative_vol is not None else None,
        "vwap": None,
        "vwap_note": "Unavailable: close/volume-only feed is insufficient for genuine VWAP.",
        "interpretation": "Research-only observations. These signals do not affect baseline forecasts."
    }
