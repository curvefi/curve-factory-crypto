from contextlib import contextmanager

import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS

MAX_UINT = 2 ** 256 - 1


@pytest.fixture(scope="module")
def mint_alice_underlying(
    underlying_coins, initial_amounts_underlying, alice, base_swap, base_token, meta_swap
):
    base_token.approve(meta_swap, MAX_UINT, {"from": alice})
    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        if coin == ZERO_ADDRESS:
            continue
        coin._mint_for_testing(alice, amount, {"from": alice})
        coin.approve(base_swap, MAX_UINT, {"from": alice})
        coin.approve(meta_swap, MAX_UINT, {"from": alice})


@pytest.fixture
def mint_bob_underlying(
    underlying_coins, initial_amounts_underlying, bob, base_swap, base_token, meta_swap
):
    base_token.approve(meta_swap, MAX_UINT, {"from": bob})
    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        if coin == ZERO_ADDRESS:
            continue
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
    is_forked,
):
    base_swap.add_liquidity(
        [amount for amount in initial_amounts_underlying[len(initial_amounts) - 1:] if amount > 0], 0, {"from": alice}
    )
    if is_forked:  # Sometimes calculations fail
        assert int(base_token.balanceOf(alice)) == pytest.approx(
            initial_amounts[-1], rel=2e-2  # virtual price of 3pool is not counted => may have such big error
        ), "bad initial_amounts"
        initial_amounts[-1] = base_token.balanceOf(alice)
    else:
        assert base_token.balanceOf(alice) >= initial_amounts[-1], "bad initial_amounts"
    meta_swap.add_liquidity(initial_amounts, 0, {"from": alice})


@pytest.fixture(scope="module")
def get_dy(underlying_coins, underlying_prices):
    def inner(i: int, j: int, dx: int):
        return (
            dx
            * underlying_prices[i]
            * 10 ** underlying_coins[j].decimals()
            // (underlying_prices[j] * 10 ** underlying_coins[i].decimals())
        )

    return inner


@pytest.fixture(scope="session")
def balances_do_not_change():
    @contextmanager
    def inner(tokens, acc):
        tokens = [token for token in tokens if token != ZERO_ADDRESS]
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
            if token == ZERO_ADDRESS:
                continue
            assert token.balanceOf(zap) == 0

    yield check
