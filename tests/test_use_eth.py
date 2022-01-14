import brownie
import pytest
from brownie.test import given, strategy

INITIAL_PRICES = [int(0.001 * 10 ** 18)]  # CRV/ETH


# Fixtures
@pytest.fixture(scope="module", autouse=True)
def coins(ERC20Mock, accounts, weth):
    yield [weth] + [ERC20Mock.deploy("CRV", "CRV", 18, {"from": accounts[0]})]


@pytest.fixture(scope="module", autouse=True)
def crypto_swap(CurveCryptoSwap2ETH, factory, coins, accounts):
    factory.deploy_pool(
        "EUR/USD",
        "EURUSD",
        coins,
        90 * 2 ** 2 * 10000,  # A
        int(2.8e-4 * 1e18),  # gamma
        int(5e-4 * 1e10),  # mid_fee
        int(4e-3 * 1e10),  # out_fee
        10 ** 10,  # allowed_extra_profit
        int(0.012 * 1e18),  # fee_gamma
        int(0.55e-5 * 1e18),  # adjustment_step
        0,  # admin_fee
        600,  # ma_half_time
        INITIAL_PRICES[0],
        {"from": accounts[0]},
    )
    return CurveCryptoSwap2ETH.at(factory.pool_list(factory.pool_count() - 1))


