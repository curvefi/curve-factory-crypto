import pytest
from brownie import ETH_ADDRESS, chain


@pytest.mark.parametrize("use_eth", [False, True])
def test_remove_liquidity(
    zap,
    weth,
    all_coins,
    coins_flat,
    default_amount,
    default_amounts,
    meta_swap,
    meta_token,
    alice,
    bob,
    balances_do_not_change,
    debug_available,
    use_eth,
    zap_is_broke,
):
    use_coins_variations = ["meta"] + (
        ["underlying"] if len(all_coins[0] + all_coins[1]) > 2 else []
    )
    for use_coins in use_coins_variations:
        lp_initial_amount = meta_token.balanceOf(alice)
        initial_balance = bob.balance()

        if use_coins == "underlying":
            min_amounts = [[amount // 5 for amount in amounts] for amounts in default_amounts]
        else:
            min_amounts = [
                [len(all_coins[i]) * default_amount * 10**18 // 10] + [0] * 4
                for i in range(len(all_coins))
            ]

        with balances_do_not_change(coins_flat + [ETH_ADDRESS], alice):
            tx = zap.remove_liquidity(
                meta_swap,
                lp_initial_amount // 2,
                min_amounts,
                use_eth,
                bob,
                {"from": alice},
            )
            if debug_available:
                amounts_received = tx.return_value
            else:
                raise NotImplementedError

        zap_is_broke()

        for i, amounts in enumerate(amounts_received):
            for j, amount in enumerate(amounts):
                if j >= len(all_coins[i]):
                    assert amount == 0, "Received coin that should not be sent"
                else:
                    if min_amounts[i][j] == 0:
                        assert amount == 0, "Received coin that should not be sent"
                    else:
                        assert amount >= min_amounts[i][j], "Received less than expected"

                    coin = all_coins[i][j]
                    if coin == weth and use_eth:
                        assert (
                            bob.balance() - initial_balance == amount
                        ), "Probably received WETH instead of raw ETH"
                        assert coin.balanceOf(bob) == 0, "Received WETH instead of raw ETH"
                        continue
                    assert coin.balanceOf(bob) == amount, "Received incorrect amount of coin"
        if weth not in coins_flat:
            assert bob.balance() == initial_balance

        chain.undo()
