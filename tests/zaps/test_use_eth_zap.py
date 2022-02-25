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
    weth_idx,
    weth,
    mint_bob_underlying,
):
    amounts = [a // 50 for a in initial_amounts_underlying]
    for i, (coin, amount) in enumerate(zip(underlying_coins, amounts)):
        if i == weth_idx:
            continue
        coin.transfer(charlie, amount, {"from": bob})
        coin.approve(zap, amount, {"from": charlie})

    zap.add_liquidity(meta_swap, amounts, 0, True, {"from": charlie, "value": amounts[weth_idx]})

    assert zap.balance() == 0
    for coin, initial_amount, amount in zip(underlying_coins, initial_amounts_underlying, amounts):
        assert coin.balanceOf(zap) == 0
        balance = meta_swap.balance() if coin == weth else coin.balanceOf(meta_swap)
        if coin in coins:
            assert balance == initial_amount + amount
        else:
            assert balance == 0


@pytest.mark.parametrize("di", range(1, 4))
def test_exchange_in(
    zap, meta_swap, base_swap, base_token, di, weth_idx, underlying_coins, alice, charlie, get_dy
):
    i = weth_idx
    j = (i + di) % 4
    dx = get_dy(1, i, 10 ** underlying_coins[1].decimals())
    dy = get_dy(i, j, dx)
    initial_balance = charlie.balance()
    zap.exchange(meta_swap, i, j, dx, 0, True, {"from": charlie, "value": dx})

    for coin in underlying_coins:
        assert coin.balanceOf(zap) == 0

    assert charlie.balance() == initial_balance - dx
    assert 0.99 <= underlying_coins[j].balanceOf(charlie) / dy <= 1


@pytest.mark.parametrize("di", range(1, 4))
def test_exchange_out(
    zap,
    meta_swap,
    base_swap,
    base_token,
    di,
    weth_idx,
    underlying_coins,
    initial_amounts_underlying,
    bob,
    get_dy,
    mint_bob_underlying,
):
    j = weth_idx
    i = (j + di) % 4
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
    alice, bob, zap, underlying_coins, initial_amounts_underlying, meta_swap, meta_token, weth_idx
):
    divisor = 50
    initial_amount = meta_token.balanceOf(alice)
    amount = initial_amount // divisor
    initial_balance = bob.balance()

    meta_token.transfer(bob, initial_amount, {"from": alice})
    zap.remove_liquidity_one_coin(meta_swap, amount, weth_idx, 0, True, {"from": bob})

    assert zap.balance() == 0
    assert meta_token.balanceOf(zap) == 0

    assert meta_token.balanceOf(bob) == initial_amount - amount
    assert underlying_coins[weth_idx].balanceOf(bob) == 0
    assert (
        0 < (bob.balance() - initial_balance) <= 6 * initial_amounts_underlying[weth_idx] // divisor
    )


def test_remove_liquidity(
    alice,
    bob,
    meta_swap,
    meta_token,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
    weth,
    weth_idx,
):
    meta_token.transfer(bob, meta_token.balanceOf(alice), {"from": alice})

    initial_balance = meta_token.balanceOf(bob)
    withdraw_amount = initial_balance // 50
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(meta_swap, withdraw_amount, min_amounts, True, {"from": bob})

    assert zap.balance() == 0
    for i, coin in enumerate(underlying_coins):
        if i == weth_idx:
            continue
        assert coin.balanceOf(zap) == 0
        if i != 0:
            assert coin.balanceOf(meta_swap) == 0
        assert coin.balanceOf(bob) > 0

    assert weth.balanceOf(zap) == 0
    assert weth.balanceOf(meta_swap) == 0
    assert weth.balanceOf(bob) == 0
    assert bob.balance() > 0
