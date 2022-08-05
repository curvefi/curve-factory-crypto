import brownie
import pytest
from brownie import chain


def get_amounts(use_coins, default_amounts, all_coins, alice):
    if use_coins == "underlying":
        amounts = default_amounts
    elif use_coins == "all":
        amounts = [
            [
                all_coins[i][j].balanceOf(alice) if j < len(all_coins[i]) else 0
                for j in range(len(default_amounts[i]))
            ]
            for i in range(len(default_amounts))
        ]
    else:
        amounts = [
            [all_coins[i][0].balanceOf(alice)] + [0] * 4 for i in range(len(default_amounts))
        ]
    return amounts


def get_send_eth(amounts, all_coins, weth, use_eth):
    if use_eth:
        for i in range(len(amounts)):
            if (sum(amounts[i][1:]) > 0 and weth in all_coins[i][1:]) or (
                amounts[i][0] > 0 and weth == all_coins[i][0]
            ):
                return True
    return False


@pytest.mark.parametrize("use_eth", [False, True])
def test_multiple_coins(
    zap,
    weth,
    all_coins,
    meta_swap,
    meta_token,
    alice,
    bob,
    balances_do_not_change,
    debug_available,
    default_amount,
    default_amounts,
    use_eth,
    zap_is_broke,
):
    use_coins_variations = ["meta"] + (
        ["underlying", "all"] if len(all_coins[0] + all_coins[1]) > 2 else []
    )
    for use_coins in use_coins_variations:
        amounts = get_amounts(use_coins, default_amounts, all_coins, alice)
        send_eth = get_send_eth(amounts, all_coins, weth, use_eth)

        with balances_do_not_change([meta_token], alice):
            calculated = zap.calc_token_amount(meta_swap, amounts)
            tx = zap.add_liquidity(
                meta_swap,
                amounts,
                0.99 * calculated,
                use_eth,
                bob,
                {"from": alice, "value": default_amount * 10**18 if send_eth else 0},
            )
            lp_received = tx.return_value if debug_available else meta_token.balanceOf(bob)

        zap_is_broke()
        for i in range(len(amounts)):
            for j in range(len(amounts[i])):
                if amounts[i][j] > 0 and not (all_coins[i][j] == weth and use_eth):
                    assert all_coins[i][j].balanceOf(alice) == 0

        assert meta_token.balanceOf(bob) == lp_received > 0
        assert abs(lp_received - calculated) <= 10 ** meta_token.decimals()

        chain.undo()


@pytest.mark.parametrize("use_eth", [False, True])
def test_bad_arguments(
    zap,
    weth,
    all_coins,
    meta_swap,
    alice,
    bob,
    default_amount,
    default_amounts,
    use_eth,
):
    use_coins_variations = ["meta"] + (
        ["underlying", "all"] if len(all_coins[0] + all_coins[1]) > 2 else []
    )
    for use_coins in use_coins_variations:
        amounts = get_amounts(use_coins, default_amounts, all_coins, alice)
        send_eth = get_send_eth(amounts, all_coins, weth, use_eth)

        # Currently can receive ETH
        # with brownie.reverts():  # incorrect ETH amount
        #     zap.add_liquidity(
        #         meta_swap, amounts, 0, use_eth, bob, {"from": alice, "value": default_amount * 10 ** 18 if not send_eth else 0}
        #     )

        with brownie.reverts():  # slippage
            calculated = zap.calc_token_amount(meta_swap, amounts)
            zap.add_liquidity(
                meta_swap,
                amounts,
                1.01 * calculated,
                use_eth,
                bob,
                {"from": alice, "value": default_amount * 10**18 if send_eth else 0},
            )
