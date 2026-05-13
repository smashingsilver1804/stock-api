from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import time
import random
from functools import wraps
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting settings
REQUESTS_PER_SECOND = 10
BATCH_SIZE = 50  # Max symbols per batch request

# Cache settings
CACHE_TTL = 30  # seconds for quotes
CHART_CACHE_TTL = 300  # seconds for charts

quote_cache = {}
chart_cache = {}

def polite_delay(base_delay=0.5, jitter=0.3):
    """Add random delay between requests"""
    time.sleep(base_delay + random.uniform(0, jitter))

def get_cached(key, cache_dict, ttl):
    if key in cache_dict:
        data, timestamp = cache_dict[key]
        if time.time() - timestamp < ttl:
            return data
    return None

def set_cached(key, data, cache_dict):
    cache_dict[key] = (data, time.time())

@app.get("/")
def root():
    return {"message": "Stock API is running", "status": "healthy"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/quote/{symbol}")
def get_quote(symbol: str):
    # Check cache first
    cache_key = f"quote_{symbol}"
    cached = get_cached(cache_key, quote_cache, CACHE_TTL)
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        history = ticker.history(period="1d")
        
        # Small delay to be polite
        polite_delay(0.2, 0.1)
        
        if len(history) > 0:
            last_row = history.iloc[-1]
            current_price = float(last_row['Close'])
            open_price = float(last_row['Open'])
            change = current_price - open_price
            change_percent = (change / open_price) * 100 if open_price > 0 else 0
            
            result = {
                "symbol": symbol.upper(),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "companyName": info.get('longName', symbol),
                "success": True
            }
            
            set_cached(cache_key, result, quote_cache)
            return result
        return {"symbol": symbol, "success": False, "error": "No data"}
    except Exception as e:
        error_msg = str(e)
        if "Rate limited" in error_msg or "Too Many Requests" in error_msg:
            return {"symbol": symbol, "success": False, "error": "Rate limited - please wait"}
        return {"symbol": symbol, "success": False, "error": error_msg}

@app.get("/bulk")
def get_bulk_quotes(symbols: str):
    """Fetch multiple quotes efficiently using batch request"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    # Use batch download for better performance
    try:
        # Batch download historical data for all symbols at once
        data = yf.download(symbol_list, period="1d", group_by='ticker', threads=True)
        
        results = []
        for symbol in symbol_list:
            try:
                if symbol in data:
                    last_row = data[symbol].iloc[-1]
                    current_price = float(last_row['Close'])
                    open_price = float(last_row['Open'])
                    change = current_price - open_price
                    change_percent = (change / open_price) * 100 if open_price > 0 else 0
                    
                    results.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_percent, 2),
                        "companyName": symbol,
                        "success": True
                    })
                else:
                    results.append({"symbol": symbol, "success": False, "error": "No data"})
            except Exception as e:
                results.append({"symbol": symbol, "success": False, "error": str(e)})
        
        return {"quotes": results}
    except Exception as e:
        # Fallback to individual requests if batch fails
        results = []
        for symbol in symbol_list:
            results.append(get_quote(symbol))
        return {"quotes": results}

@app.get("/chart/{symbol}")
def get_chart(symbol: str, period: str = "1mo"):
    cache_key = f"chart_{symbol}_{period}"
    cached = get_cached(cache_key, chart_cache, CHART_CACHE_TTL)
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        
        if period == "1d":
            history = ticker.history(period="1d", interval="5m")
        elif period == "5d":
            history = ticker.history(period="5d", interval="30m")
        else:
            history = ticker.history(period=period)
        
        polite_delay(0.2, 0.1)
        
        if not history.empty:
            chart_data = []
            for date, row in history.iterrows():
                chart_data.append({
                    "timestamp": int(date.timestamp()),
                    "close": round(float(row['Close']), 2)
                })
            
            result = {
                "symbol": symbol.upper(),
                "data": chart_data,
                "success": True,
                "count": len(chart_data)
            }
            
            set_cached(cache_key, result, chart_cache)
            return result
        
        return {"symbol": symbol, "success": False, "error": "No data"}
    except Exception as e:
        error_msg = str(e)
        if "Rate limited" in error_msg or "Too Many Requests" in error_msg:
            return {"symbol": symbol, "success": False, "error": "Rate limited - please wait"}
        return {"symbol": symbol, "success": False, "error": error_msg}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
