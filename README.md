# Paper Trading Lab

> **Note:** This is a public copy of a private repository, which I still run day to day on a schedule. The commit history is preserved. Pull request history and credentials have been removed.

This is a small project I wrote as a learning exercise. It paper-trades automatically on a schedule using GitHub Actions and the Alpaca and Gemini sandbox APIs. It has never been used with a live account.

## What it does

- **Stock bot** (`AgressiveStockStrat/`): every weekday it pulls public US Senate stock-trade disclosures, picks the stocks senators are net buying, and rebalances an Alpaca paper portfolio while holding back a cash reserve.
- **P&L reporting** (`calculate_pnl.py`): a matrix workflow that reports positions and profit/loss for each portfolio configuration.
- **Crypto bots** (`BTCParty/`): experiments against the Alpaca crypto and Gemini sandbox APIs.
- **Workflows** (`.github/workflows/`): scheduled and manually triggered jobs. Separate portfolios run as GitHub Environments, each with its own secrets.

## A note on the strategy

The trading logic is deliberately simple, and frankly it's a guess. The point of the project is the engineering: scheduled execution, broker API integration, secrets handling, and reporting. It is not trying to find an edge.

## Running it

Credentials come only from environment variables, which in this setup are GitHub Actions secrets:

```
ALPACA_API_KEY
ALPACA_API_SECRET
ALPACA_API_URL      # defaults to https://paper-api.alpaca.markets
GEMINI_API_KEY      # sandbox
GEMINI_API_SECRET   # sandbox
```

```bash
pip install -r AgressiveStockStrat/requirements.txt
python AgressiveStockStrat/alpaca_trade.py
```

Actions are disabled on this copy, so the scheduled workflows don't run here.

## License

MIT, but seriously, don't use this with real money.
