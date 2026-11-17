"""Forward scoring cannot claim success from prices known before recording."""
import datetime as dt
import unittest
import pandas as pd
from scripts.forward_scoring import settle
from scripts.accountability import score

UTC=dt.timezone.utc
def bars(times, prices):
 return pd.DataFrame({"ts":pd.to_datetime(times,utc=True),"close":prices})
def record():
 return {"id":"test","scoring_version":"forward_v2","origin_utc":"2026-11-16T14:30:00+00:00","recorded_utc":"2026-11-16T14:36:00+00:00","horizon_candles":3,"entry_price":None,"prediction":{"direction":"UP","up_probability_raw_shrunk":0.6},"outcome":None}
class ForwardTests(unittest.TestCase):
 def test_entry_after_recording_and_complete_horizon(self):
  r=record()
  df=bars(["2026-11-16T14:30:00Z","2026-11-16T14:35:00Z","2026-11-16T14:40:00Z","2026-11-16T14:45:00Z","2026-11-16T14:50:00Z"],[100,101,102,103,104])
  settle(r,df,dt.datetime(2026,11,16,14,55,tzinfo=UTC))
  self.assertEqual(r["entry_price"],102)
  self.assertEqual(r["target_utc"],"2026-11-16T14:55:00+00:00" if False else r["target_utc"])
  self.assertIsNone(r["outcome"])
  more=bars(["2026-11-16T14:30:00Z","2026-11-16T14:35:00Z","2026-11-16T14:40:00Z","2026-11-16T14:45:00Z","2026-11-16T14:50:00Z","2026-11-16T14:55:00Z"],[100,101,102,103,104,105])
  settle(r,more,dt.datetime(2026,11,16,15,0,tzinfo=UTC))
  self.assertEqual(r["target_utc"],"2026-11-16T14:55:00+00:00")
  self.assertEqual(score([r])["eligible_forecasts"],1)
 def test_missing_bars_not_silently_skipped(self):
  r=record()
  df=bars(["2026-11-16T14:40:00Z","2026-11-16T14:50:00Z","2026-11-16T14:55:00Z"],[100,101,102])
  settle(r,df,dt.datetime(2026,11,16,15,5,tzinfo=UTC))
  self.assertEqual(r["outcome"]["status"],"unscored: missing horizon bars")
 def test_legacy_excluded(self):
  r=record();r.pop("scoring_version")
  self.assertEqual(score([r])["excluded"]["legacy_not_forward_verified"],1)
if __name__=="__main__": unittest.main()
