from flask import Flask, request, jsonify
from kiteconnect import KiteConnect
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# === Zerodha credentials ===
api_key = "p723cf6z05exd4p7"
access_token = "S0ihEZH4XkIRjIJFhTM2pfxCqTg65F31"   # replace daily when renewed

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# === Helper functions ===
def get_next_month_future_symbol():
    """Return NIFTY next-month Futures symbol like NIFTY25NOVFUT."""
    today = datetime.now()
    next_month = today + relativedelta(months=+1)
    symbol = f"NIFTY{next_month:%y%b}FUT".upper()
    return symbol

def get_far_month_option_symbols(strike_price):
    """Return far-month CE and PE symbols (~2 months ahead)."""
    far_month = datetime.now() + relativedelta(months=+2)
    call_sym = f"NIFTY{far_month:%y%b}{strike_price}CE".upper()
    put_sym  = f"NIFTY{far_month:%y%b}{strike_price}PE".upper()
    return call_sym, put_sym

def get_atm_strike():
    """Fetch NIFTY spot price and round to nearest 50."""
    try:
        quote = kite.quote("NSE:NIFTY 50")
        spot = quote["NSE:NIFTY 50"]["last_price"]
        atm_strike = round(spot / 50) * 50
        return int(atm_strike)
    except Exception as e:
        logging.error(f"Error fetching ATM strike: {e}")
        return 25000  # fallback default

@app.route("/")
def home():
    return "🚀 Zerodha Algo Bridge Online"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        logging.info(f"Webhook received: {data}")

        side = data.get("side", "").upper()
        qty = int(float(data.get("qty", 75)))
        symbol_tv = data.get("symbol", "").upper()  # from TradingView

        # === Determine if FUTURE or OPTION strategy ===
        atm_strike = get_atm_strike()
        fut_symbol = get_next_month_future_symbol()
        call_sym, put_sym = get_far_month_option_symbols(atm_strike)

        # Logic: detect if this alert is from Futures or Options strategy
        if "FUT" in symbol_tv:
            tradingsymbol = fut_symbol
        else:
            tradingsymbol = call_sym if side == "BUY" else put_sym

        transaction_type = "BUY" if side == "BUY" else "SELL"

        # === Place order ===
        order_id = kite.place_order(
            variety="regular",
            tradingsymbol=tradingsymbol,
            exchange="NFO",
            transaction_type=transaction_type,
            quantity=qty,
            product="NRML",
            order_type="MARKET"
        )

        msg = f"✅ {transaction_type} {tradingsymbol} ({qty})"
        logging.info(msg)
        return jsonify({"status": "success", "order_id": order_id, "symbol": tradingsymbol})

    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
