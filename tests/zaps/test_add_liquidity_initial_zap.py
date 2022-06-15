import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_bob_underlying", "approve_zap")


def test_lp_token_balances(
    bob,
    zap,
    meta_swap,
    meta_token,
    initial_amounts_underlying,
    base_swap,
    base_token,
    underlying_coins,
    weth,
):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    assert meta_token.balanceOf(bob) > 0
    assert meta_token.totalSupply() == meta_token.balanceOf(bob)


def test_underlying_balances(
    bob, zap, meta_swap, underlying_coins, coins, weth, initial_amounts_underlying
):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        assert coin.balanceOf(zap) == 0
        balance = meta_swap.balance() if coin == weth else coin.balanceOf(meta_swap)
        if coin in coins:
            assert balance == amount
        else:
            assert balance == 0


def test_wrapped_balances(
    bob, zap, meta_swap, coins, weth, initial_amounts_underlying, initial_amounts
):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(coins, initial_amounts):
        assert coin.balanceOf(zap) == 0
        balance = meta_swap.balance() if coin == weth else coin.balanceOf(meta_swap)
        assert 0.9999 < balance / amount <= 1 + 1e-8


@pytest.mark.parametrize("idx", range(4))
def test_initial_liquidity_missing_coin(alice, zap, meta_swap, idx, underlying_coins):
    amounts = [10 ** coin.decimals() for coin in underlying_coins]
    amounts[idx] = 0

    with brownie.reverts():
        zap.add_liquidity(meta_swap, amounts, 0, {"from": alice})
