import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob_underlying", "approve_zap")


@pytest.mark.parametrize("i", range(4))
@pytest.mark.parametrize("di", range(1, 4))
def test_exchange(
    bob,
    charlie,
    zap,
    meta_swap,
    meta_token,
    i: int,
    di: int,
    underlying_coins,
    initial_amounts_underlying,
):
    j = (i + di) % 4
    dx = 10 ** underlying_coins[i].decimals()
    zap.exchange(meta_swap, i, j, dx, 0, False, charlie, {"from": bob})

    for coin in underlying_coins:
        assert coin.balanceOf(zap) == 0

    assert underlying_coins[i].balanceOf(bob) == initial_amounts_underlying[i] - dx
    assert underlying_coins[j].balanceOf(bob) == initial_amounts_underlying[j]

    assert underlying_coins[i].balanceOf(charlie) == 0
    assert underlying_coins[j].balanceOf(charlie) > 0


def test_add_liquidity(bob, charlie, zap, meta_swap, meta_token, initial_amounts_underlying):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, False, charlie, {"from": bob})

    assert meta_token.balanceOf(charlie) > 0
    assert meta_token.balanceOf(bob) == 0


def test_remove_one_coin(alice, charlie, dave, zap, underlying_coins, coins, meta_swap, meta_token):
    underlying = underlying_coins[1]

    initial_balance = meta_token.balanceOf(alice)
    amount = initial_balance // 4

    meta_token.transfer(charlie, initial_balance, {"from": alice})
    meta_token.approve(zap, 2 ** 256 - 1, {"from": charlie})
    zap.remove_liquidity_one_coin(meta_swap, amount, 1, 0, False, dave, {"from": charlie})

    assert underlying.balanceOf(zap) == 0
    assert underlying.balanceOf(charlie) == 0
    assert underlying.balanceOf(dave) > 0

    assert meta_token.balanceOf(zap) == 0
    assert meta_token.balanceOf(charlie) + amount == initial_balance
    assert meta_token.balanceOf(dave) == 0


def test_remove_liquidity(alice, charlie, dave, zap, meta_swap, meta_token, underlying_coins):
    initial_balance = meta_token.balanceOf(alice)
    withdraw_amount = initial_balance // 3

    meta_token.transfer(charlie, initial_balance, {"from": alice})
    meta_token.approve(zap, 2 ** 256 - 1, {"from": charlie})
    zap.remove_liquidity(meta_swap, withdraw_amount, [0, 0, 0, 0], False, dave, {"from": charlie})

    assert meta_token.balanceOf(charlie) > 0
    assert meta_token.balanceOf(dave) == 0
    assert meta_token.balanceOf(zap) == 0

    for coin in underlying_coins:
        assert coin.balanceOf(charlie) == 0
        assert coin.balanceOf(dave) > 0
        assert coin.balanceOf(zap) == 0
