import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


def _env_csv(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    if raw.strip() == "*":
        return ["*"]
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    app_host: str = os.getenv("SSI_APP_HOST", "127.0.0.1")
    app_bind_host: str = os.getenv("SSI_APP_BIND_HOST", "0.0.0.0")
    blockchain_network: str = os.getenv("SSI_BLOCKCHAIN_NETWORK", "local")

    issuer_port: int = _env_int("SSI_ISSUER_PORT", 5010)
    verifier_port: int = _env_int("SSI_VERIFIER_PORT", 5011)
    frontend_port: int = _env_int("SSI_FRONTEND_PORT", 8080)

    blockchain_host: str = os.getenv("SSI_BLOCKCHAIN_HOST", "127.0.0.1")
    blockchain_port: int = _env_int("SSI_BLOCKCHAIN_PORT", 8545)
    blockchain_rpc_url_env: str = os.getenv("SSI_BLOCKCHAIN_RPC_URL", "")

    issuer_wallet_file: str = os.getenv("SSI_ISSUER_WALLET_FILE", "deployments/runtime/issuer_wallet.json")
    holder_wallet_file: str = os.getenv("SSI_HOLDER_WALLET_FILE", "deployments/runtime/wallet.json")
    contract_file: str = os.getenv(
        "SSI_CONTRACT_FILE",
        "deployments/blockchain_contract.json"
        if blockchain_network == "local"
        else f"deployments/blockchain_contract.{blockchain_network}.json",
    )

    @property
    def issuer_url(self) -> str:
        return f"http://{self.app_host}:{self.issuer_port}"

    @property
    def verifier_url(self) -> str:
        return f"http://{self.app_host}:{self.verifier_port}"

    @property
    def frontend_url(self) -> str:
        return f"http://{self.app_host}:{self.frontend_port}"

    @property
    def blockchain_rpc_url(self) -> str:
        if self.blockchain_rpc_url_env:
            return self.blockchain_rpc_url_env

        if self.blockchain_network == "sepolia":
            sepolia_rpc = os.getenv("SEPOLIA_RPC_URL", "").strip()
            if sepolia_rpc:
                return sepolia_rpc

        return f"http://{self.blockchain_host}:{self.blockchain_port}"

    @property
    def cors_origins(self) -> list[str]:
        default = f"{self.frontend_url},http://localhost:{self.frontend_port}"
        return _env_csv("SSI_CORS_ORIGINS", default)


SETTINGS = Settings()
