const fs = require("fs");
const path = require("path");
const { Wallet } = require("ethers");

function main() {
  const wallet = Wallet.createRandom();
  const payload = {
    purpose: "sepolia_deployer",
    address: wallet.address,
    privateKey: wallet.privateKey,
    createdAt: new Date().toISOString(),
    network: "sepolia",
  };

  const outFile = path.resolve(__dirname, "..", "..", "sepolia_deployer_wallet.json");
  fs.writeFileSync(outFile, JSON.stringify(payload, null, 2));

  console.log(`Wallet generado: ${wallet.address}`);
  console.log(`Guardado en: ${outFile}`);
  console.log("Fondea este address con faucet de Sepolia antes de desplegar.");
}

main();
