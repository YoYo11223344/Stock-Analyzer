def score_adx(adx):
    if adx < 15: return -0.05
    if adx < 25: return 0.05
    if adx < 40: return 0.10
    return 0.15

def score_rsi(rsi, slope):
    if rsi > 60 and slope > 0: return 0.10
    if rsi > 50: return 0.05
    return -0.05

def score_macd(hist):
    return 0.05 if hist > 0 else -0.05

def score_valuation(pe):
    if pe is None: return 0
    if pe > 40: return -0.05
    if pe < 20: return 0.05
    return 0
