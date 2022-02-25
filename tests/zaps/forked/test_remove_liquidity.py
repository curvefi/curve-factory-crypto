from brownie import ETH_ADDRESS


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
):
    lp_initial_amount = meta_token.balanceOf(alice)
    initial_balance = bob.balance()
    with balances_do_not_change(underlying_coins + [ETH_ADDRESS, base_token], alice):
        amounts_received = zap.remove_liquidity(
            meta_swap,
            lp_initial_amount // 2,
            [0] * len(underlying_coins),
            False,
            bob,
            {"from": alice},
        ).return_value

    zap_has_zero_amounts()

    for coin, amount in zip(underlying_coins, amounts_received):
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
):
    lp_initial_amount = meta_token.balanceOf(alice)
    initial_balance = bob.balance()
    with balances_do_not_change(underlying_coins + [ETH_ADDRESS, base_token], alice):
        amounts_received = zap.remove_liquidity(
            meta_swap,
            lp_initial_amount // 2,
            [0] * len(underlying_coins),
            True,
            bob,
            {"from": alice},
        ).return_value

    zap_has_zero_amounts()

    for i, (coin, amount) in enumerate(zip(underlying_coins, amounts_received)):
        if i == weth_idx:
            continue
        assert coin.balanceOf(bob) == amount > 0
    assert underlying_coins[weth_idx].balanceOf(bob) == 0
    assert bob.balance() - initial_balance == amounts_received[weth_idx] > 0
