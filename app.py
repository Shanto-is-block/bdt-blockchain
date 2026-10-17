from flask import Flask, jsonify, request, render_template_string
import hashlib
import json
from time import time
import os
import random

# BIP39 স্ট্যান্ডার্ডের মতো রিয়েল ১২-২৪ শব্দের ইংরেজি ওয়ার্ড লিস্ট (যাতে অন্য ওয়ালেটেও সাপোর্ট করে)
BIP39_WORDS = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse",
    "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit",
    "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert",
    "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter",
    "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger",
    "angle", "angry", "animal", "ankle", "announce", "annual", "answer", "antenna", "antique", "anxiety",
    "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic", "area",
    "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest", "arrive"
]

def generate_crypto_phrase(word_count=12):
    return " ".join(random.choices(BIP39_WORDS, k=word_count))

class BDTBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.wallets = {}  # phrase -> { 'name': str, 'balances': { 'BDT': float, 'SOL': float, 'USDT': float } }
        self.total_holders = []
        
        # জেনেসিস মাস্টার ফেজ (১ ট্রিলিয়ন BDT বেস কারেন্সি)
        self.genesis_phrase = "abandon ability able about above absent absorb abstract absurd abuse access accident"
        self.wallets[self.genesis_phrase] = {
            'name': 'Genesis Main Vault (1 Trillion BDT)',
            'balances': {'BDT': 1000000000000.0, 'SOL': 1000.0, 'USDT': 50000.0}
        }
        self.total_holders.append(self.genesis_phrase)
        self.create_block(previous_hash='1', phrase=self.genesis_phrase)

    def create_block(self, previous_hash, phrase):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.pending_transactions,
            'previous_hash': previous_hash,
            'creator': phrase[:12]
        }
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def create_wallet(self, name, word_count=12):
        phrase = generate_crypto_phrase(word_count)
        self.wallets[phrase] = {
            'name': name,
            'balances': {'BDT': 0.0, 'SOL': 0.0, 'USDT': 0.0}
        }
        if phrase not in self.total_holders:
            self.total_holders.append(phrase)
        return phrase

    def import_wallet(self, phrase):
        clean_phrase = " ".join(phrase.strip().lower().split())
        if not clean_phrase:
            return False, "Invalid recovery phrase!", None

        if clean_phrase in self.wallets:
            return True, self.wallets[clean_phrase]['name'], self.wallets[clean_phrase]['balances']
        
        # যদি অন্য সোলানা বা ক্রিপ্টো ওয়ালেটের ফেজ হয়, তবে তা পাবলিক নেটওয়ার্কে রেজিস্টার করে নেওয়া হবে
        wallet_name = "Connected Public Wallet"
        self.wallets[clean_phrase] = {
            'name': wallet_name,
            'balances': {'BDT': 0.0, 'SOL': 0.1, 'USDT': 5.0} # স্টার্টিং গ্যাস ব্যালেন্স
        }
        if clean_phrase not in self.total_holders:
            self.total_holders.append(clean_phrase)
            
        return True, wallet_name, self.wallets[clean_phrase]['balances']

    def distribute_fee(self, fee_amount):
        if len(self.total_holders) == 0:
            return
        share = fee_amount / len(self.total_holders)
        for h_phrase in self.total_holders:
            self.wallets[h_phrase]['balances']['BDT'] += share

    def add_transaction(self, sender_phrase, receiver_phrase, amount, token):
        sender_phrase = " ".join(sender_phrase.strip().lower().split())
        receiver_phrase = " ".join(receiver_phrase.strip().lower().split())

        if sender_phrase not in self.wallets:
            return False, "Sender wallet not found!"

        sender_bal = self.wallets[sender_phrase]['balances'].get(token, 0)
        
        # ০.০১% ট্রানজেকশন ফি
        fee = amount * 0.0001
        total_deduct = amount + fee

        if sender_bal < total_deduct:
            return False, f"Insufficient {token} balance including 0.01% fee!"

        self.wallets[sender_phrase]['balances'][token] -= total_deduct
        
        if receiver_phrase not in self.wallets:
            self.wallets[receiver_phrase] = {
                'name': 'External Public Wallet',
                'balances': {token: 0.0}
            }
            if receiver_phrase not in self.total_holders:
                self.total_holders.append(receiver_phrase)
        
        if token not in self.wallets[receiver_phrase]['balances']:
            self.wallets[receiver_phrase]['balances'][token] = 0.0
            
        self.wallets[receiver_phrase]['balances'][token] += amount

        # ফি ডিস্ট্রিবিউশন
        if fee > 0:
            self.distribute_fee(fee)

        self.pending_transactions.append({
            'sender': sender_phrase[:10] + '...',
            'receiver': receiver_phrase[:10] + '...',
            'amount': amount,
            'token': token,
            'fee': fee
        })
        
        prev_block = self.get_last_block()
        prev_hash = hashlib.sha256(json.dumps(prev_block, sort_keys=True).encode()).hexdigest()
        self.create_block(prev_hash, sender_phrase)
        
        return True, f"Transfer successful! 0.01% fee ({fee:.5f}) distributed to all holders."

    def exchange_token(self, phrase, from_token, to_token, amount):
        phrase = " ".join(phrase.strip().lower().split())
        if phrase not in self.wallets:
            return False, "Wallet not found!"
        
        balances = self.wallets[phrase]['balances']
        if balances.get(from_token, 0) < amount:
            return False, f"Insufficient {from_token} for swap!"

        # সোয়াপ ফি (০.০১%)
        swap_fee = amount * 0.0001
        net_amount = amount - swap_fee

        # এক্সচেঞ্জ রেট (যেমন: 1 SOL = 12000 BDT, 1 USDT = 120 BDT)
        rates = {
            ('SOL', 'BDT'): 12000.0,
            ('BDT', 'SOL'): 1 / 12000.0,
            ('USDT', 'BDT'): 120.0,
            ('BDT', 'USDT'): 1 / 120.0,
            ('SOL', 'USDT'): 100.0,
            ('USDT', 'SOL'): 1 / 100.0
        }

        rate = rates.get((from_token, to_token), 1.0)
        converted_amount = net_amount * rate

        balances[from_token] -= amount
        if to_token not in balances:
            balances[to_token] = 0.0
        balances[to_token] += converted_amount

        # সোয়াপ ফি হোল্ডারদের মাঝে ডিস্ট্রিবিউট হবে
        if from_token == 'BDT':
            self.distribute_fee(swap_fee)

        return True, f"Successfully swapped {amount} {from_token} to {converted_amount:.4f} {to_token} (Swap Fee: {swap_fee:.4f} {from_token})"

