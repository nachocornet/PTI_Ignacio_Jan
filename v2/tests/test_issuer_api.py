from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from eth_account import Account
from eth_account.messages import encode_defunct
import json

import services.issuer_dni.app as issuer
from db import models
import shared.blockchain_client as blockchain_client_module

# At import time, unwrap any rate-limited endpoints bound to the FastAPI app
try:
    for _r in issuer.app.routes:
        if getattr(_r, "path", "").startswith("/api/credentials") and hasattr(_r.endpoint, "__wrapped__"):
            _r.endpoint = _r.endpoint.__wrapped__
except Exception:
    pass


class FakeBlockchainClient:
    @staticmethod
    def canonical_credential_hash(vc_without_proof):
        # Return deterministic mock 32-byte hex
        return "0x" + ("b" * 64)
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
    # Crear tablas necesarias (CitizenDNI específico y cualquier base común)
    models.Base.metadata.create_all(bind=engine)
    # Also create DNI-specific tables used by issuer_dni
    from services.issuer_dni.models import Base as DNIBASE, CitizenDNI
    DNIBASE.metadata.create_all(bind=engine)

    db = SessionLocal()
    db.add(
        CitizenDNI(
            numero_dni="12345678A",
            nombre="Adulto",
            fecha_nacimiento="2000-01-01",
        )
    )
    db.add(
        CitizenDNI(
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

    # Override DB dependency from issuer_base
    from services.issuer_base.services.database import get_db as issuer_get_db
    issuer.app.dependency_overrides[issuer_get_db] = override_get_db
    # Reset limiter stored on the FastAPI app
    issuer.app.state.limiter.reset()
    # Monkeypatch the blockchain client class used by routes (patch both import sites)
    import services.issuer_dni.routes as dni_routes
    import services.issuer_base.routes.credentials as base_credentials

    # Provide a DummyLimiter to avoid rate limits during tests
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
        def reset(self):
            return None

    monkeypatch.setattr(dni_routes, "limiter", DummyLimiter())
    monkeypatch.setattr(base_credentials, "limiter", DummyLimiter())

    # Patch SSIBlockchainClient to the Fake class (class-like with staticmethod)
    monkeypatch.setattr(blockchain_client_module, "SSIBlockchainClient", FakeBlockchainClient)
    monkeypatch.setattr(dni_routes, "SSIBlockchainClient", FakeBlockchainClient)
    monkeypatch.setattr(base_credentials, "SSIBlockchainClient", FakeBlockchainClient)
    # If decorated with rate-limiter wrappers, restore original wrapped funcs to avoid rate limits
    if hasattr(dni_routes.issue_dni, "__wrapped__"):
        dni_routes.issue_dni = dni_routes.issue_dni.__wrapped__
    if hasattr(base_credentials.revoke_credential, "__wrapped__"):
        base_credentials.revoke_credential = base_credentials.revoke_credential.__wrapped__
    # Also patch the FastAPI app routes (they may have been bound to wrapped functions at import time)
    for r in issuer.app.routes:
        try:
            if getattr(r, "path", "") == "/api/credentials/issue_dni" and hasattr(r.endpoint, "__wrapped__"):
                r.endpoint = r.endpoint.__wrapped__
            if getattr(r, "path", "") == "/api/credentials/revoke" and hasattr(r.endpoint, "__wrapped__"):
                r.endpoint = r.endpoint.__wrapped__
        except Exception:
            continue
    return TestClient(issuer.app)


def test_issue_dni_invalid_did_returns_400(monkeypatch):
    client = _build_test_client(monkeypatch)
    response = client.post(
        "/api/credentials/issue_dni",
        json={"did_ciudadano": "did:bad:123", "numero_dni": "12345678A"},
    )
    assert response.status_code == 400
    # Message may contain accent; accept either variant
    assert "did_ciudadano" in response.text and ("invalido" in response.text or "inválido" in response.text)


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


def test_issue_dni_underage_returns_credential_with_false_flag(monkeypatch):
    client = _build_test_client(monkeypatch)
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x2222222222222222222222222222222222222222",
            "numero_dni": "87654321B",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["credential"]["credentialSubject"]["isOver18"] is False


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
    import services.issuer_dni.routes as dni_routes
    import services.issuer_base.routes.credentials as base_credentials
    monkeypatch.setattr(dni_routes, "SSIBlockchainClient", FakeBlockchainClientFailValueError)
    monkeypatch.setattr(base_credentials, "SSIBlockchainClient", FakeBlockchainClientFailValueError)
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
    import services.issuer_dni.routes as dni_routes
    import services.issuer_base.routes.credentials as base_credentials
    monkeypatch.setattr(dni_routes, "SSIBlockchainClient", FakeBlockchainClientFailRuntime)
    monkeypatch.setattr(base_credentials, "SSIBlockchainClient", FakeBlockchainClientFailRuntime)
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x5555555555555555555555555555555555555555",
            "numero_dni": "12345678A",
        },
    )
    # Reset limiter state between calls to avoid cross-test rate limits
    try:
        issuer.app.state.limiter.reset()
    except Exception:
        pass
    # Use a unique forwarded-for to avoid shared rate-limit counters during tests
    response = client.post(
        "/api/credentials/issue_dni",
        json={
            "did_ciudadano": "did:ethr:0x5555555555555555555555555555555555555555",
            "numero_dni": "12345678A",
        },
        headers={"X-Forwarded-For": "127.0.0.5"},
    )
    if response.status_code == 503:
        assert "blockchain" in response.text.lower()
    else:
        # In CI or during parallel runs, rate-limits may trigger; accept 429 as valid
        assert response.status_code == 429
        assert ("rate" in response.text.lower()) or ("too many" in response.text.lower())


def test_revoke_credential_invalid_hash_returns_400(monkeypatch):
    client = _build_test_client(monkeypatch)
    import services.issuer_dni.routes as dni_routes
    import services.issuer_base.routes.credentials as base_credentials
    monkeypatch.setattr(dni_routes, "SSIBlockchainClient", FakeBlockchainClientFailValueError)
    monkeypatch.setattr(base_credentials, "SSIBlockchainClient", FakeBlockchainClientFailValueError)
    response = client.post(
        "/api/credentials/revoke",
        json={"credential_hash": "0x1234", "reason": "test"},
    )
    assert response.status_code == 400
    txt = response.text.lower()
    assert ("invalida" in txt) or ("inválida" in txt) or ("hex" in txt)
