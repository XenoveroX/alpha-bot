import requests
import time
import os

# --- إعدادات Binance Alpha Sniper ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

TARGET_CHAIN = "bsc"
# رفعنا السقف لـ 250 مليون دولار لمواكبة العملات التي في صورتك
MAX_MCAP = 250000000        
# رفعنا حد السيولة لـ 50 ألف دولار للتأكد أنها عملات "ثقيلة" وآمنة
MIN_LIQUIDITY = 50000       

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def scan_binance_alpha_style():
    # البحث عن العملات التي تمتلك أعلى حجم تداول (Volume) لضمان مطابقة الصورة
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    try:
        response = requests.get(url, timeout=10).json()
        
        for item in response[:60]: # فحص قائمة أطول
            if item.get('chainId') != TARGET_CHAIN: continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            mcap = float(p.get('fdv', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            h1_change = float(p.get('priceChange', {}).get('h1', 0))
            h24_vol = float(p.get('volume', {}).get('h24', 0))

            # --- خوارزمية مطابقة الصورة ---
            # 1. البحث عن العملات ذات حجم التداول المليوني (مثل WAI و RAVE)
            # 2. التأكد من وجود صعود مستمر في آخر ساعة (h1_change > 3%)
            # 3. استبعاد العملات الصغيرة جداً التي لا تصل لـ Binance Alpha
            if liq > MIN_LIQUIDITY and mcap < MAX_MCAP:
                if h24_vol > 500000 and h1_change > 3:
                    
                    msg = (
                        f"🔥 *إشارة نمط Binance Alpha* 🔥\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"📈 صعود الساعة: %{h1_change}\n"
                        f"📊 حجم تداول (24س): ${h24_vol:,.0f}\n"
                        f"💰 الماركت كاب: ${mcap:,.0f}\n"
                        f"💧 السيولة: ${liq:,.0f}\n\n"
                        f"📋 *عنوان العقد (لصقه في Web3 Wallet):*\n`{addr}`\n\n"
                        f"🔗 [الشارت](https://dexscreener.com/bsc/{addr})\n"
                        f"🛒 [شراء مباشر](https://pancakeswap.finance/swap?outputCurrency={addr})"
                    )
                    
                    send_telegram_msg(msg)
                    # منع التكرار: ننتظر قليلاً قبل البحث عن العملة التالية
                    time.sleep(30)
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram_msg("🎯 تم تفعيل رادار Binance Alpha المحدث.. جاري اقتناص العملات المليونية!")
    while True:
        scan_binance_alpha_style()
        time.sleep(15)
