import unittest
import numpy as np
import pandas as pd
import council

class CouncilTests(unittest.TestCase):
    def setUp(self):
        n=180
        x=np.arange(n)
        self.df=pd.DataFrame({"ts":pd.date_range("2026-01-05 14:30",periods=n,freq="5min",tz="UTC"),
                              "close":400+x*.08+np.sin(x/5),
                              "volume":np.full(n,100000)})
    def test_comparison_counts_match(self):
        result=council.comparison(self.df)
        self.assertGreater(result["observations"],0)
        self.assertEqual(result["original"]["n"],result["council"]["n"])
    def test_probabilities_and_abstention(self):
        result=council.council(self.df,120)
        self.assertGreaterEqual(result["up_probability"],0)
        self.assertLessEqual(result["up_probability"],1)
        self.assertIsNone(result["news_vote"])
    def test_no_future_leakage(self):
        a=council.council(self.df,120)
        changed=self.df.copy()
        changed.loc[121:,"close"]=9999
        self.assertEqual(a,council.council(changed,120))
    def test_nonoverlapping_origins(self):
        rows=council.evaluate(self.df)
        times=pd.to_datetime([r["origin"] for r in rows])
        self.assertTrue(all((times[i+1]-times[i]).total_seconds()>=900 for i in range(len(times)-1)))
if __name__=="__main__":
    unittest.main()
