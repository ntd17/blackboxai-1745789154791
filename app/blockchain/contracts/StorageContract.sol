// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StorageContract {
    // Structs
    struct File {
        uint256 id;
        string cid;
        address owner;
        uint256 timestamp;
    }
    
    struct Contract {
        uint256 id;
        string cid;
        uint256 timestamp;
        string status;  // draft, pending_signature, signed, cancelled
        address creator;
    }
    
    struct Signature {
        uint256 contractId;
        string originalCid;
        string signedCid;
        uint256 timestamp;
        string metadata;  // JSON string with signature details
    }
    
    // State variables
    mapping(string => File) public files;
    mapping(address => string[]) public userFiles;
    
    mapping(uint256 => Contract) public contracts;
    mapping(uint256 => Signature) public signatures;
    mapping(address => uint256[]) public userContracts;
    
    // Events
    event FileStored(string cid, address owner, uint256 timestamp);
    event ContractStored(uint256 indexed contractId, string cid, address creator);
    event ContractSigned(uint256 indexed contractId, string originalCid, string signedCid);
    
    // Modifiers
    modifier validCid(string memory cid) {
        require(bytes(cid).length > 0, "Invalid CID");
        _;
    }
    
    modifier contractExists(uint256 contractId) {
        require(contracts[contractId].id == contractId, "Contract not found");
        _;
    }
    
    // File storage functions
    function storeFile(string memory cid) public validCid(cid) {
        require(files[cid].timestamp == 0, "CID already registered");
        
        files[cid] = File({
            id: userFiles[msg.sender].length,
            cid: cid,
            owner: msg.sender,
            timestamp: block.timestamp
        });
        
        userFiles[msg.sender].push(cid);
        
        emit FileStored(cid, msg.sender, block.timestamp);
    }
    
    function getUserFiles(address user) public view returns (string[] memory) {
        return userFiles[user];
    }
    
    // Contract management functions
    function storeContract(uint256 contractId, string memory cid) 
        public 
        validCid(cid) 
    {
        require(contracts[contractId].timestamp == 0, "Contract already registered");
        
        contracts[contractId] = Contract({
            id: contractId,
            cid: cid,
            timestamp: block.timestamp,
            status: "draft",
            creator: msg.sender
        });
        
        userContracts[msg.sender].push(contractId);
        
        emit ContractStored(contractId, cid, msg.sender);
    }
    
    function signContract(
        uint256 contractId,
        string memory originalCid,
        string memory signedCid,
        string memory signatureMetadata
    ) 
        public 
        contractExists(contractId)
        validCid(signedCid) 
    {
        require(
            keccak256(bytes(contracts[contractId].cid)) == keccak256(bytes(originalCid)),
            "Original CID mismatch"
        );
        
        require(
            keccak256(bytes(contracts[contractId].status)) == keccak256(bytes("draft")) ||
            keccak256(bytes(contracts[contractId].status)) == keccak256(bytes("pending_signature")),
            "Contract not in signable state"
        );
        
        signatures[contractId] = Signature({
            contractId: contractId,
            originalCid: originalCid,
            signedCid: signedCid,
            timestamp: block.timestamp,
            metadata: signatureMetadata
        });
        
        contracts[contractId].status = "signed";
        
        emit ContractSigned(contractId, originalCid, signedCid);
    }
    
    function getContract(uint256 contractId) 
        public 
        view 
        contractExists(contractId)
        returns (
            uint256 id,
            string memory cid,
            uint256 timestamp,
            string memory status
        ) 
    {
        Contract memory c = contracts[contractId];
        return (c.id, c.cid, c.timestamp, c.status);
    }
    
    function getSignature(uint256 contractId)
        public
        view
        contractExists(contractId)
        returns (
            uint256 id,
            string memory originalCid,
            string memory signedCid,
            uint256 timestamp,
            string memory metadata
        )
    {
        Signature memory s = signatures[contractId];
        return (s.contractId, s.originalCid, s.signedCid, s.timestamp, s.metadata);
    }
    
    function getUserContracts(address user) 
        public 
        view 
        returns (uint256[] memory) 
    {
        return userContracts[user];
    }
    
    // Contract status management
    function updateContractStatus(uint256 contractId, string memory newStatus)
        public
        contractExists(contractId)
    {
        require(
            msg.sender == contracts[contractId].creator,
            "Only creator can update status"
        );
        
        contracts[contractId].status = newStatus;
    }
    
    // Verification functions
    function verifyFile(string memory cid) 
        public 
        view 
        validCid(cid)
        returns (bool exists, address owner, uint256 timestamp) 
    {
        File memory file = files[cid];
        return (file.timestamp > 0, file.owner, file.timestamp);
    }
    
    function verifyContract(uint256 contractId, string memory cid)
        public
        view
        returns (bool valid, uint256 timestamp)
    {
        Contract memory c = contracts[contractId];
        return (
            keccak256(bytes(c.cid)) == keccak256(bytes(cid)),
            c.timestamp
        );
    }
    
    function verifySignature(
        uint256 contractId,
        string memory originalCid,
        string memory signedCid
    )
        public
        view
        returns (bool valid, uint256 timestamp)
    {
        Signature memory s = signatures[contractId];
        return (
            keccak256(bytes(s.originalCid)) == keccak256(bytes(originalCid)) &&
            keccak256(bytes(s.signedCid)) == keccak256(bytes(signedCid)),
            s.timestamp
        );
    }
}
