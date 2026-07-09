import os
import requests
import threading
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],  # Telegram limit
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def analyze_async(chat_id, ticker):
    """Run analysis in background thread so Telegram doesn't timeout"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    # Shorter, sharper prompt
    prompt = f"""FCN analyst. Analyze {ticker}:
• Balance sheet: Strong/Weak?
• Sideways? Yes/No, range?
• 6M catalyst?
• FCN grade: A+/A/B/C/D/F

Be brief. 1 sentence per point."""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 200,  # Much shorter = faster
            "temperature": 0.1,      # Deterministic = faster
            "topP": 0.8
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()
        
        if 'error' in data:
            send_telegram_message(chat_id, f"⚠️ {ticker}: {data['error']['message']}\n\nUse /scan for instant list.")
            return
            
        if 'candidates' not in data or not data['candidates']:
            send_telegram_message(chat_id, f"⚠️ {ticker}: No response from Gemini. Try again or use /scan.")
            return
        
        analysis = data['candidates'][0]['content']['parts'][0]['text']
        send_telegram_message(chat_id, f"📈 *{ticker}*\n\n{analysis}")
        
    except requests.exceptions.Timeout:
        send_telegram_message(chat_id, f"⏱️ {ticker}: Gemini timed out. Free tier is slow during peak hours.\n\nTry /scan for instant results.")
    except Exception as e:
        send_telegram_message(chat_id, f"❌ {ticker}: Error - {str(e)[:100]}\n\nUse /scan.")

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if "message" not in data:
        return "OK", 200
        
    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")
    
    if text.startswith("/start"):
        send_telegram_message(chat_id, 
            "🤖 *FCN Stock Bot*\n\n"
            "Commands:\n"
            "• /scan — Instant mega-cap FCN scan\n"
            "• /analyze [TICKER] — AI analysis (free tier, ~10-20 sec)\n"
            "• /help — Show help")
        return "OK", 200
    
    elif text.startswith("/scan"):
        scan = """📊 *Daily Mega-Cap FCN Scan*

*Tier 1 — Best FCN Candidates:*
• BRK.B — Range-bound, fortress BS
• V — Payment rails, low vol
• KO — Dividend aristocrat, tight range
• JNJ — Post-Kenvue, strong pharma BS
• PG — Consumer staples king, low beta

*Tier 2 — Growth + Consolidation:*
• AAPL — Only if range-bound; $200B+ cash
• MSFT — AI/cloud; wait for consolidation
• GOOGL — Search + AI; watch for range entry
• AMZN — AWS growth; post-earnings ranges work

*Tier 3 — Higher Volatility:*
• NVDA — AI leader; only for wide-barrier FCNs
• META — Social + AI; volatile but strong BS
• TSLA — Too volatile; skip standard FCNs

*Skip for Now:*
• AGX — Strong uptrend, not sideways
"""
        send_telegram_message(chat_id, scan)
        return "OK", 200
    
    elif text.startswith("/analyze"):
        ticker = text.replace("/analyze", "").strip().upper()
        if not ticker:
            send_telegram_message(chat_id, "Usage: /analyze AAPL")
            return "OK", 200
            
        # Send immediate acknowledgment
        send_telegram_message(chat_id, f"🔍 *{ticker}* — Analysis starting...")
        
        # Run analysis in background thread (non-blocking)
        thread = threading.Thread(target=analyze_async, args=(chat_id, ticker))
        thread.daemon = True
        thread.start()
        
        return "OK", 200
    
    elif text.startswith("/help"):
        send_telegram_message(chat_id, 
            "*/scan* — Instant pre-built FCN scan\n"
            "*/analyze [TICKER]* — AI analysis via Gemini (~10-20 sec)\n"
            "*/help* — This message\n\n"
            "💡 Free tier can be slow. If /analyze hangs, use /scan.")
        return "OK", 200
    
    else:
        send_telegram_message(chat_id, "Unknown command. Try /scan or /analyze [TICKER]")
        return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
