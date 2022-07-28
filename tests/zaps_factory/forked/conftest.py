import json

import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS, Contract
from brownie.project.main import get_loaded_projects

_data = {}


def pytest_addoption(parser):
    parser.addoption("--deployed_data", help="addresses of deployed contracts")


def pytest_generate_tests(metafunc):
    deployed_data = metafunc.config.getoption("deployed_data", "mainnet")
    if deployed_data:
        project = get_loaded_projects()[0]
        with open(
            f"{project._path}/contracts/testing/stable_factory/data/{deployed_data}.json", "r"
        ) as f:
            global _data
            _data = json.load(f)
    if "mintable_fork_token" in metafunc.fixturenames:
        metafunc.parametrize("mintable_fork_token", [deployed_data], indirect=True, scope="session")


@pytest.fixture(scope="session", autouse=True)
def debug_available():
    """debug_traceTransaction"""
    yield _data.get("debug_available", True)


@pytest.fixture(scope="module")
def weth(mintable_fork_token):
    yield mintable_fork_token(_data["weth"])


@pytest.fixture(scope="module")
def new_coin(ERC20Mock, alice):
    def deploy():
        return ERC20Mock.deploy("Test coin", "TST", 18, {"from": alice})

    return deploy


@pytest.fixture(
    scope="module",
    params=[
        ("weth", "coin"),
        ("coin", "coin"),
        ("coin", "weth"),
        ("weth", (False, 2)),
        ("coin", (False, 4)),
        ((False, 2), "weth"),
        ((True, 3), "coin"),
        ((False, 2), (False, 2)),
        ((True, 2), (False, 2)),
        (("weth", 2), "coin"),
        ((False, 3), ("weth", 4)),
    ],
)
def all_coins(weth, stable_factory, new_coin, mintable_fork_token, alice, request):
    coins = []
    for i in range(2):
        coin_type = request.param[i]
        if isinstance(coin_type, str):
            if coin_type == "weth":
                coins.append([weth])
            else:
                coins.append([new_coin()])
        elif coin_type[0] == "weth":
            _coins = [new_coin() for _ in range(0, coin_type[1] - 1)] + [weth]
            address = stable_factory.deploy_plain_pool(
                "Test pool with WETH",
                "TST",
                _coins + [ZERO_ADDRESS] * (4 - len(_coins)),
                100,
                4000000,
                3,  # asset type
                1,  # implementation idx
                {"from": alice},
            ).return_value
            implementation = Contract(
                stable_factory.plain_implementations(len(_coins), 2 if coin_type[0] else 3)
            )
            coins.append([Contract.from_abi("StableSwap", address, implementation.abi)] + _coins)
        else:
            address = _data["base_pool"][str(coin_type[1])]["eth" if coin_type[0] else "no_eth"]
            if address:
                coins.append([mintable_fork_token(address)])
                coins[-1] += [
                    mintable_fork_token(weth.address if coin == ETH_ADDRESS else coin)
                    for coin in stable_factory.get_coins(coins[-1][0])
                    if coin != ZERO_ADDRESS
                ]
            else:
                _coins = [ETH_ADDRESS if coin_type[0] else new_coin()]
                _coins += [new_coin() for _ in range(1, coin_type[1])]
                address = stable_factory.deploy_plain_pool(
                    f"Test pool{' with ETH' if coin_type[0] else ''}",
                    "TST",
                    _coins + [ZERO_ADDRESS] * (4 - len(_coins)),
                    100,
                    4000000,
                    3,  # asset type
                    2 if coin_type[0] else 3,  # implementation idx
                    {"from": alice},
                ).return_value
                implementation = Contract(
                    stable_factory.plain_implementations(len(_coins), 2 if coin_type[0] else 3)
                )
                coins.append(
                    [Contract.from_abi("StableSwap", address, implementation.abi)] + _coins
                )
        coins[-1] = [coin if coin != ETH_ADDRESS else weth for coin in coins[-1]]
    yield coins


@pytest.fixture(scope="module")
def coins_flat(all_coins):
    """List of all coins instead of structured."""
    return [c for cs in all_coins for c in cs]


@pytest.fixture(scope="module")
def meta_coins(all_coins):
    return [all_coins[i][0] for i in range(2)]


@pytest.fixture(scope="module")
def initial_price():
    return 10**18


