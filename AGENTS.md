# QQQ Intelligence — instructions for coding agents

Goal: Improve a free-tier, paper-only QQQ market research monitor.

## Ground rules
- No live orders, brokerage credentials, secrets, paid APIs, or auto-merging.
- Keep changes on a branch and open a pull request for human review.
- Run `python -m unittest discover -s tests -v` and report results.
- Do not claim a profitable strategy without forward, out-of-sample, cost-adjusted evidence.
- Do not claim headlines prove market causality.
- Prevent look-ahead leakage: features and training examples must precede forecast origin.
- Do not silently discard failed fetches or hide stale timestamps.
- Avoid modifying historical forecast snapshots or overwriting recorded outcomes.
- Prioritize reliability, proper backtesting, benchmark comparisons, and dashboard clarity.

## Suggested workflow
1. Read README, engine.py, tests, and latest development-review artifact.
2. Select one scoped improvement from GitHub Issues.
3. Implement with tests and explain data limitations.
4. Open a pull request; do not merge or deploy autonomously.

Note: This file guides an agent when an agent is explicitly launched or assigned. It does not launch an agent by itself.
