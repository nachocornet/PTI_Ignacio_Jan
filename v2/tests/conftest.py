import json
import sys
from pathlib import Path

from eth_account import Account
from eth_account.messages import encode_defunct

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.blockchain_client import SSIBlockchainClient  # noqa: E402


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def build_signed_vc(issuer_account, holder_did: str) -> dict:
    issuer_did = f"did:ethr:{issuer_account.address}"
    vc = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "id": "urn:uuid:test-vc-1",
        "type": ["VerifiableCredential", "Over18Credential"],
        "issuer": issuer_did,
        "issuanceDate": "2026-04-21T12:00:00Z",
        "credentialSubject": {
            "id": holder_did,
            "isOver18": True,
        },
    }

    vc_hash = SSIBlockchainClient.canonical_credential_hash(vc)
    vc["credentialHash"] = vc_hash

    signature = Account.sign_message(
        encode_defunct(text=canonical_json(vc)),
        private_key=issuer_account.key,
    ).signature.hex()

    vc["proof"] = {
        "type": "EcdsaSecp256k1RecoverySignature2020",
        "created": "2026-04-21T12:00:00Z",
        "verificationMethod": issuer_did,
        "proofPurpose": "assertionMethod",
        "proofValue": signature,
    }
    return vc


def build_signed_vp(holder_account, vc: dict) -> dict:
    holder_did = f"did:ethr:{holder_account.address}"
    vp = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiablePresentation"],
        "verifiableCredential": vc,
    }

    signature = Account.sign_message(
        encode_defunct(text=canonical_json(vp)),
        private_key=holder_account.key,
    ).signature.hex()

    vp["proof"] = {
        "type": "EcdsaSecp256k1RecoverySignature2020",
        "proofPurpose": "authentication",
        "verificationMethod": holder_did,
        "proofValue": signature,
    }
    return vp
