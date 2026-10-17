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
        self.wallets = {}  # phrase -> { 'name': str, 'balances': { 'BDT': float, 'SOL': float, 'USDT': float } }
        self.total_holders = []
        
        # জেনেসিস ব্লক এবং ১ ট্রিলিয়ন বেস কারেন্সি BDT সাপ্লাই
        initial_balances = {'BDT': 1000000000000.0, 'SOL': 10.0, 'USDT': 5000.0}
        genesis_phrase = "bdt-genesis-master-recovery-phrase-2026"
        self.wallets[genesis_phrase] = {
            'name': 'Genesis Vault',
            'balances': initial_balances
        }
        self.total_holders.append(genesis_phrase)
        self.create_block(previous_hash='1', phrase=genesis_phrase)

    def create_block(self, previous_hash, phrase):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'previous_hash': previous_hash,
            'creator': phrase
        }
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def create_wallet(self, name):
        phrase = "bdt-" + str(uuid.uuid4()) + "-" + str(uuid.uuid4())
        self.wallets[phrase] = {
            'name': name,
            'balances': {'BDT': 1000.0, 'SOL': 0.1, 'USDT': 10.0}  # ফ্রি স্টার্টিং ব্যালেন্স
        }
        if phrase not in self.total_holders:
            self.total_holders.append(phrase)
        return phrase

    def import_wallet(self, phrase):
        if phrase in self.wallets:
            return True, self.wallets[phrase]['name']
        return False, "ভুল রিকভারি ফ্রেজ!"

    def distribute_fee(self, fee_amount):
        if len(self.total_holders) == 0:
            return
        share = fee_amount / len(self.total_holders)
        for h_phrase in self.total_holders:
            self.wallets[h_phrase]['balances']['BDT'] += share

    def add_transaction(self, sender_phrase, receiver_phrase, amount, token):
        sender_bal = self.wallets[sender_phrase]['balances'].get(token, 0)
        
        # ট্রানজেকশন ফি (১% কাটা হবে এবং হোল্ডারদের মধ্যে ডিস্ট্রিবিউট হবে)
        fee = amount * 0.01 if token == 'BDT' else 0
        total_deduct = amount + fee

        if sender_bal < total_deduct:
            return False, "অপর্যাপ্ত ব্যালেন্স ও ফি!"

        # ব্যালেন্স কাটাকাটি
        self.wallets[sender_phrase]['balances'][token] -= total_deduct
        
        if receiver_phrase not in self.wallets:
            # যদি প্রাপক নতুন হয়, তার জন্য স্বয়ংক্রয় ওয়ালেট তৈরি
            rec_name = "Wallet_" + receiver_phrase[:6]
            self.wallets[receiver_phrase] = {'name': rec_name, 'balances': {token: 0}}
            if receiver_phrase not in self.total_holders:
                self.total_holders.append(receiver_phrase)
        
        if token not in self.wallets[receiver_phrase]['balances']:
            self.wallets[receiver_phrase]['balances'][token] = 0
            
        self.wallets[receiver_phrase]['balances'][token] += amount

        # ফি ডিস্ট্রিবিউশন
        if fee > 0:
            self.distribute_fee(fee)

        self.pending_transactions.append({
            'sender': sender_phrase[:8] + '...',
            'receiver': receiver_phrase[:8] + '...',
            'amount': amount,
            'token': token,
            'fee': fee
        })
        
        prev_block = self.get_last_block()
        prev_hash = hashlib.sha256(json.dumps(prev_block, sort_keys=True).encode()).hexdigest()
        self.create_block(prev_hash, sender_phrase)
        
        return True, f"সফল! ফি কাটা হয়েছে {fee} BDT যা অন্যান্য হোল্ডারদের মাঝে ডিস্ট্রিবিউট করা হয়েছে।"

