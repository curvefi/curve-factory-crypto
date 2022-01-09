import pytest
from .test_stateful import NumbaGoUp
from .conftest import _crypto_swap_with_deposit

COINS = [
    ('USDC', 6),
    ('EURX', 17)]

INITIAL_PRICES = [int(1.2 * 10**18)]

MAX_SAMPLES = 20
MAX_COUNT = 20


# Fixtures
@pytest.fixture(scope="module", autouse=True)
def coins_mp(ERC20Mock, accounts):
    yield [ERC20Mock.deploy(name, name, decimals, {"from": accounts[0]})
           for name, decimals in COINS]


@pytest.fixture(scope="module", autouse=True)
def crypto_swap_mp(CurveCryptoSwap2ETH, factory, coins_mp, accounts):
    factory.deploy_pool(
        'EUR/USD',
        'EURUSD',
        coins_mp,
        90 * 2**2 * 10000,  # A
        int(2.8e-4 * 1e18),  # gamma
        int(5e-4 * 1e10),  # mid_fee
        int(4e-3 * 1e10),  # out_fee
        10**10,  # allowed_extra_profit
        int(0.012 * 1e18),  # fee_gamma
        int(0.55e-5 * 1e18),  # adjustment_step
        0,  # admin_fee
        600,  # ma_half_time
        INITIAL_PRICES[0],
        {'from': accounts[0]})
    return CurveCryptoSwap2ETH.at(factory.pool_list(factory.pool_count() - 1))


@pytest.fixture(scope="module", autouse=True)
def token_mp(CurveTokenV5, crypto_swap_mp):
    yield CurveTokenV5.at(crypto_swap_mp.token())


@pytest.fixture(scope="module")
def crypto_swap_with_deposit_mp(crypto_swap_mp, coins_mp, accounts):
    return _crypto_swap_with_deposit(crypto_swap_mp, coins_mp, accounts)


class Multiprecision(NumbaGoUp):
    def rule_exchange(self, exchange_amount_in, exchange_i, user):
        exchange_amount_in = exchange_amount_in // 10**(18-self.decimals[exchange_i])
        super().rule_exchange(exchange_amount_in, exchange_i, user)


def test_multiprecision(crypto_swap_mp, token_mp, chain, accounts, coins_mp, state_machine):
    from hypothesis._settings import HealthCheck

    state_machine(Multiprecision, chain, accounts, coins_mp, crypto_swap_mp, token_mp,
                  settings={'max_examples': MAX_SAMPLES, 'stateful_step_count': MAX_COUNT, 'suppress_health_check': HealthCheck.all()})
