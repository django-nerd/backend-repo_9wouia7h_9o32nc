import os
from typing import Optional
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CMC_API_BASE = "https://pro-api.coinmarketcap.com"
CMC_API_KEY = os.getenv("CMC_API_KEY")


def require_api_key():
    if not CMC_API_KEY:
        raise HTTPException(status_code=503, detail="CoinMarketCap API key not configured. Set CMC_API_KEY environment variable.")


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if backend is running and environment is set"""
    response = {
        "backend": "✅ Running",
        "coinmarketcap_api_key": "✅ Set" if os.getenv("CMC_API_KEY") else "❌ Not Set",
    }
    # Optional database diagnostics (kept from template)
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception:
        response["database"] = "❌ Not Available"
    return response


# -----------------------------
# CoinMarketCap proxied endpoints
# -----------------------------

@app.get("/api/cmc/global")
def cmc_global(convert: str = Query("USD", min_length=3, max_length=6)):
    require_api_key()
    url = f"{CMC_API_BASE}/v1/global-metrics/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"convert": convert}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json().get("data", {})
        return {"data": data}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/cmc/listings")
def cmc_listings(convert: str = Query("USD"), limit: int = Query(100, ge=1, le=500)):
    require_api_key()
    url = f"{CMC_API_BASE}/v1/cryptocurrency/listings/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"convert": convert, "limit": limit, "sort": "market_cap"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json().get("data", [])
        return {"data": data}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/cmc/quotes")
def cmc_quotes(symbols: str = Query(..., description="Comma separated symbols e.g. BTC,ETH"), convert: str = Query("USD")):
    require_api_key()
    url = f"{CMC_API_BASE}/v2/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
    params = {"symbol": symbols, "convert": convert}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.json().get("data", {})
        return {"data": data}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
