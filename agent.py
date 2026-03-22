import os, time, requests
from web3 import Web3
from dotenv import load_dotenv
from groq import Groq
from eth_account.messages import encode_typed_data

load_dotenv()
UNISWAP_API_KEY = os.getenv("UNISWAP_API_KEY")
WALLET_ADDRESS  = os.getenv("WALLET_ADDRESS")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
PRIVATE_KEY     = os.getenv("PRIVATE_KEY")
ALCHEMY_RPC_URL = os.getenv("ALCHEMY_RPC_URL")
groq_client = Groq(api_key=GROQ_API_KEY)
w3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))
HEADERS = {"x-api-key": UNISWAP_API_KEY, "Content-Type": "application/json"}
TOKEN_IN  = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"
TOKEN_OUT = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
AMOUNT    = "1000000000000000"
def get_quote():
    url = "https://trading-api-labs.interface.gateway.uniswap.org/v1/quote"
    payload = {"tokenInChainId": 11155111, "tokenOutChainId": 11155111,
                "tokenIn": TOKEN_IN, "tokenOut": TOKEN_OUT,
                "amount": AMOUNT, "type": "EXACT_INPUT", "swapper": WALLET_ADDRESS}
    return requests.post(url, json=payload, headers=HEADERS).json()

def ai_decision(quote_data):
    prompt = f"Analyze this Uniswap quote and decide: {quote_data.get('quote', {})}. Reply DECISION: SWAP or SKIP and REASON."
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return "SWAP", response.choices[0].message.content

def execute_swap(quote_data):
    try:
        permit_data = quote_data.get("permitData")
        types = permit_data["types"]
        structured_data = {
            "types": {
                "EIP712Domain": [{"name": "name", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
                "PermitSingle": types.get("PermitSingle", []),
                "PermitDetails": types.get("PermitDetails", [])
            },
            "primaryType": "PermitSingle",
            "domain": permit_data["domain"],
            "message": permit_data["values"]
        }
        encoded = encode_typed_data(full_message=structured_data)
        signed_permit = w3.eth.account.sign_message(encoded, private_key=PRIVATE_KEY)
        payload = {
            "quote": quote_data.get("quote"),
            "swapperAddress": WALLET_ADDRESS,
            "permitData": permit_data,
            "signature": "0x" + signed_permit.signature.hex()
        }
        swap_data = requests.post("https://trading-api-labs.interface.gateway.uniswap.org/v1/swap", json=payload, headers=HEADERS).json()
        if "swap" not in swap_data:
            print(f"Swap build failed: {swap_data}")
            return None
        tx = swap_data["swap"]
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        transaction = {"from": WALLET_ADDRESS, "to": tx.get("to"), "data": tx.get("data"),
                       "value": int(tx.get("value", "0"), 16), "gas": int(tx.get("gas", "200000"), 16),
                       "maxFeePerGas": int(quote_data["quote"]["maxFeePerGas"]),
                       "maxPriorityFeePerGas": int(quote_data["quote"]["maxPriorityFeePerGas"]),
                       "nonce": nonce, "chainId": 11155111, "type": 2}
        signed = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print(f"SUCCESS! TxID: {tx_hash.hex()}")
        print(f"View: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        print(f"Swap failed: {e}")
        return None
def run_agent():
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*50}")
        print(f"Cycle #{cycle} | Wallet: {WALLET_ADDRESS}")
        print(f"{'='*50}")
        balance = w3.from_wei(w3.eth.get_balance(WALLET_ADDRESS), 'ether')
        print(f"ETH Balance: {balance}")
        if balance < 0.001:
            print("Low balance! Get ETH from https://sepoliafaucet.com")
            time.sleep(60)
            continue
        quote = get_quote()
        if "errorCode" in quote:
            print(f"Quote error: {quote}")
            time.sleep(30)
            continue
        q = quote.get("quote", {})
        print(f"0.001 WETH -> {int(q.get('output',{}).get('amount',0))/1e6:.4f} USDC")
        print(f"Gas: ${float(q.get('gasFeeUSD',0)):.4f} | Impact: {q.get('priceImpact',0)}%")
        decision, reasoning = ai_decision(quote)
        print(f"Decision: {decision}")
        print(f"Reason: {reasoning}")
        if decision == "SWAP":
            print("Executing swap...")
            tx_hash = execute_swap(quote)
            if tx_hash:
                print(f"SUCCESS: {tx_hash}")
        print("Waiting 2 minutes...")
        time.sleep(120)

if __name__ == "__main__":
    run_agent()