def _crypto_swap_with_deposit(crypto_swap, coins, accounts):
    user = accounts[1]
    quantities = [50 * 10 ** 36 // p for p in [10 ** 18] + INITIAL_PRICES]
    coins[0].deposit({"from": user, "value": quantities[0]})
    coins[0].approve(crypto_swap, 2 ** 256 - 1, {"from": user})
    coins[1]._mint_for_testing(user, quantities[1])
    coins[1].approve(crypto_swap, 2 ** 256 - 1, {"from": user})

    # Very first deposit
    crypto_swap.add_liquidity(quantities, 0, {"from": user})

    return crypto_swap


@pytest.fixture(scope="module")
def swap(crypto_swap, coins, accounts):
    return _crypto_swap_with_deposit(crypto_swap, coins, accounts)


# End fixtures


@given(amount=strategy("uint256", min_value=10 ** 6, max_value=10 ** 18))
def test_exchange_eth_in(swap, amount, coins, accounts):
    user = accounts[1]

    assert coins[1].balanceOf(user) == 0
    b0 = swap.balances(0)
    swap.exchange(0, 1, amount, 0, True, {"value": amount, "from": user})
    assert coins[1].balanceOf(user) > 0
    assert swap.balances(0) - b0 == amount

    b0 = swap.balances(0)
    b1 = swap.balances(1)
    old_balance = coins[1].balanceOf(user)
    swap.exchange_underlying(0, 1, amount, 0, {"value": amount, "from": user})
    assert swap.balances(0) - b0 == amount
    assert b1 - swap.balances(1) > 0
    assert b1 - swap.balances(1) == coins[1].balanceOf(user) - old_balance


@given(amount=strategy("uint256", min_value=1000 * 10 ** 6, max_value=10 * 10 ** 18))
def test_exchange_eth_out(swap, amount, coins, accounts):
    user = accounts[1]

    old_balance = accounts[1].balance()
    b0 = swap.balances(0)
    b1 = swap.balances(1)
    coins[1]._mint_for_testing(user, amount)
    swap.exchange(1, 0, amount, 0, True, {"from": user})
    assert accounts[1].balance() - old_balance > 0
    assert accounts[1].balance() - old_balance == b0 - swap.balances(0)
    assert swap.balances(1) - b1 == amount

    old_balance = accounts[1].balance()
    b0 = swap.balances(0)
    b1 = swap.balances(1)
    coins[1]._mint_for_testing(user, amount)
    swap.exchange_underlying(1, 0, amount, 0, {"from": user})
    assert accounts[1].balance() - old_balance > 0
    assert accounts[1].balance() - old_balance == b0 - swap.balances(0)
    assert swap.balances(1) - b1 == amount


@given(
    amount=strategy("uint256", min_value=1000 * 10 ** 6, max_value=10 * 10 ** 18),
    i=strategy("int8", min_value=0, max_value=1),
)
def test_exchange_weth(swap, coins, accounts, amount, i):
    user = accounts[1]

    old_balance = coins[1 - i].balanceOf(user)
    b0 = swap.balances(i)
    b1 = swap.balances(1 - i)
    if i == 1:
        coins[1]._mint_for_testing(user, amount)
    else:
        coins[0].deposit({"from": user, "value": amount})
    swap.exchange(i, 1 - i, amount, 0, {"from": user})
    assert coins[1 - i].balanceOf(user) - old_balance > 0
    assert coins[1 - i].balanceOf(user) - old_balance == b1 - swap.balances(1 - i)
    assert swap.balances(i) - b0 == amount


def test_exchange_fail_eth(swap, coins, accounts):
    user = accounts[1]
    coins[0].deposit({"from": user, "value": 10 ** 15})
    coins[1]._mint_for_testing(user, 10 ** 18)
    with brownie.reverts():
        swap.exchange(0, 1, 10 ** 15, 0, {"from": user, "value": 10 ** 15})
    with brownie.reverts():
        swap.exchange(1, 0, 10 ** 18, 0, {"from": user, "value": 10 ** 18})
    with brownie.reverts():
        swap.exchange_underlying(1, 0, 10 ** 18, 0, {"from": user, "value": 10 ** 18})


@given(
    amounts=strategy("uint256[2]", min_value=10 ** 10, max_value=10 ** 19), use_eth=strategy("bool")
)
def test_add_liquidity_eth(swap, coins, accounts, amounts, use_eth):
    user = accounts[1]
    amounts[1] = amounts[1] * 10 ** 18 // INITIAL_PRICES[0]

    coins[0].deposit({"from": user, "value": amounts[0]})
    coins[1]._mint_for_testing(user, amounts[1])

    initial_coin_balances = [c.balanceOf(user) for c in coins]
    initial_eth_balance = user.balance()

    if use_eth:
        with brownie.reverts():  # XXX 'dev: incorrect eth amount'
            swap.add_liquidity(amounts, 0, True, {"from": user})
        swap.add_liquidity(amounts, 0, True, {"from": user, "value": amounts[0]})

        assert coins[0].balanceOf(user) == initial_coin_balances[0]
        assert initial_eth_balance - user.balance() == amounts[0]

    else:
        with brownie.reverts():  # XXX 'dev: nonzero eth amount'
            swap.add_liquidity(amounts, 0, False, {"from": user, "value": amounts[0]})
        swap.add_liquidity(amounts, 0, False, {"from": user})

        assert initial_coin_balances[0] - coins[0].balanceOf(user) == amounts[0]
        assert initial_eth_balance == user.balance()

    assert initial_coin_balances[1] - coins[1].balanceOf(user) == amounts[1]


@given(frac=strategy("uint256", min_value=10 ** 10, max_value=10 ** 18), use_eth=strategy("bool"))
def test_remove_liquidity_eth(swap, token, coins, accounts, frac, use_eth):
    user = accounts[1]
    token_amount = token.balanceOf(user) * frac // 10 ** 18
    assert token_amount > 0

    initial_coin_balances = [c.balanceOf(user) for c in coins]
    initial_eth_balance = user.balance()
    to_remove = [swap.balances(i) * (token_amount - 1) // token.balanceOf(user) for i in range(2)]

    swap.remove_liquidity(token_amount, [0, 0], use_eth, {"from": user})

    assert coins[1].balanceOf(user) - initial_coin_balances[1] == to_remove[1]
    if use_eth:
        assert coins[0].balanceOf(user) == initial_coin_balances[0]
        assert user.balance() - initial_eth_balance == to_remove[0]
    else:
        assert user.balance() == initial_eth_balance
        assert coins[0].balanceOf(user) - initial_coin_balances[0] == to_remove[0]


@given(
    frac=strategy("uint256", min_value=10 ** 10, max_value=5 * 10 ** 17),
    i=strategy("uint8", min_value=0, max_value=1),
    use_eth=strategy("bool"),
)
def test_remove_liquidity_one_coin_eth(swap, token, coins, accounts, frac, i, use_eth):
    user = accounts[1]
    token_amount = token.balanceOf(user) * frac // 10 ** 18
    assert token_amount > 0

    initial_coin_balances = [c.balanceOf(user) for c in coins]
    initial_eth_balance = user.balance()

    swap.remove_liquidity_one_coin(token_amount, i, 0, use_eth, {"from": user})

    if i == 1 or not use_eth:
        assert coins[i].balanceOf(user) > initial_coin_balances[i]
        assert initial_eth_balance == user.balance()
    else:
        assert user.balance() > initial_eth_balance
        assert coins[i].balanceOf(user) == initial_coin_balances[i]
    assert coins[1 - i].balanceOf(user) == initial_coin_balances[1 - i]


def test_lp_price(swap, token):
    tvl = swap.balances(0) + swap.balances(1) * swap.price_scale() // 10 ** 18
    naive_price = tvl * 10 ** 18 // token.totalSupply()

    assert abs(swap.lp_price() / naive_price - 1) < 2e-3
