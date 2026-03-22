Project Name
UniswapAutoTrader — Autonomous AI Trading Agent

Description
UniswapAutoTrader is a fully autonomous AI agent that integrates the Uniswap Trading API to fetch real-time quotes, analyze market conditions using Groq AI, and execute real on-chain token swaps using Permit2 signatures — all without human intervention.
The agent runs 24/7 on a cloud VPS, continuously monitoring the WETH/USDC pair on Ethereum Sepolia testnet. Every cycle it fetches a live quote from the Uniswap Trading API, passes the data to an LLM for analysis, and either executes a swap or skips based on price impact, slippage tolerance, and gas fees.
This demonstrates what agentic finance looks like in practice — an AI that doesn't just talk about trading, but actually trades.

Problem Statement
AI agents today lack simple, reliable infrastructure to autonomously execute on-chain trades. Most demos use mocks or simulations. UniswapAutoTrader solves this by combining the Uniswap Trading API with AI decision-making to create a real, working autonomous trading agent with verifiable on-chain transactions.

How It Works

Quote — Agent calls Uniswap Trading API to get a real WETH → USDC quote on Sepolia
Analyze — Groq LLM analyzes price impact, slippage, and gas fees
Decide — AI returns SWAP or SKIP with reasoning
Execute — Agent signs Permit2 data and submits real transaction on-chain
Loop — Repeats every 2 minutes autonomously


Tech Stack

Python + Web3.py
Uniswap Trading API (v1 quote + swap endpoints)
Permit2 signatures
Groq AI (llama-3.3-70b-versatile)
Sepolia Testnet
Ubuntu VPS on Vultr


Real Transaction Proof
TxID: d0162394e164cb857fcc696c2b1c26ffba74aaebd368d4b20641a321fc9128d6
Explorer: https://sepolia.etherscan.io/tx/d0162394e164cb857fcc696c2b1c26ffba74aaebd368d4b20641a321fc9128d6
