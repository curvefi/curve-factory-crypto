import brownie
import pytest

pytestmark = pytest.mark.usefixtures("mint_bob_underlying", "approve_zap")


def test_lp_token_balances(bob, zap, meta_swap, meta_token, initial_amounts_underlying):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    assert meta_token.balanceOf(bob) > 0
    assert meta_token.totalSupply() == meta_token.balanceOf(bob)


def test_underlying_balances(
    bob, zap, meta_swap, underlying_coins, coins, initial_amounts_underlying
):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        assert coin.balanceOf(zap) == 0
        if coin in coins:
            assert coin.balanceOf(meta_swap) == amount
        else:
            assert coin.balanceOf(meta_swap) == 0


def test_wrapped_balances(bob, zap, meta_swap, coins, initial_amounts_underlying, initial_amounts):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(coins, initial_amounts):
        assert coin.balanceOf(zap) == 0
        assert 0.9999 < coin.balanceOf(meta_swap) / amount <= 1


@pytest.mark.parametrize("idx", range(4))
def test_initial_liquidity_missing_coin(alice, zap, meta_swap, idx, underlying_coins):
    amounts = [10 ** coin.decimals() for coin in underlying_coins]
    amounts[idx] = 0

    with brownie.reverts():
        zap.add_liquidity(meta_swap, amounts, 0, {"from": alice})
