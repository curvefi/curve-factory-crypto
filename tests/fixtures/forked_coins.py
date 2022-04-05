import pytest
from brownie import ZERO_ADDRESS, Contract, interface
from brownie.convert import to_bytes
from brownie_tokens import MintableForkToken


class MintableForkTokenArbitrum(Contract):
    wrapped = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
    bridged_coins = [
        "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
        "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    ]
    lps = ["0x8e0b8c8bb9db49a46697f3a5bb8a308e744821d2"]

    def __init__(self, address):
        if address == self.wrapped:
            self.from_abi("WrappedETH", address, interface.WETH.abi)
        elif address in self.bridged_coins:
            self.from_abi("BridgedERC20", address, interface.ArbitrumERC20.abi)
        elif address in self.lps:
            self.from_abi("CurveLPToken", address, interface.CurveTokenV5.abi)
        else:
            self.from_explorer(address)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:
            # Wrapped Avax, send from Sushiswap
            self.transfer(target, amount, {"from": "0x0c1cf6883efa1b496b01f654e247b9b419873054"})
        elif hasattr(self, "bridgeMint"):
            # Bridged token
            self.bridgeMint(target, amount, {"from": self.l2Gateway()})
        elif hasattr(self, "mint") and hasattr(self, "owner"):
            # Curve LP Token
            self.mint(target, amount, {"from": self.owner()})
        else:
            raise ValueError("Unsupported Token")


class MintableForkTokenAvalanche(Contract):
    wrapped = "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7"
    anyswap_coins = [
        "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70",
        "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664",
        "0xc7198437980c041c805A1EDcbA50c1Ce5db95118",
        "0x50b7545627a5162F82A992c33b87aDc75187B218",
        "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",
    ]
    lps = ["0x1daB6560494B04473A0BE3E7D83CF3Fdf3a51828"]

    def __init__(self, address):
        if address == self.wrapped:
            self.from_abi("WrappedAvax", address, interface.WETH.abi)
        elif address in self.anyswap_coins:
            self.from_abi("BridgedERC20", address, interface.AvalancheERC20.abi)
        elif address in self.lps:
            self.from_abi("CurveLPToken", address, interface.CurveTokenV5.abi)
        else:
            self.from_explorer(address)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:
            # Wrapped Avax, send from Iron Bank
            self.transfer(target, amount, {"from": "0xb3c68d69e95b095ab4b33b4cb67dbc0fbf3edf56"})
        elif hasattr(self, "mint") and not hasattr(self, "owner"):
            # Bridged token
            self.mint(
                target,
                amount,
                ZERO_ADDRESS,
                0,
                0x0,
                {"from": "0x50Ff3B278fCC70ec7A9465063d68029AB460eA04"},
            )
        elif hasattr(self, "mint"):
            # Curve LP Token
            self.mint(target, amount, {"from": self.owner()})
        else:
            raise ValueError("Unsupported Token")


class MintableForkTokenFantom(Contract):
    wrapped = "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83"
    anyswap_coins = [
        "0x049d68029688eAbF473097a2fC38ef61633A3C7A",
        "0x321162Cd933E2Be498Cd2267a90534A804051b11",
        "0x74b23882a30290451A17c44f4F05243b6b58C76d",
    ]
    lps = ["0x58e57cA18B7A47112b877E31929798Cd3D703b0f"]

    def __init__(self, address):
        if address == self.wrapped:
            self.from_abi("WrappedFantom", address, interface.WETH.abi)
        elif address in self.anyswap_coins:
            self.from_abi("AnyswapERC20", address, interface.AnyswapERC20.abi)
        elif address in self.lps:
            self.from_abi("CurveLPToken", address, interface.CurveTokenV5.abi)
        else:
            self.from_explorer(address)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:
            # Wrapped Fantom, send from SpookySwap
            self.transfer(target, amount, {"from": "0x2a651563c9d3af67ae0388a5c8f89b867038089e"})
        elif hasattr(self, "Swapin"):
            # Anyswap
            tx_hash = to_bytes("0x4475636b204475636b20476f6f7365")
            self.Swapin(tx_hash, target, amount, {"from": self.owner()})
        elif hasattr(self, "mint") and hasattr(self, "owner"):
            # Curve LP Token
            self.mint(target, amount, {"from": self.owner()})
        else:
            raise ValueError("Unsupported Token")


class MintableForkTokenPolygon(Contract):
    wrapped = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
    bridged_coins = [
        "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
        "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
        "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    ]
    lps = ["0xdAD97F7713Ae9437fa9249920eC8507e5FbB23d3"]

    def __init__(self, address):
        if address == self.wrapped:
            self.from_abi("WrappedMatic", address, interface.WETH.abi)
        elif address in self.bridged_coins:
            self.from_abi("PolygonERC20", address, interface.PolygonERC20.abi)
        elif address in self.lps:
            self.from_abi("CurveLPToken", address, interface.CurveTokenV5.abi)
        else:
            self.from_explorer(address)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:
            # Wrapped Matic, send from amWMATIC
            self.transfer(target, amount, {"from": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"})
        elif hasattr(self, "getRoleMember"):
            # POS bridge ERC20
            role = "0x8f4f2da22e8ac8f11e15f9fc141cddbb5deea8800186560abb6e68c5496619a9"
            minter = self.getRoleMember(role, 0)
            amount = to_bytes(amount, "bytes32")
            self.deposit(target, amount, {"from": minter})
        elif hasattr(self, "mint"):
            self.mint(target, amount, {"from": self.owner()})
        else:
            raise ValueError("Unsupported Token")


class MintableForkTokenHarmony(Contract):
    wrapped = "0xcF664087a5bB0237a0BAd6742852ec6c8d69A27a"
    bridged_coins = [
        "0xEf977d2f931C1978Db5F6747666fa1eACB0d0339",
        "0x985458e523db3d53125813ed68c274899e9dfab4",
        "0x3c2b8be99c50593081eaa2a724f0b8285f5aba8f",
        "0x3095c7557bcb296ccc6e363de01b760ba031f2d9",
        "0x6983d1e6def3690c4d616b13597a09e6193ea013",
    ]
    lps = ["0x99E8eD28B97c7F1878776eD94fFC77CABFB9B726"]

    def __init__(self, address):
        if address == self.wrapped:
            self.from_abi("WrappedOne", address, interface.WETH.abi)
        elif address in self.bridged_coins:
            self.from_abi("BridgedERC20", address, interface.HarmonyERC20.abi)
        elif address in self.lps:
            self.from_abi("CurveLPToken", address, interface.CurveTokenV5.abi)
        else:
            self.from_explorer(address)

        super().__init__(address)

    def _mint_for_testing(self, target, amount, kwargs=None):
        if self.address == self.wrapped:
            # Wrapped One, send from Sushiswap
            self.transfer(target, amount, {"from": "0xeb049f1ed546f8efc3ad57f6c7d22f081ccc7375"})
        elif hasattr(self, "mint") and not hasattr(self, "owner"):
            # ETH <-> ONE Bridged ERC20
            minter = "0xbadb6897cf2e35aca73b6f37361a35eeb6f71637"
            self.mint(target, amount, {"from": minter})
        elif hasattr(self, "mint"):
            self.mint(target, amount, {"from": self.owner()})
        else:
            raise ValueError("Unsupported Token")


fork_tokens = {
    "mainnet": MintableForkToken,
    "arbitrum": MintableForkTokenArbitrum,
    "avalanche": MintableForkTokenAvalanche,
    "polygon": MintableForkTokenPolygon,
    "fantom": MintableForkTokenFantom,
    "harmony": MintableForkTokenHarmony,
}


@pytest.fixture(scope="session")
def mintable_fork_token(request):
    if not hasattr(request, "param"):
        return MintableForkToken
    return fork_tokens.get(request.param)
