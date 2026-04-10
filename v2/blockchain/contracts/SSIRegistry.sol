// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SSI Registry for DID trust and credential revocation
/// @notice Stores authorized issuers, holder DID status and credential revocations.
contract SSIRegistry {
    struct DidRecord {
        bool exists;
        bool active;
        uint64 updatedAt;
        bytes32 metadataHash;
    }

    struct CredentialRecord {
        bool exists;
        bool revoked;
        address subject;
        address issuer;
        uint64 issuedAt;
        uint64 revokedAt;
        bytes32 revocationReasonHash;
    }

    address public owner;

    mapping(address => bool) private _authorizedIssuers;
    mapping(address => DidRecord) private _didRecords;
    mapping(bytes32 => CredentialRecord) private _credentialRecords;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event IssuerAuthorizationUpdated(address indexed issuer, bool indexed authorized, uint64 indexed timestamp);
    event DidStatusUpdated(address indexed didAddress, bool indexed active, bytes32 metadataHash, uint64 indexed timestamp);
    event CredentialRegistered(
        bytes32 indexed credentialHash,
        address indexed subject,
        address indexed issuer,
        uint64 timestamp
    );
    event CredentialRevoked(
        bytes32 indexed credentialHash,
        address indexed subject,
        address indexed issuer,
        bytes32 reasonHash,
        uint64 timestamp
    );

    error Unauthorized();
    error InvalidAddress();
    error CredentialAlreadyExists();
    error CredentialUnknown();
    error CredentialAlreadyRevoked();

    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert Unauthorized();
        }
        _;
    }

    modifier onlyAuthorizedIssuer() {
        if (!_authorizedIssuers[msg.sender]) {
            revert Unauthorized();
        }
        _;
    }

    constructor(address initialOwner) {
        if (initialOwner == address(0)) {
            revert InvalidAddress();
        }
        owner = initialOwner;
        _authorizedIssuers[initialOwner] = true;
        emit OwnershipTransferred(address(0), initialOwner);
        emit IssuerAuthorizationUpdated(initialOwner, true, uint64(block.timestamp));
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) {
            revert InvalidAddress();
        }
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    function setIssuerAuthorization(address issuer, bool authorized) external onlyOwner {
        if (issuer == address(0)) {
            revert InvalidAddress();
        }
        _authorizedIssuers[issuer] = authorized;
        emit IssuerAuthorizationUpdated(issuer, authorized, uint64(block.timestamp));
    }

    function setDidStatus(address didAddress, bool active, bytes32 metadataHash) external onlyAuthorizedIssuer {
        if (didAddress == address(0)) {
            revert InvalidAddress();
        }

        _didRecords[didAddress] = DidRecord({
            exists: true,
            active: active,
            updatedAt: uint64(block.timestamp),
            metadataHash: metadataHash
        });

        emit DidStatusUpdated(didAddress, active, metadataHash, uint64(block.timestamp));
    }

    function registerCredential(bytes32 credentialHash, address subject) external onlyAuthorizedIssuer {
        if (subject == address(0)) {
            revert InvalidAddress();
        }
        if (_credentialRecords[credentialHash].exists) {
            revert CredentialAlreadyExists();
        }

        _credentialRecords[credentialHash] = CredentialRecord({
            exists: true,
            revoked: false,
            subject: subject,
            issuer: msg.sender,
            issuedAt: uint64(block.timestamp),
            revokedAt: 0,
            revocationReasonHash: bytes32(0)
        });

        emit CredentialRegistered(credentialHash, subject, msg.sender, uint64(block.timestamp));
    }

    function revokeCredential(bytes32 credentialHash, bytes32 reasonHash) external onlyAuthorizedIssuer {
        CredentialRecord storage record = _credentialRecords[credentialHash];
        if (!record.exists) {
            revert CredentialUnknown();
        }
        if (record.revoked) {
            revert CredentialAlreadyRevoked();
        }

        record.revoked = true;
        record.revokedAt = uint64(block.timestamp);
        record.revocationReasonHash = reasonHash;

        emit CredentialRevoked(credentialHash, record.subject, msg.sender, reasonHash, uint64(block.timestamp));
    }

    function isIssuerAuthorized(address issuer) external view returns (bool) {
        return _authorizedIssuers[issuer];
    }

    function getDidRecord(address didAddress) external view returns (DidRecord memory) {
        return _didRecords[didAddress];
    }

    function isDidActive(address didAddress) external view returns (bool) {
        DidRecord memory record = _didRecords[didAddress];
        return record.exists && record.active;
    }

    function getCredentialRecord(bytes32 credentialHash) external view returns (CredentialRecord memory) {
        return _credentialRecords[credentialHash];
    }

    function isCredentialRevoked(bytes32 credentialHash) external view returns (bool) {
        CredentialRecord memory record = _credentialRecords[credentialHash];
        return record.exists && record.revoked;
    }
}
