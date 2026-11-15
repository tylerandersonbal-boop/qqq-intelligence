"""Regression test for missing forecast target timestamps."""
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import engine


class MissingTargetTest(unittest.TestCase):
    def test_old_forecast_without_target(self):
        times = pd.date_range("2026-11-13 14:30", periods=150, freq="5min", tz="UTC")
        df = pd.DataFrame({"ts": times, "close": 400 + np.arange(150) * .1, "volume": np.full(150, 1000)})
        old = {"id": "old-h3", "origin_utc": times[100].isoformat(),
               "horizon_candles": 3, "entry_price": float(df.close.iloc[100]),
               "prediction": {"direction": "UP", "features": {}},
               "outcome": None, "why": []}
        state = {"forecasts": [old], "articles": [], "candles": []}
        with patch.object(engine, "market", return_value=df), patch.object(engine, "news", return_value=[]), patch.object(engine, "read", return_value=state), patch.object(engine, "save"), patch.object(engine.Path, "write_text"):
            engine.main()
        self.assertIsNotNone(old["outcome"])
        self.assertIn("target_utc", old)


if __name__ == "__main__":
    unittest.main()
