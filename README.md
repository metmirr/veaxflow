# VeaxFlow AI Agent

Optimizes the NEAR/USDT pool using live data from `/rpc/#get_pools` and `/rpc/#chart_volume`. Reduces fees and slippage, widens ranges to mitigate IL, and maximizes yield for high-volume providers.

## Setup

```bash
# Make sure you have uv installed
uv sync # install dependencies
```

## Usage

```bash
python src/veaxflow_agent/main.py
```
