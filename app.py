from flask import Flask, jsonify, request, render_template_string
import hashlib
import json
from time import time

class BDTBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_block(previous_hash='1', passcode='0000')

    def create_block(self, previous_hash, passcode):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'previous_hash': previous_hash,
            'passcode': passcode
        }
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, receiver, amount):
        self.pending_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        return self.get_last_block()['index'] + 1

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_balance(self, username):
        balance = 1000  # প্রাথমিক ফ্রি ব্যালেন্স
        for block in self.chain:
            for tx in block['transactions']:
                if tx['sender'] == username:
                    balance -= tx['amount']
                if tx['receiver'] == username:
                    balance += tx['amount']
        return balance

app = Flask(__name__)
blockchain = BDTBlockchain()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDT Crypto Wallet</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 400px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); margin: auto; }
        h2 { text-align: center; color: #333; }
        .box { margin-bottom: 15px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; }
        input, button { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #007BFF; color: white; border: none; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        #result { margin-top: 15px; padding: 10px; background: #e9ecef; border-radius: 5px; word-break: break-all; }
    </style>
</head>
<body>

<div class="container">
    <h2>BDT Crypto Wallet</h2>

    <div class="box">
        <label>ওয়ালেট হোল্ডার:</label>
        <input type="text" id="username" value="Shanto">
        <button onclick="checkBalance()">ব্যালেন্স চেক করুন</button>
    </div>

    <hr style="margin: 20px 0;">

    <div class="box">
        <label>প্রেরক (Sender):</label>
        <input type="text" id="sender" value="Shanto">
        
        <label>প্রাপক (Receiver):</label>
        <input type="text" id="receiver" value="Friend">
        
        <label>পরিমাণ (BDT):</label>
        <input type="number" id="amount" placeholder="পরিমাণ লিখুন">
        
        <label>পাসকোড (Passcode):</label>
        <input type="password" id="passcode" value="1234" placeholder="পাসকোড দিন">
        
        <button onclick="sendMoney()">BDT পাঠান</button>
    </div>

    <div id="result">আউটপুট এখানে দেখাবে...</div>
</div>

<script>
    async function checkBalance() {
        const user = document.getElementById('username').value;
        try {
            let response = await fetch(`/balance/${user}`);
            let data = await response.json();
            if (response.ok) {
                document.getElementById('result').innerHTML = `<b>${data.username}</b>-এর ব্যালেন্স: <b>${data.balance} BDT</b>`;
            } else {
                document.getElementById('result').innerHTML = `ত্রুটি: ${data.error}`;
            }
        } catch (error) {
            document.getElementById('result').innerHTML = "সার্ভারের সাথে কানেক্ট করা যায়নি!";
        }
    }

    async function sendMoney() {
        const sender = document.getElementById('sender').value;
        const receiver = document.getElementById('receiver').value;
        const amount = parseFloat(document.getElementById('amount').value);
        const passcode = document.getElementById('passcode').value;

        try {
            let response = await fetch('/transfer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender, receiver, amount, passcode })
            });
            let data = await response.json();
            document.getElementById('result').innerHTML = data.message || data.error;
        } catch (error) {
            document.getElementById('result').innerHTML = "ট্রানজেকশন সম্পন্ন করা যায়নি!";
        }
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/balance/<username>', methods=['GET'])
def balance(username):
    bal = blockchain.get_balance(username)
    return jsonify({'username': username, 'balance': bal}), 200

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'ডাটা পাওয়া যায়নি!'}), 400

    sender = data.get('sender')
    receiver = data.get('receiver')
    amount = data.get('amount')
    passcode = data.get('passcode')

    if not sender or not receiver or amount is None or not passcode:
        return jsonify({'error': 'সব তথ্য সঠিকভাবে দিন!'}), 400

    if passcode != '1234':
        return jsonify({'error': 'ভুল পাসকোড! সঠিক পাসকোড (1234) দিন।'}), 401

    current_balance = blockchain.get_balance(sender)
    if current_balance < amount:
        return jsonify({'error': 'অপর্যাপ্ত ব্যালেন্স!'}), 400

    blockchain.add_transaction(sender, receiver, amount)
    previous_block = blockchain.get_last_block()
    previous_hash = blockchain.hash(previous_block)
    blockchain.create_block(previous_hash, passcode)

    return jsonify({'message': 'ট্রানজেকশন সফল হয়েছে!'}), 201

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
