import pytest
import json
from brownie_tokens import MintableForkToken
from brownie.project.main import get_loaded_projects

EURT = "0xC581b735A1688071A1746c968e0798D642EDE491"
COINS = [
    "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # usdt
    "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # wbtc
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # weth
]
SWAP = "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"
TOKEN = "0xc4AD29ba4B3c580e6D59105FFf484999997675Ff"
FACTORY = "0xF18056Bbd320E96A48e3Fbf8bC061322531aac99"


@pytest.fixture(scope="module")
def weth(weth, is_forked):
    if not is_forked:
        yield weth
    else:
        yield MintableForkToken(COINS[-1])


@pytest.fixture(scope="module")
def base_coins(base_coins, is_forked):
    if not is_forked:
        yield base_coins
    else:
        yield [MintableForkToken(addr) for addr in COINS]


@pytest.fixture(scope="module")
def base_swap(base_swap, is_forked, Tricrypto):
    if not is_forked:
        yield base_swap
    else:
        yield Tricrypto.at(SWAP)


@pytest.fixture(scope="module")
def base_token(base_token, is_forked, CurveTokenV4):
    if not is_forked:
        yield base_token
    else:
        yield CurveTokenV4.at(TOKEN)


@pytest.fixture(scope="module")
def factory(factory, is_forked, Factory):
    if not is_forked:
        yield factory
    else:
        yield Factory.at(FACTORY)


@pytest.fixture(scope="module")
def coins(coins, is_forked, base_token):
    if not is_forked:
        yield coins
    else:
        yield [
            MintableForkToken(EURT),
            base_token,
        ]


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
def pre_mining(alice, zap, underlying_coins, weth, weth_idx, base_token, meta_token, amounts_underlying):
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
