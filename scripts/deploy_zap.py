import json
from brownie import (
    ZapETH,
    ZapETHZap,
    accounts,
    network,
)
from brownie.project.main import get_loaded_projects


def main(deployed_data: str):
    deployer = accounts.load("curve")
    txparams = {"from": deployer}
    if "fork" not in network.show_active():
        txparams.update({"required_confs": 5})

    project = get_loaded_projects()[0]
    with open(
            f"{project._path}/contracts/testing/tricrypto/data/{deployed_data}.json", "r"
    ) as f:
        data = json.load(f)

    base_swap = data["swap"]
    base_token = data["token"]
    base_coins = data["coins"]
    weth = data["weth"]

    contract = ZapETH if len(base_coins) == 3 else ZapETHZap
    zap = contract.deploy(base_swap, base_token, weth, base_coins, txparams)
