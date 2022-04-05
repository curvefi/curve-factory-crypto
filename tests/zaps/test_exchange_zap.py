import brownie
import pytest

pytestmark = pytest.mark.usefixtures("add_initial_liquidity", "approve_zap", "mint_bob_underlying")


@pytest.mark.parametrize("i", range(4))
@pytest.mark.parametrize("di", range(1, 4))
def test_exchange(
    zap,
    meta_swap,
    base_swap,
    base_token,
    i: int,
    di: int,
    underlying_coins,
    initial_amounts_underlying,
    bob,
    get_dy,
):
    j = (i + di) % 4
    dx = get_dy(1, i, 10 ** underlying_coins[1].decimals())
    dy = get_dy(i, j, dx)
    zap.exchange(meta_swap, i, j, dx, 0.9 * dy, {"from": bob})

    for coin in underlying_coins:
        assert coin.balanceOf(zap) == 0

    assert underlying_coins[i].balanceOf(bob) == initial_amounts_underlying[i] - dx
    assert 0.99 <= (underlying_coins[j].balanceOf(bob) - initial_amounts_underlying[j]) / dy <= 1


@pytest.mark.parametrize("i", range(4))
@pytest.mark.parametrize("di", range(1, 4))
def test_exchange_min_dy(
    zap, meta_swap, i: int, di: int, underlying_coins, initial_amounts_underlying, bob, get_dy
):
    j = (i + di) % 4
    dx = get_dy(1, i, 10 ** underlying_coins[1].decimals())
    min_dy = 1.1 * get_dy(i, j, dx)
    with brownie.reverts():
        zap.exchange(meta_swap, i, j, dx, min_dy, {"from": bob})


@pytest.mark.parametrize("i", range(4))
@pytest.mark.parametrize("di", range(1, 4))
def test_get_dy(
    zap,
    meta_swap,
    base_swap,
    base_token,
    i: int,
    di: int,
    underlying_coins,
    initial_amounts_underlying,
    bob,
    get_dy,
):
    j = (i + di) % 4
    dx = get_dy(1, i, 10 ** underlying_coins[1].decimals())
    calculated = zap.get_dy(meta_swap, i, j, dx)
    zap.exchange(meta_swap, i, j, dx, 0, {"from": bob})

    assert underlying_coins[j].balanceOf(bob) - initial_amounts_underlying[j] == calculated
