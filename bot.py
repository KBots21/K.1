import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def get_ai_analysis(stock_query):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = f"""You are an FCN (Fixed Coupon Note) stock analyst.
Analyze {stock_query} for:
1. Balance sheet strength
2. Whether it's trading sideways (range-bound)
3. 6-month catalyst potential
4. FCN suitability grade (A+ to F)

Be concise. Use bullet points. Current date: July 2026."""
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 500,
            "temperature": 0.3
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        
        if 'error' in data:
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            return f"⚠️ Gemini API Error: {error_msg}\n\nTry /scan for a static list instead."
        
        if 'candidates' not in data or not data['candidates']:
            return "⚠️ No response from Gemini. The model may be busy.\n\nTry again in a moment, or use /scan."
        
        analysis = data['candidates'][0]['content']['parts'][0]['text']
        return analysis
        
    except requests.exceptions.Timeout:
        return "⏱️ Gemini took too long to respond.\n\nThe free tier can be slow during peak hours. Try again later, or use /scan."
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error to Gemini.\n\nCheck your internet or try again later. Use /scan as backup."
    except Exception as e:
        return f"❌ Error: {str(e)}\n\nTry /scan for a pre-built mega-cap list."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text.startswith("/start"):
            send_telegram_message(chat_id, 
                "🤖 *FCN Stock Bot*\n\n"
                "Commands:\n"
                "• /scan — Daily mega-cap FCN scan\n"
                "• /analyze [TICKER] — Analyze any stock\n"
                "• /help — Show help\n\n"
                "Example: /analyze AAPL")
        
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
        
        elif text.startswith("/analyze"):
            ticker = text.replace("/analyze", "").strip().upper()
            if ticker:
                # Send immediate feedback
                send_telegram_message(chat_id, f"🔍 Analyzing {ticker}... (this may take 10-15 seconds on free tier)")
                
                # Get analysis
                analysis = get_ai_analysis(ticker)
                
                # Send result
                send_telegram_message(chat_id, f"📈 *{ticker} Analysis*\n\n{analysis}")
            else:
                send_telegram_message(chat_id, "Usage: /analyze AAPL")
        
        elif text.startswith("/help"):
            send_telegram_message(chat_id, 
                "*/scan* — Daily pre-built FCN scan (instant)\n"
                "*/analyze [TICKER]* — AI analysis via Gemini (10-15 sec)\n"
                "*/help* — This message\n\n"
                "💡 *Tip:* Free tier can be slow. If /analyze hangs, use /scan.")
        
        else:
            send_telegram_message(chat_id, 
                "Unknown command. Try /scan or /analyze [TICKER]")
    
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
