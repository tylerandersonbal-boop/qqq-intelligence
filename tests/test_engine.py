"""Offline checks: no network calls or trading credentials required."""
import unittest
import numpy as np
import pandas as pd
import engine

class EngineTests(unittest.TestCase):
    def setUp(self):
        n = 150
        self.df = pd.DataFrame({
            "ts": pd.date_range("2026-01-05 14:30", periods=n, freq="5min", tz="UTC"),
            "close": 400 + np.arange(n) * .08 + np.sin(np.arange(n) / 5),
            "volume": np.full(n, 100000),
        })

    def test_insufficient_history(self):
        self.assertIsNone(engine.predict(self.df, 20))

    def test_prediction_is_bounded(self):
        p = engine.predict(self.df, 120)
        self.assertIsNotNone(p)
        self.assertGreaterEqual(p["up_probability_raw_shrunk"], 0)
        self.assertLessEqual(p["up_probability_raw_shrunk"], 1)
        self.assertIn(p["direction"], ("UP", "DOWN", "UNCERTAIN"))

    def test_future_prices_do_not_change_past_prediction(self):
        before = engine.predict(self.df, 110)
        changed = self.df.copy()
        changed.loc[111:, "close"] = 10000
        after = engine.predict(changed, 110)
        self.assertEqual(before, after)

    def test_why_does_not_claim_news_caused_move(self):
        rec = {"prediction": {"direction": "UP", "features": {}},
               "outcome": {"actual_return": .01, "direction_correct": True}}
        result = engine.investigate(rec, [{"title": "Example"}])
        self.assertTrue(any("Not causally identifiable" in x["answer"] for x in result))

if __name__ == "__main__":
    unittest.main()
