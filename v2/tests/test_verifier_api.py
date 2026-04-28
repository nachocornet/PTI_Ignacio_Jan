from fastapi.testclient import TestClient
from eth_account import Account
from eth_account.messages import encode_defunct
import json

from services.verifier import app as verifier
from conftest import build_signed_vc, build_signed_vp


class FakeBlockchainClient:
    def __init__(self):
        self.issuer_authorized = True
        self.did_active = True
        self.credential_revoked = False

    def is_issuer_authorized(self, issuer_did):
        return self.issuer_authorized

    def is_did_active(self, holder_did):
        return self.did_active

    def is_credential_revoked(self, credential_hash):
        return self.credential_revoked


def _build_test_client(monkeypatch):
    fake = FakeBlockchainClient()
    monkeypatch.setattr(verifier, "get_blockchain_client", lambda: fake)
    return TestClient(verifier.app), fake


def _make_valid_payload():
    issuer_account = Account.create()
    holder_account = Account.create()
    holder_did = f"did:ethr:{holder_account.address}"
    vc = build_signed_vc(issuer_account, holder_did)
    vp = build_signed_vp(holder_account, vc)
    return vp, holder_account


def test_verify_missing_vp_returns_400(monkeypatch):
    client, _ = _build_test_client(monkeypatch)
    response = client.post("/api/verify_presentation", json={})
    assert response.status_code == 400


def test_verify_missing_verifiable_credential_returns_400(monkeypatch):
    client, _ = _build_test_client(monkeypatch)
    response = client.post("/api/verify_presentation", json={"vp": {"type": ["VerifiablePresentation"]}})
    assert response.status_code == 400


def test_verify_success(monkeypatch):
    client, fake = _build_test_client(monkeypatch)
    vp, _ = _make_valid_payload()
    response = client.post("/api/verify_presentation", json={"vp": vp})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["onchain"]["issuerAuthorized"] is True


def test_verify_rejects_unauthorized_issuer(monkeypatch):
    client, fake = _build_test_client(monkeypatch)
    fake.issuer_authorized = False
    vp, _ = _make_valid_payload()
    response = client.post("/api/verify_presentation", json={"vp": vp})
    assert response.status_code == 401
    assert "issuer" in response.text.lower()


def test_verify_rejects_revoked_credential(monkeypatch):
    client, fake = _build_test_client(monkeypatch)
    fake.credential_revoked = True
    vp, _ = _make_valid_payload()
    response = client.post("/api/verify_presentation", json={"vp": vp})
    assert response.status_code == 401
    assert "revocada" in response.text.lower()


def test_verify_rejects_holder_mismatch(monkeypatch):
    client, _ = _build_test_client(monkeypatch)
    vp, _ = _make_valid_payload()
    attacker = Account.create()
    vp["proof"] = build_signed_vp(attacker, vp["verifiableCredential"])["proof"]

    response = client.post("/api/verify_presentation", json={"vp": vp})
    assert response.status_code == 401
    assert "titular" in response.text.lower()


def test_verify_works_without_credential_hash_field(monkeypatch):
    client, _ = _build_test_client(monkeypatch)
    issuer_account = Account.create()
    holder = Account.create()
    holder_did = f"did:ethr:{holder.address}"
    vc = build_signed_vc(issuer_account, holder_did)

    # Remove hash and re-sign VC so verifier fallback hash path can be exercised.
    vc.pop("credentialHash", None)
    vc_payload = dict(vc)
    vc_payload.pop("proof", None)
    vc_signature = Account.sign_message(
        encode_defunct(text=json.dumps(vc_payload, separators=(",", ":"), sort_keys=True)),
        private_key=issuer_account.key,
    ).signature.hex()
    vc["proof"] = {
        "type": "EcdsaSecp256k1RecoverySignature2020",
        "created": "2026-04-21T12:00:00Z",
        "verificationMethod": f"did:ethr:{issuer_account.address}",
        "proofPurpose": "assertionMethod",
        "proofValue": vc_signature,
    }

    vp = build_signed_vp(holder, vc)

    response = client.post("/api/verify_presentation", json={"vp": vp})
    assert response.status_code == 200
