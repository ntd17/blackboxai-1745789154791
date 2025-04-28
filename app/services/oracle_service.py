from app.blockchain.web3_client import Web3Client
from app.utils.logger import get_logger

logger = get_logger()

class OracleService:
    def __init__(self):
        self.web3_client = Web3Client()
        self.contract = self.web3_client.get_storage_contract()

    def store_oracle_data(self, oracle_type: str, data_hash: str, adjusted_days: int, original_duration: int, recommended_duration: int):
        try:
            tx_hash = self.contract.functions.storeOracleData(
                oracle_type,
                data_hash,
                adjusted_days,
                original_duration,
                recommended_duration
            ).transact({'from': self.web3_client.default_account})
            receipt = self.web3_client.wait_for_transaction_receipt(tx_hash)
            logger.info(f"Oracle data stored on-chain: {oracle_type}, tx: {tx_hash.hex()}")
            return receipt
        except Exception as e:
            logger.error(f"Failed to store oracle data on-chain: {str(e)}")
            raise
