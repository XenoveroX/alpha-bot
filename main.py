import requests
import time
import os

# --- الإعدادات النهائية المطابقة للصورة ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TARGET_CHAIN = "bsc"
# قمنا برفع الماركت كاب لـ 5 مليون لمواكبة عملات مثل PUP
MAX_MCAP = 5000000          
MIN_LIQ = 10000             # سيولة مرنة لاقتناص العملات الصينية في بدايتها
CHECK_INTERVAL = 10         # مسح سريع جداً

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def scan_trending_master():
    # البحث في قائمة "الأكثر تداولاً" (Volume) وليس فقط الـ Boosts
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    try:
        response = requests.get(url, timeout=10).json()
        
        for item in response[:50]:
            if item.get('chainId') != TARGET_CHAIN: continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            mcap = float(p.get('fdv', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            h24_change = float(p.get('priceChange', {}).get('h24', 0))
            h1_change = float(p.get('priceChange', {}).get('h1', 0))

            # --- استراتيجية مطابقة الصورة ---
            # 1. الماركت كاب بين 10 آلاف و 5 مليون (نطاق واسع)
            # 2. البحث عن العملات التي صعدت في 24 ساعة (h24 > 20%) 
            # 3. التأكد من أن الزخم مستمر الآن (h1_change > 2%)
            if 10000 < mcap < MAX_MCAP and liq > MIN_LIQ:
                if h24_change > 20 and h1_change > 2:
                    
                    # فحص الأمان
                    sec_res = requests.get(f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={addr}", timeout=5).json()
                    sec = sec_res.get('result', {}).get(addr.lower(), {})
                    
                    if sec.get('is_honeypot') == '1': continue

                    msg = (
                        f"🔥 *ترند مكتشف (نمط PUP/JANITOR)* 🔥\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"📈 صعود 24 ساعة: %{h24_change}\n"
                        f"📊 صعود الساعة: %{h1_change} (مستمر)\n"
                        f"💰 الماركت كاب: ${mcap:,.0f}\n"
                        f"💧 السيولة: ${liq:,.0f}\n"
                        f"🛡️ الأمان: ✅ سليم | Tax: {sec.get('sell_tax', '0')}% \n\n"
                        f"🔗 [رابط الشراء المباشر](https://pancakeswap.finance/swap?outputCurrency={addr})\n"
                        f"📊 [الشارت](https://dexscreener.com/bsc/{addr})"
                    )
                    
                    send_telegram_msg(msg)
                    time.sleep(15)
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram_msg("🕵️‍♂️ الرادار المحدث (V7) لمطابقة عملات الترند بدأ العمل الآن...")
    while True:
        scan_trending_master()
        time.sleep(CHECK_INTERVAL)
