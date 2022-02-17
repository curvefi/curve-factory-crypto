import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


@pytest.mark.parametrize("idx", range(4))
@pytest.mark.parametrize("divisor", [10, 50, 100])
def test_remove_one(
    alice,
    bob,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
    meta_swap,
    meta_token,
    idx,
    divisor,
):
    underlying = underlying_coins[idx]
    wrapped = coins[min(idx, 1)]

    initial_amount = meta_token.balanceOf(alice)
    amount = initial_amount // divisor

    meta_token.transfer(bob, initial_amount, {"from": alice})
    zap.remove_liquidity_one_coin(meta_swap, amount, idx, 0, {"from": bob})

    assert underlying.balanceOf(zap) == 0
    assert wrapped.balanceOf(zap) == 0
    assert meta_token.balanceOf(zap) == 0

    if wrapped != underlying:
        assert wrapped.balanceOf(bob) == 0

    assert meta_token.balanceOf(bob) == initial_amount - amount
    assert 0 < underlying.balanceOf(bob) <= 6 * initial_amounts_underlying[idx] // divisor


@pytest.mark.parametrize("idx", range(4))
def test_amount_exceeds_balance(bob, zap, meta_swap, idx):
    with brownie.reverts():
        zap.remove_liquidity_one_coin(meta_swap, 1, idx, 0, {"from": bob})


@pytest.mark.parametrize("idx", range(4))
def test_calc_withdraw_one_coin(alice, bob, zap, underlying_coins, meta_swap, meta_token, idx):
    lp_amount = meta_token.balanceOf(alice) // 5
    meta_token.transfer(bob, lp_amount, {"from": alice})

    calculated = zap.calc_withdraw_one_coin(meta_swap, lp_amount, idx)
    zap.remove_liquidity_one_coin(meta_swap, lp_amount, idx, 0, {"from": bob})

    assert underlying_coins[idx].balanceOf(bob) == calculated
