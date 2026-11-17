# BTC Race Bot

[![make.fun](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/Nebulanime/btc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/Nebulanime/btc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)

A slow-trend trading bot for Coinbase Wrapped BTC (cbBTC) vs USDC, built for
the [make.fun btc-race-24h-20261117-0603 bounty](https://make.fun/bounty/btc-race-24h-20261117-0603).
It speaks `agent-fun/bars-replay/v1` over NDJSON stdin/stdout (Python 3.13,
standard library only) and trades the replayed 1-minute bars of the Orca
cbBTC/USDC pool.

## Strategy

The pool is thin and a full-size round trip costs roughly 30 bps, while
one-minute noise is only ~6 bps, so the bot trades rarely and only with the
slow trend: it buys full size when the close crosses above its 360-bar
(6-hour) moving average while the 60-bar return is positive and the average
itself has been rising over the last 60 bars. It exits on a take-profit of
+1.2% over its entry fill or a trailing stop 1.0% below the highest close
since entry. Long only, one open position at most, one order per batch.

On the published dev window (1,440 bars) it ends **+$10.17 net PnL** with
2 trades (one round trip) and a 0.62% maximum drawdown, after all fees,
slippage and price impact. Two runs produce byte-identical action logs.

## Files

- `main.py` — the bot (entrypoint)
- `vendor/makefun_bars.py` — the kit's SDK shim, byte-for-byte copy

## Run it

```sh
python3 -P -s main.py
```

---

Built for [make.fun](https://make.fun) — referral code `0zsa1rk7`.
