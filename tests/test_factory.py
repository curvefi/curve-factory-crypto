import brownie
import pytest
from brownie import network


def test_find_pool(factory, crypto_swap, coins):
    assert factory.find_pool_for_coins(*coins) == crypto_swap.address
    assert factory.find_pool_for_coins(*coins[::-1]) == crypto_swap.address


def test_get_coins(factory, crypto_swap):
    coins = [crypto_swap.coins(0), crypto_swap.coins(1)]
    assert factory.get_coins(crypto_swap) == coins


def test_get_decimals(factory, crypto_swap, coins):
    assert factory.get_decimals(crypto_swap) == [c.decimals() for c in coins]


def test_get_balances(factory, crypto_swap, coins):
    assert factory.get_balances(crypto_swap) == [crypto_swap.balances(i) for i in [0, 1]]


def test_get_coin_indices(factory, crypto_swap, coins):
    assert factory.get_coin_indices(crypto_swap, *coins) == [0, 1]
    assert factory.get_coin_indices(crypto_swap, *coins[::-1]) == [1, 0]


def test_add_gauge(factory, crypto_swap, accounts, LiquidityGauge):
    if 'fork' not in network.show_active():
        pytest.skip('Only for forkmode')
    assert factory.get_gauge(crypto_swap) == "0x0000000000000000000000000000000000000000"
    factory.deploy_gauge(crypto_swap, {'from': accounts[0]})
    gauge = LiquidityGauge.at(factory.get_gauge(crypto_swap))
    assert gauge.lp_token() == crypto_swap.token()


def test_get_eth_index(factory, crypto_swap):
    assert factory.get_eth_index(crypto_swap) == 2**256 - 1


def test_get_token(factory, crypto_swap):
    assert factory.get_token(crypto_swap) == crypto_swap.token()


def test_admin(factory, crypto_swap, accounts):
    crypto_swap.revert_new_parameters({'from': accounts[0]})
    with brownie.reverts():
        crypto_swap.revert_new_parameters({'from': accounts[1]})
