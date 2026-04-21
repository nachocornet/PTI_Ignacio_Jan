from fastapi.testclient import TestClient
from eth_account import Account

import verifier
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
