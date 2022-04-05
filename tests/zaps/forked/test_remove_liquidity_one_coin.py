import pytest
from brownie import ETH_ADDRESS


@pytest.mark.parametrize("idx", range(4))
def test_remove_liquidity_one_coin(
    zap,
    base_token,
    meta_swap,
    meta_token,
    underlying_coins,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    idx,
    debug_available,
):
    lp_amount = meta_token.balanceOf(alice) // 2
    initial_balance = bob.balance()

    with balances_do_not_change(underlying_coins + [ETH_ADDRESS, base_token], alice):
        calculated = zap.calc_withdraw_one_coin(meta_swap, lp_amount, idx)
        tx = zap.remove_liquidity_one_coin(
            meta_swap, lp_amount, idx, 0.99 * calculated, False, bob, {"from": alice}
        )
        received = tx.return_value if debug_available else underlying_coins[idx].balanceOf(bob)

    zap_has_zero_amounts()

    assert bob.balance() == initial_balance
    assert underlying_coins[idx].balanceOf(bob) == received > 0
    assert abs(received - calculated) <= 10 ** underlying_coins[idx].decimals()


def test_remove_liquidity_one_coin_use_eth(
    zap,
    base_token,
    meta_swap,
    meta_token,
    underlying_coins,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    weth_idx,
    debug_available,
):
    lp_amount = meta_token.balanceOf(alice) // 2
    initial_balance = bob.balance()

    with balances_do_not_change(underlying_coins + [ETH_ADDRESS, base_token], alice):
        calculated = zap.calc_withdraw_one_coin(meta_swap, lp_amount, weth_idx)
        tx = zap.remove_liquidity_one_coin(
            meta_swap, lp_amount, weth_idx, 0.99 * calculated, True, bob, {"from": alice}
        )
        received = tx.return_value if debug_available else bob.balance() - initial_balance

    zap_has_zero_amounts()

    assert underlying_coins[weth_idx].balanceOf(bob) == 0
    assert bob.balance() - initial_balance == received > 0
    assert abs(received - calculated) <= 10 ** 18
