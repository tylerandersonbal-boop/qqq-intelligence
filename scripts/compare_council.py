"""Run historical council-vs-original benchmark on stored candles."""
import json
from pathlib import Path
import pandas as pd
from council import comparison
root=Path(__file__).resolve().parents[1]
state=json.loads((root/"data/state.json").read_text())
df=pd.DataFrame(state.get("candles",[])).rename(columns={"time":"ts"})
if len(df):
    df["ts"]=pd.to_datetime(df["ts"],utc=True)
    df["close"]=pd.to_numeric(df["close"])
    df["volume"]=pd.to_numeric(df["volume"])
result=comparison(df)
print(json.dumps(result,indent=2))
(root/"council-comparison.json").write_text(json.dumps(result,indent=2))
