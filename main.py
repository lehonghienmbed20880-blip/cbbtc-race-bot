"""Patient, depth-aware BTC mean reversion; protocol handled by the vendored SDK."""
import os
import sys
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor'))
import makefun_bars as bars

EMA = 45
DIP = 130
EXIT = 0
STOP = 150
HOLD = 120
COOLDOWN = 30
TREND = 100
IMPACT = 15

class Strategy:
    def __init__(self):
        self.ema = None
        self.history = []
        self.entry = None
        self.entered = 0
        self.cool_until = 0
        self.peak = 0
        self.braked = False

    def __call__(self, state, batch):
        self.peak = max(self.peak, state.equity)
        if state.equity * 10000 < self.peak * 9500:
            self.braked = True
        if not any(b['symbol'] == 'CBBTC' for b in batch['bars']):
            return []
        p = state.close('CBBTC')
        self.ema = p if self.ema is None else (self.ema * (EMA - 1) + 2 * p) // (EMA + 1)
        self.history.append(self.ema)
        if len(self.history) > 31:
            self.history.pop(0)
        held = state.positions.get('CBBTC')
        if held and self.entry is None:
            # Position cost includes fees and gives a conservative stop reference.
            self.entry = held.cost * 10000000 // held.qty
            self.entered = state.seq
        if not held and self.entry is not None:
            self.entry = None
            self.cool_until = state.seq + COOLDOWN
        # The published race is 1,440 minutes; final orders cannot fill.
        if state.seq >= state.warmup_bars + 1439:
            return []
        if state.warming_up:
            return []
        if held:
            if (p * 10000 >= self.ema * (10000 + EXIT)
                    or p * 10000 <= self.entry * (10000 - STOP)
                    or state.seq - self.entered >= HOLD or self.braked):
                return [{'side': 'sell', 'symbol': 'CBBTC', 'qty': held.qty, 'max_slippage_bps': 150}]
        elif (not self.braked and state.seq >= max(EMA, self.cool_until)
              and self.ema * 10000 >= self.history[0] * (10000 - TREND)
              and p * 10000 <= self.ema * (10000 - DIP)):
            amount = min(state.cash, state.weight_room('CBBTC'))
            depths = state.depth_at('CBBTC')
            if not depths or any(d <= 0 for d in depths):
                return []
            # Cap a/D across every pool hop, before fees and integer rounding.
            inverse_depth = sum((Fraction(1, d) for d in depths), Fraction(0))
            impact_limit = Fraction(IMPACT, 10000) / inverse_depth
            amount = min(amount, impact_limit.numerator // impact_limit.denominator)
            if amount >= 1000000:
                return [{'side': 'buy', 'symbol': 'CBBTC', 'notional_quote_units': amount, 'max_slippage_bps': 150}]
        return []

if __name__ == '__main__':
    bars.run(Strategy())
