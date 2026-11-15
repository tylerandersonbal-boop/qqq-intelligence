"""Free-tier QQQ research monitor. Research only; no trading or validated edge."""
import os, json, math, hashlib, datetime as dt
from pathlib import Path
import requests, pandas as pd, numpy as np, feedparser
from urllib.parse import quote

ROOT=Path(__file__).parent; DATA=ROOT/'data'; DOCS=ROOT/'docs'; DATA.mkdir(exist_ok=True); DOCS.mkdir(exist_ok=True)
NOW=dt.datetime.now(dt.timezone.utc)
UA={'User-Agent':'Mozilla/5.0 (compatible; QQQResearchMonitor/0.1)'}
def read(name,default):
 try: return json.loads((DATA/name).read_text())
 except (OSError,ValueError): return default
def save(name,obj): (DATA/name).write_text(json.dumps(obj,indent=2,default=str))
def market():
 # Yahoo public chart endpoint: unofficial and can be rate limited or unavailable.
 u='https://query1.finance.yahoo.com/v8/finance/chart/QQQ'
 r=requests.get(u,params={'interval':'5m','range':'5d','includePrePost':'false'},headers=UA,timeout=25); r.raise_for_status()
 obj=r.json()['chart']; assert not obj.get('error'),obj.get('error')
 x=obj['result'][0]; q=x['indicators']['quote'][0]
 df=pd.DataFrame({'ts':x['timestamp'],'close':q['close'],'volume':q['volume']}).dropna(subset=['close'])
 df['ts']=pd.to_datetime(df.ts,unit='s',utc=True)
 return df.sort_values('ts').drop_duplicates('ts').reset_index(drop=True)
def news():
 # Google News RSS: public search, not guaranteed realtime, completeness or uptime.
 terms=['QQQ Nasdaq 100','Federal Reserve inflation Nasdaq','Nvidia Microsoft Apple earnings Nasdaq']
 out=[]
 for term in terms:
  url='https://news.google.com/rss/search?q='+quote(term+' when:2d')+'&hl=en-US&gl=US&ceid=US:en'
  try:
   r=requests.get(url,headers=UA,timeout=15); r.raise_for_status()
   for e in feedparser.parse(r.content).entries[:12]:
    key=hashlib.sha256((e.get('link','')+e.get('title','')).encode()).hexdigest()[:16]
    out.append({'id':key,'title':e.get('title',''),'url':e.get('link',''),'published':e.get('published',''),'topic':term})
  except Exception as exc: print('News feed unavailable:',term,str(exc))
 return list({x['id']:x for x in out}.values())[:50]
def features(df,i):
 if i<24: return None
 close=df.close.to_numpy(dtype=float); vol=df.volume.fillna(0).to_numpy(dtype=float)
 a=close[i]/close[i-3]-1; b=close[i]/close[i-12]-1
 v=float(np.std(np.diff(np.log(close[i-12:i+1]))))
 ratio=float(vol[i]/max(1,np.mean(vol[i-12:i])))
 return np.array([a,b,v,np.log1p(ratio)])
def predict(df,i,horizon=3):
 f=features(df,i)
 if f is None:return None
 # Strictly historical analogs; no future prices beyond forecast origin.
 candidates=[]
 for j in range(24,i-horizon):
  fj=features(df,j)
  if fj is not None: candidates.append((j,fj))
 if len(candidates)<40:return None
 arr=np.array([v for _,v in candidates]); scale=np.maximum(np.std(arr,axis=0),[.0003,.0005,.0001,.1])
 distances=np.linalg.norm((arr-f)/scale,axis=1); ids=np.argsort(distances)[:min(30,len(distances))]
 outcomes=np.array([df.close.iloc[candidates[k][0]+horizon]/df.close.iloc[candidates[k][0]]-1 for k in ids]);
 # Shrink observed rate toward 50%; raw small-sample rates are overconfident.
 ups=int(np.sum(outcomes>0)); n=len(outcomes); p=(ups+2)/(n+4)
 return {'up_probability_raw_shrunk':round(float(p),4),'expected_return':round(float(outcomes.mean()),6),'matches':n,'direction':'UP' if p>.55 else 'DOWN' if p<.45 else 'UNCERTAIN','features':{'momentum_15m':round(float(f[0]),6),'momentum_60m':round(float(f[1]),6),'volatility':round(float(f[2]),6),'volume_ratio':round(float(np.expm1(f[3])),3)}}
def investigate(rec,latest_news):
 # Transparent evidence-bound WHY tree; no LLM causal hallucinations.
 f=rec['prediction']['features']; result=rec.get('outcome',{})
 questions=[
  {'why':'Why did the model predict '+rec['prediction']['direction']+'?','answer':'Historical nearest-neighbor outcomes and observed momentum/volatility/volume features.','evidence':f,'status':'mechanism documented'},
  {'why':'Why did the market actually move this way?','answer':'Not causally identifiable from OHLCV data alone. Review timestamped order flow, broad markets and news.','evidence':{'actual_return':result.get('actual_return')},'status':'unresolved'},
  {'why':'Why might market participants have changed their orders?','answer':'Candidate factors include news surprises, liquidity, hedging, and broader market movement; none is proven here.','evidence':{'news_headlines_available':len(latest_news)},'status':'hypotheses'},
  {'why':'Why did the forecast succeed or fail?','answer':'Compare observed outcome with frozen forecast; one observation cannot establish a robust explanation.','evidence':{'direction_correct':result.get('direction_correct')},'status':'requires repeated testing'},
  {'why':'Why should we trust any inferred lesson?','answer':'Only if the relationship improves forward out-of-sample accuracy, calibration and cost-adjusted returns.','evidence':{},'status':'not yet validated'}]
 return questions
