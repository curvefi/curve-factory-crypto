import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


@pytest.fixture(autouse=True)
def setup(add_initial_liquidity, approve_zap, alice, bob, meta_token):
    meta_token.transfer(bob, meta_token.balanceOf(alice), {"from": alice})


@pytest.mark.parametrize("divisor", [1, 23, 1337])
def test_lp_token_balances(bob, zap, meta_swap, meta_token, underlying_coins, divisor):
    initial_balance = meta_token.balanceOf(bob)
    withdraw_amount = initial_balance // divisor
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(meta_swap, withdraw_amount, min_amounts, {"from": bob})

    # bob is the only LP, total supply is affected in the same way as his balance
    assert meta_token.balanceOf(bob) == initial_balance - withdraw_amount
    assert meta_token.totalSupply() == initial_balance - withdraw_amount


@pytest.mark.parametrize("divisor", [1, 23, 1337])
def test_wrapped_balances(
    bob,
    meta_swap,
    meta_token,
    zap,
    underlying_coins,
    coins,
    initial_amounts,
    divisor,
):
    initial_balance = meta_token.balanceOf(bob)
    withdraw_amount = initial_balance // divisor
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(meta_swap, withdraw_amount, min_amounts, {"from": bob})

    for coin, initial in zip(coins, initial_amounts):
        assert coin.balanceOf(zap) == 0
        assert abs(coin.balanceOf(meta_swap) - (initial - (initial // divisor))) <= 100


@pytest.mark.parametrize("divisor", [1, 23, 1337])
def test_underlying_balances(
    bob,
    meta_swap,
    meta_token,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
    divisor,
):
    initial_balance = meta_token.balanceOf(bob)
    withdraw_amount = initial_balance // divisor
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(meta_swap, withdraw_amount, min_amounts, {"from": bob})

    for coin in underlying_coins[1:]:
        assert coin.balanceOf(zap) == 0
        assert coin.balanceOf(meta_swap) == 0
        assert coin.balanceOf(bob) > 0


@pytest.mark.parametrize("idx", range(4))
def test_below_min_amount(alice, meta_swap, meta_token, zap, initial_amounts_underlying, idx):
    min_amount = initial_amounts_underlying.copy()
    min_amount[idx] += 1

    amount = 2000000 * 10 ** 18
    with brownie.reverts():
        zap.remove_liquidity(meta_swap, amount, min_amount, {"from": alice})


def test_amount_exceeds_balance(alice, meta_swap, zap, underlying_coins):
    amount = (2000000 * 10 ** 18) + 1
    with brownie.reverts():
        zap.remove_liquidity(meta_swap, amount, [0, 0, 0, 0], {"from": alice})


def test_use_eth(
    bob,
    meta_swap,
    meta_token,
    zap,
    underlying_coins,
    coins,
    initial_amounts_underlying,
):
    initial_balance = meta_token.balanceOf(bob)
    withdraw_amount = initial_balance // 50
    min_amounts = [0] * len(underlying_coins)
    zap.remove_liquidity(meta_swap, withdraw_amount, min_amounts, True, {"from": bob})

    assert zap.balance() == 0
    for coin in underlying_coins[1:-1]:
        assert coin.balanceOf(zap) == 0
        assert coin.balanceOf(meta_swap) == 0
        assert coin.balanceOf(bob) > 0

    weth = underlying_coins[-1]
    assert weth.balanceOf(zap) == 0
    assert weth.balanceOf(meta_swap) == 0
    assert weth.balanceOf(bob) == 0
    assert bob.balance() > 0