@pytest.fixture(scope="module")
def meta_swap(CurveCryptoSwap2ETH, factory, coins, meta_coins, initial_price, alice):
    symbol = f"{meta_coins[0].symbol()[:4]}/{meta_coins[1].symbol()[:5]}"  # String[10]
    address = factory.deploy_pool(
        f"{symbol} metapool",
        symbol,
        meta_coins,
        90 * 2**2 * 10000,  # A
        int(2.8e-4 * 1e18),  # gamma
        int(5e-4 * 1e10),  # mid_fee
        int(4e-3 * 1e10),  # out_fee
        10**10,  # allowed_extra_profit
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
def zap(ZapStableSwapFactory, weth, stable_factory, alice):
    contract = ZapStableSwapFactory.deploy(weth, stable_factory, {"from": alice})
    return contract


@pytest.fixture(scope="session")
def default_amount():
    return 10  # Small for tiny pools


@pytest.fixture(scope="module")
def default_amounts(all_coins, default_amount):
    amounts = []
    for base_coins in all_coins:
        amounts.append([])
        if len(base_coins) == 1:
            amounts[-1] += [default_amount * 10 ** base_coins[0].decimals()]
        else:
            amounts[-1] += [0]
            for c in base_coins[1:]:
                amounts[-1] += [default_amount * 10 ** c.decimals()]
        amounts[-1] += [0] * (5 - len(amounts[-1]))
    return amounts


@pytest.fixture(scope="module")
def factory(factory, Factory):
    yield Factory.at(_data["crypto_factory"])


@pytest.fixture(scope="module")
def stable_factory():
    yield Contract(_data["stable_factory"])


@pytest.fixture(scope="module", autouse=True)
def pre_mining(alice, coins_flat, weth, default_amount):
    """Mint a bunch of test tokens"""
    if weth.balanceOf(alice) > 0:
        weth.transfer(ZERO_ADDRESS, weth.balanceOf(alice), {"from": alice})
    for coin in coins_flat:
        amount = 2 * default_amount * 10 ** coin.decimals()
        if hasattr(coin, "_mint_for_testing"):
            coin._mint_for_testing(alice, amount, {"from": alice})

    # Get ETH
    amount = 2 * default_amount * 10 ** weth.decimals()
    weth._mint_for_testing(alice, amount, {"from": alice})
    weth.withdraw(amount, {"from": alice})


@pytest.fixture(scope="module", autouse=True)
def approve_zap(zap, alice, bob, coins_flat, meta_token):
    MAX_UINT256 = 2**256 - 1
    for coin in coins_flat + [meta_token]:
        coin.approve(zap, MAX_UINT256, {"from": alice})
        coin.approve(zap, MAX_UINT256, {"from": bob})


@pytest.fixture(scope="module", autouse=True)
def add_initial_liquidity(
    pre_mining, zap, all_coins, weth, default_amount, meta_swap, meta_coins, alice
):
    """Always add initial liquidity to get LP Tokens and have liquidity in meta pool."""
    amounts = [default_amount * 10 ** coin.decimals() for coin in meta_coins]
    for i, base_coins in enumerate(all_coins):
        if len(base_coins) > 1:
            pool = base_coins[0]
            underlying_coins = base_coins[1:]
            underlying_amounts = [
                default_amount * 10 ** coin.decimals() for coin in underlying_coins
            ]

            for coin, amount in zip(underlying_coins, underlying_amounts):
                coin.approve(pool, amount, {"from": alice})
            pool.add_liquidity(
                underlying_amounts,
                0,
                {
                    "from": alice,
                    "value": default_amount * 10**18 if weth == underlying_coins[0] else 0,
                },
            )
            if weth == underlying_coins[0]:  # Remove extra weth
                weth.transfer(ZERO_ADDRESS, default_amount * 10**18, {"from": alice})

            # Keep some LP for tests
            amounts[i] = pool.balanceOf(alice) // 2
        base_coins[0].approve(meta_swap, amounts[i], {"from": alice})

    meta_swap.add_liquidity(amounts, 0, {"from": alice})


@pytest.fixture(scope="module")
def zap_is_broke(zap, coins_flat, meta_token):
    def inner():
        assert zap.balance() == 0
        for coin in coins_flat + [meta_token]:
            if coin != ETH_ADDRESS:
                assert coin.balanceOf(zap) == 0

    return inner
