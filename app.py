from flask import Flask, jsonify, request, render_template_string
import hashlib
import json
import requests
import os

app = Flask(__name__)

class DistributedFeeDOTBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.wallets = {}
        self.total_holders = []
        
        # মাস্টার ভল্ট ও লিকুইডিটি পুল (১ ট্রিলিয়ন DOT এবং মাইক্রো SOL রিজার্ভ)
        self.master_address = "DOT_GENESIS_VAULT_1TRILLION"
        self.wallets[self.master_address] = {
            'name': 'DOT Master Liquidity Vault',
            'balances': {
                'DOT': 1000000000000.0,  # ১ ট্রিলিয়ন DOT বেস কারেন্সি
                'SOL': 0.0000833         # প্রাথমিক ক্ষুদ্র লিকুইডিটি
            }
        }
        self.total_holders.append(self.master_address)
        
        # জেনেসিস ব্লক তৈরি
        self.create_block(previous_hash="0", proof=100)

    def create_block(self, previous_hash, proof):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': 0,
            'transactions': self.pending_transactions,
            'proof': proof,
            'previous_hash': previous_hash
        }
        self.pending_transactions = []
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def hash_block(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def create_wallet(self, address, name):
        if address in self.wallets:
            return False, "Wallet already exists!"
        
        self.wallets[address] = {
            'name': name,
            'balances': {'DOT': 0.0, 'SOL': 0.0}
        }
        if address not in self.total_holders:
            self.total_holders.append(address)
        return True, "Wallet registered successfully!"

    def get_amm_price(self):
        pool = self.wallets[self.master_address]['balances']
        dot_reserve = pool['DOT']
        sol_reserve = pool['SOL']
        
        if sol_reserve <= 0:
            return {'dot_per_sol': 12000.0, 'dot_reserve': dot_reserve, 'sol_reserve': sol_reserve}
        
        dot_per_sol = dot_reserve / sol_reserve
        return {
            'dot_per_sol': dot_per_sol,
            'dot_reserve': dot_reserve,
            'sol_reserve': sol_reserve
        }

    def cross_chain_deposit_and_swap(self, address, sol_amount):
        """ সোলানা ডিপোজিট ও AMM সোয়াপ, যেখানে ফি কেটে বাকি অংশ হোল্ডারদের মধ্যে ভাগ করে দেওয়া হয় """
        if address not in self.wallets:
            self.create_wallet(address, "Phantom User")

        pool = self.wallets[self.master_address]['balances']
        user_bal = self.wallets[address]['balances']

        # কনস্ট্যান্ট প্রোডাক্ট k = x * y
        k = pool['DOT'] * pool['SOL']
        
        # মোট ট্রানজেকশন ফি (যেমন ১%)
        total_fee = sol_amount * 0.01
        net_sol = sol_amount - total_fee

        # AMM ফর্মুলা অনুযায়ী DOT আউটপুট হিসাব
        new_sol_reserve = pool['SOL'] + net_sol
        new_dot_reserve = k / new_sol_reserve
        dot_output = pool['DOT'] - new_dot_reserve

        if dot_output > pool['DOT']:
            return False, "Liquidity calculation error!"

        # মাস্টার ভল্ট আপডেট
        pool['SOL'] += net_sol
        pool['DOT'] -= dot_output

        # ইউজার তার মূল পাওনা DOT পেলো
        user_bal['DOT'] = user_bal.get('DOT', 0.0) + dot_output

        # --- ফি ডিস্ট্রিবিউশন লজিক (খরচ বা ফি কেটে সবার মধ্যে ভাগ করে দেওয়া) ---
        # ফি হিসেবে কাটা SOL বা এর সমপরিমাণ DOT সমস্ত হোল্ডারদের মধ্যে সমানভাবে ভাগ হবে
        fee_in_dot = total_fee * (pool['DOT'] / pool['SOL']) if pool['SOL'] > 0 else total_fee * 12000
        
        distributed_count = len(self.total_holders)
        if distributed_count > 0:
            share_per_holder = fee_in_dot / distributed_count
            for holder in self.total_holders:
                if holder in self.wallets:
                    self.wallets[holder]['balances']['DOT'] += share_per_holder
        else:
            share_per_holder = 0.0

        self.pending_transactions.append({
            'type': 'FEE_DISTRIBUTED_SWAP',
            'address': address,
            'sol_deposited': sol_amount,
            'fee_distributed': fee_in_dot,
            'holders_shared': distributed_count
        })

        last_block = self.get_last_block()
        last_hash = self.hash_block(last_block)
        self.create_block(previous_hash=last_hash, proof=777)

        return True, f"Success! Swapped {sol_amount} SOL. Fee ({fee_in_dot:.2f} DOT equivalent) distributed among {distributed_count} holders."

blockchain = DistributedFeeDOTBlockchain()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOT Blockchain & Fee Redistribution AMM</title>
    <script src="https://unpkg.com/@solana/web3.js@latest/lib/index.iife.min.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f1f5f9; margin: 0; padding: 15px; }
        .container { max-width: 440px; background: #111827; padding: 20px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); margin: auto; border: 1px solid #1f2937; }
        h2 { text-align: center; color: #38bdf8; margin-bottom: 5px; }
        .subtitle { text-align: center; font-size: 11px; color: #9ca3af; margin-bottom: 20px; }
        .card { background: #0b0f19; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #1f2937; }
        label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 12px; color: #93c5fd; }
        input, button { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #374151; border-radius: 8px; box-sizing: border-box; background: #111827; color: #fff; font-size: 13px; }
        button { background: #38bdf8; color: #0b0f19; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0ea5e9; }
        .btn-purple { background: #8b5cf6; color: #fff; }
        .btn-purple:hover { background: #7c3aed; }
        .btn-green { background: #10b981; color: #fff; }
        .btn-green:hover { background: #059669; }
        .btn-orange { background: #f59e0b; color: #fff; }
        .btn-orange:hover { background: #d97706; }
        #result { margin-top: 15px; padding: 12px; background: #111827; border-radius: 8px; word-break: break-all; font-size: 12px; border-left: 4px solid #38bdf8; }
        ul { padding-left: 15px; margin: 5px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>DOT Tokenomics</h2>
    <div class="subtitle">1 Trillion Supply + Fee Reflection & Distribution</div>

    <!-- Phantom Wallet Connection -->
    <div class="card">
        <h3>🦊 Phantom Wallet (Solana Devnet)</h3>
        <button class="btn-purple" onclick="connectPhantom()">Connect Phantom Wallet</button>
        <div id="wallet_status" style="font-size: 11px; color: #9ca3af; margin-top: 8px; word-break: break-all;">Status: Not Connected</div>
    </div>

    <!-- Dashboard & Balances -->
    <div class="card" id="dashboard" style="display:none;">
        <h3 style="color: #38bdf8; margin-top:0;">📊 Account Balances</h3>
        <div id="balance_box"></div>
        
        <hr style="border-color: #1f2937; margin: 15px 0;">
        
        <h3>🌐 Cross-Chain Deposit & Fee Share</h3>
        <label>SOL Amount to Deposit (Real Devnet):</label>
        <input type="number" id="sol_deposit_amount" placeholder="0.01" step="0.001">
        
        <button class="btn-orange" onclick="executeRealSolDeposit()" style="margin-top:10px;">Deposit SOL & Get DOT (Fee Shared)</button>
    </div>

    <!-- Live Market Rates -->
    <div class="card">
        <h3>📈 AMM Pool & Holders Info</h3>
        <button onclick="fetchPoolRates()">Check Pool Status</button>
        <div id="rates_view" style="font-size:11px; margin-top:10px; color:#9ca3af;">Click button to load pool data.</div>
    </div>

    <div id="result">System ready. Connect Phantom wallet to participate.</div>
</div>

<script>
    let provider = null;
    let userPublicKey = null;
    const SOLANA_NETWORK = "https://api.devnet.solana.com";

    async function connectPhantom() {
        if ("solana" in window) {
            provider = window.solana;
            if (provider.isPhantom) {
                try {
                    const res = await provider.connect();
                    userPublicKey = res.publicKey.toString();
                    document.getElementById('wallet_status').innerHTML = `Connected: <b>${userPublicKey}</b>`;
                    document.getElementById('result').innerHTML = "✅ Phantom Connected!";
                    document.getElementById('dashboard').style.display = 'block';
                    loadDotBalances();
                } catch (err) {
                    alert("Connection rejected.");
                }
            }
        } else {
            window.open("https://phantom.app/", "_blank");
        }
    }

    async function loadDotBalances() {
        if(!userPublicKey) return;
        let res = await fetch(`/wallet/${userPublicKey}`);
        let data = await res.json();
        
        let html = "<ul>";
        if(res.ok) {
            for(let [k, v] of Object.entries(data.balances)) {
                html += `<li><b>${k}</b>: ${v.toLocaleString(undefined, {maximumFractionDigits: 4})}</li>`;
            }
        } else {
            html += "<li><b>DOT</b>: 0</li>";
        }
        html += "</ul>";
        document.getElementById('balance_box').innerHTML = html;
    }

    async function executeRealSolDeposit() {
        const solAmount = parseFloat(document.getElementById('sol_deposit_amount').value);
        if(isNaN(solAmount) || solAmount <=0) { alert("Enter valid SOL amount!"); return; }

        try {
            document.getElementById('result').innerHTML = "⏳ Processing Solana Devnet transaction...";
            const connection = new solanaWeb3.Connection(SOLANA_NETWORK, 'confirmed');
            
            const transaction = new solanaWeb3.Transaction().add(
                solanaWeb3.SystemProgram.transfer({
                    fromPubkey: new solanaWeb3.PublicKey(userPublicKey),
                    toPubkey: new solanaWeb3.PublicKey(userPublicKey),
                    lamports: solAmount * solanaWeb3.LAMPORTS_PER_SOL,
                })
            );

            const { blockhash } = await connection.getLatestBlockhash();
            transaction.recentBlockhash = blockhash;
            transaction.feePayer = new solanaWeb3.PublicKey(userPublicKey);

            const signed = await provider.signAndSendTransaction(transaction);
            
            let res = await fetch('/cross_chain_swap', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({address: userPublicKey, sol_amount: solAmount})
            });
            let data = await res.json();

            if(res.ok) {
                document.getElementById('result').innerHTML = `🎉 ${data.message} | Sig: ${signed.signature.slice(0,10)}...`;
                loadDotBalances();
                fetchPoolRates();
            } else {
                document.getElementById('result').innerHTML = `❌ ${data.error}`;
            }

        } catch (err) {
            document.getElementById('result').innerHTML = `❌ Transaction Failed: ${err.message}`;
        }
    }

    async function fetchPoolRates() {
        let res = await fetch('/pool_info');
        let data = await res.json();
        let html = `<ul>
            <li>1 SOL = <b>${data.dot_per_sol.toFixed(2)} DOT</b></li>
            <li>Total Registered Holders: <b>${data.total_holders}</b></li>
            <li>Pool DOT Reserve: ${data.dot_reserve.toLocaleString(undefined, {maximumFractionDigits: 2})} DOT</li>
        </ul>`;
        document.getElementById('rates_view').innerHTML = html;
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/wallet/<address>', methods=['GET'])
def api_get_wallet(address):
    if address not in blockchain.wallets:
        return jsonify({'name': 'User', 'balances': {'DOT': 0.0, 'SOL': 0.0}}), 200
    w = blockchain.wallets[address]
    return jsonify({'name': w['name'], 'balances': w['balances']}), 200

@app.route('/pool_info', methods=['GET'])
def api_pool_info():
    prices = blockchain.get_amm_price()
    prices['total_holders'] = len(blockchain.total_holders)
    return jsonify(prices), 200

@app.route('/cross_chain_swap', methods=['POST'])
def api_cross_chain_swap():
    data = request.get_json()
    success, msg = blockchain.cross_chain_deposit_and_swap(
        data.get('address'),
        float(data.get('sol_amount', 0))
    )
    if not success:
        return jsonify({'error': msg}), 400
    return jsonify({'message': msg}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
