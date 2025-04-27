import os
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from solcx import compile_source
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def compile_contract():
    """Compile the Solidity contract"""
    
    # Read contract source
    contract_path = os.path.join(
        'app', 'blockchain', 'contracts', 'StorageContract.sol'
    )
    with open(contract_path, 'r') as f:
        contract_source = f.read()
    
    # Compile contract
    compiled_sol = compile_source(
        contract_source,
        output_values=['abi', 'bin']
    )
    
    # Extract contract interface
    contract_id, contract_interface = compiled_sol.popitem()
    
    return contract_interface

def deploy_contract():
    """Deploy the contract to Ganache"""
    
    try:
        # Connect to Ganache
        w3 = Web3(Web3.HTTPProvider(os.getenv('GANACHE_URL', 'http://ganache:8545')))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise Exception("Could not connect to Ganache")
        
        # Compile contract
        contract_interface = compile_contract()
        
        # Get deployment account
        account = w3.eth.accounts[0]
        
        # Create contract instance
        contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Build transaction
        transaction = contract.constructor().build_transaction({
            'from': account,
            'gas': 2000000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(account),
            'chainId': int(os.getenv('CHAIN_ID', 1337))
        })
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(
            transaction,
            private_key=w3.eth.account.create().key
        )
        
        # Send transaction and wait for receipt
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Save contract data
        contract_data = {
            'address': tx_receipt.contractAddress,
            'abi': contract_interface['abi'],
            'bytecode': contract_interface['bin'],
            'deployment_tx': w3.to_hex(tx_hash)
        }
        
        # Save to file
        output_path = os.path.join(
            'app', 'blockchain', 'contracts', 'StorageContract.json'
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(contract_data, f, indent=2)
        
        print(f"Contract deployed successfully!")
        print(f"Address: {tx_receipt.contractAddress}")
        print(f"Transaction: {w3.to_hex(tx_hash)}")
        
        return tx_receipt.contractAddress
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        raise

if __name__ == '__main__':
    # Wait for Ganache to be ready
    import time
    time.sleep(5)
    
    # Deploy contract
    deploy_contract()
