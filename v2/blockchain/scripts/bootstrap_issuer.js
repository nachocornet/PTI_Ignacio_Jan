const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

function didToAddress(did) {
  if (typeof did !== "string" || !did.toLowerCase().startsWith("did:ethr:")) {
    throw new Error(`Invalid DID format: ${did}`);
  }
  return did.slice("did:ethr:".length);
}

async function main() {
  const deploymentFile = path.resolve(__dirname, "..", "deployments", "local", "ssi_registry.json");
  const issuerWalletFile = path.resolve(__dirname, "..", "..", "issuer_wallet.json");

  if (!fs.existsSync(deploymentFile)) {
    throw new Error("Deployment metadata not found. Run deploy_registry.js first.");
  }
  if (!fs.existsSync(issuerWalletFile)) {
    throw new Error("issuer_wallet.json not found at project root.");
  }

  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf-8"));
  const issuerWallet = JSON.parse(fs.readFileSync(issuerWalletFile, "utf-8"));

  const [owner] = await hre.ethers.getSigners();
  const registry = await hre.ethers.getContractAt("SSIRegistry", deployment.address, owner);

  const issuerAddress = didToAddress(issuerWallet.did);
  const isAlreadyAuthorized = await registry.isIssuerAuthorized(issuerAddress);

  if (!isAlreadyAuthorized) {
    const tx = await registry.setIssuerAuthorization(issuerAddress, true);
    await tx.wait();
    console.log(`[bootstrap] issuer authorized: ${issuerAddress}`);
  } else {
    console.log(`[bootstrap] issuer already authorized: ${issuerAddress}`);
  }

  const output = {
    owner: owner.address,
    issuerDid: issuerWallet.did,
    issuerAddress,
    authorized: true,
    timestamp: new Date().toISOString(),
  };

  fs.writeFileSync(
    path.resolve(__dirname, "..", "deployments", "local", "bootstrap_issuer.json"),
    JSON.stringify(output, null, 2)
  );

  console.log("[bootstrap] bootstrap output exported");
}

main().catch((err) => {
  console.error("[bootstrap] failed", err);
  process.exitCode = 1;
});
