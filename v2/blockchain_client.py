import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict

from eth_utils import keccak
from web3 import Web3

DID_PATTERN = re.compile(r"^did:ethr:(0x[a-fA-F0-9]{40})$")


@dataclass
class ContractMetadata:
    address: str
    abi: Any
    chain_id: int


class SSIBlockchainClient:
    def __init__(
        self,
        rpc_url: str = "http://127.0.0.1:8545",
        contract_file: str = "blockchain_contract.json",
    ) -> None:
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError(f"No se pudo conectar al nodo Ethereum en {rpc_url}")

        self.meta = self._load_contract_metadata(contract_file)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.meta.address), abi=self.meta.abi
        )

        chain_id = self.w3.eth.chain_id
        if self.meta.chain_id and chain_id != self.meta.chain_id:
            raise RuntimeError(
                f"Chain ID no coincide. Nodo={chain_id} contrato={self.meta.chain_id}"
            )

    @staticmethod
    def _load_contract_metadata(contract_file: str) -> ContractMetadata:
        if not os.path.exists(contract_file):
            raise FileNotFoundError(
                f"No existe {contract_file}. Ejecuta deploy y bootstrap de Hardhat primero."
            )

        with open(contract_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ContractMetadata(
            address=data["address"],
            abi=data["abi"],
            chain_id=int(data.get("chainId", 0)),
        )

    @staticmethod
    def did_to_address(did: str) -> str:
        match = DID_PATTERN.match(did)
        if not match:
            raise ValueError(f"DID invalido: {did}")
        return Web3.to_checksum_address(match.group(1))

    @staticmethod
    def canonical_credential_hash(vc_without_proof: Dict[str, Any]) -> str:
        canonical = json.dumps(vc_without_proof, separators=(",", ":"), sort_keys=True)
        digest = keccak(text=canonical)
        return "0x" + digest.hex()

    def is_issuer_authorized(self, issuer_did: str) -> bool:
        issuer_address = self.did_to_address(issuer_did)
        return bool(self.contract.functions.isIssuerAuthorized(issuer_address).call())

    def is_did_active(self, holder_did: str) -> bool:
        holder_address = self.did_to_address(holder_did)
        return bool(self.contract.functions.isDidActive(holder_address).call())

    def is_credential_revoked(self, credential_hash: str) -> bool:
        return bool(self.contract.functions.isCredentialRevoked(credential_hash).call())

    def health(self) -> Dict[str, Any]:
        return {
            "connected": self.w3.is_connected(),
            "rpc_chain_id": self.w3.eth.chain_id,
            "contract_chain_id": self.meta.chain_id,
            "contract_address": self.meta.address,
        }
