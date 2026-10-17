from flask import Flask, jsonify, request, render_template_string
import hashlib
import json
import requests
import os

app = Flask(__name__)

class HybridIndependentDOTBlockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.wallets = {}
        self.total_holders = []
        
        # মাস্টার ভল্ট ও লিকুইডিটি পুল (১ ট্রিলিয়ন DOT বেস কারেন্সি)
        self.master_address = "DOT_GENESIS_VAULT_1TRILLION"
        self.wallets[self.master_address] = {
            'name': 'DOT Master Liquidity Vault',
            'balances': {
                'DOT': 1000000000000.0,
                'SOL': 0.0000833
            }
        }
        self.total_holders.append(self.master_address)
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
            return False, "এই ওয়ালেট অ্যাড্রেসটি আগেই তৈরি করা আছে!"
        
        self.wallets[address] = {
            'name': name,
            'balances': {'DOT': 0.0, 'SOL': 0.0}
        }
        if address not in self.total_holders:
            self.total_holders.append(address)
        return True, "DOT ব্লকচেইনে সফলভাবে নিজস্ব ওয়ালেট তৈরি হয়েছে!"

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
        if address not in self.wallets:
            self.create_wallet(address, "Independent User")

        pool = self.wallets[self.master_address]['balances']
        user_bal = self.wallets[address]['balances']

        k = pool['DOT'] * pool['SOL']
        total_fee = sol_amount * 0.01
        net_sol = sol_amount - total_fee

        new_sol_reserve = pool['SOL'] + net_sol
        new_dot_reserve = k / new_sol_reserve
        dot_output = pool['DOT'] - new_dot_reserve

        if dot_output > pool['DOT']:
            return False, "লিকুইডিটি ক্যালকুলেশন ত্রুটি!"

        pool['SOL'] += net_sol
        pool['DOT'] -= dot_output
        user_bal['DOT'] = user_bal.get('DOT', 0.0) + dot_output

        fee_in_dot = total_fee * (pool['DOT'] / pool['SOL']) if pool['SOL'] > 0 else total_fee * 12000
        distributed_count = len(self.total_holders)
        
        if distributed_count > 0:
            share_per_holder = fee_in_dot / distributed_count
            for holder in self.total_holders:
                if holder in self.wallets:
                    self.wallets[holder]['balances']['DOT'] += share_per_holder

        self.pending_transactions.append({
            'type': 'CROSS_CHAIN_SWAP',
            'address': address,
            'sol_deposited': sol_amount,
            'dot_minted': dot_output
        })

        last_block = self.get_last_block()
        last_hash = self.hash_block(last_block)
        self.create_block(previous_hash=last_hash, proof=888)

        return True, f"সফল! {sol_amount} SOL দিয়ে {dot_output:.4f} DOT কেনা হয়েছে এবং ফি সব হোল্ডারদের মাঝে ভাগ করা হয়েছে।"

