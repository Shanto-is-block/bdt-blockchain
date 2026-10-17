from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)

# ডেভনেট ব্যাকএন্ড লজিক ও অ্যাকাউন্ট রেজিস্ট্রি
network_wallets = {}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BDT Web3 Real Solana Wallet</title>
    <!-- Solana Web3.js CDN -->
    <script src="https://unpkg.com/@solana/web3.js@latest/lib/index.iife.min.js"></script>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f1f5f9; margin: 0; padding: 15px; }
        .container { max-width: 440px; background: #111827; padding: 20px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.6); margin: auto; border: 1px solid #1f2937; }
        h2 { text-align: center; color: #38bdf8; margin-bottom: 5px; }
        .subtitle { text-align: center; font-size: 11px; color: #9ca3af; margin-bottom: 20px; }
        .card { background: #0b0f19; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #1f2937; }
        label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 12px; color: #93c5fd; }
        input, select, button { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #374151; border-radius: 8px; box-sizing: border-box; background: #111827; color: #fff; font-size: 13px; }
        button { background: #38bdf8; color: #0b0f19; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0ea5e9; }
        .btn-purple { background: #8b5cf6; color: #fff; }
        .btn-purple:hover { background: #7c3aed; }
        .btn-green { background: #10b981; color: #fff; }
        .btn-green:hover { background: #059669; }
        #result { margin-top: 15px; padding: 12px; background: #111827; border-radius: 8px; word-break: break-all; font-size: 12px; border-left: 4px solid #38bdf8; }
        ul { padding-left: 15px; margin: 5px 0; }
    </style>
</head>
<body>

<div class="container">
    <h2>BDT Web3 Wallet</h2>
    <div class="subtitle">Solana Devnet | Real Phantom Wallet Integration</div>

    <!-- Connect Phantom Wallet -->
    <div class="card">
        <h3>🦊 Connect Real Phantom Wallet</h3>
        <button class="btn-purple" onclick="connectPhantom()">Connect Phantom (Devnet)</button>
    </div>

    <!-- Dashboard -->
    <div class="card" id="dashboard" style="display:none;">
        <h3 style="color: #38bdf8; margin-top:0;">Connected Wallet</h3>
        <div id="wallet_pubkey" style="font-size: 11px; color: #9ca3af; word-break: break-all; margin-bottom: 10px;"></div>
        <div id="balance_box"></div>
        
        <hr style="border-color: #1f2937; margin: 15px 0;">
        
        <h3>🚀 Send Devnet SOL / Tokens</h3>
        <label>Recipient Public Key:</label>
        <input type="text" id="recipient" placeholder="Solana address...">
        
        <label>Amount (SOL):</label>
        <input type="number" id="sol_amount" placeholder="0.01" step="0.001">
        
        <button class="btn-green" onclick="sendSolanaTransaction()" style="margin-top:10px;">Send Real Devnet SOL (0.01% Fee)</button>
    </div>

    <div id="result">System activity will appear here...</div>
</div>

<script>
    let selectedPublicKey = null;
    const connection = new solanaWeb3.Connection(solanaWeb3.clusterApiUrl('devnet'), 'confirmed');

    async function connectPhantom() {
        try {
            const provider = window.solana;
            if (!provider || !provider.isPhantom) {
                alert("Phantom Wallet not found! Please install Phantom extension.");
                window.open("https://phantom.app/", "_blank");
                return;
            }
            
            const response = await provider.connect();
            selectedPublicKey = response.publicKey.toString();
            
            document.getElementById('dashboard').style.display = 'block';
            document.getElementById('wallet_pubkey').innerText = "Address: " + selectedPublicKey;
            
            // Fetch real Devnet SOL balance
            const balance = await connection.getBalance(response.publicKey);
            const solBalance = balance / solanaWeb3.LAMPORTS_PER_SOL;
            
            document.getElementById('balance_box').innerHTML = `
                <b>Balances:</b>
                <ul>
                    <li><b>SOL (Devnet)</b>: ${solBalance.toFixed(4)} SOL</li>
                    <li><b>BDT (Base Currency)</b>: 1,000,000,000 BDT</li>
                    <li><b>USDT</b>: 50.00 USDT</li>
                </ul>
            `;
            document.getElementById('result').innerHTML = "Phantom Wallet successfully connected to Solana Devnet!";
        } catch (err) {
            console.error(err);
            document.getElementById('result').innerHTML = `<span style="color:#f87171;">❌ Error: ${err.message}</span>`;
        }
    }

    async function sendSolanaTransaction() {
        if (!selectedPublicKey) {
            alert("Please connect Phantom wallet first!");
            return;
        }

        const recipientAddr = document.getElementById('recipient').value.trim();
        const amount = parseFloat(document.getElementById('sol_amount').value);

        if (!recipientAddr || isNaN(amount) || amount <= 0) {
            alert("Please enter valid recipient address and amount!");
            return;
        }

        try {
            document.getElementById('result').innerHTML = "Preparing real blockchain transaction...";
            
            const provider = window.solana;
            const senderPubKey = new solanaWeb3.PublicKey(selectedPublicKey);
            const recipientPubKey = new solanaWeb3.PublicKey(recipientAddr);

            const transaction = new solanaWeb3.Transaction().add(
                solanaWeb3.SystemProgram.transfer({
                    fromPubkey: senderPubKey,
                    toPubkey: recipientPubKey,
                    lamports: amount * solanaWeb3.LAMPORTS_PER_SOL,
                })
            );

            let blockhashObj = await connection.getLatestBlockhash();
            transaction.recentBlockhash = blockhashObj.blockhash;
            transaction.feePayer = senderPubKey;

            // Request Phantom to sign and send transaction
            const signed = await provider.signAndSendTransaction(transaction);
            await connection.confirmTransaction(signed.signature);

            document.getElementById('result').innerHTML = `✅ Real Transaction Successful!<br>Tx Signature: <a href="https://explorer.solana.com/tx/${signed.signature}?cluster=devnet" target="_blank" style="color:#38bdf8;">View on Explorer</a>`;
            connectPhantom(); // Refresh balance
        } catch (err) {
            console.error(err);
            document.getElementById('result').innerHTML = `<span style="color:#f87171;">❌ Transaction Failed: ${err.message}</span>`;
        }
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
