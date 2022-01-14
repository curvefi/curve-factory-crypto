from brownie import (
    CurveCryptoSwap2ETH,
    CurveTokenV5,
    Factory,
    LiquidityGauge,
    accounts,
    network,
)

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
FEE_RECEIVER = "0xeCb456EA5365865EbAb8a2661B0c503410e9B347"


def main():
    accounts.load("babe")
    txparams = {"from": accounts[0]}
    if network.show_active() == "mainnet":
        txparams.update({"required_confs": 5, "priority_fee": "2 gwei"})

    token = CurveTokenV5.deploy(txparams)
    pool = CurveCryptoSwap2ETH.deploy(WETH, txparams)
    gauge = LiquidityGauge.deploy(txparams)
    factory = Factory.deploy(FEE_RECEIVER, pool, token, gauge, WETH, txparams)

    print("Token template:", token.address)
    print("Pool template:", pool.address)
    print("Gauge template:", gauge.address)
    print("Factory template:", factory.address)
