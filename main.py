from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Stock API is running", "status": "healthy"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/quote/{symbol}")
def get_quote(symbol: str):
    """Get real-time quote for a stock"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        history = ticker.history(period="1d")
        
        if len(history) > 0:
            # Convert to list to avoid pandas issues
            last_row = history.iloc[-1]
            current_price = float(last_row['Close'])
            open_price = float(last_row['Open'])
            change = current_price - open_price
            change_percent = (change / open_price) * 100 if open_price > 0 else 0
            
            return {
                "symbol": symbol.upper(),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "companyName": info.get('longName', symbol),
                "success": True
            }
        return {"symbol": symbol, "success": False, "error": "No data"}
    except Exception as e:
        return {"symbol": symbol, "success": False, "error": str(e)}

@app.get("/bulk")
def get_bulk_quotes(symbols: str):
    """Get multiple quotes at once"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = []
    for symbol in symbol_list:
        results.append(get_quote(symbol))
    return {"quotes": results}

@app.get("/chart/{symbol}")
def get_chart(symbol: str, period: str = "1mo"):
    """Get historical chart data"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period)
        
        if len(history) > 0:
            chart_data = []
            for date, row in history.iterrows():
                chart_data.append({
                    "timestamp": int(date.timestamp()),
                    "close": round(float(row['Close']), 2)
                })
            return {"symbol": symbol, "data": chart_data, "success": True}
        return {"symbol": symbol, "success": False, "error": "No data"}
    except Exception as e:
        return {"symbol": symbol, "success": False, "error": str(e)}
