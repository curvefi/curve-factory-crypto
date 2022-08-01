import pytest

from tests.fixtures.tricrypto import LP_PRICE_USD


def pytest_addoption(parser):
    parser.addoption("--zap_base", action="store", default=["tricrypto", "3pool"], help="Base pool of zap to test")


def pytest_generate_tests(metafunc):
    deployed_data = metafunc.config.getoption("deployed_data", None)
    if deployed_data:
        # Test in fork
        # Will be set in forked/conftest.py
        return

    zap_base = metafunc.config.getoption("zap_base")
    zap_bases = zap_base if isinstance(zap_base, list) else [zap_base]
    values = []
    for base in zap_bases:
        if base == "tricrypto":
            values.extend([(base, 0), (base, 3)])
        elif base == "3pool":
            values.append((base, 0))
        else:
            raise ValueError(f"Unknown zap base: {base}")
    metafunc.parametrize(["zap_base", "weth_idx"], values, indirect=True, scope="session")


@pytest.fixture(scope="session", autouse=True)
def zap_base(request):
    yield request.param


@pytest.fixture(scope="session", autouse=True)
def weth_idx(request):
    yield request.param


@pytest.fixture(scope="module")
def coins(base_token, weth, seth, weth_idx):
    yield [
        weth if weth_idx == 0 else seth,
        base_token,
    ]


@pytest.fixture(scope="module")
def initial_price(zap_base):
    if zap_base == "3pool":
        return 10 ** (18 - 4)
    elif zap_base == "tricrypto":
        return int(LP_PRICE_USD // 10 ** 4 + 1)  # usd to eth, added 1 for errors
    else:
        return 10 ** 18


@pytest.fixture(scope="module")
def lp_price_usd(zap_base):
    if zap_base == "3pool":
        return 10 ** 18
    elif zap_base == "tricrypto":
        return LP_PRICE_USD


@pytest.fixture(scope="module")
def meta_swap(CurveCryptoSwap2ETH, factory, coins, initial_price, alice):
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
        initial_price,
        {"from": alice},
    ).return_value
    yield CurveCryptoSwap2ETH.at(address)


@pytest.fixture(scope="module")
def meta_token(CurveTokenV5, meta_swap):
    yield CurveTokenV5.at(meta_swap.token())


@pytest.fixture(scope="module")
def zap(ZapETH, ZapETHZap, Zap3PoolETH, ZapStableSwapFactoryOne, zap_base, base_swap, base_token, weth, base_coins, accounts):
    if zap_base == "3pool":
        contract = Zap3PoolETH
    elif zap_base == "stable_factory":
        # from tests.zaps.forked.conftest import _data
        return ZapStableSwapFactoryOne.deploy(weth, "0xB9fC157394Af804a3578134A6585C0dc9cc990d4", {"from": accounts[0]})
    elif len(base_coins) == 3:
        contract = ZapETH
    else:
        contract = ZapETHZap
    return contract.deploy(base_swap, base_token, weth, base_coins, {"from": accounts[0]})


@pytest.fixture(scope="module")
def approve_zap(zap, alice, bob, underlying_coins, base_token, meta_token, coins):
    MAX_UINT256 = 2 ** 256 - 1

    base_token.approve(zap, MAX_UINT256, {"from": alice})
    base_token.approve(zap, MAX_UINT256, {"from": bob})

    meta_token.approve(zap, MAX_UINT256, {"from": alice})
    meta_token.approve(zap, MAX_UINT256, {"from": bob})

    for coin in coins[:-1] + underlying_coins:
        coin.approve(zap, MAX_UINT256, {"from": alice})
        coin.approve(zap, MAX_UINT256, {"from": bob})


@pytest.fixture(scope="session")
def initial_amount_usd():
    return 100_000


@pytest.fixture(scope="module")
def base_coins(zap_base, tricrypto_coins, tripool_coins):
    if zap_base == "tricrypto":
        return tricrypto_coins
    elif zap_base == "3pool":
        return tripool_coins


@pytest.fixture(scope="module")
def base_token(zap_base, tricrypto_token, tripool_token):
    if zap_base == "tricrypto":
        return tricrypto_token
    elif zap_base == "3pool":
        return tripool_token


@pytest.fixture(scope="module")
def base_swap(zap_base, tricrypto, tripool):
    if zap_base == "tricrypto":
        return tricrypto
    elif zap_base == "3pool":
        return tripool


@pytest.fixture(scope="module")
def initial_prices_base(zap_base, tricrypto_initial_prices, tripool_initial_prices, base_swap, base_coins):
    if zap_base == "tricrypto":
        return tricrypto_initial_prices
    elif zap_base == "3pool":
        return tripool_initial_prices
    else:
        initial_prices = [10 ** 18]
        for i, coin in zip(range(1, len(base_coins)), base_coins[1:]):
            initial_prices.append(
                base_swap.get_dy(i, 0, 10 ** coin.decimals()) * 10 ** (18 - base_coins[0].decimals())
            )
        return initial_prices


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


@pytest.fixture(scope="module")
def initial_prices(zap_base, Tricrypto, is_forked, base_swap, meta_swap, initial_price, lp_price_usd):
    """
    Meta pool coins prices in first base pool coin
    """
    if not is_forked:
        return [lp_price_usd * 10 ** 18 // initial_price, lp_price_usd + 1000]

    if zap_base in ["3pool", "stable_factory"]:
        vp = base_swap.get_virtual_price()
        return [10 ** 36 // meta_swap.price_scale(), vp]

    if hasattr(base_swap, "pool"):  # Zap
        base_swap = Tricrypto.at(base_swap.pool())
    vp = base_swap.virtual_price() or 10 ** 18  # 0 when empty
    p1 = base_swap.price_oracle(0)
    p2 = base_swap.price_oracle(1)
    lp_token_price = (
        3 * vp * int(p1 ** (1 / 3)) * int(p2 ** (1 / 3)) // 10 ** (18 - 6) + 1000
    )  # 1000 for calc errors

    return [
        lp_token_price * 10 ** 18 // meta_swap.price_scale(),
        lp_token_price,
    ]


@pytest.fixture(scope="module")
def initial_amounts(is_forked, base_swap, meta_swap, coins, initial_amount_usd, initial_prices):
    return [  # 18 - 4 + decimals
        3 * initial_amount_usd * 10 ** (18 + coin.decimals()) // price
        for price, coin in zip(initial_prices, coins)
    ]


@pytest.fixture(scope="module")
def initial_amounts_underlying(initial_amounts, initial_amounts_base):
    return initial_amounts[:-1] + initial_amounts_base


@pytest.fixture(scope="module")
def underlying_coins(base_coins, coins):
    return coins[:-1] + base_coins


@pytest.fixture(scope="module")
def underlying_prices(initial_prices, initial_prices_base):
    return initial_prices[:-1] + initial_prices_base
