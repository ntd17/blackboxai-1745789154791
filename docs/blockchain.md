# Blockchain Guide for the Decentralized Painting Contract Platform

## Compiling and Migrating Solidity Smart Contracts

### Compile Contracts

If using Truffle:

```bash
truffle compile
```

Or using solc directly:

```bash
solc --bin --abi -o build/contracts contracts/StorageContract.sol
```

### Migrate Contracts to Ganache

Start Ganache CLI or GUI:

```bash
ganache-cli
```

Then run migration scripts (example with Truffle):

```bash
truffle migrate --network development
```

### Manual Migration Using Web3.py

You can deploy contracts manually using Web3.py scripts:

```python
from web3 import Web3
from solcx import compile_standard

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Compile contract and deploy (example code here)
```

## Interacting with Contracts Using Web3.py and Ganache

- Connect to Ganache network via Web3.py.
- Use contract ABI and address to create contract instance.
- Call contract functions to read or write data.

Example:

```python
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
result = contract.functions.getData().call()
```

## Tips

- Ensure Ganache is running before deploying or interacting.
- Use the correct network ID and account addresses.
- Monitor Ganache logs for transaction status.

![Blockchain](https://images.pexels.com/photos/373543/pexels-photo-373543.jpeg)
