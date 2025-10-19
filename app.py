from flask import Flask, render_template, request, jsonify
from web3 import Web3
from decimal import Decimal
import os
from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI

load_dotenv()

app = Flask(__name__)

# Web3 setup
INFURA_KEY = os.getenv("INFURA_KEY")
INFURA_URL = f"https://mainnet.infura.io/v3/{INFURA_KEY}"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# CoinGecko client
cg = CoinGeckoAPI()

# Currencies to display
FIATS = ["usd", "eur", "gbp", "inr", "jpy"]

def fetch_eth_data(wallet_address):
    data = {
        "balance": 0,
        "values": {},
        "price_trends": {},
        "error": ""
    }

    if not web3.is_address(wallet_address):
        data["error"] = "Invalid Ethereum wallet address"
        return data

    try:
        # 1️⃣ ETH balance
        balance = Decimal(web3.from_wei(web3.eth.get_balance(wallet_address), "ether"))
        data["balance"] = round(balance, 5)

        # 2️⃣ Current prices
        prices = cg.get_price(ids=["ethereum"], vs_currencies=FIATS)
        for fiat in FIATS:
            data["values"][fiat] = round(balance * Decimal(prices["ethereum"].get(fiat, 0)), 2)

        # 3️⃣ 24h USD price chart
        chart_usd = cg.get_coin_market_chart_by_id(id="ethereum", vs_currency="usd", days=1)
        hourly_usd = [p[1] for p in chart_usd.get("prices", [])]
        data["price_trends"]["usd"] = hourly_usd

        # Convert USD chart to other currencies
        for fiat in FIATS:
            if fiat == "usd":
                continue
            rate = prices["ethereum"].get(fiat, 1) / prices["ethereum"].get("usd", 1)
            data["price_trends"][fiat] = [round(p * rate, 2) for p in hourly_usd]

    except Exception as e:
        data["error"] = f"Error fetching data: {e}"

    return data

@app.route("/", methods=["GET", "POST"])
def index():
    wallet_address = ""
    eth_data = {}

    if request.method == "POST":
        wallet_address = request.form.get("wallet_address", "").strip()
        eth_data = fetch_eth_data(wallet_address)

    return render_template(
        "index.html",
        wallet_address=wallet_address,
        fiats=FIATS,
        **eth_data
    )

@app.route("/refresh/<wallet_address>")
def refresh(wallet_address):
    eth_data = fetch_eth_data(wallet_address)
    return jsonify(eth_data)

if __name__ == "__main__":
    app.run(debug=True)
