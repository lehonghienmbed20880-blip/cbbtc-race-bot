# Patient BTC reversion

A deterministic, long-only paper trading bot for the agent-fun/bars-replay/v1 protocol. It buys meaningful dips below a slow EMA when that average is not falling too quickly, and exits on recovery, a hard stop, or a holding-time limit. Exits trigger a cooldown; a 5% account drawdown permanently stops new entries.

Position size respects available cash, position caps, and estimated pool impact. EMA and signal arithmetic use integers; impact sizing uses exact rational arithmetic. The unmodified kit SDK handles JSON lines and order validation. Run with `python3 -P -s main.py`; only the standard library is required.

The chosen settings are a 45-minute EMA, a 130 bps dip, recovery to the EMA, a 150 bps stop, a 120-minute holding limit, a 30-minute cooldown, a 100 bps maximum EMA decline over 30 observations, and a 15 bps impact cap. The slippage limit is 150 bps. Dev validation returned +7.904515 USDC after costs with 0.622215% maximum drawdown and two filled orders; both final action logs match. See [GRADES.md](GRADES.md) for every trial and neighbour check. This single-window result does not establish future performance.
