import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "mint_bob_underlying", "approve_zap")


def test_lp_token_balances(
    bob, zap, base_swap, base_token, base_coins, meta_swap, meta_token, initial_amounts_underlying
):
    initial_supply = meta_token.totalSupply()
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    assert meta_token.balanceOf(bob) > 0
    assert 0.9999 < (meta_token.totalSupply() / 2) / initial_supply <= 1


def test_underlying_balances(
    bob, zap, meta_swap, underlying_coins, coins, initial_amounts_underlying
):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(underlying_coins, initial_amounts_underlying):
        assert coin.balanceOf(zap) == 0
        if coin in coins:
            assert coin.balanceOf(meta_swap) == amount * 2
        else:
            assert coin.balanceOf(meta_swap) == 0


def test_wrapped_balances(bob, zap, meta_swap, coins, initial_amounts_underlying, initial_amounts):
    zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})

    for coin, amount in zip(coins, initial_amounts):
        assert coin.balanceOf(zap) == 0
        assert 0.9999 < coin.balanceOf(meta_swap) / (amount * 2) <= 1


@pytest.mark.parametrize("idx", range(4))
@pytest.mark.parametrize("mod", [0.95, 1.05])
def test_slippage(
    bob, meta_swap, meta_token, zap, underlying_coins, coins, initial_amounts_underlying, idx, mod
):
    amounts = [i // 10 ** 6 for i in initial_amounts_underlying]
    amounts[idx] = int(amounts[idx] * mod)

    zap.add_liquidity(meta_swap, amounts, 0, {"from": bob})

    for coin in underlying_coins + coins:
        assert coin.balanceOf(zap) == 0

    assert meta_token.balanceOf(zap) == 0


@pytest.mark.parametrize("idx", range(4))
def test_add_one_coin(bob, meta_swap, meta_token, zap, underlying_coins, coins, idx, get_dy):
    amounts = [0] * len(underlying_coins)
    amounts[idx] = get_dy(1, idx, 10 ** underlying_coins[1].decimals())
    zap.add_liquidity(meta_swap, amounts, 0, {"from": bob})

    for coin in underlying_coins + [meta_token]:
        assert coin.balanceOf(zap) == 0

    assert 0 < meta_token.balanceOf(bob) / 10 ** 18 < 1


def test_insufficient_balance(charlie, meta_swap, zap, underlying_coins):
    amounts = [(10 ** coin.decimals()) for coin in underlying_coins]
    with brownie.reverts():
        zap.add_liquidity(meta_swap, amounts, 0, {"from": charlie})


@pytest.mark.parametrize("min_amount", [False, True])
def test_min_amount_too_high(alice, meta_swap, zap, initial_amounts_underlying, min_amount):
    amounts = [i // 10 ** 6 for i in initial_amounts_underlying]
    min_amount = 2 * 10 ** 18 + 1 if min_amount else 2 ** 256 - 1
    with brownie.reverts():
        zap.add_liquidity(meta_swap, amounts, min_amount, {"from": alice})


def test_min_amount_with_slippage(bob, meta_swap, zap, initial_amounts_underlying):
    amounts = [i // 10 ** 6 for i in initial_amounts_underlying]
    amounts[0] = int(amounts[0] * 0.99)
    amounts[1] = int(amounts[1] * 1.01)
    with brownie.reverts():
        zap.add_liquidity(meta_swap, amounts, 2 * 10 ** 18, {"from": bob})


def test_calc_token_amount(zap, meta_swap, meta_token, bob, initial_amounts_underlying):
    amounts = [
        amount // divisor
        for amount, divisor in zip(initial_amounts_underlying, [10, 50, 100, 1000])
    ]

    calculated = zap.calc_token_amount(meta_swap, amounts)
    zap.add_liquidity(meta_swap, amounts, 0, {"from": bob})

    assert meta_token.balanceOf(bob) == calculated
