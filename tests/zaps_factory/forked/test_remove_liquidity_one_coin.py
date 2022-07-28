import pytest
from brownie import ETH_ADDRESS, chain


@pytest.mark.parametrize("use_eth", [False, True])
def test_remove_liquidity_one_coin(
    zap,
    weth,
    all_coins,
    coins_flat,
    meta_swap,
    meta_token,
    alice,
    bob,
    balances_do_not_change,
    debug_available,
    use_eth,
    zap_is_broke,
):
    indexes = [5 * j + i for j in range(len(all_coins)) for i in range(len(all_coins[j]))]
    for idx in indexes:
        initial_lp_balance = meta_token.balanceOf(alice)
        lp_amount = initial_lp_balance // 2
        initial_balances = {bob: bob.balance()}

        coin = all_coins[idx // 5][idx % 5]

        with balances_do_not_change(coins_flat + [ETH_ADDRESS], alice):
            calculated = zap.calc_withdraw_one_coin(meta_swap, lp_amount, idx)
            tx = zap.remove_liquidity_one_coin(
                meta_swap, lp_amount, idx, 0.99 * calculated, use_eth, bob, {"from": alice}
            )
            received = tx.return_value if debug_available else coin.balanceOf(bob)

        zap_is_broke()

        assert meta_token.balanceOf(alice) + lp_amount == initial_lp_balance

        if use_eth and coin == weth:
            assert bob.balance() == initial_balances[bob] + received
            assert coin.balanceOf(bob) == 0
        else:
            assert bob.balance() == initial_balances[bob]
            assert coin.balanceOf(bob) == received > 0
        assert abs(received - calculated) <= 10 ** coin.decimals()
        chain.undo()
