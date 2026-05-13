from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
from datetime import datetime

app = FastAPI()

# Enable CORS for your Android app
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
        
        if not history.empty:
            current_price = history['Close'].iloc[-1]
            open_price = history['Open'].iloc[-1]
            change = current_price - open_price
            change_percent = (change / open_price) * 100
            
            return {
                "symbol": symbol.upper(),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "changePercent": round(change_percent, 2),
                "companyName": info.get('longName', symbol),
                "success": True
            }
        else:
            return {"symbol": symbol, "success": False, "error": "No data available"}
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
        
        if not history.empty:
            chart_data = []
            for date, row in history.iterrows():
                chart_data.append({
                    "timestamp": int(date.timestamp()),
                    "close": round(row['Close'], 2)
                })
            return {"symbol": symbol, "data": chart_data, "success": True}
        else:
            return {"symbol": symbol, "success": False, "error": "No data available"}
    except Exception as e:
        return {"symbol": symbol, "success": False, "error": str(e)}