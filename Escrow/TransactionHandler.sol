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

    mapping(bytes32 => Transaction) public transactions;
    mapping(address => uint256) public balances;

    event TransactionCreated(bytes32 transactionId, address sender, address receiver, uint256 amount);
    event TransactionConfirmed(bytes32 transactionId);

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function createTransaction(
        address _receiver,
        uint256 _amount
    ) external returns (bytes32) {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        balances[msg.sender] -= _amount;

        bytes32 transactionId = keccak256(abi.encodePacked(msg.sender, _receiver, _amount, block.timestamp));
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

    function confirmTransaction(bytes32 _transactionId) external {
        Transaction storage txn = transactions[_transactionId];
        require(msg.sender == txn.receiver, "Only the receiver can confirm the transaction");
        require(!txn.confirmed, "Transaction already confirmed");

        txn.confirmed = true;
        emit TransactionConfirmed(_transactionId);
    }

    function getTransaction(bytes32 _transactionId) external view returns (Transaction memory) {
        return transactions[_transactionId];
    }
}
