require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const HOST = process.env.HARDHAT_HOST || "127.0.0.1";
const PORT = Number(process.env.HARDHAT_PORT || 8545);
const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL || "";
const SEPOLIA_DEPLOYER_PRIVATE_KEY = process.env.SEPOLIA_DEPLOYER_PRIVATE_KEY || "";
const SSI_BLOCKCHAIN_NETWORK = process.env.SSI_BLOCKCHAIN_NETWORK || "local";

const sepoliaAccounts = SEPOLIA_DEPLOYER_PRIVATE_KEY ? [SEPOLIA_DEPLOYER_PRIVATE_KEY] : [];

if (SSI_BLOCKCHAIN_NETWORK === "sepolia" && !SEPOLIA_RPC_URL) {
  throw new Error("SEPOLIA_RPC_URL is required when SSI_BLOCKCHAIN_NETWORK=sepolia");
}

if (SSI_BLOCKCHAIN_NETWORK === "sepolia" && !SEPOLIA_DEPLOYER_PRIVATE_KEY) {
  throw new Error("SEPOLIA_DEPLOYER_PRIVATE_KEY is required when SSI_BLOCKCHAIN_NETWORK=sepolia");
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 300,
      },
    },
  },
  paths: {
    sources: "./contracts",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  networks: {
    hardhat: {
      chainId: 31337,
    },
    localhost: {
      url: `http://${HOST}:${PORT}`,
      chainId: 31337,
    },
    sepolia: {
      url: SEPOLIA_RPC_URL,
      chainId: 11155111,
      accounts: sepoliaAccounts,
    },
  },
};
