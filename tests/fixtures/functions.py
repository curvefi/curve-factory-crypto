from contextlib import contextmanager

import pytest
from brownie import ETH_ADDRESS

from .tricrypto import INITIAL_PRICES_BASE

MAX_UINT = 2 ** 256 - 1


@pytest.fixture(scope="module")
def mint_alice_underlying(
    underlying_coins, initial_amounts_underlying, alice, base_swap, base_token, meta_swap
):
    base_token.approve(meta_swap, MAX_UINT, {"from": alice})
    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(base_swap, MAX_UINT, {"from": alice})
        coin.approve(meta_swap, MAX_UINT, {"from": alice})


@pytest.fixture
def mint_bob_underlying(
    underlying_coins, initial_amounts_underlying, bob, base_swap, base_token, meta_swap
):
    base_token.approve(meta_swap, MAX_UINT, {"from": bob})
    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        coin._mint_for_testing(bob, amount, {"from": bob})
        coin.approve(base_swap, MAX_UINT, {"from": bob})
        coin.approve(meta_swap, MAX_UINT, {"from": bob})


@pytest.fixture(scope="module")
def add_initial_liquidity(
    base_swap,
    base_token,
    meta_swap,
    initial_amounts,
    initial_amounts_underlying,
    alice,
    mint_alice_underlying,
):
    base_swap.add_liquidity(
        initial_amounts_underlying[len(initial_amounts) - 1:], 0, {"from": alice}
    )
    assert base_token.balanceOf(alice) >= initial_amounts[-1], "bad initial_amounts"
    meta_swap.add_liquidity(initial_amounts, 0, {"from": alice})


@pytest.fixture(scope="module")
def get_dy(underlying_coins):
    all_prices = [10_000 * 10 ** 18, 10 ** 18] + INITIAL_PRICES_BASE

    def inner(i: int, j: int, dx: int):
        return (
            dx
            * all_prices[i]
            * 10 ** underlying_coins[j].decimals()
            // (all_prices[j] * 10 ** underlying_coins[i].decimals())
        )

    return inner


@pytest.fixture(scope="session")
def balances_do_not_change():
    @contextmanager
    def inner(tokens, acc):
        initial_amounts = [
            acc.balance() if token == ETH_ADDRESS else token.balanceOf(acc) for token in tokens
        ]

        yield

        for token, initial_amount in zip(tokens, initial_amounts):
            if token == ETH_ADDRESS:
                assert acc.balance() == initial_amount
            else:
                assert token.balanceOf(acc) == initial_amount

    return inner


@pytest.fixture(scope="module")
def zap_has_zero_amounts(meta_token, base_token, underlying_coins, zap):
    def check():
        assert zap.balance() == 0
        for token in [meta_token, base_token] + underlying_coins:
            assert token.balanceOf(zap) == 0

    yield check
