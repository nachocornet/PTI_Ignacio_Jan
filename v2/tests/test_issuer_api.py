from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from eth_account import Account
from eth_account.messages import encode_defunct
import json

from services.issuer import app as issuer
from db import models


class FakeBlockchainClient:
    def set_did_status(self, holder_did, active, metadata_text="", sender_private_key=""):
        return {
            "txHash": "0x" + ("11" * 32),
            "blockNumber": 1,
            "status": 1,
            "sender": "0x" + ("aa" * 20),
            "gasUsed": 70000,
        }

    def register_credential(self, credential_hash, subject_did, sender_private_key=""):
        return {
            "txHash": "0x" + ("22" * 32),
            "blockNumber": 2,
            "status": 1,
            "sender": "0x" + ("aa" * 20),
            "gasUsed": 71000,
        }

    def revoke_credential(self, credential_hash, reason_text="", sender_private_key=""):
        return {
            "txHash": "0x" + ("33" * 32),
            "blockNumber": 3,
            "status": 1,
            "sender": "0x" + ("aa" * 20),
            "gasUsed": 72000,
        }


class FakeBlockchainClientFailValueError(FakeBlockchainClient):
    def register_credential(self, credential_hash, subject_did, sender_private_key=""):
        raise ValueError("credential_hash invalido")

    def revoke_credential(self, credential_hash, reason_text="", sender_private_key=""):
        raise ValueError("credential_hash invalido")


class FakeBlockchainClientFailRuntime(FakeBlockchainClient):
    def set_did_status(self, holder_did, active, metadata_text="", sender_private_key=""):
        raise RuntimeError("nodo no disponible")

    def register_credential(self, credential_hash, subject_did, sender_private_key=""):
        return {
            "txHash": "0x" + ("22" * 32),
            "blockNumber": 2,
            "status": 1,
            "sender": "0x" + ("aa" * 20),
            "gasUsed": 71000,
        }

    def revoke_credential(self, credential_hash, reason_text="", sender_private_key=""):
        return {
            "txHash": "0x" + ("33" * 32),
            "blockNumber": 3,
            "status": 1,
            "sender": "0x" + ("aa" * 20),
            "gasUsed": 72000,
        }


def _build_test_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    db.add(
        models.CitizenDB(
            numero_dni="12345678A",
            nombre="Adulto",
            fecha_nacimiento="2000-01-01",
        )
    )
    db.add(
        models.CitizenDB(
            numero_dni="87654321B",
            nombre="Menor",
            fecha_nacimiento="2012-01-01",
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        test_db = SessionLocal()
        try:
            yield test_db
        finally:
            test_db.close()

    issuer.app.dependency_overrides[issuer.get_db] = override_get_db
    issuer.limiter.reset()
    monkeypatch.setattr(issuer, "get_blockchain_client", lambda: FakeBlockchainClient())
    return TestClient(issuer.app)


def test_issue_dni_invalid_did_returns_400(monkeypatch):
    client = _build_test_client(monkeypatch)
    response = client.post(
        "/api/credentials/issue_dni",
        json={"did_ciudadano": "did:bad:123", "numero_dni": "12345678A"},
    )
    assert response.status_code == 400
    assert "did_ciudadano invalido" in response.text


def test_issue_dni_missing_citizen_returns_404(monkeypatch):
    client = _build_test_client(monkeypatch)
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x1111111111111111111111111111111111111111",
            "numero_dni": "00000000Z",
        },
    )
    assert response.status_code == 404


def test_issue_dni_underage_returns_403(monkeypatch):
    client = _build_test_client(monkeypatch)
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x2222222222222222222222222222222222222222",
            "numero_dni": "87654321B",
        },
    )
    assert response.status_code == 403
    assert "menor" in response.text.lower()


def test_issue_dni_success_returns_signed_credential(monkeypatch):
    client = _build_test_client(monkeypatch)
    holder_did = "did:ethr:0x3333333333333333333333333333333333333333"

    response = client.post(
        "/api/credentials/issue_dni",
        json={"did_ciudadano": holder_did, "numero_dni": "12345678A"},
    )

    assert response.status_code == 200
    body = response.json()
    credential = body["credential"]

    assert credential["credentialSubject"]["id"] == holder_did
    assert credential["credentialSubject"]["isOver18"] is True
    assert credential["credentialHash"].startswith("0x")
    assert len(credential["credentialHash"]) == 66
    assert "didStatusTx" in body["onchain"]
    assert "registerCredentialTx" in body["onchain"]

    # Verify VC signature integrity.
    payload = dict(credential)
    proof = payload.pop("proof")
    recovered = Account.recover_message(
        encode_defunct(text=json.dumps(payload, separators=(",", ":"), sort_keys=True)),
        signature=proof["proofValue"],
    )
    assert f"did:ethr:{recovered.lower()}" == payload["issuer"].lower()


def test_revoke_credential_success(monkeypatch):
    client = _build_test_client(monkeypatch)
    response = client.post(
        "/api/credentials/revoke",
        json={"credential_hash": "0x" + ("ab" * 32), "reason": "test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "revoked"
    assert body["tx"]["status"] == 1


def test_issue_dni_blockchain_valueerror_returns_400(monkeypatch):
    client = _build_test_client(monkeypatch)
    monkeypatch.setattr(issuer, "get_blockchain_client", lambda: FakeBlockchainClientFailValueError())
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x4444444444444444444444444444444444444444",
            "numero_dni": "12345678A",
        },
    )
    assert response.status_code == 400
    assert "blockchain" in response.text.lower()


def test_issue_dni_blockchain_runtime_returns_503(monkeypatch):
    client = _build_test_client(monkeypatch)
    monkeypatch.setattr(issuer, "get_blockchain_client", lambda: FakeBlockchainClientFailRuntime())
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x5555555555555555555555555555555555555555",
            "numero_dni": "12345678A",
        },
    )
    assert response.status_code == 503
    assert "blockchain" in response.text.lower()


def test_revoke_credential_invalid_hash_returns_400(monkeypatch):
    client = _build_test_client(monkeypatch)
    monkeypatch.setattr(issuer, "get_blockchain_client", lambda: FakeBlockchainClientFailValueError())
    response = client.post(
        "/api/credentials/revoke",
        json={"credential_hash": "0x1234", "reason": "test"},
    )
    assert response.status_code == 400
    assert "invalida" in response.text.lower() or "hex" in response.text.lower()
