// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransactionHandler {
    struct Transaction {
        address sender;
        address receiver;
        uint256 amount;
        uint256 timestamp;
        bool confirmed;
    }

    struct ReceivedTransaction {
        address sender;
        uint256 amount;
        uint256 timestamp;
    }

    mapping(bytes32 => Transaction) public transactions;
    mapping(address => ReceivedTransaction[]) public receivedTransactions; // Store received transactions

    address public owner; // Contract owner address

    event TransactionCreated(bytes32 transactionId, address sender, address receiver, uint256 amount);
    event TransactionConfirmed(bytes32 transactionId);
    event TransactionReceived(address indexed sender, uint256 amount, uint256 timestamp); // Event for received transactions

    constructor() {
        owner = msg.sender; // Set the contract deployer as the owner
    }

    // Create a transaction between sender and receiver, with a specified amount
    function createTransaction(
        address _receiver,
        uint256 _amount
    ) external returns (bytes32) {
        // Generate a unique transaction ID
        bytes32 transactionId = keccak256(abi.encodePacked(msg.sender, _receiver, _amount, block.timestamp));

        // Store the transaction details
        transactions[transactionId] = Transaction({
            sender: msg.sender,
            receiver: _receiver,
            amount: _amount,
            timestamp: block.timestamp,
            confirmed: false
        });

        emit TransactionCreated(transactionId, msg.sender, _receiver, _amount);
        return transactionId;
    }

    // Confirm the transaction by the receiver, transferring funds automatically
    function confirmTransaction(bytes32 _transactionId) external {
        Transaction storage txn = transactions[_transactionId];
        require(msg.sender == txn.receiver, "Only the receiver can confirm the transaction");
        require(!txn.confirmed, "Transaction already confirmed");

        // Mark the transaction as confirmed
        txn.confirmed = true;

        // Transfer the amount to the receiver
        (bool success, ) = txn.receiver.call{value: txn.amount}("");
        require(success, "ETH transfer failed");

        emit TransactionConfirmed(_transactionId);
    }

    // Function to receive ETH and log the transaction
    receive() external payable {
        // Log the received transaction
        receivedTransactions[owner].push(ReceivedTransaction({
            sender: msg.sender,
            amount: msg.value,
            timestamp: block.timestamp
        }));

        emit TransactionReceived(msg.sender, msg.value, block.timestamp);
    }

    // View a transaction's details by ID
    function getTransaction(bytes32 _transactionId) external view returns (Transaction memory) {
        return transactions[_transactionId];
    }
    
    // Function to get received transactions
    function getReceivedTransactions() external view returns (ReceivedTransaction[] memory) {
        return receivedTransactions[owner];
    }
}
