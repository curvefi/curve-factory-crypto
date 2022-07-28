import itertools

import brownie
import pytest
from brownie import chain


@pytest.mark.parametrize("use_eth", [False, True])
def test_exchange(
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
    for i, j in itertools.combinations(indexes, 2):
        initial_balances = {alice: alice.balance(), bob: bob.balance()}
        coin_i = all_coins[i // 5][i % 5]
        coin_j = all_coins[j // 5][j % 5]
        dx = coin_i.balanceOf(alice)
        send_eth = use_eth and coin_i == weth

        with balances_do_not_change(
            [meta_token] + [coin for coin in coins_flat if coin != coin_i], alice
        ):
            calculated = zap.get_dy(meta_swap, i, j, dx)
            tx = zap.exchange(
                meta_swap,
                i,
                j,
                dx,
                0.99 * calculated,
                use_eth,
                bob,
                {"from": alice, "value": dx if send_eth else 0},
            )
            received = tx.return_value if debug_available else all_coins[j].balanceOf(bob)

        zap_is_broke()

        # Check Alice's balances
        if use_eth and coin_i == weth:
            assert initial_balances[alice] - alice.balance() == dx > 0
        else:
            assert initial_balances[alice] == alice.balance()
            assert coin_i.balanceOf(alice) == 0

        # Check Bob's balances
        assert coin_i.balanceOf(bob) == 0
        if use_eth and coin_j == weth:
            assert bob.balance() - initial_balances[bob] == received > 0
        else:
            assert bob.balance() == initial_balances[bob]
            assert coin_j.balanceOf(bob) == received
        assert abs(received - calculated) <= 10 ** coin_j.decimals()

        chain.undo()


@pytest.mark.parametrize("use_eth", [False, True])
def test_bad_values(
    zap,
    weth,
    all_coins,
    meta_swap,
    alice,
    bob,
    use_eth,
):
    indexes = [5 * j + i for j in range(len(all_coins)) for i in range(len(all_coins[j]))]
    for i, j in itertools.combinations(indexes, 2):
        coin_i = all_coins[i // 5][i % 5]
        dx = coin_i.balanceOf(alice)
        send_eth = use_eth and coin_i == weth

        with brownie.reverts():  # invalid ETH amount
            zap.exchange(
                meta_swap,
                i,
                j,
                dx,
                0,
                use_eth,
                bob,
                {"from": alice, "value": dx if not send_eth else 0},
            )

        with brownie.reverts():  # slippage
            calculated = zap.get_dy(meta_swap, i, j, dx)
            zap.exchange(
                meta_swap,
                i,
                j,
                dx,
                1.01 * calculated,
                use_eth,
                bob,
                {"from": alice, "value": dx if send_eth else 0},
            )
