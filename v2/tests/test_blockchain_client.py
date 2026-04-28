import pytest

from shared.blockchain_client import SSIBlockchainClient


def test_canonical_hash_is_deterministic():
    vc_a = {
        "issuer": "did:ethr:0x1111111111111111111111111111111111111111",
        "credentialSubject": {"id": "did:ethr:0x2222222222222222222222222222222222222222", "isOver18": True},
        "type": ["VerifiableCredential", "Over18Credential"],
    }
    vc_b = {
        "type": ["VerifiableCredential", "Over18Credential"],
        "credentialSubject": {"isOver18": True, "id": "did:ethr:0x2222222222222222222222222222222222222222"},
        "issuer": "did:ethr:0x1111111111111111111111111111111111111111",
    }

    assert SSIBlockchainClient.canonical_credential_hash(vc_a) == SSIBlockchainClient.canonical_credential_hash(vc_b)


def test_did_to_address_valid():
    did = "did:ethr:0x1111111111111111111111111111111111111111"
    address = SSIBlockchainClient.did_to_address(did)
    assert address == "0x1111111111111111111111111111111111111111"


def test_did_to_address_invalid_raises():
    with pytest.raises(ValueError):
        SSIBlockchainClient.did_to_address("did:example:bad")


def test_validate_hex32_rejects_bad_values():
    with pytest.raises(ValueError):
        SSIBlockchainClient._validate_hex32("0x1234", "credential_hash")
