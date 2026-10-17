from flask import Flask, jsonify, request, render_template_string
import hashlib
import json
from time import time
import os
import uuid

class BDTBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.users = {}  # ইউজার এবং তাদের পাসফ্রেজ (Passphrase) সংরক্ষণের জন্য
        # জেনেসিস ব্লক তৈরি
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

    def register_user(self, username):
        if username in self.users:
            return None, "এই ইউজারনেমটি ইতিমধ্যে রেজিস্টার্ড আছে!"
        # নতুন ইউজারের জন্য ইউনিক ১২ শব্দের মতো সিক্রেট পাসফ্রেজ তৈরি
        passphrase = str(uuid.uuid4()) + "-" + str(uuid.uuid4())
        self.users[username] = {
            'passphrase': passphrase,
            'balances': {'BDT': 1000.0, 'USDT': 50.0, 'ETH': 0.5}  # মাল্টি-টোকেন ফ্রি ব্যালেন্স
        }
        return passphrase, "সফলভাবে অ্যাকাউন্ট খোলা হয়েছে!"

    def add_transaction(self, sender, receiver, amount, token):
        self.pending_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'token': token
        })
        return self.get_last_block()['index'] + 1

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def get_balances(self, username):
        if username not in self.users:
            return None
        
        # ডিফল্ট ব্যালেন্স কপি
        balances = self.users[username]['balances'].copy()
        
        # ব্লকচেইন থেকে ট্রানজেকশন হিসেব করে ব্যালেন্স আপডেট করা
        for block in self.chain:
            for tx in block['transactions']:
                t = tx['token']
                if tx['sender'] == username:
                    if t not in balances: balances[t] = 0
                    balances[t] -= tx['amount']
                if tx['receiver'] == username:
                    if t not in balances: balances[t] = 0
                    balances[t] += tx['amount']
        return balances

