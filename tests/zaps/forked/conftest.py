import json

import pytest
from brownie import Contract, interface
from brownie.project.main import get_loaded_projects

_data = {}


def pytest_addoption(parser):
    parser.addoption("--deployed_data", help="addresses of deployed contracts")


def pytest_generate_tests(metafunc):
    deployed_data = metafunc.config.getoption("deployed_data", None)
    weth_indexes = [0, 3]
    if deployed_data:
        project = get_loaded_projects()[0]
        with open(
            f"{project._path}/contracts/testing/tricrypto/data/{deployed_data}.json", "r"
        ) as f:
            global _data
            _data = json.load(f)
        weth_indexes = [_data["weth_idx"]]
    metafunc.parametrize("weth_idx", weth_indexes, indirect=True, scope="session")
    if "mintable_fork_token" in metafunc.fixturenames:
        metafunc.parametrize("mintable_fork_token", [deployed_data], indirect=True, scope="session")


@pytest.fixture(scope="session", autouse=True)
def debug_available():
    """debug_traceTransaction"""
    yield _data.get("debug_available", True)


@pytest.fixture(scope="session", autouse=True)
def weth_idx(request):
    yield request.param


@pytest.fixture(scope="module")
def weth(weth, mintable_fork_token, is_forked):
    if not is_forked:
        yield weth
    else:
        yield mintable_fork_token(_data["weth"])


@pytest.fixture(scope="module")
def base_coins(base_coins, mintable_fork_token, is_forked):
    if not is_forked:
        yield base_coins
    else:
        yield [mintable_fork_token(addr) for addr in _data["coins"]]


@pytest.fixture(scope="module")
def base_swap(Tricrypto, base_swap, base_coins, is_forked):
    yield base_swap or (
        Tricrypto.at(_data["swap"])
        if len(base_coins) == 3
        else Contract.from_abi("TricryptoZap", _data["swap"], interface.TricryptoZap.abi)
    )


@pytest.fixture(scope="module")
def base_token(base_token, is_forked, CurveTokenV4):
    yield base_token or CurveTokenV4.at(_data["token"])


@pytest.fixture(scope="module")
def factory(factory, is_forked, Factory):
    if not is_forked or not _data["factory"]:
        yield factory
    else:
        yield Factory.at(_data["factory"])


@pytest.fixture(scope="session")
def initial_amount_usd(initial_amount_usd, is_forked):
    if not is_forked:
        return initial_amount_usd
    else:
        return 1_000


@pytest.fixture(scope="module")
def amounts_underlying(underlying_coins):
    """Small amounts"""
    return [10 ** coin.decimals() for coin in underlying_coins]


@pytest.fixture(scope="module", autouse=True)
def pre_mining(
    alice, zap, underlying_coins, weth, weth_idx, base_token, meta_token, amounts_underlying
):
    """Mint a bunch of test tokens"""
    meta_token.approve(zap, 2 ** 256 - 1, {"from": alice})
    base_token.approve(zap, 2 ** 256 - 1, {"from": alice})
    for coin, amount in zip(underlying_coins, amounts_underlying):
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(zap, 2 ** 256 - 1, {"from": alice})

    # Get ETH
    weth._mint_for_testing(alice, amounts_underlying[weth_idx], {"from": alice})
    weth.withdraw(amounts_underlying[weth_idx], {"from": alice})


@pytest.fixture(scope="module", autouse=True)
def add_initial_liquidity(add_initial_liquidity):
    """Always add initial liquidity to get LP Tokens and have liquidity in meta pool."""
    pass
