import pytest


@pytest.fixture(scope="module")
def tripool_initial_prices(zap_base, is_forked, base_coins, base_swap):
    if not is_forked or zap_base != "3pool":
        return [10 ** 18 for _ in range(3)]

    tripool = base_swap
    tripool_coins = base_coins
    prices = [10 ** 18]
    for i in range(2):
        prices.append(tripool.get_dy(1 + i, 0, 10 ** tripool_coins[1 + i].decimals()) * 10 ** (18 - tripool_coins[0].decimals()))
    return prices


@pytest.fixture(scope="module")
def tripool_coins(ERC20Mock, seth, weth, weth_idx, alice, dave, eve, is_forked):
    if is_forked:
        return
    dave.transfer(weth, dave.balance())
    eve.transfer(weth, eve.balance())
    return [
        ERC20Mock.deploy("DAI", "DAI", 18, {"from": alice}),
        ERC20Mock.deploy("USD Coin", "USDC", 6, {"from": alice}),
        ERC20Mock.deploy("Tether USD", "USDT", 6, {"from": alice}),
    ]


@pytest.fixture(scope="module")
def tripool_token(CurveTokenV2, alice, bob, weth_idx, is_forked):
    if is_forked:
        return
    return CurveTokenV2.deploy("Curve.fi 3pool", "3crv", 18, 0, {"from": alice})


@pytest.fixture(scope="module")
def tripool(
    StableSwap3Pool,
    tripool_token,
    tripool_coins,
    alice,
    is_forked,
):
    if is_forked:
        return
    contract = StableSwap3Pool.deploy(
        alice,  # owner
        tripool_coins,
        tripool_token,
        200,  # A
        0,  # fee = 0.3%
        0,  # admin_fee
        {"from": alice},
    )
    if tripool_token.minter() == alice:
        tripool_token.set_minter(contract, {"from": alice})
    return contract