app = Flask(__name__)
blockchain = BDTBlockchain()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDT Multi-Token Blockchain Wallet</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 450px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); margin: auto; }
        h2 { text-align: center; color: #333; }
        .box { margin-bottom: 15px; background: #fafafa; padding: 12px; border-radius: 8px; border: 1px solid #ddd; }
        label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 14px; }
        input, select, button { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background: #28a745; color: white; border: none; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background: #218838; }
        .btn-blue { background: #007BFF; }
        .btn-blue:hover { background: #0056b3; }
        #result { margin-top: 15px; padding: 10px; background: #e9ecef; border-radius: 5px; word-break: break-all; font-size: 14px; }
    </style>
</head>
<body>

<div class="container">
    <h2>BDT Multi-Token Wallet</h2>

    <!-- নতুন অ্যাকাউন্ট খোলার সেকশন -->
    <div class="box">
        <h3>নতুন অ্যাকাউন্ট তৈরি করুন</h3>
        <label>আপনার নাম / ইউজারনেম:</label>
        <input type="text" id="reg_username" placeholder="আপনার নাম দিন">
        <button class="btn-blue" onclick="registerUser()" style="margin-top:10px;">একাউন্ট খুলুন ও পাসফ্রেজ নিন</button>
    </div>

    <!-- ব্যালেন্স চেক সেকশন -->
    <div class="box">
        <h3>মাল্টি-টোকেন ব্যালেন্স চেক</h3>
        <label>ইউজারনেম:</label>
        <input type="text" id="username" placeholder="ইউজারনেম লিখুন">
        <button onclick="checkBalance()" style="margin-top:10px;">ব্যালেন্স দেখুন</button>
    </div>

    <!-- টোকেন ট্রান্সফার সেকশন -->
    <div class="box">
        <h3>টোকেন পাঠান</h3>
        <label>প্রেরক (Sender):</label>
        <input type="text" id="sender" placeholder="আপনার ইউজারনেম">
        
        <label>প্রাপক (Receiver):</label>
        <input type="text" id="receiver" placeholder="প্রাপকের ইউজারনেম">
        
        <label>টোকেনের ধরণ (Token):</label>
        <select id="token">
            <option value="BDT">BDT (Bangladeshi Taka Token)</option>
            <option value="USDT">USDT (Tether)</option>
            <option value="ETH">ETH (Ethereum)</option>
        </select>

        <label>পরিমাণ:</label>
        <input type="number" id="amount" placeholder="পরিমাণ লিখুন">
        
        <label>পাসফ্রেজ / পাসকোড:</label>
        <input type="password" id="passcode" placeholder="আপনার সিক্রেট পাসফ্রেজ দিন">
        
        <button onclick="sendMoney()" style="margin-top:10px;">টোকেন ট্রান্সফার করুন</button>
    </div>

    <div id="result">আউটপুট এখানে দেখাবে...</div>
</div>

<script>
    async function registerUser() {
        const username = document.getElementById('reg_username').value;
        if(!username) {
            alert("দয়া করে নাম লিখুন!");
            return;
        }
        try {
            let response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username })
            });
            let data = await response.json();
            if(response.ok) {
                document.getElementById('result').innerHTML = `<b>সফল!</b> একাউন্ট তৈরি হয়েছে।<br><b>আপনার সিক্রেট পাসফ্রেজ (সংরক্ষণ করুন):</b> <span style="color:red; user-select:all;">${data.passphrase}</span>`;
            } else {
                document.getElementById('result').innerHTML = `ত্রুটি: ${data.error}`;
            }
        } catch (e) {
            document.getElementById('result').innerHTML = "সার্ভার কানেক্ট করা যায়নি!";
        }
    }

    async function checkBalance() {
        const user = document.getElementById('username').value;
        try {
            let response = await fetch(`/balance/${user}`);
            let data = await response.json();
            if (response.ok) {
                let balancesHTML = "";
                for (let [token, bal] of Object.entries(data.balances)) {
                    balancesHTML += `<li>${token}: <b>${bal}</b></li>`;
                }
                document.getElementById('result').innerHTML = `<b>${data.username}</b>-এর মাল্টি-টোকেন ব্যালেন্স:<ul>${balancesHTML}</ul>`;
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
        const token = document.getElementById('token').value;
        const amount = parseFloat(document.getElementById('amount').value);
        const passcode = document.getElementById('passcode').value;

        try {
            let response = await fetch('/transfer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender, receiver, amount, token, passcode })
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

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'ইউজারনেম দিন!'}), 400
    
    passphrase, msg = blockchain.register_user(username)
    if not passphrase:
        return jsonify({'error': msg}), 400
    
    return jsonify({'message': msg, 'passphrase': passphrase}), 201

@app.route('/balance/<username>', methods=['GET'])
def balance(username):
    balances = blockchain.get_balances(username)
    if balances is None:
        return jsonify({'error': 'ইউজার পাওয়া যায়নি!'}), 404
    return jsonify({'username': username, 'balances': balances}), 200

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'ডাটা পাওয়া যায়নি!'}), 400

    sender = data.get('sender')
    receiver = data.get('receiver')
    amount = data.get('amount')
    token = data.get('token', 'BDT')
    passcode = data.get('passcode')

    if not sender or not receiver or amount is None or not passcode:
        return jsonify({'error': 'সব তথ্য সঠিকভাবে দিন!'}), 400

    if sender not in blockchain.users:
        return jsonify({'error': 'প্রেরক অ্যাকাউন্ট বিদ্যমান নেই!'}), 404

    if blockchain.users[sender]['passphrase'] != passcode:
        return jsonify({'error': 'ভুল পাসফ্রেজ (Passphrase)! সঠিক পাসফ্রেজ দিন।'}), 401

    current_balances = blockchain.get_balances(sender)
    if current_balances.get(token, 0) < amount:
        return jsonify({'error': f'অপর্যাপ্ত {token} ব্যালেন্স!'}), 400

    blockchain.add_transaction(sender, receiver, amount, token)
    previous_block = blockchain.get_last_block()
    previous_hash = blockchain.hash(previous_block)
    blockchain.create_block(previous_hash, passcode)

    return jsonify({'message': f'{amount} {token} সফলভাবে ট্রান্সফার হয়েছে!'}), 201

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
