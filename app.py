from flask import Flask, request, jsonify
from kiteconnect import KiteConnect
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# === Zerodha credentials ===
api_key = "p723cf6z05exd4p7"
access_token = "yxY3i9SiCMmDTs3OzrMtIRbVOnoxBx5b"   # replace daily when renewed

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

@app.route("/")
def home():
    return "🚀 Zerodha Algo Bridge Online"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        logging.info(f"Webhook received: {data}")

        symbol = data.get("symbol")
        side = data.get("side", "").upper()
        qty = int(data.get("qty", 75))

        if side == "BUY":
            order_id = kite.place_order(
                variety="regular",
                tradingsymbol=symbol,
                exchange="NFO",
                transaction_type="BUY",
                quantity=qty,
                product="NRML",
                order_type="MARKET"
            )
        elif side == "SELL":
            order_id = kite.place_order(
                variety="regular",
                tradingsymbol=symbol,
                exchange="NFO",
                transaction_type="SELL",
                quantity=qty,
                product="NRML",
                order_type="MARKET"
            )
        else:
            return jsonify({"status": "error", "message": "Invalid side"})

        return jsonify({"status": "success", "order_id": order_id})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
