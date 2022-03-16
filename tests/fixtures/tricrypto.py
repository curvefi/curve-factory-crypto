import pytest

INITIAL_PRICES_BASE = [
    100_000 * 10 ** 18,
    10_000 * 10 ** 18,
]  # prices chosen, so qubic root is integer
LP_PRICE_USD = 3 * 1000 * 10 ** 18  # 3 * (p1 * p2) ^ 1/3


@pytest.fixture(scope="module")
def initial_prices_base(Tricrypto, is_forked, base_coins, base_swap):
    if not is_forked:
        return [10 ** 18] + INITIAL_PRICES_BASE
    prices = [10 ** 18] * (len(base_coins) - 2)  # underlying usd coins
    if hasattr(base_swap, "pool"):  # Zap
        base_swap = Tricrypto.at(base_swap.pool())
    for i in range(2):
        prices.append(base_swap.price_oracle(i))
    return prices


@pytest.fixture(scope="module")
def seth(ERC20Mock, alice):
    yield ERC20Mock.deploy("Second eth", "SETH", 18, {"from": alice})


@pytest.fixture(scope="module")
def base_coins(ERC20Mock, seth, weth, weth_idx, alice, dave, eve, is_forked):
    if is_forked:
        return
    dave.transfer(weth, dave.balance())
    eve.transfer(weth, eve.balance())
    return [
        ERC20Mock.deploy("Tether USD", "USDT", 6, {"from": alice}),
        ERC20Mock.deploy("Wrapped BTC", "WBTC", 8, {"from": alice}),
        weth if weth_idx == 3 else seth,
    ]


@pytest.fixture(scope="module")
def base_token(CurveTokenV4, alice, bob, weth_idx, is_forked):
    if is_forked:
        return
    return CurveTokenV4.deploy("Curve.fi USD-BTC-ETH", "crv3crypto", {"from": alice})


@pytest.fixture(scope="module")
def tricrypto_math(CurveCryptoMath3, alice, is_forked):
    if is_forked:
        return
    return CurveCryptoMath3.deploy({"from": alice})


@pytest.fixture(scope="module")
def tricrypto_views(CurveCryptoViews3, tricrypto_math, base_coins, alice, is_forked):
    if is_forked:
        return
    return CurveCryptoViews3.deploy(
        tricrypto_math,
        [10 ** (18 - coin.decimals()) for coin in base_coins],
        {"from": alice},
    )


@pytest.fixture(scope="module")
def base_swap(
    Tricrypto,
    base_token,
    tricrypto_math,
    tricrypto_views,
    base_coins,
    alice,
    is_forked,
):
    if is_forked:
        return
    contract = Tricrypto.deploy(
        int(0.2 * 3 ** 3 * 10000),  # A
        int(3.5e-3 * 1e18),  # gamma
        int(1.1e-3 * 1e10),  # mid_fee
        int(4.5e-3 * 1e10),  # out_fee
        2 * 10 ** 12,  # allowed_extra_profit
        int(5e-4 * 1e18),  # fee_gamma
        int(0.00049 * 1e18),  # adjustment_step
        5 * 10 ** 9,  # admin_fee
        600,  # ma_half_time
        INITIAL_PRICES_BASE,
        tricrypto_math,
        base_token,
        tricrypto_views,
        base_coins,
        [10 ** (18 - coin.decimals()) for coin in base_coins],
        {"from": alice},
    )
    if base_token.minter() == alice:
        base_token.set_minter(contract, {"from": alice})
    return contract


@pytest.fixture(scope="module")
def initial_amounts_base(base_coins, initial_amount_usd, initial_prices_base):
    usd_cnt = len(base_coins) - 2
    amounts = [
        initial_amount_usd * 10 ** (18 + coin.decimals()) // (usd_cnt * price)
        for price, coin in zip(initial_prices_base[:usd_cnt], base_coins[:usd_cnt])
    ]
    return amounts + [
        initial_amount_usd * 10 ** (18 + coin.decimals()) // price
        for price, coin in zip(initial_prices_base[usd_cnt:], base_coins[usd_cnt:])
    ]
