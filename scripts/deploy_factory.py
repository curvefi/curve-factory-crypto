from brownie import (
    CurveCryptoSwap2ETH,
    CurveTokenV5,
    Factory,
    LiquidityGauge,
    accounts,
    ZERO_ADDRESS,
    network,
)

WETH = ZERO_ADDRESS
FEE_RECEIVER = "0xe8269B33E47761f552E1a3070119560d5fa8bBD6"


def main():
    dev = accounts.load("dev")
    txparams = {"from": dev, "priority_fee": "auto"}

    token = CurveTokenV5.deploy(txparams)
    pool = CurveCryptoSwap2ETH.deploy(WETH, txparams)
    gauge = ZERO_ADDRESS
    factory = Factory.deploy(FEE_RECEIVER, pool, token, gauge, WETH, txparams)

    print("Token template:", token.address)
    print("Pool template:", pool.address)
    # print("Gauge template:", gauge.address)
    print("Factory template:", factory.address)
