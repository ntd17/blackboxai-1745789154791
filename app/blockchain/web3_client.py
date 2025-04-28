from web3 import Web3
from web3.middleware import geth_poa_middleware
from flask import current_app
from typing import Dict, Optional, List, Tuple
import json
import os
from enum import IntEnum
from app.utils.error_handlers import BlockchainError

class ContractStatus(IntEnum):
    """Mirror of smart contract's ContractStatus enum"""
    Draft = 0
    PendingSignature = 1
    Signed = 2
    Cancelled = 3

class Web3Client:
    """Client for interacting with Ethereum blockchain"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(current_app.config['GANACHE_URL']))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.chain_id = current_app.config['CHAIN_ID']
        self.contract = None
        self._load_contract()
        
        # Set up event filters
        self.contract_stored_filter = self.contract.events.ContractStored.create_filter(fromBlock='latest')
        self.contract_signed_filter = self.contract.events.ContractSigned.create_filter(fromBlock='latest')
        self.contract_status_filter = self.contract.events.ContractStatusChanged.create_filter(fromBlock='latest')
    
    def _load_contract(self):
        """Load the deployed contract"""
        try:
            # Load contract ABI and address
            contract_path = os.path.join(
                current_app.root_path,
                'blockchain/contracts/StorageContract.json'
            )
            
            with open(contract_path) as f:
                contract_data = json.load(f)
            
            contract_address = current_app.config.get('CONTRACT_ADDRESS')
            if not contract_address:
                # Deploy new contract if address not configured
                contract_address = self._deploy_contract(contract_data['abi'], contract_data['bytecode'])
                
            self.contract = self.w3.eth.contract(
                address=contract_address,
                abi=contract_data['abi']
            )
            
        except Exception as e:
            current_app.logger.error(f"Failed to load contract: {str(e)}")
            raise BlockchainError("Failed to load smart contract", str(e))
    
    def _deploy_contract(self, abi: list, bytecode: str) -> str:
        """Deploy a new contract"""
        try:
            account = self.w3.eth.accounts[0]
            contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            transaction = contract.constructor().build_transaction({
                'from': account,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return tx_receipt.contractAddress
            
        except Exception as e:
            current_app.logger.error(f"Contract deployment failed: {str(e)}")
            raise BlockchainError("Failed to deploy contract", str(e))
    
    def register_contract(self, contract_id: int, cid: str, party_a: str, party_b: str) -> str:
        """Register a contract on the blockchain"""
        try:
            account = self.w3.eth.accounts[0]
            
            transaction = self.contract.functions.storeContract(
                contract_id,
                cid,
                party_a,
                party_b
            ).build_transaction({
                'from': account,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"Contract registration failed: {str(e)}")
            raise BlockchainError("Failed to register contract", str(e))
    
    def request_signature(self, contract_id: int) -> str:
        """Request contract signature"""
        try:
            account = self.w3.eth.accounts[0]
            
            transaction = self.contract.functions.requestSignature(
                contract_id
            ).build_transaction({
                'from': account,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"Signature request failed: {str(e)}")
            raise BlockchainError("Failed to request signature", str(e))
    
    def sign_contract(self, contract_id: int, original_cid: str,
                     signed_cid: str, signature_metadata: Dict) -> str:
        """Sign a contract"""
        try:
            account = self.w3.eth.accounts[0]
            
            transaction = self.contract.functions.signContract(
                contract_id,
                original_cid,
                signed_cid,
                json.dumps(signature_metadata)
            ).build_transaction({
                'from': account,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"Contract signing failed: {str(e)}")
            raise BlockchainError("Failed to sign contract", str(e))
    
    def cancel_contract(self, contract_id: int) -> str:
        """Cancel a contract"""
        try:
            account = self.w3.eth.accounts[0]
            
            transaction = self.contract.functions.cancelContract(
                contract_id
            ).build_transaction({
                'from': account,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"Contract cancellation failed: {str(e)}")
            raise BlockchainError("Failed to cancel contract", str(e))
    
    def get_contract_details(self, contract_id: int) -> Dict:
        """Get detailed contract information"""
        try:
            contract_data = self.contract.functions.getContract(contract_id).call()
            
            return {
                'id': contract_data[0],
                'cid': contract_data[1],
                'timestamp': contract_data[2],
                'status': ContractStatus(contract_data[3]).name,
                'creator': contract_data[4],
                'party_a': contract_data[5],
                'party_b': contract_data[6],
                'is_party_a_signed': contract_data[7],
                'is_party_b_signed': contract_data[8]
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to get contract details: {str(e)}")
            raise BlockchainError("Failed to get contract details", str(e))
    
    def get_signature_details(self, contract_id: int) -> Dict:
        """Get detailed signature information"""
        try:
            signature_data = self.contract.functions.getSignature(contract_id).call()
            
            return {
                'contract_id': signature_data[0],
                'original_cid': signature_data[1],
                'signed_cid': signature_data[2],
                'timestamp': signature_data[3],
                'metadata': json.loads(signature_data[4]) if signature_data[4] else None,
                'signer': signature_data[5]
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to get signature details: {str(e)}")
            raise BlockchainError("Failed to get signature details", str(e))
    
    def verify_contract(self, contract_id: int, cid: str) -> Dict:
        """Verify contract on blockchain"""
        try:
            result = self.contract.functions.verifyContract(contract_id, cid).call()
            
            return {
                'is_valid': result[0],
                'timestamp': result[1],
                'status': ContractStatus(result[2]).name
            }
            
        except Exception as e:
            current_app.logger.error(f"Contract verification failed: {str(e)}")
            raise BlockchainError("Failed to verify contract", str(e))
    
    def get_contract_events(self, contract_id: int) -> List[Dict]:
        """Get all events for a specific contract"""
        try:
            events = []
            
            # Get ContractStored events
            stored_events = self.contract_stored_filter.get_all_entries()
            events.extend([
                {
                    'type': 'ContractStored',
                    'contract_id': event['args']['contractId'],
                    'cid': event['args']['cid'],
                    'creator': event['args']['creator'],
                    'timestamp': self.w3.eth.get_block(event['blockNumber'])['timestamp']
                }
                for event in stored_events
                if event['args']['contractId'] == contract_id
            ])
            
            # Get ContractSigned events
            signed_events = self.contract_signed_filter.get_all_entries()
            events.extend([
                {
                    'type': 'ContractSigned',
                    'contract_id': event['args']['contractId'],
                    'original_cid': event['args']['originalCid'],
                    'signed_cid': event['args']['signedCid'],
                    'signer': event['args']['signer'],
                    'timestamp': self.w3.eth.get_block(event['blockNumber'])['timestamp']
                }
                for event in signed_events
                if event['args']['contractId'] == contract_id
            ])
            
            # Get status change events
            status_events = self.contract_status_filter.get_all_entries()
            events.extend([
                {
                    'type': 'StatusChanged',
                    'contract_id': event['args']['contractId'],
                    'new_status': ContractStatus(event['args']['newStatus']).name,
                    'timestamp': self.w3.eth.get_block(event['blockNumber'])['timestamp']
                }
                for event in status_events
                if event['args']['contractId'] == contract_id
            ])
            
            # Sort events by timestamp
            events.sort(key=lambda x: x['timestamp'])
            return events
            
        except Exception as e:
            current_app.logger.error(f"Failed to get contract events: {str(e)}")
            raise BlockchainError("Failed to get contract events", str(e))
