require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const HOST = process.env.HARDHAT_HOST || "127.0.0.1";
const PORT = Number(process.env.HARDHAT_PORT || 8545);

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
  },
};
