import pytest

from tests.fixtures.tricrypto import LP_PRICE_USD

INITIAL_PRICES = [int(LP_PRICE_USD // 10 ** 4 + 1)]  # usd to eth, added 1 for errors


@pytest.fixture(scope="session", autouse=True, params=[0, 3])
def weth_idx(request):
    yield request.param


@pytest.fixture(scope="module")
def coins(base_token, weth, seth, weth_idx):
    yield [
        weth if weth_idx == 0 else seth,
        base_token,
    ]


@pytest.fixture(scope="module")
def meta_swap(CurveCryptoSwap2ETH, factory, coins, alice):
    address = factory.deploy_pool(
        "euro/tricrypto metapool",
        "EUR/3CRV",
        coins,
        90 * 2 ** 2 * 10000,  # A
        int(2.8e-4 * 1e18),  # gamma
        int(5e-4 * 1e10),  # mid_fee
        int(4e-3 * 1e10),  # out_fee
        10 ** 10,  # allowed_extra_profit
        int(0.012 * 1e18),  # fee_gamma
        int(0.55e-5 * 1e18),  # adjustment_step
        0,  # admin_fee
        600,  # ma_half_time
        INITIAL_PRICES[0],
        {"from": alice},
    ).return_value
    yield CurveCryptoSwap2ETH.at(address)


@pytest.fixture(scope="module")
def meta_token(CurveTokenV5, meta_swap):
    yield CurveTokenV5.at(meta_swap.token())


@pytest.fixture(scope="module")
def zap(ZapETH, base_swap, base_token, weth, base_coins, accounts):
    yield ZapETH.deploy(base_swap, base_token, weth, base_coins, {"from": accounts[0]})


@pytest.fixture(scope="module")
def approve_zap(zap, alice, bob, underlying_coins, base_token, meta_token, coins):
    MAX_UINT256 = 2 ** 256 - 1

    base_token.approve(zap, MAX_UINT256, {"from": alice})
    base_token.approve(zap, MAX_UINT256, {"from": bob})

    meta_token.approve(zap, MAX_UINT256, {"from": alice})
    meta_token.approve(zap, MAX_UINT256, {"from": bob})

    for coin in coins + underlying_coins:
        coin.approve(zap, MAX_UINT256, {"from": alice})
        coin.approve(zap, MAX_UINT256, {"from": bob})


@pytest.fixture(scope="session")
def initial_amount_usd():
    return 100_000


@pytest.fixture(scope="module")
def initial_amounts(is_forked, base_swap, meta_swap, coins, initial_amount_usd):
    if not is_forked:
        return [
            3 * initial_amount_usd * 10 ** (18 - 4 + coin.decimals()) // price
            for price, coin in zip([10 ** 18] + INITIAL_PRICES, coins)
        ]

    vp = base_swap.virtual_price() or 10 ** 18  # 0 when empty
    p1 = base_swap.price_oracle(0)
    p2 = base_swap.price_oracle(1)
    lp_token_price = 3 * vp * int(p1 ** (1 / 3)) * int(p2 ** (1 / 3)) // 10 ** (18 - 6)

    amounts = [0, 3 * initial_amount_usd * 10 ** 36 // (lp_token_price + 1000)]
    amounts[0] = amounts[1] * meta_swap.price_scale() // 10 ** (36 - coins[0].decimals())
    return amounts


@pytest.fixture(scope="module")
def initial_amounts_underlying(initial_amounts, initial_amounts_base):
    return initial_amounts[:-1] + initial_amounts_base


@pytest.fixture(scope="module")
def underlying_coins(base_coins, coins):
    return coins[:-1] + base_coins
