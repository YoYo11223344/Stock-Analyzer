from engine.data import fetch_data
from engine.indicators import compute_features

stock, _ = fetch_data("TCS")
feat = compute_features(stock)
print(type(stock.columns))
print(stock.columns)
