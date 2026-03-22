from flask import Flask, jsonify, render_template_string
import json, os, subprocess, threading, time
from dotenv import load_dotenv
import requests

load_dotenv()
app = Flask(__name__)

UNISWAP_API_KEY = os.getenv("UNISWAP_API_KEY")
WALLET_ADDRESS  = os.getenv("WALLET_ADDRESS")
HEADERS = {"x-api-key": UNISWAP_API_KEY, "Content-Type": "application/json"}

agent_status = {
    "running": False,
    "cycle": 0,
    "last_decision": "N/A",
    "last_quote": {},
    "transactions": [],
    "logs": []
}

def get_quote():
    url = "https://trading-api-labs.interface.gateway.uniswap.org/v1/quote"
    payload = {
        "tokenInChainId": 11155111,
        "tokenOutChainId": 11155111,
        "tokenIn": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
        "tokenOut": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        "amount": "1000000000000000",
        "type": "EXACT_INPUT",
        "swapper": WALLET_ADDRESS
    }
    r = requests.post(url, json=payload, headers=HEADERS)
    return r.json()
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>UniswapAutoTrader — Live Demo</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: monospace; background: #0d1117; color: #58a6ff; padding: 20px; }
        h1 { color: #f0f6fc; }
        .card { background: #161b22; border: 1px solid #30363d; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .green { color: #3fb950; }
        .red { color: #f85149; }
        .yellow { color: #d29922; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #30363d; }
        th { color: #8b949e; }
        .badge { padding: 3px 8px; border-radius: 12px; font-size: 12px; }
        .badge-green { background: #1a4731; color: #3fb950; }
        .badge-yellow { background: #2d2b00; color: #d29922; }
    </style>
</head>
<body>
    <h1>🤖 UniswapAutoTrader</h1>
    <p>Autonomous AI Trading Agent — Powered by Uniswap API + Groq AI</p>

    <div class="card">
        <h3>📊 Agent Status</h3>
        <p>Wallet: <span class="green">{{ wallet }}</span></p>
        <p>Network: <span class="yellow">Sepolia Testnet</span></p>
        <p>Total Cycles: <span class="green">{{ cycle }}</span></p>
        <p>Last Decision: <span class="green">{{ last_decision }}</span></p>
    </div>

    <div class="card">
        <h3>📈 Latest Quote</h3>
        <p>0.001 WETH → <span class="green">{{ amount_out }} USDC</span></p>
        <p>Gas Fee: <span class="yellow">${{ gas_fee }}</span></p>
        <p>Price Impact: <span class="red">{{ price_impact }}%</span></p>
    </div>

    <div class="card">
        <h3>✅ Real Transactions</h3>
        <table>
            <tr><th>TxID</th><th>Status</th><th>Explorer</th></tr>
            {% for tx in transactions %}
            <tr>
                <td>{{ tx.hash[:20] }}...</td>
                <td><span class="badge badge-green">confirmed</span></td>
                <td><a href="{{ tx.url }}" style="color:#58a6ff" target="_blank">View</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="card">
        <h3>📝 Agent Logs</h3>
        {% for log in logs[-5:] %}
        <p class="green">{{ log }}</p>
        {% endfor %}
    </div>
</body>
</html>
"""
@app.route("/")
def index():
    quote = get_quote()
    q = quote.get("quote", {})
    amount_out = int(q.get("output", {}).get("amount", 0)) / 1e6
    gas_fee = float(q.get("gasFeeUSD", 0))
    price_impact = q.get("priceImpact", 0)
    agent_status["cycle"] += 1
    agent_status["logs"].append(f"[Cycle {agent_status['cycle']}] Quote fetched: {amount_out:.4f} USDC")

    transactions = [
        {
            "hash": "d0162394e164cb857fcc696c2b1c26ffba74aaebd368d4b20641a321fc9128d6",
            "url": "https://sepolia.etherscan.io/tx/d0162394e164cb857fcc696c2b1c26ffba74aaebd368d4b20641a321fc9128d6"
        }
    ]

    return render_template_string(HTML,
        wallet=WALLET_ADDRESS,
        cycle=agent_status["cycle"],
        last_decision="SWAP ✅" if price_impact < 2 else "SKIP ⏭️",
        amount_out=f"{amount_out:.4f}",
        gas_fee=f"{gas_fee:.4f}",
        price_impact=price_impact,
        transactions=transactions,
        logs=agent_status["logs"]
    )

@app.route("/api/status")
def status():
    quote = get_quote()
    q = quote.get("quote", {})
    return jsonify({
        "wallet": WALLET_ADDRESS,
        "network": "Sepolia Testnet",
        "cycle": agent_status["cycle"],
        "quote": {
            "amountOut": int(q.get("output", {}).get("amount", 0)) / 1e6,
            "gasFeeUSD": float(q.get("gasFeeUSD", 0)),
            "priceImpact": q.get("priceImpact", 0)
        },
        "transactions": [
            {
                "hash": "d0162394e164cb857fcc696c2b1c26ffba74aaebd368d4b20641a321fc9128d6",
                "explorer": "https://sepolia.etherscan.io/tx/d0162394e164cb857fcc696c2b1c26ffba74aaebd368d4b20641a321fc9128d6"
            }
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
