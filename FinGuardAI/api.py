import aiohttp
import statistics


COINGECKO_URL = "https://api.coingecko.com/api/v3"


COIN_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "MATIC": "matic-network",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "ATOM": "cosmos",
    "ETC": "ethereum-classic",
    "UNI": "uniswap",
    "XLM": "stellar",
    "NEAR": "near",
    "APT": "aptos",
}


async def coingecko_request(endpoint, params=None):
    url = COINGECKO_URL + endpoint

    timeout = aiohttp.ClientTimeout(total=15)

    headers = {
        "Accept": "application/json",
        "User-Agent": "FinGuardAI/1.0"
    }

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers
    ) as session:

        async with session.get(
            url,
            params=params
        ) as response:

            if response.status != 200:
                text = await response.text()

                raise Exception(
                    f"CoinGecko HTTP {response.status}: {text[:200]}"
                )

            return await response.json()


def get_coin_id(symbol):
    symbol = (
        symbol
        .upper()
        .replace("/", "")
        .replace("-", "")
    )

    if symbol.endswith("USDT"):
        symbol = symbol[:-4]

    if symbol not in COIN_IDS:
        raise Exception(
            f"Актив {symbol} пока не поддерживается"
        )

    return symbol, COIN_IDS[symbol]


async def get_24h_ticker(symbol):
    symbol, coin_id = get_coin_id(symbol)

    data = await coingecko_request(
        "/simple/price",
        {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_24hr_high": "true",
            "include_24hr_low": "true"
        }
    )

    coin = data.get(coin_id)

    if not coin:
        raise Exception(
            f"Не удалось получить данные для {symbol}"
        )

    return {
        "symbol": symbol,
        "price": float(
            coin.get("usd", 0)
        ),
        "change_24h": float(
            coin.get("usd_24h_change", 0)
        ),
        "volume": float(
            coin.get("usd_24h_vol", 0)
        ),
        "high_24h": float(
            coin.get("usd_24h_high", 0)
        ),
        "low_24h": float(
            coin.get("usd_24h_low", 0)
        )
    }


async def get_klines(
    symbol,
    interval="1h",
    limit=100
):
    symbol, coin_id = get_coin_id(symbol)

    data = await coingecko_request(
        f"/coins/{coin_id}/market_chart",
        {
            "vs_currency": "usd",
            "days": "7",
            "interval": "hourly"
        }
    )

    prices = data.get("prices", [])
    volumes = data.get("total_volumes", [])

    if not prices:
        raise Exception(
            f"Нет исторических данных для {symbol}"
        )

    prices = prices[-limit:]
    volumes = volumes[-limit:]

    candles = []

    for i, price_data in enumerate(prices):
        timestamp = price_data[0]
        close = float(price_data[1])

        if i < len(volumes):
            volume = float(volumes[i][1])
        else:
            volume = 0

        candles.append([
            timestamp,
            close,
            close,
            close,
            close,
            volume
        ])

    return candles


def sma(values, period):
    if len(values) < period:
        return None

    return sum(
        values[-period:]
    ) / period


def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(
        values[:period]
    ) / period

    for price in values[period:]:
        result = (
            price - result
        ) * multiplier + result

    return result


def calculate_rsi(
    values,
    period=14
):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = (
            values[i] - values[i - 1]
        )

        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(
                abs(change)
            )

    avg_gain = (
        sum(gains[-period:])
        / period
    )

    avg_loss = (
        sum(losses[-period:])
        / period
    )

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


def calculate_volatility(values):
    if len(values) < 2:
        return 0

    returns = []

    for i in range(1, len(values)):
        if values[i - 1] == 0:
            continue

        returns.append(
            (
                values[i]
                / values[i - 1]
                - 1
            ) * 100
        )

    if len(returns) < 2:
        return 0

    return statistics.stdev(
        returns
    )


async def get_price(symbol):
    return await get_24h_ticker(symbol)


async def get_market_analysis(symbol):
    ticker = await get_price(symbol)

    candles = await get_klines(
        symbol,
        "1h",
        100
    )

    closes = [
        float(candle[4])
        for candle in candles
    ]

    volumes = [
        float(candle[5])
        for candle in candles
    ]

    if not closes:
        raise Exception(
            "Исторические данные отсутствуют"
        )

    current_price = closes[-1]

    sma20 = sma(
        closes,
        20
    )

    sma50 = sma(
        closes,
        50
    )

    ema20 = ema(
        closes,
        20
    )

    rsi = calculate_rsi(
        closes
    )

    volatility = calculate_volatility(
        closes
    )

    volume_period = min(
        20,
        len(volumes)
    )

    avg_volume = (
        sum(
            volumes[-volume_period:]
        )
        / volume_period
    )

    volume_ratio = (
        volumes[-1] / avg_volume
        if avg_volume
        else 0
    )

    if (
        sma20 is not None
        and current_price > sma20
    ):
        trend = "Восходящий"

    elif (
        sma20 is not None
        and current_price < sma20
    ):
        trend = "Нисходящий"

    else:
        trend = "Нейтральный"

    anomaly_score = 0

    if volume_ratio > 2:
        anomaly_score += 30

    elif volume_ratio > 1.5:
        anomaly_score += 15

    change_24h = ticker["change_24h"]

    if abs(change_24h) > 10:
        anomaly_score += 30

    elif abs(change_24h) > 5:
        anomaly_score += 15

    if volatility > 5:
        anomaly_score += 20

    anomaly_score = min(
        anomaly_score,
        100
    )

    return {
        **ticker,
        "sma20": sma20,
        "sma50": sma50,
        "ema20": ema20,
        "rsi": rsi,
        "volatility": volatility,
        "volume_ratio": volume_ratio,
        "trend": trend,
        "anomaly_score": anomaly_score
    }
