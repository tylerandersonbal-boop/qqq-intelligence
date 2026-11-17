"""Forward-only paper entry and evaluation. Bar timestamps denote START times."""
import datetime as dt
from zoneinfo import ZoneInfo

BAR = dt.timedelta(minutes=5)
NY = ZoneInfo("America/New_York")

def parse(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))

def session(t):
    return t.astimezone(NY).date()

def settle(rec, df, now):
    """Only use completed bars. Entry is first close observed AFTER recording.

    Target is the third subsequent completed five-minute close. No entry-price
    or outcome is known at prediction time; delayed/missing bars are unscored.
    """
    if rec.get("scoring_version") != "forward_v2" or rec.get("outcome") is not None:
        return
    recorded = parse(rec["recorded_utc"])
    origin = parse(rec["origin_utc"])
    bars = [(t.to_pydatetime(), float(c)) for t,c in zip(df.ts,df.close)]
    if not rec.get("entry_bar_utc"):
        possible = [(t,c) for t,c in bars if t >= recorded and session(t) == session(origin)]
        if possible:
            t,c = possible[0]
            # Never silently enter at a much later candle due to missing data.
            if t - recorded > BAR:
                rec["outcome"] = {"status":"unscored: missing timely entry bar", "evaluated_utc":now.isoformat()}
                return
            rec["entry_bar_utc"] = t.isoformat()
            rec["entry_price"] = c
    if not rec.get("entry_bar_utc"):
        if session(now) != session(origin) or now.astimezone(NY).time() >= dt.time(16,5):
            rec["outcome"] = {"status":"unscored: no entry bar", "evaluated_utc":now.isoformat()}
        return
    entry = parse(rec["entry_bar_utc"])
    target = entry + 3 * BAR
    if session(target) != session(entry) or target.astimezone(NY).time() >= dt.time(16,0):
        rec["outcome"] = {"status":"unscored: horizon crosses session", "evaluated_utc":now.isoformat()}
        return
    # Require all three successive bars: never bridge missing intervals.
    times = {t:c for t,c in bars}
    if all(entry + k*BAR in times for k in (1,2,3)):
        ret = times[target] / rec["entry_price"] - 1
        direction = rec["prediction"]["direction"]
        rec["target_utc"] = target.isoformat()
        rec["outcome"] = {
            "actual_return":round(ret,6),
            "direction_correct":None if direction=="UNCERTAIN" else (ret>0 if direction=="UP" else ret<0),
            "evaluated_utc":now.isoformat()
        }
    elif now >= target + BAR * 2:
        rec["outcome"] = {"status":"unscored: missing horizon bars", "evaluated_utc":now.isoformat()}
