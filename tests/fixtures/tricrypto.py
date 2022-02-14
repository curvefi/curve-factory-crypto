import pytest

INITIAL_PRICES_BASE = [
    100_000 * 10 ** 18,
    10_000 * 10 ** 18,
]  # prices chosen, so qubic root is integer
LP_PRICE_USD = 3 * (1000 * 10 ** 18 + 300)  # 3 * (p1 * p2) ^ 1/3, added 300 for errors


@pytest.fixture(scope="module")
def base_coins(ERC20Mock, weth, alice, dave, eve):
    dave.transfer(weth, dave.balance())
    eve.transfer(weth, eve.balance())
    yield [
        ERC20Mock.deploy("Tether USD", "USDT", 6, {"from": alice}),
        ERC20Mock.deploy("Wrapped BTC", "WBTC", 8, {"from": alice}),
        weth,
    ]


@pytest.fixture(scope="module")
def base_token(CurveTokenV4, alice, bob):
    yield CurveTokenV4.deploy("Curve.fi USD-BTC-ETH", "crv3crypto", {"from": alice})


@pytest.fixture(scope="module")
def tricrypto_math(CurveCryptoMath3, alice):
    yield CurveCryptoMath3.deploy({"from": alice})


@pytest.fixture(scope="module")
def tricrypto_views(CurveCryptoViews3, tricrypto_math, base_coins, alice):
    yield CurveCryptoViews3.deploy(
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
):
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
    yield contract


@pytest.fixture(scope="module")
def initial_amounts_base(base_swap, base_coins, initial_amount_usd):
    p1 = base_swap.price_oracle(0)
    p2 = base_swap.price_oracle(1)
    return [
        initial_amount_usd * 10 ** (18 + coin.decimals()) // price
        for price, coin in zip([10 ** 18, p1, p2], base_coins)
    ]
