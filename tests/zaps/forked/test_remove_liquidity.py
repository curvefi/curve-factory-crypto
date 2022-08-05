from brownie import ETH_ADDRESS, ZERO_ADDRESS


def test_remove_liquidity(
    zap,
    base_token,
    meta_swap,
    meta_token,
    alice,
    bob,
    underlying_coins,
    balances_do_not_change,
    zap_has_zero_amounts,
    debug_available,
):
    lp_initial_amount = meta_token.balanceOf(alice)
    initial_balance = bob.balance()
    with balances_do_not_change(underlying_coins + [ETH_ADDRESS, base_token], alice):
        tx = zap.remove_liquidity(
            meta_swap,
            lp_initial_amount // 2,
            [0] * len(underlying_coins),
            False,
            bob,
            {"from": alice},
        )
        amounts_received = (
            tx.return_value
            if debug_available
            else [coin.balanceOf(bob) for coin in underlying_coins]
        )

    zap_has_zero_amounts()

    for coin, amount in zip(underlying_coins, amounts_received):
        if coin == ZERO_ADDRESS:
            assert amount == 0
        else:
            assert coin.balanceOf(bob) == amount > 0
    assert bob.balance() - initial_balance == 0


def test_remove_liquidity_use_eth(
    zap,
    base_token,
    meta_swap,
    meta_token,
    alice,
    bob,
    underlying_coins,
    balances_do_not_change,
    zap_has_zero_amounts,
    weth_idx,
    debug_available,
):
    lp_initial_amount = meta_token.balanceOf(alice)
    initial_balance = bob.balance()
    with balances_do_not_change(underlying_coins + [ETH_ADDRESS, base_token], alice):
        tx = zap.remove_liquidity(
            meta_swap,
            lp_initial_amount // 2,
            [0] * len(underlying_coins),
            True,
            bob,
            {"from": alice},
        )
        if debug_available:
            amounts_received = tx.return_value
        else:
            amounts_received = [coin.balanceOf(bob) for coin in underlying_coins]
            amounts_received[weth_idx] = bob.balance() - initial_balance

    zap_has_zero_amounts()

    for i, (coin, amount) in enumerate(zip(underlying_coins, amounts_received)):
        if coin == ZERO_ADDRESS:
            assert amount == 0
        elif i == weth_idx:
            assert coin.balanceOf(bob) == 0
        else:
            assert coin.balanceOf(bob) == amount > 0
    assert bob.balance() - initial_balance == amounts_received[weth_idx] > 0
