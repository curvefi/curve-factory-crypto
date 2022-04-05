import pytest
from brownie import ETH_ADDRESS


def test_multiple_coins(
    zap,
    factory,
    base_swap,
    base_token,
    meta_swap,
    meta_token,
    underlying_coins,
    amounts_underlying,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    debug_available,
):
    with balances_do_not_change([ETH_ADDRESS, meta_token, base_token], alice):
        calculated = zap.calc_token_amount(meta_swap, amounts_underlying)
        tx = zap.add_liquidity(
            meta_swap, amounts_underlying, 0.99 * calculated, False, bob, {"from": alice}
        )
        lp_received = tx.return_value if debug_available else meta_token.balanceOf(bob)

    zap_has_zero_amounts()

    assert meta_token.balanceOf(bob) == lp_received > 0
    assert abs(lp_received - calculated) <= 10 ** meta_token.decimals()


@pytest.mark.parametrize("idx", range(4))
def test_one_coin(
    zap,
    meta_swap,
    meta_token,
    base_token,
    underlying_coins,
    amounts_underlying,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    idx,
    debug_available,
):
    with balances_do_not_change([ETH_ADDRESS, meta_token, base_token], alice):
        amounts = [0] * len(amounts_underlying)
        amounts[idx] = amounts_underlying[idx]
        calculated = zap.calc_token_amount(meta_swap, amounts)
        tx = zap.add_liquidity(meta_swap, amounts, 0.99 * calculated, False, bob, {"from": alice})
        lp_received = tx.return_value if debug_available else meta_token.balanceOf(bob)

    zap_has_zero_amounts()

    assert meta_token.balanceOf(bob) == lp_received > 0
    assert abs(lp_received - calculated) <= 10 ** meta_token.decimals()


def test_multiple_coins_use_eth(
    zap,
    meta_swap,
    meta_token,
    base_token,
    underlying_coins,
    amounts_underlying,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    weth,
    weth_idx,
    debug_available,
):
    initial_balance = alice.balance()
    with balances_do_not_change([weth, meta_token, base_token], alice):
        calculated = zap.calc_token_amount(meta_swap, amounts_underlying)
        tx = zap.add_liquidity(
            meta_swap,
            amounts_underlying,
            0.99 * calculated,
            True,
            bob,
            {"from": alice, "value": amounts_underlying[weth_idx]},
        )
        lp_received = tx.return_value if debug_available else meta_token.balanceOf(bob)

    zap_has_zero_amounts()

    assert alice.balance() == initial_balance - amounts_underlying[weth_idx]

    assert meta_token.balanceOf(bob) == lp_received > 0
    assert abs(lp_received - calculated) <= 10 ** meta_token.decimals()


def test_one_coin_use_eth(
    zap,
    meta_swap,
    meta_token,
    base_token,
    underlying_coins,
    amounts_underlying,
    alice,
    bob,
    balances_do_not_change,
    zap_has_zero_amounts,
    weth_idx,
    debug_available,
):
    initial_balance = alice.balance()
    amounts = [0] * len(amounts_underlying)
    amounts[weth_idx] = amounts_underlying[weth_idx]
    with balances_do_not_change(underlying_coins + [meta_token, base_token], alice):
        calculated = zap.calc_token_amount(meta_swap, amounts)
        tx = zap.add_liquidity(
            meta_swap,
            amounts,
            0.99 * calculated,
            True,
            bob,
            {"from": alice, "value": amounts[weth_idx]},
        )
        lp_received = tx.return_value if debug_available else meta_token.balanceOf(bob)

    zap_has_zero_amounts()

    assert alice.balance() == initial_balance - amounts[weth_idx]

    assert meta_token.balanceOf(bob) == lp_received > 0
    assert abs(lp_received - calculated) <= 10 ** meta_token.decimals()
