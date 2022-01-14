import pytest  # noqa
from brownie.test import strategy

from .stateful_base import StatefulBase

MAX_SAMPLES = 60
STEP_COUNT = 30


class StatefulGas(StatefulBase):
    exchange_amount_in = strategy("uint256", min_value=10 * 10 ** 18, max_value=100 * 10 ** 18)
    deposit_amount = strategy("uint256", min_value=10 * 10 ** 18, max_value=100 * 10 ** 18)
    token_fraction = strategy("uint256", min_value=10 ** 14, max_value=5 * 10 ** 16)
    sleep_time = strategy("uint256", max_value=100)
    update_D = strategy("bool")

    def rule_exchange(self, exchange_amount_in, exchange_i, user):
        if exchange_i > 0:
            exchange_amount_in = exchange_amount_in * 10 ** 18 // self.swap.price_oracle()
        super().rule_exchange(exchange_amount_in, exchange_i, user)

    def rule_deposit(self, deposit_amount, exchange_i, user):
        amounts = [0] * 2
        if exchange_i > 0:
            amounts[exchange_i] = deposit_amount * 10 ** 18 // self.swap.price_oracle()
        else:
            amounts[exchange_i] = deposit_amount
        new_balances = [x + y for x, y in zip(self.balances, amounts)]

        self.coins[exchange_i]._mint_for_testing(user, deposit_amount)

        try:
            tokens = self.token.balanceOf(user)
            self.swap.add_liquidity(amounts, 0, {"from": user})
            tokens = self.token.balanceOf(user) - tokens
            self.total_supply += tokens
            self.balances = new_balances
        except Exception:
            if self.check_limits(amounts):
                raise

    def rule_remove_liquidity_one_coin(self, token_fraction, exchange_i, user, update_D):
        if update_D:
            self.swap.claim_admin_fees({"from": user})

        token_amount = token_fraction * self.total_supply // 10 ** 18
        d_token = self.token.balanceOf(user)
        if token_amount == 0 or token_amount > d_token:
            return

        try:
            calc_out_amount = self.swap.calc_withdraw_one_coin(token_amount, exchange_i)
        except Exception:
            if self.check_limits([0] * 2) and not (token_amount > self.total_supply):
                raise
            return

        d_balance = self.coins[exchange_i].balanceOf(user)
        try:
            self.swap.remove_liquidity_one_coin(token_amount, exchange_i, 0, {"from": user})
        except Exception:
            # Small amounts may fail with rounding errors
            if (
                calc_out_amount > 100
                and token_amount / self.total_supply > 1e-10
                and calc_out_amount / self.swap.balances(exchange_i) > 1e-10
            ):
                raise
            return

        d_balance = self.coins[exchange_i].balanceOf(user) - d_balance
        d_token = d_token - self.token.balanceOf(user)

        if update_D:
            assert (
                calc_out_amount == d_balance
            ), f"{calc_out_amount} vs {d_balance} for {token_amount}"

        self.balances[exchange_i] -= d_balance
        self.total_supply -= d_token

        # Virtual price resets if everything is withdrawn
        if self.total_supply == 0:
            self.virtual_price = 10 ** 18


@pytest.mark.skip()
def test_gas(crypto_swap, token, chain, accounts, coins, state_machine):
    from hypothesis._settings import HealthCheck

    state_machine(
        StatefulGas,
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
