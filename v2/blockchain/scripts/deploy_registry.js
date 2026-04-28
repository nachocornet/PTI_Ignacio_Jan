const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log(`[deploy] network=${hre.network.name}`);
  console.log(`[deploy] deployer=${deployer.address}`);

  const RegistryFactory = await hre.ethers.getContractFactory("SSIRegistry");
  const registry = await RegistryFactory.deploy(deployer.address);
  await registry.waitForDeployment();

  const registryAddress = await registry.getAddress();
  const deploymentTx = registry.deploymentTransaction();
  const deployedBlock = deploymentTx ? await deploymentTx.wait() : null;

  console.log(`[deploy] SSIRegistry=${registryAddress}`);

  const artifact = await hre.artifacts.readArtifact("SSIRegistry");
  const networkName = hre.network.name;

  const exportPayload = {
    contractName: "SSIRegistry",
    network: networkName,
    chainId: Number(hre.network.config.chainId || 0),
    deployedAt: new Date().toISOString(),
    deployer: deployer.address,
    deploymentTxHash: deploymentTx ? deploymentTx.hash : null,
    deploymentBlock: deployedBlock ? deployedBlock.blockNumber : null,
    address: registryAddress,
    abi: artifact.abi,
  };

  const deploymentDir = path.resolve(__dirname, "..", "deployments", networkName);
  const localArtifactDir = path.resolve(__dirname, "..", "artifacts_export");
  const rootBridgeFile = path.resolve(__dirname, "..", "..", `blockchain_contract.${networkName}.json`);
  const activeBridgeFile = path.resolve(__dirname, "..", "..", "deployments", "blockchain_contract.json");

  fs.mkdirSync(deploymentDir, { recursive: true });
  fs.mkdirSync(localArtifactDir, { recursive: true });

  fs.writeFileSync(
    path.join(deploymentDir, "ssi_registry.json"),
    JSON.stringify(exportPayload, null, 2)
  );
  fs.writeFileSync(
    path.join(localArtifactDir, "ssi_registry_abi.json"),
    JSON.stringify(artifact.abi, null, 2)
  );
  fs.writeFileSync(rootBridgeFile, JSON.stringify(exportPayload, null, 2));
  fs.writeFileSync(activeBridgeFile, JSON.stringify(exportPayload, null, 2));

  console.log("[deploy] exported deployment files");
}

main().catch((err) => {
  console.error("[deploy] failed", err);
  process.exitCode = 1;
});
