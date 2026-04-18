import requests
import time
import os

# --- الإعدادات الاحترافية ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# معايير "النمو المنظم" (نمط PALU / JANITOR)
TARGET_CHAIN = "bsc"
MIN_LIQ = 15000             # سيولة "أرضية" لضمان عدم الانهيار المفاجئ
MAX_MCAP = 400000           # الدخول في مرحلة الانفجار الأولى
CHECK_INTERVAL = 15         # فحص سريع لعدم فوات أي فرصة

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def scan_professional_momentum():
    # استخدام API الـ Top Boosts لاقتناص العملات التي يدعمها "صناع السوق" حالياً
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    try:
        response = requests.get(url, timeout=10).json()
        
        for item in response[:35]:
            if item.get('chainId') != TARGET_CHAIN: continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            mcap = float(p.get('fdv', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            h1_change = float(p.get('priceChange', {}).get('h1', 0))
            m5_change = float(p.get('priceChange', {}).get('m5', 0))
            
            # --- استراتيجية "الإتقان" (The Mastery Logic) ---
            # 1. شرط "الاستمرارية": صعود ساعة ممتاز (>12%) وصعود 5 دقائق حيوي (>2%)
            # 2. شرط "السيولة النشطة": السيولة كافية للشراء والبيع دون انزلاق سعري كبير
            # 3. استبعاد العملات في "مرحلة الهبوط" (مثل BLESS حالياً) عبر شرط m5_change > 0
            if MIN_LIQ < liq < 250000 and 20000 < mcap < MAX_MCAP:
                if h1_change > 12 and m5_change > 2:
                    
                    # فحص الأمان المتقدم (GoPlus)
                    sec_res = requests.get(f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={addr}", timeout=5).json()
                    sec = sec_res.get('result', {}).get(addr.lower(), {})
                    
                    if sec.get('is_honeypot') == '1' or float(sec.get('sell_tax', 0)) > 10: 
                        continue

                    # تمييز العملات ذات الطابع الصيني أو الأسماء القوية
                    is_alpha_name = any(k in p['baseToken']['symbol'].lower() for k in ["pa", "pu", "jan", "shang", "dragon"])
                    header = "🏮 *Alpha Trend (Chinese Pattern)* 🏮" if is_alpha_name else "🚀 *Momentum Breakout*"

                    msg = (
                        f"{header}\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"📈 صعود (ساعة): %{h1_change}\n"
                        f"📊 صعود (5 دقائق): %{m5_change} (تأكيد الاستمرار)\n"
                        f"💰 الماركت كاب: ${mcap:,.0f}\n"
                        f"💧 السيولة: ${liq:,.0f}\n"
                        f"🛡️ الأمان: ✅ سليم | ضريبة البيع: {sec.get('sell_tax')}% \n"
                        f"🔒 السيولة: {'🔥 محروقة' if float(sec.get('lp_burned_percent', 0)) > 50 else '🔒 مقفولة'}\n\n"
                        f"🔗 [اقتناص الفرصة](https://dexscreener.com/bsc/{addr})"
                    )
                    
                    send_telegram_msg(msg)
                    print(f"🎯 تم اكتشاف عملة بنمط صاعد: {p['baseToken']['symbol']}")
                    time.sleep(30) # منع التكرار لتركيزك على الصفقة
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram_msg("🕵️‍♂️ رادار 'إتقان الصعود' مفعّل.. استبعاد الهبوط واقتناص الزخم الحقيقي!")
    while True:
        scan_professional_momentum()
        time.sleep(CHECK_INTERVAL)
