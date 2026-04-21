import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict

from eth_account import Account
from eth_utils import keccak
from web3 import Web3
from settings import SETTINGS

DID_PATTERN = re.compile(r"^did:ethr:(0x[a-fA-F0-9]{40})$")
HEX32_PATTERN = re.compile(r"^0x[a-fA-F0-9]{64}$")


@dataclass
class ContractMetadata:
    address: str
    abi: Any
    chain_id: int


class SSIBlockchainClient:
    def __init__(
        self,
        rpc_url: str | None = None,
        contract_file: str | None = None,
    ) -> None:
        rpc_url = rpc_url or SETTINGS.blockchain_rpc_url
        contract_file = contract_file or SETTINGS.contract_file
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
        self._validate_hex32(credential_hash, "credential_hash")
        return bool(self.contract.functions.isCredentialRevoked(credential_hash).call())

    @staticmethod
    def _validate_hex32(value: str, field_name: str) -> None:
        if not isinstance(value, str) or not HEX32_PATTERN.match(value):
            raise ValueError(f"{field_name} debe ser un hex bytes32 valido (0x + 64 hex)")

    @staticmethod
    def _zero_bytes32() -> str:
        return "0x" + ("00" * 32)

    @staticmethod
    def _hash_text_to_bytes32(text: str) -> str:
        if not text:
            return SSIBlockchainClient._zero_bytes32()
        digest = keccak(text=text)
        return "0x" + digest.hex()

    def _send_contract_tx(self, contract_fn: Any, sender_private_key: str = "") -> Dict[str, Any]:
        if sender_private_key:
            account = Account.from_key(sender_private_key)
            nonce = self.w3.eth.get_transaction_count(account.address)
            gas_price = self.w3.eth.gas_price
            tx = contract_fn.build_transaction(
                {
                    "from": account.address,
                    "nonce": nonce,
                    "chainId": self.w3.eth.chain_id,
                    "gas": 500000,
                    "gasPrice": gas_price,
                }
            )
            signed = self.w3.eth.account.sign_transaction(tx, private_key=sender_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            sender = account.address
        else:
            accounts = self.w3.eth.accounts
            if not accounts:
                raise RuntimeError("No hay cuentas desbloqueadas en el nodo para enviar transacciones")
            sender = Web3.to_checksum_address(accounts[0])
            tx_hash = contract_fn.transact({"from": sender})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return {
            "txHash": tx_hash.hex(),
            "blockNumber": int(receipt.blockNumber),
            "status": int(receipt.status),
            "sender": sender,
            "gasUsed": int(receipt.gasUsed),
        }

    def set_did_status(
        self,
        holder_did: str,
        active: bool,
        metadata_text: str = "",
        sender_private_key: str = "",
    ) -> Dict[str, Any]:
        holder_address = self.did_to_address(holder_did)
        metadata_hash = self._hash_text_to_bytes32(metadata_text)
        contract_fn = self.contract.functions.setDidStatus(holder_address, active, metadata_hash)
        return self._send_contract_tx(contract_fn, sender_private_key=sender_private_key)

    def register_credential(
        self,
        credential_hash: str,
        subject_did: str,
        sender_private_key: str = "",
    ) -> Dict[str, Any]:
        self._validate_hex32(credential_hash, "credential_hash")
        subject_address = self.did_to_address(subject_did)
        contract_fn = self.contract.functions.registerCredential(credential_hash, subject_address)
        return self._send_contract_tx(contract_fn, sender_private_key=sender_private_key)

    def revoke_credential(
        self,
        credential_hash: str,
        reason_text: str = "",
        sender_private_key: str = "",
    ) -> Dict[str, Any]:
        self._validate_hex32(credential_hash, "credential_hash")
        reason_hash = self._hash_text_to_bytes32(reason_text)
        contract_fn = self.contract.functions.revokeCredential(credential_hash, reason_hash)
        return self._send_contract_tx(contract_fn, sender_private_key=sender_private_key)

    def health(self) -> Dict[str, Any]:
        return {
            "connected": self.w3.is_connected(),
            "rpc_chain_id": self.w3.eth.chain_id,
            "contract_chain_id": self.meta.chain_id,
            "contract_address": self.meta.address,
        }