app = Flask(__name__)
blockchain = BDTBlockchain()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDT Web3 Multi-Token Wallet</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: #e0e0e0; margin: 0; padding: 15px; }
        .container { max-width: 420px; background: #1e1e1e; padding: 20px; border-radius: 16px; box-shadow: 0px 8px 24px rgba(0,0,0,0.5); margin: auto; border: 1px solid #333; }
        h2 { text-align: center; color: #fbc02d; margin-bottom: 5px; }
        .subtitle { text-align: center; font-size: 12px; color: #888; margin-bottom: 20px; }
        .card { background: #2a2a2a; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #444; }
        label { display: block; font-weight: bold; margin-bottom: 5px; font-size: 13px; color: #bbb; }
        input, select, button { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #555; border-radius: 8px; box-sizing: border-box; background: #333; color: #fff; font-size: 14px; }
        button { background: #fbc02d; color: #121212; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background: #f57f17; }
        .btn-blue { background: #29b6f6; color: #121212; }
        .btn-blue:hover { background: #0288d1; }
        #result { margin-top: 15px; padding: 12px; background: #252525; border-radius: 8px; word-break: break-all; font-size: 13px; border-left: 4px solid #fbc02d; }
        ul { padding-left: 15px; margin: 5px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>BDT Web3 Wallet</h2>
    <div class="subtitle">Base Currency: BDT (1 Trillion Supply) + Solana Support</div>

    <!-- নতুন ওয়ালেট তৈরি -->
    <div class="card">
        <h3>➕ Create new wallet</h3>
        <label>ওয়ালেটের নাম:</label>
        <input type="text" id="wallet_name" placeholder="যেমন: My Main Wallet">
        <button class="btn-blue" onclick="createWallet()" style="margin-top:10px;">নতুন ওয়ালেট তৈরি করুন</button>
    </div>

    <!-- ফেজ কোড দিয়ে লগইন / ইমপোর্ট -->
    <div class="card">
        <h3>📥 Import existing wallet</h3>
        <label>রিকভারি ফেজ কোড (Recovery Phrase):</label>
        <input type="text" id="import_phrase" placeholder="আপনার ফেজ কোড এখানে পেস্ট করুন">
        <button onclick="importWallet()" style="margin-top:10px;">ওয়ালেটে প্রবেশ করুন</button>
    </div>

    <!-- ব্যালেন্স ও ট্রান্সফার সেকশন -->
    <div class="card" id="dashboard" style="display:none;">
        <h3 id="wel_name" style="color: #29b6f6; margin-top:0;"></h3>
        <div id="balance_box"></div>
        
        <hr style="border-color: #444; margin: 15px 0;">
        
        <h3>🚀 Send Crypto / BDT</h3>
        <label>আমার ফেজ কোড (Sender Phrase):</label>
        <input type="text" id="sender_phrase" placeholder="আপনার ফেজ কোড দিন">

        <label>প্রাপকের ফেজ কোড বা আইডি:</label>
        <input type="text" id="receiver_phrase" placeholder="প্রাপকের ফেজ কোড দিন">
        
        <label>কারেন্সি / টোকেন:</label>
        <select id="token">
            <option value="BDT">BDT (Base Currency - 1 Trillion)</option>
            <option value="SOL">Solana (SOL)</option>
            <option value="USDT">USDT (Tether)</option>
        </select>

        <label>পরিমাণ:</label>
        <input type="number" id="amount" placeholder="পরিমাণ লিখুন">
        
        <button onclick="sendToken()" style="margin-top:10px;">সেন্ড করুন (১% ফি ডিস্ট্রিবিউশনসহ)</button>
    </div>

    <div id="result">আপনার ওয়ালেট অ্যাক্টিভিটি এখানে দেখাবে...</div>
</div>

<script>
    async function createWallet() {
        const name = document.getElementById('wallet_name').value;
        if(!name) { alert("ওয়ালেটের নাম দিন!"); return; }
        let res = await fetch('/create_wallet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        let data = await res.json();
        if(res.ok) {
            document.getElementById('result').innerHTML = `<b>সফল! নতুন ওয়ালেট তৈরি হয়েছে।</b><br>আপনার সিক্রেট ফেজ কোড (সংরক্ষণ করুন): <br><span style="color:#fbc02d; user-select:all; font-weight:bold;">${data.phrase}</span>`;
            document.getElementById('import_phrase').value = data.phrase;
            document.getElementById('sender_phrase').value = data.phrase;
        } else {
            document.getElementById('result').innerHTML = data.error;
        }
    }

    async function importWallet() {
        const phrase = document.getElementById('import_phrase').value;
        if(!phrase) { alert("ফেজ কোড দিন!"); return; }
        let res = await fetch('/import_wallet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phrase})
        });
        let data = await res.json();
        if(res.ok) {
            document.getElementById('dashboard').style.display = 'block';
            document.getElementById('wel_name').innerText = `Welcome: ${data.name}`;
            document.getElementById('sender_phrase').value = phrase;
            
            let balHtml = "<b>মাল্টি-কারেন্সি ব্যালেন্স:</b><ul>";
            for(let [k, v] of Object.entries(data.balances)) {
                balHtml += `<li><b>${k}</b>: ${v.toLocaleString()}</li>`;
            }
            balHtml += "</ul>";
            document.getElementById('balance_box').innerHTML = balHtml;
            document.getElementById('result').innerHTML = "ওয়ালেট সফলভাবে লোড হয়েছে!";
        } else {
            document.getElementById('result').innerHTML = data.error;
        }
    }

    async function sendToken() {
        const sender_phrase = document.getElementById('sender_phrase').value;
        const receiver_phrase = document.getElementById('receiver_phrase').value;
        const token = document.getElementById('token').value;
        const amount = parseFloat(document.getElementById('amount').value);

        if(!sender_phrase || !receiver_phrase || isNaN(amount)) {
            alert("সব তথ্য সঠিকভাবে পূরণ করুন!");
            return;
        }

        let res = await fetch('/transfer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({sender_phrase, receiver_phrase, amount, token})
        });
        let data = await res.json();
        if(res.ok) {
            document.getElementById('result').innerHTML = `✅ ${data.message}`;
            importWallet(); // ব্যালেন্স রিফ্রেশ
        } else {
            document.getElementById('result').innerHTML = `❌ ${data.error}`;
        }
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/create_wallet', methods=['POST'])
def api_create_wallet():
    data = request.get_json()
    name = data.get('name', 'My Wallet')
    phrase = blockchain.create_wallet(name)
    return jsonify({'phrase': phrase}), 201

@app.route('/import_wallet', methods=['POST'])
def api_import_wallet():
    data = request.get_json()
    phrase = data.get('phrase', '')
    success, info = blockchain.import_wallet(phrase)
    if not success:
        return jsonify({'error': info}), 404
    
    balances = blockchain.wallets[phrase]['balances']
    return jsonify({'name': info, 'balances': balances}), 200

@app.route('/transfer', methods=['POST'])
def api_transfer():
    data = request.get_json()
    sender_phrase = data.get('sender_phrase')
    receiver_phrase = data.get('receiver_phrase')
    amount = data.get('amount')
    token = data.get('token', 'BDT')

    if not sender_phrase or not receiver_phrase or amount is None:
        return jsonify({'error': 'সব ফিল্ড পূরণ করুন!'}), 400

    if sender_phrase not in blockchain.wallets:
        return jsonify({'error': 'প্রেরকের ওয়ালেট পাওয়া যায়নি!'}), 404

    success, msg = blockchain.add_transaction(sender_phrase, receiver_phrase, amount, token)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg}), 201

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
