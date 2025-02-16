import logging

import aiohttp
from aiocache import cached


_logger = logging.getLogger(__name__)


@cached(ttl=120)
async def get_spr_price():
    """Fetches the current SPR price in USD."""
    market_data = await fetch_market_data()
    return market_data.get("current_price", {}).get("usd", None)


@cached(ttl=120)
async def get_spr_volume():
    """Fetches the 24h total volume in USD."""
    market_data = await fetch_market_data()
    return market_data.get("total_volume", {}).get("usd", None)


@cached(ttl=300)
async def fetch_market_data():
    url = "https://api.coingecko.com/api/v3/coins/spectre-network"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return (await resp.json()).get("market_data", {})
                elif resp.status == 429:
                    _logger.warning(
                        "Rate limit exceeded. Returning cached data if available."
                    )
                else:
                    _logger.error(
                        f"Failed to fetch market data. Status code: {resp.status}"
                    )
    except Exception as e:
        _logger.error(f"Error fetching market data: {e}")
    return {}
