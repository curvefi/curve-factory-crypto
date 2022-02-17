import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


def test_send_eth(alice, zap):
    amount = alice.balance() // 2
    with brownie.reverts():
        alice.transfer(zap, amount)


def test_add_liquidity(
    alice,
    bob,
    charlie,
    zap,
    meta_swap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
    mint_bob_underlying,
):
    amounts = [a // 50 for a in initial_amounts_underlying]
    for coin, amount in zip(underlying_coins[:-1], amounts[:-1]):
        coin.transfer(charlie, amount, {"from": bob})
        coin.approve(zap, amount, {"from": charlie})

    zap.add_liquidity(meta_swap, amounts, 0, True, {"from": charlie, "value": amounts[-1]})

    assert zap.balance() == 0
    for coin, initial_amount, amount in zip(underlying_coins, initial_amounts_underlying, amounts):
        assert coin.balanceOf(zap) == 0
        if coin in coins:
            assert coin.balanceOf(meta_swap) == initial_amount + amount
        else:
            assert coin.balanceOf(meta_swap) == 0


@pytest.mark.parametrize("j", range(3))
def test_exchange_in(
    zap, meta_swap, base_swap, base_token, j, underlying_coins, alice, charlie, get_dy
):
    i = 3
    dx = get_dy(1, i, 10 ** underlying_coins[1].decimals())
    dy = get_dy(i, j, dx)
    initial_balance = charlie.balance()
    zap.exchange(meta_swap, i, j, dx, 0, True, {"from": charlie, "value": dx})

    for coin in underlying_coins:
        assert coin.balanceOf(zap) == 0

    assert charlie.balance() == initial_balance - dx
    assert 0.99 <= underlying_coins[j].balanceOf(charlie) / dy <= 1


@pytest.mark.parametrize("i", range(3))
def test_exchange_out(
    zap,
    meta_swap,
    base_swap,
    base_token,
    i,
    underlying_coins,
    initial_amounts_underlying,
    bob,
    get_dy,
    mint_bob_underlying,
):
    j = 3
    dx = get_dy(1, i, 10 ** underlying_coins[1].decimals())
    dy = get_dy(i, j, dx)
    initial_balance = bob.balance()
    zap.exchange(meta_swap, i, j, dx, 0, True, {"from": bob})

    assert zap.balance() == 0
    for coin in underlying_coins:
        assert coin.balanceOf(zap) == 0

    assert underlying_coins[i].balanceOf(bob) == initial_amounts_underlying[i] - dx
    assert 0.99 <= (bob.balance() - initial_balance) / dy <= 1


def test_remove_liquidity_one_coin(
    alice, bob, zap, underlying_coins, initial_amounts_underlying, meta_swap, meta_token
):
    divisor = 50
    initial_amount = meta_token.balanceOf(alice)
    amount = initial_amount // divisor
    initial_balance = bob.balance()

    meta_token.transfer(bob, initial_amount, {"from": alice})
    zap.remove_liquidity_one_coin(meta_swap, amount, 3, 0, True, {"from": bob})

    assert zap.balance() == 0
    assert meta_token.balanceOf(zap) == 0

    assert meta_token.balanceOf(bob) == initial_amount - amount
    assert underlying_coins[-1].balanceOf(bob) == 0
    assert 0 < (bob.balance() - initial_balance) <= 6 * initial_amounts_underlying[-1] // divisor


def test_remove_liquidity(
    alice,
    bob,
    meta_swap,
    meta_token,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
):
    meta_token.transfer(bob, meta_token.balanceOf(alice), {"from": alice})

    initial_balance = meta_token.balanceOf(bob)
    withdraw_amount = initial_balance // 50
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(meta_swap, withdraw_amount, min_amounts, True, {"from": bob})

    assert zap.balance() == 0
    for coin in underlying_coins[1:-1]:
        assert coin.balanceOf(zap) == 0
        assert coin.balanceOf(meta_swap) == 0
        assert coin.balanceOf(bob) > 0

    weth = underlying_coins[-1]
    assert weth.balanceOf(zap) == 0
    assert weth.balanceOf(meta_swap) == 0
    assert weth.balanceOf(bob) == 0
    assert bob.balance() > 0
