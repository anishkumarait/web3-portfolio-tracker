from flask import Flask, render_template, request, jsonify
from web3 import Web3
import requests, os
from dotenv import load_dotenv
from pycoingecko import CoinGeckoAPI

load_dotenv()

app = Flask(__name__)

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
INFURA_KEY = os.getenv("INFURA_KEY")
INFURA_URL = f"https://mainnet.infura.io/v3/{INFURA_KEY}"

web3 = Web3(Web3.HTTPProvider(INFURA_URL))
cg = CoinGeckoAPI()

def fetch_wallet_data(wallet_address):
    result = {
        "tokens": [],
        "transactions": [],
        "total_usd_value": 0,
        "price_trends": {},
        "price_changes": {},
        "error": ""
    }

    if not web3.is_address(wallet_address):
        result["error"] = "Invalid Ethereum wallet address"
        return result

    try:
        prices = cg.get_price(ids=['ethereum', 'tether', 'usd-coin', 'dai'], vs_currencies='usd', include_24hr_change='true')

        eth_balance = web3.eth.get_balance(wallet_address)
        eth_balance = web3.from_wei(eth_balance, 'ether')
        eth_usd_value = round(float(eth_balance) * prices['ethereum']['usd'], 2)
        result["total_usd_value"] += eth_usd_value
        result["tokens"].append({
            "name": "ETH",
            "balance": round(eth_balance, 4),
            "usd_value": eth_usd_value,
            "change": round(prices['ethereum']['usd_24h_change'], 2)
        })

        tx_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&page=1&offset=5&sort=desc&apikey={ETHERSCAN_API_KEY}"
        tx_response = requests.get(tx_url).json()
        if tx_response.get("status") == "1":
            result["transactions"] = tx_response["result"]

        tracked_tokens = {
            "USDT": ("0xdAC17F958D2ee523a2206206994597C13D831ec7", "tether"),
            "USDC": ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "usd-coin"),
            "DAI": ("0x6B175474E89094C44Da98b954EedeAC495271d0F", "dai")
        }

        for name, (contract, coingecko_id) in tracked_tokens.items():
            token_url = f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress={contract}&address={wallet_address}&tag=latest&apikey={ETHERSCAN_API_KEY}"
            resp = requests.get(token_url).json()
            if resp.get("status") == "1":
                decimals = 6 if name in ["USDT", "USDC"] else 18
                token_balance = int(resp["result"]) / (10**decimals)
                token_usd_value = round(token_balance * prices[coingecko_id]['usd'], 2)
                result["total_usd_value"] += token_usd_value
                result["tokens"].append({
                    "name": name,
                    "balance": round(token_balance, 4),
                    "usd_value": token_usd_value,
                    "change": round(prices[coingecko_id]['usd_24h_change'], 2)
                })

        result["total_usd_value"] = round(result["total_usd_value"], 2)

        for asset_id in ['ethereum', 'tether', 'usd-coin', 'dai']:
            chart_data = cg.get_coin_market_chart_by_id(id=asset_id, vs_currency='usd', days=1)
            hourly = [p[1] for p in chart_data["prices"]]
            result["price_trends"][asset_id] = hourly

    except Exception as e:
        result["error"] = f"Error fetching data: {e}"

    return result


@app.route("/", methods=["GET", "POST"])
def index():
    wallet_address = ""
    wallet_data = {}

    if request.method == "POST":
        wallet_address = request.form.get("wallet_address")
        wallet_data = fetch_wallet_data(wallet_address)

    return render_template("index.html",
                           wallet_address=wallet_address,
                           **wallet_data)


@app.route("/refresh/<wallet_address>")
def refresh(wallet_address):
    wallet_data = fetch_wallet_data(wallet_address)
    return jsonify(wallet_data)


if __name__ == "__main__":
    app.run(debug=True)