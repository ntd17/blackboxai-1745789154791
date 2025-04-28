// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StorageContract {
    // Enums for better gas optimization and type safety
    enum ContractStatus {
        Draft,
        PendingSignature,
        Signed,
        Cancelled
    }

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
        ContractStatus status;
        address creator;
        address partyA;
        address partyB;
        bool isPartyASigned;
        bool isPartyBSigned;
    }
    
    struct Signature {
        uint256 contractId;
        string originalCid;
        string signedCid;
        uint256 timestamp;
        string metadata;  // JSON string with signature details
        address signer;
    }
    
    // State variables
    mapping(string => File) public files;
    mapping(address => string[]) public userFiles;
    
    mapping(uint256 => Contract) public contracts;
    mapping(uint256 => Signature) public signatures;
    mapping(address => uint256[]) public userContracts;
    
    // Events
    event FileStored(string cid, address owner, uint256 timestamp);
    event ContractStored(uint256 indexed contractId, string cid, address creator, address partyA, address partyB);
    event ContractStatusChanged(uint256 indexed contractId, ContractStatus newStatus);
    event SignatureRequested(uint256 indexed contractId, address requestedBy, address requestedFrom);
    event ContractSigned(uint256 indexed contractId, string originalCid, string signedCid, address signer);
    event ContractCancelled(uint256 indexed contractId, address cancelledBy, uint256 timestamp);
    
    // Modifiers
    modifier validCid(string memory cid) {
        require(bytes(cid).length > 0, "Invalid CID");
        _;
    }
    
    modifier contractExists(uint256 contractId) {
        require(contracts[contractId].id == contractId, "Contract not found");
        _;
    }

    modifier onlyContractParty(uint256 contractId) {
        require(
            msg.sender == contracts[contractId].partyA ||
            msg.sender == contracts[contractId].partyB,
            "Only contract parties can perform this action"
        );
        _;
    }

    modifier notCancelled(uint256 contractId) {
        require(
            contracts[contractId].status != ContractStatus.Cancelled,
            "Contract is cancelled"
        );
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
    function storeContract(
        uint256 contractId, 
        string memory cid,
        address partyA,
        address partyB
    ) 
        public 
        validCid(cid) 
    {
        require(contracts[contractId].timestamp == 0, "Contract already registered");
        require(partyA != address(0) && partyB != address(0), "Invalid party addresses");
        
        contracts[contractId] = Contract({
            id: contractId,
            cid: cid,
            timestamp: block.timestamp,
            status: ContractStatus.Draft,
            creator: msg.sender,
            partyA: partyA,
            partyB: partyB,
            isPartyASigned: false,
            isPartyBSigned: false
        });
        
        userContracts[msg.sender].push(contractId);
        
        emit ContractStored(contractId, cid, msg.sender, partyA, partyB);
    }

    function requestSignature(uint256 contractId)
        public
        contractExists(contractId)
        notCancelled(contractId)
        onlyContractParty(contractId)
    {
        Contract storage c = contracts[contractId];
        require(
            c.status == ContractStatus.Draft,
            "Contract must be in draft status"
        );

        c.status = ContractStatus.PendingSignature;
        
        address requestedFrom = (msg.sender == c.partyA) ? c.partyB : c.partyA;
        emit SignatureRequested(contractId, msg.sender, requestedFrom);
        emit ContractStatusChanged(contractId, ContractStatus.PendingSignature);
    }
    
    function signContract(
        uint256 contractId,
        string memory originalCid,
        string memory signedCid,
        string memory signatureMetadata
    ) 
        public 
        contractExists(contractId)
        notCancelled(contractId)
        onlyContractParty(contractId)
        validCid(signedCid) 
    {
        Contract storage c = contracts[contractId];
        require(
            keccak256(bytes(c.cid)) == keccak256(bytes(originalCid)),
            "Original CID mismatch"
        );
        
        require(
            c.status == ContractStatus.Draft ||
            c.status == ContractStatus.PendingSignature,
            "Contract not in signable state"
        );

        // Update signature status
        if (msg.sender == c.partyA) {
            require(!c.isPartyASigned, "Party A already signed");
            c.isPartyASigned = true;
        } else {
            require(!c.isPartyBSigned, "Party B already signed");
            c.isPartyBSigned = true;
        }
        
        signatures[contractId] = Signature({
            contractId: contractId,
            originalCid: originalCid,
            signedCid: signedCid,
            timestamp: block.timestamp,
            metadata: signatureMetadata,
            signer: msg.sender
        });
        
        // If both parties have signed, update status to Signed
        if (c.isPartyASigned && c.isPartyBSigned) {
            c.status = ContractStatus.Signed;
            emit ContractStatusChanged(contractId, ContractStatus.Signed);
        }
        
        emit ContractSigned(contractId, originalCid, signedCid, msg.sender);
    }

    function cancelContract(uint256 contractId)
        public
        contractExists(contractId)
        onlyContractParty(contractId)
    {
        Contract storage c = contracts[contractId];
        require(
            c.status != ContractStatus.Signed &&
            c.status != ContractStatus.Cancelled,
            "Cannot cancel signed or already cancelled contract"
        );

        c.status = ContractStatus.Cancelled;
        emit ContractCancelled(contractId, msg.sender, block.timestamp);
        emit ContractStatusChanged(contractId, ContractStatus.Cancelled);
    }
    
    function getContract(uint256 contractId) 
        public 
        view 
        contractExists(contractId)
        returns (
            uint256 id,
            string memory cid,
            uint256 timestamp,
            ContractStatus status,
            address creator,
            address partyA,
            address partyB,
            bool isPartyASigned,
            bool isPartyBSigned
        ) 
    {
        Contract memory c = contracts[contractId];
        return (
            c.id,
            c.cid,
            c.timestamp,
            c.status,
            c.creator,
            c.partyA,
            c.partyB,
            c.isPartyASigned,
            c.isPartyBSigned
        );
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
            string memory metadata,
            address signer
        )
    {
        Signature memory s = signatures[contractId];
        return (
            s.contractId,
            s.originalCid,
            s.signedCid,
            s.timestamp,
            s.metadata,
            s.signer
        );
    }
    
    function getUserContracts(address user) 
        public 
        view 
        returns (uint256[] memory) 
    {
        return userContracts[user];
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
        returns (bool valid, uint256 timestamp, ContractStatus status)
    {
        Contract memory c = contracts[contractId];
        return (
            keccak256(bytes(c.cid)) == keccak256(bytes(cid)),
            c.timestamp,
            c.status
        );
    }
    
    function verifySignature(
        uint256 contractId,
        string memory originalCid,
        string memory signedCid
    )
        public
        view
        returns (bool valid, uint256 timestamp, address signer)
    {
        Signature memory s = signatures[contractId];
        return (
            keccak256(bytes(s.originalCid)) == keccak256(bytes(originalCid)) &&
            keccak256(bytes(s.signedCid)) == keccak256(bytes(signedCid)),
            s.timestamp,
            s.signer
        );
    }
}
