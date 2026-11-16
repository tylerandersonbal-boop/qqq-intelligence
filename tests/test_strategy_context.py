"""Strategy context must use only historical observations available at origin."""
import unittest
import numpy as np
import pandas as pd
from scripts.strategy_context import snapshot

class StrategyContextTests(unittest.TestCase):
 def test_snapshot_does_not_look_ahead(self):
  prices=np.linspace(100,120,60)
  df=pd.DataFrame({"close":prices,"volume":np.full(60,100)})
  original=snapshot(df,45)
  df.loc[46:,"close"]=999999
  self.assertEqual(original,snapshot(df,45))
 def test_insufficient_history(self):
  df=pd.DataFrame({"close":[100.0]*10,"volume":[100]*10})
  self.assertEqual(snapshot(df,9)["status"],"insufficient_history")
 def test_vwap_not_invented(self):
  df=pd.DataFrame({"close":np.linspace(100,110,50),"volume":[100]*50})
  self.assertIsNone(snapshot(df,40)["vwap"])
 def test_breakout_detected(self):
  prices=[100.0]*39+[110.0]
  df=pd.DataFrame({"close":prices,"volume":[100]*40})
  self.assertTrue(snapshot(df,39)["close_breakout_above_prior_resistance"])

if __name__=="__main__": unittest.main()
