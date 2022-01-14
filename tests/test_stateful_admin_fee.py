from math import log

from brownie.test import strategy

from .stateful_base import StatefulBase

MAX_SAMPLES = 20
STEP_COUNT = 100
NO_CHANGE = 2 ** 256 - 1


def approx(x1, x2, precision):
    return abs(log(x1 / x2)) <= precision


class StatefulAdmin(StatefulBase):
    exchange_amount_in = strategy("uint256", min_value=10 ** 17, max_value=10 ** 5 * 10 ** 18)

    def setup(self):
        super().setup(user_id=1)
        admin = self.accounts[0]
        self.swap.commit_new_parameters(
            NO_CHANGE,
            NO_CHANGE,
            5 * 10 ** 9,  # admin fee
            NO_CHANGE,
            NO_CHANGE,
            NO_CHANGE,
            NO_CHANGE,
            {"from": admin},
        )
        self.chain.sleep(3 * 86400 + 1)
        self.swap.apply_new_parameters({"from": admin})
        assert self.swap.admin_fee() == 5 * 10 ** 9
        self.mid_fee = self.swap.mid_fee()
        self.out_fee = self.swap.out_fee()
        self.admin_fee = 5 * 10 ** 9

    def rule_exchange(self, exchange_amount_in, exchange_i, user):
        admin_balance = self.token.balanceOf(self.accounts[0])
        if exchange_i == 1:
            exchange_amount_in_converted = exchange_amount_in * 10 ** 18 // self.swap.price_oracle()
        else:
            exchange_amount_in_converted = exchange_amount_in
        super().rule_exchange(exchange_amount_in_converted, exchange_i, user)
        admin_balance = self.token.balanceOf(self.accounts[0]) - admin_balance
        self.total_supply += admin_balance
        if admin_balance > 0:
            self.xcp_profit = self.swap.xcp_profit()

    def rule_claim_admin_fees(self):
        balance = self.token.balanceOf(self.accounts[0])

        self.swap.claim_admin_fees({"from": self.accounts[0]})
        admin_balance = self.token.balanceOf(self.accounts[0])
        balance = admin_balance - balance
        self.total_supply += balance

        if balance > 0:
            self.xcp_profit = self.swap.xcp_profit()
            measured_profit = admin_balance / self.total_supply
            assert approx(measured_profit, log(self.xcp_profit / 1e18) / 2, 0.1)


def test_admin(crypto_swap, token, chain, accounts, coins, state_machine):
    from hypothesis._settings import HealthCheck

    state_machine(
        StatefulAdmin,
        chain,
        accounts,
        coins,
        crypto_swap,
        token,
        settings={
            "max_examples": MAX_SAMPLES,
            "stateful_step_count": STEP_COUNT,
            "suppress_health_check": HealthCheck.all(),
        },
    )
