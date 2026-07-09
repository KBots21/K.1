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
    requests.post(url, json=payload)

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
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()
        
        if 'error' in data:
            return f"API Error: {data['error']['message']}\n\nTry /scan instead."
        
        # Extract text from Gemini response
        analysis = data['candidates'][0]['content']['parts'][0]['text']
        return analysis
        
    except Exception as e:
        return f"Error getting analysis: {str(e)}\n\nTry: /scan for a pre-built mega-cap list."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text.startswith("/start"):
            send_telegram_message(chat_id, 
                "FCN Stock Bot\n\n"
                "Commands:\n"
                "/scan — Daily mega-cap FCN scan\n"
                "/analyze [TICKER] — Analyze any stock\n"
                "/help — Show help\n\n"
                "Example: /analyze AAPL")
        
        elif text.startswith("/scan"):
            scan = """Daily Mega-Cap FCN Scan

Tier 1 — Best FCN Candidates:
• BRK.B — Range-bound, fortress BS, Buffett's cash pile
• V — Payment rails, low vol, predictable FCF
• KO — Dividend aristocrat, historically tight range
• JNJ — Post-Kenvue, strong pharma BS
• PG — Consumer staples king, low beta

Tier 2 — Growth + Consolidation:
• AAPL — Only if range-bound; $200B+ cash
• MSFT — AI/cloud; wait for consolidation
• GOOGL — Search + AI; watch for range entry
• AMZN — AWS growth; post-earnings ranges work

Tier 3 — Higher Volatility:
• NVDA — AI leader; only for wide-barrier FCNs
• META — Social + AI; volatile but strong BS
• TSLA — Too volatile; skip standard FCNs

Currently Trending (Skip for now):
• AGX — Strong uptrend, not sideways
"""
            send_telegram_message(chat_id, scan)
        
        elif text.startswith("/analyze"):
            ticker = text.replace("/analyze", "").strip().upper()
            if ticker:
                send_telegram_message(chat_id, f"Analyzing {ticker}...")
                analysis = get_ai_analysis(ticker)
                send_telegram_message(chat_id, analysis)
            else:
                send_telegram_message(chat_id, "Usage: /analyze AAPL")
        
        elif text.startswith("/help"):
            send_telegram_message(chat_id, 
                "/scan — Daily pre-built FCN scan (no API cost)\n"
                "/analyze [TICKER] — AI analysis of any stock (uses Gemini)\n"
                "/help — This message\n\n"
                "Note: /analyze uses Google Gemini free tier.")
        
        else:
            send_telegram_message(chat_id, 
                "Unknown command. Try /scan or /analyze [TICKER]")
    
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
