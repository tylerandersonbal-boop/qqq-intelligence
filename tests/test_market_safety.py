"""Regression checks for candle completion and session boundaries."""
import datetime as dt
import unittest
import pandas as pd
from engine import completed_bars, same_session, predict

UTC = dt.timezone.utc

class MarketSafetyTests(unittest.TestCase):
 def test_incomplete_bar_excluded(self):
  df=pd.DataFrame({'ts':pd.to_datetime(['2026-11-16T14:30:00Z','2026-11-16T14:35:00Z']),'close':[100.,101.],'volume':[1,1]})
  at=dt.datetime(2026,11,16,14,37,tzinfo=UTC)
  result=completed_bars(df,at)
  self.assertEqual(len(result),1)
  self.assertEqual(float(result.close.iloc[0]),100.)
 def test_completed_bar_included(self):
  df=pd.DataFrame({'ts':pd.to_datetime(['2026-11-16T14:30:00Z']),'close':[100.],'volume':[1]})
  self.assertEqual(len(completed_bars(df,dt.datetime(2026,11,16,14,35,tzinfo=UTC))),1)
 def test_overnight_is_not_same_session(self):
  self.assertFalse(same_session(dt.datetime(2026,11,13,20,55,tzinfo=UTC),dt.datetime(2026,11,16,14,30,tzinfo=UTC)))
 def test_intraday_is_same_session(self):
  self.assertTrue(same_session(dt.datetime(2026,11,16,15,0,tzinfo=UTC),dt.datetime(2026,11,16,15,15,tzinfo=UTC)))

if __name__=='__main__': unittest.main()
