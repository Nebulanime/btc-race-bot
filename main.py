"""Slow-trend cbBTC bot for agent-fun/bars-replay/v1 (make.fun btc-race).

Strategy, in one paragraph: the pool is thin and a full-size round trip costs
roughly 30 bps, while one-minute noise is only ~6 bps, so this bot trades
rarely and only with the slow trend. It watches the close against its 360-bar
(6-hour) simple moving average and buys full size when the close crosses above
that average while the 60-bar return is positive and the average itself has
been rising over the last 60 bars (so a cross off a still-falling average,
a dead-cat bounce, does not trigger a buy). It exits on either a
take-profit of +1.2% over its entry fill or a trailing stop 1.0% below the
highest close seen since entry. Long only, at most one open position, at most
one order per batch.

Deterministic: no randomness, no wall clock, no environment, no files. Every
decision is a pure function of the closes the harness has sent.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
# Slow-trend window: 360 one-minute bars (6 hours).
SMA_BARS = 360
# Entry needs the trend to be moving up over the last hour as well.
MOM_BARS = 60
# Exits, as fractions of price.
TAKE_PROFIT = 0.012
TRAIL = 0.010
# Cap the move from the latest close a fill may cost us (modelled slippage
# plus impact): 150 bps covers the usual open-vs-close gap with room.
MAX_SLIPPAGE_BPS = 150


class TrendBot:
    """Keeps the close history and the open trade's state."""

    def __init__(self):
        self.closes = []          # closes in bar order (price-scale ints)
        self.smas = []            # SMA(360) value after each bar
        self.prev_above = None    # close above SMA(360) on the previous bar
        self.entry_px = None      # entry fill price (price-scale int)
        self.run_max = None       # highest close since entry

    def on_batch(self, state, batch):
        bar = state.latest.get(SYMBOL)
        if bar is None:
            return []
        close = int(bar["c"])
        self.closes.append(close)
        holding = state.positions.get(SYMBOL)
        if holding is None:
            self.entry_px = None
            self.run_max = None
        else:
            # Entry fill price from the position's cost (spend after fee):
            # value(qty, px) = qty * px * 10**quote / 10**(qty+price), so
            # px = cost * 10**(qty+price) / (qty * 10**quote).
            if self.entry_px is None:
                self.entry_px = holding.cost * 10 ** 13 // (holding.qty * 10 ** 6)
            self.run_max = close if self.run_max is None else max(self.run_max, close)

        if len(self.closes) < SMA_BARS:
            return []
        sma = sum(self.closes[-SMA_BARS:]) / SMA_BARS
        self.smas.append(sma)
        above = close > sma
        crossed_up = self.prev_above is False and above
        self.prev_above = above

        if holding is None:
            if not crossed_up:
                return []
            # 60-bar momentum must agree: no buying into a falling cross.
            if len(self.closes) > MOM_BARS and self.closes[-1] <= self.closes[-1 - MOM_BARS]:
                return []
            # The average itself must be rising: a cross off a falling
            # average is a bounce, not a trend.
            if len(self.smas) > MOM_BARS and self.smas[-1] <= self.smas[-1 - MOM_BARS]:
                return []
            if state.cash < 1_000_000:
                return []
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]

        # Holding: take profit first, then the trailing stop.
        if self.entry_px and close >= self.entry_px * (1 + TAKE_PROFIT):
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        if self.run_max and close <= self.run_max * (1 - TRAIL):
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []


BOT = TrendBot()


def on_batch(state, batch):
    return BOT.on_batch(state, batch)


makefun_bars.run(on_batch)