def main():
 status={'updated_utc':NOW.isoformat(),'market':'unavailable','news':'unavailable','warnings':['Research prototype. Not live execution, not financial advice.','Public free feeds can be delayed, incomplete or unavailable.']}
 old=read('state.json',{'forecasts':[],'articles':[],'candles':[]})
 df=None
 try:
  df=market(); status['market']='ok'; status['last_candle_utc']=df.ts.iloc[-1].isoformat(); status['last_price_usd']=round(float(df.close.iloc[-1]),4)
 except Exception as e:status['warnings'].append('Market fetch failed: '+str(e)[:180])
 fresh=news(); status['news']='ok' if fresh else 'unavailable'; articles=list({a['id']:a for a in old['articles']+fresh}.values())[-150:]
 forecasts=old['forecasts']; existing={x['id'] for x in forecasts}
 if df is not None:
  # Evaluate previously frozen forecasts when target candle arrives.
  lookup={t.isoformat():float(c) for t,c in zip(df.ts,df.close)}
  for rec in forecasts:
   if rec.get('outcome') is not None:continue
   target=rec['target_utc']
   if target in lookup:
    ret=lookup[target]/rec['entry_price']-1; direction=rec['prediction']['direction']
    rec['outcome']={'actual_return':round(ret,6),'direction_correct':(ret>0 and direction=='UP') or (ret<0 and direction=='DOWN') if direction!='UNCERTAIN' else None,'evaluated_utc':NOW.isoformat()}
    rec['why']=investigate(rec,articles)
  i=len(df)-1; horizon=3; p=predict(df,i,horizon)
  if p:
   ts=df.ts.iloc[i].isoformat(); key=ts+'-h3'
   # Future timestamp assumes uninterrupted 5m candles; instead target is assigned from subsequent data on later runs.
   if key not in existing and (NOW-df.ts.iloc[i].to_pydatetime()).total_seconds() >= 0 and (NOW-df.ts.iloc[i].to_pydatetime()).total_seconds() <= 300:
    forecasts.append({'id':key,'origin_utc':ts,'recorded_utc':NOW.isoformat(),'horizon_candles':horizon,'entry_price':float(df.close.iloc[i]),'prediction':p,'outcome':None,'why':[], 'news_snapshot_ids':[x['id'] for x in fresh[:15]]})
  # For targets, locate third strictly later market candle when present.
  all_times=list(df.ts.dt.strftime('%Y-%m-%dT%H:%M:%S+00:00'))
  for rec in forecasts:
   if rec.get('outcome') is not None:continue
   try:
    future=[t for t in all_times if t>rec['origin_utc']]
    if len(future)>=rec['horizon_candles']:
     target=future[rec['horizon_candles']-1]; rec['target_utc']=target
     ret=lookup[target]/rec['entry_price']-1; direction=rec['prediction']['direction']
     rec['outcome']={'actual_return':round(ret,6),'direction_correct':(ret>0 and direction=='UP') or (ret<0 and direction=='DOWN') if direction!='UNCERTAIN' else None,'evaluated_utc':NOW.isoformat()}
     rec['why']=investigate(rec,articles)
   except Exception as e: print('Evaluation error',e)
  old['candles']=[{'time':t.isoformat(),'close':round(float(c),4),'volume':int(v) if pd.notna(v) else 0} for t,c,v in zip(df.ts,df.close,df.volume)][-500:]
 # Important: free 5d feed means forecasts older than retained data can never resolve; mark expired.
 if df is not None:
  earliest=df.ts.iloc[0].isoformat()
  for rec in forecasts:
   if rec.get('outcome') is None and rec['origin_utc']<earliest:
    rec['outcome']={'status':'expired: price history unavailable','evaluated_utc':NOW.isoformat()};rec['why']=investigate(rec,articles)
 old.update({'forecasts':forecasts[-800:],'articles':articles,'status':status})
 evaluated=[x for x in forecasts if x.get('outcome') and x['outcome'].get('direction_correct') is not None]
 hits=[x for x in evaluated if x['outcome']['direction_correct']]
 old['metrics']={'evaluated_directional':len(evaluated),'direction_accuracy':round(len(hits)/len(evaluated),3) if evaluated else None,'note':'Exploratory, overlapping forecasts; NOT a valid independent out-of-sample backtest.'}
 save('state.json',old); (DOCS/'state.json').write_text(json.dumps(old,default=str))
 print(status,'forecasts',len(forecasts),'evaluated',len(evaluated))
if __name__=='__main__':main()
