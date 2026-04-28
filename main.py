import requests
import time
import os

# --- إعدادات وضع القوة (V11) ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def scan_god_mode():
    # البحث في العملات الأكثر "دفعاً" للترند (Paid Boosts) لضمان مطابقة قائمة Alpha
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    try:
        response = requests.get(url, timeout=10).json()
        
        for item in response[:80]: # فحص قائمة موسعة جداً
            if item.get('chainId') != "bsc": continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            mcap = float(p.get('fdv', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            h24_change = float(p.get('priceChange', {}).get('h24', 0))
            h1_change = float(p.get('priceChange', {}).get('h1', 0))
            vol_24h = float(p.get('volume', {}).get('h24', 0))

            # --- استراتيجية "مطابقة الصورة" (ZKJ & KLINK Style) ---
            # 1. الماركت كاب: نقبل حتى 150 مليون دولار (ليشمل ZKJ)
            # 2. حجم التداول: يجب أن يكون ضخماً (> 150k$) لضمان أنها ليست عملة وهمية
            # 3. الصعود اليومي: نبحث عن العملات التي انفجرت فعلياً (> 30%)
            # 4. زخم الساعة: صعود مستمر (> 2%) لضمان أنك لا تشتري عند الهبوط
            if liq > 20000 and 50000 < mcap < 150000000:
                if h24_change > 30 and h1_change > 2 and vol_24h > 150000:
                    
                    msg = (
                        f"🚀 *إنذار انفجار (نمط ZKJ/KLINK)* 🚀\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"🔥 صعود 24 ساعة: %{h24_change}\n"
                        f"📈 زخم الساعة الحالية: %{h1_change}\n"
                        f"💰 الماركت كاب: ${mcap:,.0f}\n"
                        f"📊 تداول (24س): ${vol_24h:,.0f}\n\n"
                        f"📋 *عنوان العقد (لصقه في Web3 Wallet):*\n`{addr}`\n\n"
                        f"🔗 [الشارت](https://dexscreener.com/bsc/{addr})\n"
                        f"🛒 [تبديل سريع (Swap)](https://pancakeswap.finance/swap?outputCurrency={addr})"
                    )
                    
                    send_telegram_msg(msg)
                    time.sleep(15) # سرعة في الإرسال لاقتناص التالي
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram_msg("⚠️ *تم تفعيل وضع الـ God Mode V11*.. رادار الملايين والعملات الانفجارية يعمل الآن!")
    while True:
        scan_god_mode()
        time.sleep(10) # فحص متكرر جداً