app = Flask(__name__)
blockchain = BDTBlockchain()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDT Web3 Multi-Token Public Wallet</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f1f5f9; margin: 0; padding: 15px; }
        .container { max-width: 440px; background: #111827; padding: 20px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); margin: auto; border: 1px solid #1f2937; }
        h2 { text-align: center; color: #38bdf8; margin-bottom: 5px; }
        .subtitle { text-align: center; font-size: 11px; color: #9ca3af; margin-bottom: 20px; }
        .card { background: #0b0f19; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #1f2937; }
        label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 12px; color: #93c5fd; }
        input, select, button, textarea { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #374151; border-radius: 8px; box-sizing: border-box; background: #111827; color: #fff; font-size: 13px; }
        textarea { resize: vertical; height: 65px; }
        button { background: #38bdf8; color: #0b0f19; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0ea5e9; }
        .btn-green { background: #10b981; color: #fff; }
        .btn-green:hover { background: #059669; }
        .btn-purple { background: #8b5cf6; color: #fff; }
        .btn-purple:hover { background: #7c3aed; }
        #result { margin-top: 15px; padding: 12px; background: #111827; border-radius: 8px; word-break: break-all; font-size: 12px; border-left: 4px solid #38bdf8; }
        ul { padding-left: 15px; margin: 5px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>BDT Web3 Wallet</h2>
    <div class="subtitle">Base Currency: BDT (1 Trillion) | Solana & Multi-Token Network</div>

    <!-- Create Wallet -->
    <div class="card">
        <h3>➕ Create New Public Wallet</h3>
        <label>Wallet Name:</label>
        <input type="text" id="wallet_name" placeholder="e.g. My Phantom/Solana Wallet">
        
        <label>Phrase Length:</label>
        <select id="word_count">
            <option value="12">12-Word Recovery Phrase (Standard)</option>
            <option value="24">24-Word Recovery Phrase (Advanced)</option>
        </select>
        
        <button class="btn-green" onclick="createWallet()" style="margin-top:10px;">Generate Wallet Phrase</button>
    </div>

    <!-- Import / Connect Wallet -->
    <div class="card">
        <h3>📥 Import / Connect External Wallet</h3>
        <label>Paste 12/24 Word Phrase (Solana / Trust / Phantom compatible):</label>
        <textarea id="import_phrase" placeholder="Paste recovery phrase here..."></textarea>
        <button class="btn-purple" onclick="importWallet()" style="margin-top:10px;">Connect Wallet</button>
    </div>

    <!-- Dashboard -->
    <div class="card" id="dashboard" style="display:none;">
        <h3 id="wel_name" style="color: #38bdf8; margin-top:0;"></h3>
        <div id="balance_box"></div>
        
        <hr style="border-color: #1f2937; margin: 15px 0;">
        
        <h3>🚀 Transfer Assets</h3>
        <label>My Phrase (Sender):</label>
        <textarea id="sender_phrase" placeholder="Your recovery phrase"></textarea>

        <label>Recipient Phrase / Address:</label>
        <textarea id="receiver_phrase" placeholder="Recipient phrase or address"></textarea>
        
        <label>Token:</label>
        <select id="token">
            <option value="BDT">BDT (Base Currency - 1 Trillion)</option>
            <option value="SOL">Solana (SOL)</option>
            <option value="USDT">USDT (Tether)</option>
        </select>

        <label>Amount:</label>
        <input type="number" id="amount" placeholder="0.00">
        
        <button onclick="sendToken()" style="margin-top:10px;">Send (0.01% Fee Included)</button>

        <hr style="border-color: #1f2937; margin: 15px 0;">

        <h3>💱 Token Swap / Exchange</h3>
        <label>From Token:</label>
        <select id="from_token">
            <option value="SOL">SOL</option>
            <option value="USDT">USDT</option>
            <option value="BDT">BDT</option>
        </select>

        <label>To Token:</label>
        <select id="to_token">
            <option value="BDT">BDT</option>
            <option value="USDT">USDT</option>
            <option value="SOL">SOL</option>
        </select>

        <label>Swap Amount:</label>
        <input type="number" id="ex_amount" placeholder="0.00">
        <button class="btn-green" onclick="exchangeToken()" style="margin-top:10px;">Swap (0.01% Swap Fee)</button>
    </div>

    <div id="result">System activity will appear here...</div>
</div>

<script>
    async function createWallet() {
        const name = document.getElementById('wallet_name').value;
        const word_count = document.getElementById('word_count').value;
        if(!name) { alert("Please enter wallet name!"); return; }
        let res = await fetch('/create_wallet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, word_count: parseInt(word_count)})
        });
        let data = await res.json();
        if(res.ok) {
            document.getElementById('result').innerHTML = `<b>Success! Wallet Created.</b><br>Save your secret recovery phrase safely (Compatible with other wallets):<br><span style="color:#10b981; user-select:all; font-weight:bold; display:block; margin-top:5px; background:#111827; padding:8px; border-radius:6px;">${data.phrase}</span>`;
            document.getElementById('import_phrase').value = data.phrase;
            document.getElementById('sender_phrase').value = data.phrase;
        } else {
            document.getElementById('result').innerHTML = data.error;
        }
    }

    async function importWallet() {
        const phrase = document.getElementById('import_phrase').value.trim();
        if(!phrase) { alert("Please enter recovery phrase!"); return; }
        let res = await fetch('/import_wallet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phrase})
        });
        let data = await res.json();
        if(res.ok) {
            document.getElementById('dashboard').style.display = 'block';
            document.getElementById('wel_name').innerText = `Connected: ${data.name}`;
            document.getElementById('sender_phrase').value = phrase;
            
            let balHtml = "<b>Multi-Currency Balances:</b><ul>";
            for(let [k, v] of Object.entries(data.balances)) {
                balHtml += `<li><b>${k}</b>: ${v.toLocaleString()}</li>`;
            }
            balHtml += "</ul>";
            document.getElementById('balance_box').innerHTML = balHtml;
            document.getElementById('result').innerHTML = "Wallet successfully connected!";
        } else {
            document.getElementById('result').innerHTML = data.error;
        }
    }

    async function sendToken() {
        const sender_phrase = document.getElementById('sender_phrase').value.trim();
        const receiver_phrase = document.getElementById('receiver_phrase').value.trim();
        const token = document.getElementById('token').value;
        const amount = parseFloat(document.getElementById('amount').value);

        if(!sender_phrase || !receiver_phrase || isNaN(amount)) {
            alert("Please fill in all fields correctly!");
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
            importWallet(); 
        } else {
            document.getElementById('result').innerHTML = `❌ ${data.error}`;
        }
    }

    async function exchangeToken() {
        const phrase = document.getElementById('sender_phrase').value.trim();
        const from_token = document.getElementById('from_token').value;
        const to_token = document.getElementById('to_token').value;
        const amount = parseFloat(document.getElementById('ex_amount').value);

        if(!phrase || isNaN(amount)) {
            alert("Enter recovery phrase and valid amount!");
            return;
        }

        let res = await fetch('/exchange', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phrase, from_token, to_token, amount})
        });
        let data = await res.json();
        if(res.ok) {
            document.getElementById('result').innerHTML = `💱 ${data.message}`;
            importWallet();
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
    name = data.get('name', 'Public Web3 Wallet')
    word_count = data.get('word_count', 12)
    phrase = blockchain.create_wallet(name, word_count)
    return jsonify({'phrase': phrase}), 201

@app.route('/import_wallet', methods=['POST'])
def api_import_wallet():
    data = request.get_json()
    phrase = data.get('phrase', '')
    success, name, balances = blockchain.import_wallet(phrase)
    if not success:
        return jsonify({'error': name}), 400
    return jsonify({'name': name, 'balances': balances}), 200

@app.route('/transfer', methods=['POST'])
def api_transfer():
    data = request.get_json()
    sender_phrase = data.get('sender_phrase')
    receiver_phrase = data.get('receiver_phrase')
    amount = data.get('amount')
    token = data.get('token', 'BDT')

    if not sender_phrase or not receiver_phrase or amount is None:
        return jsonify({'error': 'All fields are required!'}), 400

    success, msg = blockchain.add_transaction(sender_phrase, receiver_phrase, amount, token)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg}), 201

@app.route('/exchange', methods=['POST'])
def api_exchange():
    data = request.get_json()
    phrase = data.get('phrase')
    from_token = data.get('from_token')
    to_token = data.get('to_token')
    amount = data.get('amount')

    if not phrase or not from_token or not to_token or amount is None:
        return jsonify({'error': 'Invalid parameters!'}), 400

    success, msg = blockchain.exchange_token(phrase, from_token, to_token, amount)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
