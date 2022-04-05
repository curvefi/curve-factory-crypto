import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap")


@pytest.mark.parametrize("i", range(4))
@pytest.mark.parametrize("di", range(1, 4))
def test_exchange(
    bob,
    zap,
    meta_swap,
    underlying_coins,
    initial_amounts_underlying,
    i: int,
    di: int,
    mint_bob_underlying,
):
    j = (i + di) % 4
    dx = 10 ** underlying_coins[i].decimals()
    tx = zap.exchange(meta_swap, i, j, dx, 0, {"from": bob})

    assert underlying_coins[j].balanceOf(bob) - initial_amounts_underlying[j] == tx.return_value


def test_remove_liquidity(alice, bob, zap, meta_swap, meta_token, underlying_coins):
    amount = meta_token.balanceOf(alice)
    meta_token.transfer(bob, amount, {"from": alice})
    tx = zap.remove_liquidity(meta_swap, amount // 3, [0, 0, 0, 0], {"from": bob})
    for coin, expected_amount in zip(underlying_coins, tx.return_value):
        assert coin.balanceOf(bob) == expected_amount


@pytest.mark.parametrize("idx", range(4))
def test_remove_one(alice, bob, zap, underlying_coins, coins, meta_swap, meta_token, idx):
    meta_token.transfer(bob, meta_token.balanceOf(alice), {"from": alice})
    tx = zap.remove_liquidity_one_coin(meta_swap, 10 ** 18, idx, 0, {"from": bob})

    assert tx.return_value == underlying_coins[idx].balanceOf(bob)


def test_add_liquidity(
    bob, zap, initial_amounts_underlying, meta_swap, meta_token, mint_bob_underlying
):
    tx = zap.add_liquidity(meta_swap, initial_amounts_underlying, 0, {"from": bob})
    assert meta_token.balanceOf(bob) == tx.return_value
