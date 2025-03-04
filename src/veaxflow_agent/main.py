"""VeaxFlow AI Agent: Optimizes NEAR/USDT liquidity pool for high-volume providers."""

import requests
import pandas as pd
import time
from typing import Optional, List, Dict


class LiquidityPool:
    """Represents a liquidity pool with dynamic management capabilities."""

    def __init__(self, pool_data: Dict[str, str]):
        """Initialize pool with data from Veax API."""
        self.token_a = pool_data["token_a"]
        self.token_b = pool_data["token_b"]
        self.reserve_a = int(pool_data["reserve_a"])  # yoctoNEAR (10^-24)
        self.reserve_b = int(pool_data["reserve_b"])  # USDT (10^-6)
        self.spot_price = float(pool_data["spot_price"])
        self.fee_tier = 0.3  # Default fee: 0.3%
        self.price_range = (self.spot_price * 0.95, self.spot_price * 1.05)  # ±5% range
        self.total_liquidity = sum(
            float(liq) for liq in pool_data["liquidities"] if liq != "0"
        )
        self.pair_id = f"{self.token_a}-{self.token_b}"

    def status(self) -> str:
        """Return formatted pool status."""
        return (
            f"Pool: {self.token_a}/{self.token_b}, "
            f"Reserves: {self.reserve_a / 10**24:.2f} NEAR/{self.reserve_b / 10**6:.2f} USDT, "
            f"Fee: {self.fee_tier:.2f}%, "
            f"Range: {self.price_range[0]:.4f}-{self.price_range[1]:.4f}, "
            f"Liquidity: {self.total_liquidity:,.0f}"
        )


def fetch_pool_data() -> Optional[List[Dict[str, str]]]:
    """Fetch pool data from Veax RPC endpoint."""
    url = "https://veax-liquidity-pool.veax.com/v1/rpc/#get_pools"
    payload = {
        "jsonrpc": "2.0",
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "method": "get_pools",
        "params": {},
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()["result"]["pools"]
    except requests.RequestException as e:
        print(f"Pool API Error: {e}")
        return None


def fetch_volume_data(pool: LiquidityPool, spot_price: float) -> pd.DataFrame:
    """Fetch volume data for a pool from Veax chart_volume endpoint."""
    url = "https://veax-liquidity-pool.veax.com/v1/rpc/#chart_volume"
    payload = {
        "jsonrpc": "2.0",
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "method": "chart_volume",
        "params": {"token_a": pool.token_a, "token_b": pool.token_b, "range": "DAY"},
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()["result"]["chart"]
        df = pd.DataFrame(data)
        df["volume"] = df["value"].astype(float) * spot_price  # Convert NEAR to USDT
        return df[["time_label", "volume"]]
    except requests.RequestException as e:
        print(f"Volume API Error: {e}")
        return pd.DataFrame({"volume": [5_000_000]})  # Fallback: $5M USDT


def ai_agent(
    pool: LiquidityPool, volume_data: pd.DataFrame
) -> tuple[float, tuple[float, float]]:
    """Optimize pool parameters based on trading volume."""
    avg_volume = (
        volume_data["volume"].mean()
        if not volume_data.empty and "volume" in volume_data
        else 5_000_000  # Fallback: $5M USDT
    )
    threshold = 700  # $700/hour threshold

    # Fee optimization
    if avg_volume >= threshold:
        new_fee = max(0.05, pool.fee_tier - 0.1)
        print(f"High volume ({avg_volume:,.2f} USDT): Reducing fee to {new_fee:.2f}%")
        pool.reserve_a = int(pool.reserve_a * 1.1)
        pool.reserve_b = int(pool.reserve_b * 1.1)
        print(
            f"Slippage reduction: Reserves boosted to {pool.reserve_a / 10**24:.2f} NEAR/{pool.reserve_b / 10**6:.2f} USDT"
        )
    else:
        new_fee = min(1.0, pool.fee_tier + 0.1)
        print(
            f"Low volume ({avg_volume:,.2f} USDT): Increasing fee to {new_fee:.2f}% for yield"
        )

    # Pricing model: Adjust range to reduce IL
    lower, upper = pool.price_range
    if avg_volume >= threshold:
        new_range = (lower * 0.95, upper * 1.05)
        print(f"Reducing IL: Widening range to {new_range[0]:.4f}-{new_range[1]:.4f}")
    else:
        new_range = (lower + 0.02, upper - 0.02)
        print(f"Stabilizing: Narrowing range to {new_range[0]:.4f}-{new_range[1]:.4f}")

    # Yield estimate
    yield_estimate = (new_fee / 100) * avg_volume
    print(f"Yield estimate: {yield_estimate:,.2f} USDT/hour")

    pool.fee_tier = new_fee
    pool.price_range = new_range
    return new_fee, new_range


def main():
    """Run the VeaxFlow AI Agent for NEAR/USDT pool optimization."""
    print("Starting VeaxFlow AI Agent...")
    pools = fetch_pool_data()
    if not pools:
        print("Failed to fetch pools—check endpoint or network.")
        return
    near_usdt_pool = next(
        (
            pool
            for pool in pools
            if pool["token_a"] == "wrap.near"
            and pool["token_b"] == "usdt.tether-token.near"
        ),
        None,
    )
    if not near_usdt_pool:
        print("NEAR/USDT pool not found.")
        return

    pool = LiquidityPool(near_usdt_pool)
    print("Initial:", pool.status())

    for _ in range(3):  # Simulate real-time adjustments
        volume_data = fetch_volume_data(pool, pool.spot_price)
        ai_agent(pool, volume_data)
        print("Updated:", pool.status())
        time.sleep(2)

    print("Agent execution complete.")


if __name__ == "__main__":
    main()
