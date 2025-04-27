from web3 import Web3
from web3.middleware import geth_poa_middleware
from flask import current_app
from typing import Dict, Optional
import json
import os

class Web3Client:
    """Client for interacting with Ethereum blockchain"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(current_app.config['GANACHE_URL']))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.chain_id = current_app.config['CHAIN_ID']
        self.contract = None
        self._load_contract()
    
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
            raise
    
    def _deploy_contract(self, abi: list, bytecode: str) -> str:
        """
        Deploy a new contract
        
        Args:
            abi: Contract ABI
            bytecode: Contract bytecode
            
        Returns:
            str: Deployed contract address
        """
        try:
            # Get deployment account
            account = self.w3.eth.accounts[0]
            
            # Create contract instance
            contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Build transaction
            transaction = contract.constructor().build_transaction({
                'from': account,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            # Send transaction and wait for receipt
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return tx_receipt.contractAddress
            
        except Exception as e:
            current_app.logger.error(f"Contract deployment failed: {str(e)}")
            raise
    
    def register_cid(self, cid: str, user_id: int) -> Optional[str]:
        """
        Register a CID on the blockchain
        
        Args:
            cid: IPFS CID to register
            user_id: ID of the user registering the CID
            
        Returns:
            str: Transaction hash if successful, None otherwise
        """
        try:
            account = self.w3.eth.accounts[0]
            
            # Build transaction
            transaction = self.contract.functions.storeFile(cid).build_transaction({
                'from': account,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"CID registration failed: {str(e)}")
            return None
    
    def register_contract(self, contract_id: int, cid: str) -> Optional[str]:
        """
        Register a contract on the blockchain
        
        Args:
            contract_id: Contract ID
            cid: Contract document CID
            
        Returns:
            str: Transaction hash if successful, None otherwise
        """
        try:
            account = self.w3.eth.accounts[0]
            
            # Build transaction
            transaction = self.contract.functions.storeContract(
                contract_id,
                cid
            ).build_transaction({
                'from': account,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account),
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"Contract registration failed: {str(e)}")
            return None
    
    def register_signature(self, contract_id: int, original_cid: str,
                         signed_cid: str, signature_metadata: Dict) -> Optional[str]:
        """
        Register a contract signature
        
        Args:
            contract_id: Contract ID
            original_cid: Original contract CID
            signed_cid: Signed contract CID
            signature_metadata: Signature metadata
            
        Returns:
            str: Transaction hash if successful, None otherwise
        """
        try:
            account = self.w3.eth.accounts[0]
            
            # Build transaction
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
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.w3.eth.account.create().key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return self.w3.to_hex(tx_hash)
            
        except Exception as e:
            current_app.logger.error(f"Signature registration failed: {str(e)}")
            return None
    
    def verify_contract(self, contract_id: int, cid: str) -> Dict:
        """
        Verify contract on blockchain
        
        Args:
            contract_id: Contract ID
            cid: Contract CID to verify
            
        Returns:
            dict: Verification result
        """
        try:
            # Get contract data from blockchain
            contract_data = self.contract.functions.getContract(contract_id).call()
            
            return {
                'is_registered': contract_data[1] == cid,
                'registration_time': contract_data[2],
                'status': contract_data[3]
            }
            
        except Exception as e:
            current_app.logger.error(f"Contract verification failed: {str(e)}")
            return {
                'is_registered': False,
                'error': str(e)
            }
    
    def verify_signature(self, contract_id: int, original_cid: str,
                        signed_cid: str) -> Dict:
        """
        Verify contract signature
        
        Args:
            contract_id: Contract ID
            original_cid: Original contract CID
            signed_cid: Signed contract CID
            
        Returns:
            dict: Verification result
        """
        try:
            # Get signature data from blockchain
            signature_data = self.contract.functions.getSignature(contract_id).call()
            
            return {
                'is_valid': (
                    signature_data[1] == original_cid and
                    signature_data[2] == signed_cid
                ),
                'signature_time': signature_data[3],
                'metadata': json.loads(signature_data[4]) if signature_data[4] else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Signature verification failed: {str(e)}")
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def estimate_register_gas(self, contract_id: int, cid: str) -> Dict:
        """
        Estimate gas for contract registration
        
        Args:
            contract_id: Contract ID
            cid: Contract CID
            
        Returns:
            dict: Gas estimation details
        """
        try:
            gas_estimate = self.contract.functions.storeContract(
                contract_id,
                cid
            ).estimate_gas()
            
            gas_price = self.w3.eth.gas_price
            
            return {
                'gas_estimate': gas_estimate,
                'gas_price': gas_price,
                'total_cost_wei': gas_estimate * gas_price,
                'total_cost_eth': self.w3.from_wei(gas_estimate * gas_price, 'ether')
            }
            
        except Exception as e:
            current_app.logger.error(f"Gas estimation failed: {str(e)}")
            return {
                'error': str(e)
            }
    
    def estimate_signature_gas(self, contract_id: int, cid: str) -> Dict:
        """
        Estimate gas for signature registration
        
        Args:
            contract_id: Contract ID
            cid: Contract CID
            
        Returns:
            dict: Gas estimation details
        """
        try:
            gas_estimate = self.contract.functions.signContract(
                contract_id,
                '',  # original_cid
                cid,
                '{}'  # empty metadata for estimation
            ).estimate_gas()
            
            gas_price = self.w3.eth.gas_price
            
            return {
                'gas_estimate': gas_estimate,
                'gas_price': gas_price,
                'total_cost_wei': gas_estimate * gas_price,
                'total_cost_eth': self.w3.from_wei(gas_estimate * gas_price, 'ether')
            }
            
        except Exception as e:
            current_app.logger.error(f"Gas estimation failed: {str(e)}")
            return {
                'error': str(e)
            }
