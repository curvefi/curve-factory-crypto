import pytest
from brownie import ETH_ADDRESS


@pytest.mark.parametrize("i", range(4))
@pytest.mark.parametrize("di", range(1, 4))
def test_exchange(
    zap,
    base_token,
    meta_swap,
    meta_token,
    underlying_coins,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    i: int,
    di: int,
    debug_available,
):
    j = (i + di) % 4
    initial_balance = bob.balance()
    dx = underlying_coins[i].balanceOf(alice)
    with balances_do_not_change(
        underlying_coins[:i] + underlying_coins[i + 1:] + [ETH_ADDRESS, meta_token, base_token],
        alice,
    ):
        calculated = zap.get_dy(meta_swap, i, j, dx)
        tx = zap.exchange(meta_swap, i, j, dx, 0.99 * calculated, False, bob, {"from": alice})
        received = tx.return_value if debug_available else underlying_coins[j].balanceOf(bob)

    zap_has_zero_amounts()

    assert underlying_coins[i].balanceOf(alice) == 0

    assert underlying_coins[i].balanceOf(bob) == 0
    assert underlying_coins[j].balanceOf(bob) == received > 0
    assert bob.balance() == initial_balance
    assert abs(received - calculated) <= 10 ** underlying_coins[j].decimals()


@pytest.mark.parametrize("di", range(1, 4))
def test_exchange_use_eth_in(
    zap,
    base_token,
    meta_swap,
    meta_token,
    underlying_coins,
    amounts_underlying,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    di,
    weth_idx,
    debug_available,
):
    i = weth_idx
    j = (i + di) % len(underlying_coins)
    initial_balance_alice = alice.balance()
    initial_balance_bob = bob.balance()
    dx = amounts_underlying[i]
    with balances_do_not_change(underlying_coins + [meta_token, base_token], alice):
        calculated = zap.get_dy(meta_swap, i, j, dx)
        tx = zap.exchange(
            meta_swap, i, j, dx, 0.99 * calculated, True, bob, {"from": alice, "value": dx}
        )
        received = tx.return_value if debug_available else underlying_coins[j].balanceOf(bob)

    zap_has_zero_amounts()

    assert alice.balance() == initial_balance_alice - dx

    assert underlying_coins[i].balanceOf(bob) == 0
    assert underlying_coins[j].balanceOf(bob) == received > 0
    assert bob.balance() == initial_balance_bob
    assert abs(received - calculated) <= 10 ** underlying_coins[j].decimals()


@pytest.mark.parametrize("di", range(1, 4))
def test_exchange_use_eth_out(
    zap,
    base_token,
    meta_swap,
    meta_token,
    underlying_coins,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    di,
    weth_idx,
    debug_available,
):
    j = weth_idx
    i = (j + di) % len(underlying_coins)
    initial_balance = bob.balance()
    dx = underlying_coins[i].balanceOf(alice)
    with balances_do_not_change(
        underlying_coins[:i] + underlying_coins[i + 1:] + [ETH_ADDRESS, meta_token, base_token],
        alice,
    ):
        calculated = zap.get_dy(meta_swap, i, j, dx)
        tx = zap.exchange(meta_swap, i, j, dx, 0.99 * calculated, True, bob, {"from": alice})
        received = tx.return_value if debug_available else bob.balance() - initial_balance

    zap_has_zero_amounts()

    assert underlying_coins[i].balanceOf(alice) == 0

    assert underlying_coins[i].balanceOf(bob) == 0
    assert underlying_coins[j].balanceOf(bob) == 0
    assert bob.balance() - initial_balance == received > 0
    assert abs(received - calculated) <= 10 ** 18
