import brownie
import pytest
from brownie import ETH_ADDRESS, ZERO_ADDRESS


def test_get_coins(zap, meta_swap, all_coins, weth):
    zap_coins = zap.get_coins(meta_swap)
    for base_coins_zap, base_coins in zip(zap_coins, all_coins):
        base_coins += [ZERO_ADDRESS] * (len(base_coins_zap) - len(base_coins))
        for coin, coin_zap in zip(base_coins, base_coins_zap):
            if coin_zap == ETH_ADDRESS:
                assert coin == weth, "Coins do not match"
            else:
                assert coin_zap == coin, "Coins do not match"


def test_coins(zap, meta_swap, all_coins, weth):
    for i in range(10):
        if i % 5 < len(all_coins[i // 5]) and all_coins[i // 5][i % 5] != ZERO_ADDRESS:
            real_coin = all_coins[i // 5][i % 5]
            zap_coin = zap.coins(meta_swap, i)
            if zap_coin == brownie.ETH_ADDRESS:
                zap_coin = weth
            assert zap_coin == real_coin, "Coins do not match"
        else:
            with brownie.reverts():
                zap.coins(meta_swap, i)


def test_price_oracle(zap, meta_swap, initial_price):
    _0_to_1 = int(zap.price_oracle(meta_swap))
    _1_to_0 = int(zap.price_oracle(meta_swap, False))
    assert _0_to_1 == pytest.approx(initial_price)
    assert _1_to_0 == pytest.approx(initial_price)
    assert _0_to_1 * _1_to_0 == pytest.approx(10 ** (2 * 18))


def test_price_scale(zap, meta_swap, initial_price):
    _0_to_1 = int(zap.price_scale(meta_swap))
    _1_to_0 = int(zap.price_scale(meta_swap, False))
    assert _0_to_1 == pytest.approx(initial_price)
    assert _1_to_0 == pytest.approx(initial_price)
    assert _0_to_1 * _1_to_0 == pytest.approx(10 ** (2 * 18))


def test_lp_price(zap, meta_swap):
    lp_price = int(zap.lp_price(meta_swap))
    lp_price_inverse = int(zap.lp_price(meta_swap, 1))
    assert lp_price == pytest.approx(2 * 10**18)
    assert lp_price * lp_price_inverse == pytest.approx((2 * 10**18) ** 2)
