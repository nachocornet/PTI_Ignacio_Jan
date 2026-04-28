from shared.blockchain_client import SSIBlockchainClient


def main() -> None:
    client = SSIBlockchainClient()
    health = client.health()
    print("Blockchain health:")
    print(health)


if __name__ == "__main__":
    main()