blockchain = HybridIndependentDOTBlockchain()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOT Native Blockchain & Cross-Chain Hub</title>
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
        .btn-green { background: #10b981; color: #fff; }
        .btn-orange { background: #f59e0b; color: #fff; }
        #result { margin-top: 15px; padding: 12px; background: #111827; border-radius: 8px; word-break: break-all; font-size: 12px; border-left: 4px solid #38bdf8; }
        ul { padding-left: 15px; margin: 5px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>DOT Blockchain Hub</h2>
    <div class="subtitle">1 Trillion Supply + Native & Cross-Chain Wallets</div>

    <!-- 1. DOT নিজস্ব ব্লকচেইন ওয়ালেট তৈরি ও লগইন -->
    <div class="card">
        <h3>👤 DOT নেটিভ ব্লকচেইন ওয়ালেট</h3>
        <label>আপনার নিজস্ব ওয়ালেট নাম বা আইডি:</label>
        <input type="text" id="native_wallet_id" placeholder="যেমন: shanto_wallet">
        <button class="btn-green" onclick="createNativeWallet()" style="margin-top:8px;">নতুন ওয়ালেট খুলুন / লগইন করুন</button>
    </div>

    <!-- 2. এক্সটার্নাল সোলানা ওয়ালেট কানেকশন -->
    <div class="card">
        <h3>🦊 এক্সটার্নাল সোলানা ওয়ালেট (Phantom)</h3>
        <button class="btn-purple" onclick="connectPhantom()">ফ্যান্টম ওয়ালেট কানেক্ট করুন</button>
        <div id="wallet_status" style="font-size: 11px; color: #9ca3af; margin-top: 8px; word-break: break-all;">স্ট্যাটাস: কানেক্টেড নয়</div>
    </div>

    <!-- ড্যাশবোর্ড ও ব্যালেন্স -->
    <div class="card" id="dashboard" style="display:none;">
        <h3 style="color: #38bdf8; margin-top:0;">📊 বর্তমান অ্যাকাউন্ট ব্যালেন্স</h3>
        <div id="balance_box"></div>
        
        <hr style="border-color: #1f2937; margin: 15px 0;">
        
        <h3>🌐 সোলানা দিয়ে DOT এক্সচেঞ্জ (Cross-Chain)</h3>
        <label>কত SOL ডিপোজিট করতে চান:</label>
        <input type="number" id="sol_deposit_amount" placeholder="0.01" step="0.001">
        <button class="btn-orange" onclick="executeCrossChainSwap()" style="margin-top:10px;">SOL পাঠিয়ে DOT নিন (মার্কেট রেট)</button>
    </div>

    <!-- পুল ইনফো -->
    <div class="card">
        <h3>📈 DOT পুল ও মার্কেট রেট</h3>
        <button onclick="fetchPoolRates()">মার্কেট স্ট্যাটাস দেখুন</button>
        <div id="rates_view" style="font-size:11px; margin-top:10px; color:#9ca3af;">স্ট্যাটাস দেখতে উপরে ক্লিক করুন।</div>
    </div>

    <div id="result">সিস্টেম প্রস্তুত। ওয়ালেট তৈরি বা কানেক্ট করুন।</div>
</div>

<script>
    let provider = null;
    let activeAddress = null;

    // নিজস্ব DOT ওয়ালেট তৈরি বা লোড করা
    async function createNativeWallet() {
        const address = document.getElementById('native_wallet_id').value.trim();
        if(!address) { alert("দয়া করে ওয়ালেট আইডি দিন!"); return; }

        let res = await fetch('/create_wallet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({address, name: "Native User"})
        });
        let data = await res.json();
        
        activeAddress = address;
        document.getElementById('result').innerHTML = `✅ ${data.message || 'ওয়ালেট লোড হয়েছে!'}`;
        loadBalances();
    }

    // ফ্যান্টম ওয়ালেট কানেক্ট করা
    async function connectPhantom() {
        if ("solana" in window) {
            provider = window.solana;
            if (provider.isPhantom) {
                try {
                    const res = await provider.connect();
                    activeAddress = res.publicKey.toString();
                    document.getElementById('wallet_status').innerHTML = `কানেক্টেড: <b>${activeAddress}</b>`;
                    document.getElementById('native_wallet_id').value = activeAddress; // অটো ফিল
                    document.getElementById('result').innerHTML = "✅ ফ্যান্টম ওয়ালেট সফলভাবে যুক্ত হয়েছে!";
                    loadBalances();
                } catch (err) {
                    alert("ওয়ালেট কানেকশন বাতিল করা হয়েছে।");
                }
            }
        } else {
            window.open("https://phantom.app/", "_blank");
        }
    }

    async function loadBalances() {
        if(!activeAddress) return;
        let res = await fetch(`/wallet/${activeAddress}`);
        let data = await res.json();
        
        let html = "<ul>";
        if(res.ok) {
            for(let [k, v] of Object.entries(data.balances)) {
                html += `<li><b>${k}</b>: ${v.toLocaleString(undefined, {maximumFractionDigits: 4})}</li>`;
            }
        }
        html += "</ul>";
        document.getElementById('balance_box').innerHTML = html;
        document.getElementById('dashboard').style.display = 'block';
    }

    async function executeCrossChainSwap() {
        const solAmount = parseFloat(document.getElementById('sol_deposit_amount').value);
        if(!activeAddress) { alert("আগে ওয়ালেট তৈরি বা কানেক্ট করুন!"); return; }
        if(isNaN(solAmount) || solAmount <= 0) { alert("সঠিক SOL পরিমাণ দিন!"); return; }

        try {
            document.getElementById('result').innerHTML = "⏳ সোলানা ডেভনেট ট্রানজেকশন প্রসেসিং হচ্ছে...";
            
            // যদি ফ্যান্টম ওয়ালেট কানেক্ট থাকে, তবে আসল ডেভনেট ট্রানজেকশন ট্রিগার হবে
            if(provider && provider.isConnected) {
                const connection = new solanaWeb3.Connection("https://api.devnet.solana.com", 'confirmed');
                const transaction = new solanaWeb3.Transaction().add(
                    solanaWeb3.SystemProgram.transfer({
                        fromPubkey: new solanaWeb3.PublicKey(activeAddress),
                        toPubkey: new solanaWeb3.PublicKey(activeAddress),
                        lamports: solAmount * solanaWeb3.LAMPORTS_PER_SOL,
                    })
                );
                const { blockhash } = await connection.getLatestBlockhash();
                transaction.recentBlockhash = blockhash;
                transaction.feePayer = new solanaWeb3.PublicKey(activeAddress);
                await provider.signAndSendTransaction(transaction);
            }

            // ব্যাকএন্ডে DOT মিন্ট ও ফি ডিস্ট্রিবিউশন
            let res = await fetch('/cross_chain_swap', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({address: activeAddress, sol_amount: solAmount})
            });
            let data = await res.json();

            if(res.ok) {
                document.getElementById('result').innerHTML = `🎉 ${data.message}`;
                loadBalances();
                fetchPoolRates();
            } else {
                document.getElementById('result').innerHTML = `❌ ${data.error}`;
            }

        } catch (err) {
            document.getElementById('result').innerHTML = `❌ ট্রানজেকশন ফেইল হয়েছে: ${err.message}`;
        }
    }

    async function fetchPoolRates() {
        let res = await fetch('/pool_info');
        let data = await res.json();
        let html = `<ul>
            <li>1 SOL = <b>${data.dot_per_sol.toFixed(2)} DOT</b></li>
            <li>মোট নিবন্ধিত হোল্ডার: <b>${data.total_holders}</b></li>
            <li>পুল DOT রিজার্ভ: ${data.dot_reserve.toLocaleString(undefined, {maximumFractionDigits: 2})} DOT</li>
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

@app.route('/create_wallet', methods=['POST'])
def api_create_wallet():
    data = request.get_json()
    success, msg = blockchain.create_wallet(data.get('address'), data.get('name'))
    return jsonify({'message': msg}), (201 if success else 200)

@app.route('/wallet/<address>', methods=['GET'])
def api_get_wallet(address):
    if address not in blockchain.wallets:
        blockchain.create_wallet(address, "User")
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
