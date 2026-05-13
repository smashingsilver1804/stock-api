from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

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
        
        if len(history) > 0:
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
    """Get historical chart data with intraday support for 1d period"""
    try:
        ticker = yf.Ticker(symbol)
        
        # For 1d period, get intraday 5-minute data for detailed chart
        if period == "1d":
            history = ticker.history(period="1d", interval="5m")
        # For 5d period, get 30-minute intervals
        elif period == "5d":
            history = ticker.history(period="5d", interval="30m")
        else:
            # For longer periods, use daily data
            history = ticker.history(period=period)
        
        if not history.empty:
            chart_data = []
            for date, row in history.iterrows():
                # Convert pandas timestamp to Unix timestamp
                timestamp = int(date.timestamp())
                close_price = round(float(row['Close']), 2)
                chart_data.append({
                    "timestamp": timestamp,
                    "close": close_price
                })
            
            # Log for debugging on Render
            print(f"Chart for {symbol} ({period}): {len(chart_data)} points")
            
            return {
                "symbol": symbol.upper(),
                "data": chart_data,
                "success": True,
                "count": len(chart_data)
            }
        else:
            return {
                "symbol": symbol.upper(), 
                "success": False, 
                "error": "No data available for this period"
            }
    except Exception as e:
        print(f"Error fetching chart for {symbol}: {str(e)}")
        return {"symbol": symbol.upper(), "success": False, "error": str(e)}

@app.get("/historical/{symbol}")
def get_historical(symbol: str, start_date: str, end_date: str):
    """Get historical data for a custom date range"""
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(start=start_date, end=end_date)
        
        if not history.empty:
            chart_data = []
            for date, row in history.iterrows():
                chart_data.append({
                    "timestamp": int(date.timestamp()),
                    "open": round(float(row['Open']), 2),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "close": round(float(row['Close']), 2),
                    "volume": int(row['Volume']) if row['Volume'] else 0
                })
            return {"symbol": symbol.upper(), "data": chart_data, "success": True}
        return {"symbol": symbol.upper(), "success": False, "error": "No data"}
    except Exception as e:
        return {"symbol": symbol.upper(), "success": False, "error": str(e)}

@app.get("/info/{symbol}")
def get_stock_info(symbol: str):
    """Get detailed stock information"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return {
            "symbol": symbol.upper(),
            "companyName": info.get('longName', symbol),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "marketCap": info.get('marketCap', 0),
            "peRatio": info.get('trailingPE', 0),
            "dividendYield": info.get('dividendYield', 0),
            "fiftyTwoWeekHigh": info.get('fiftyTwoWeekHigh', 0),
            "fiftyTwoWeekLow": info.get('fiftyTwoWeekLow', 0),
            "avgVolume": info.get('averageVolume', 0),
            "success": True
        }
    except Exception as e:
        return {"symbol": symbol.upper(), "success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
