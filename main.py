import requests
import time
import os

# --- الإعدادات الفائقة ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# معايير "الفا" الصارمة لشبكة BNB
TARGET_CHAIN = "bsc"
MIN_LIQ = 18000             # سيولة قوية لضمان عدم الانهيار السريع
MAX_MCAP = 450000           # الدخول المبكر قبل الانفجار الكبير
VOL_ACCELERATION = 1.5      # حجم تداول الـ 5 دقائق يجب أن يكون 1.5 مرة من المتوسط

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def get_deep_security(addr):
    """تحليل أمان عميق (GoPlus API)"""
    try:
        res = requests.get(f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={addr}", timeout=5).json()
        data = res.get('result', {}).get(addr.lower(), {})
        # شروط الأمان القاسية
        is_safe = (
            data.get('is_honeypot') == '0' and 
            data.get('is_open_source') == '1' and
            float(data.get('sell_tax', 0)) < 15 # ضريبة البيع أقل من 15%
        )
        return is_safe, data
    except: return False, {}

def scan_bnb_master():
    # سحب العملات التي بدأت "تغلي" الآن في الـ Trending
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    try:
        response = requests.get(url, timeout=10).json()
        
        for item in response[:50]: # فحص أكبر 50 عملة مرشحة للترند
            if item.get('chainId') != TARGET_CHAIN: continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            mcap = float(p.get('fdv', 0))
            liq = float(p.get('liquidity', {}).get('usd', 0))
            
            # تحليل التسارع (حجم 5 دقائق مقابل حجم ساعة)
            v5 = float(p.get('volume', {}).get('m5', 0))
            v1h = float(p.get('volume', {}).get('h1', 0))
            
            # إذا كانت السيولة والماركت كاب ضمن النطاق الذهبي
            if 15000 < mcap < MAX_MCAP and liq > MIN_LIQ:
                # خوارزمية التسارع: هل بدأ ضخ السيولة الآن؟
                if v5 > (v1h / 12) * VOL_ACCELERATION:
                    
                    is_safe, sec_data = get_deep_security(addr)
                    if not is_safe: continue

                    # تصنيف نوع الفرصة بناءً على طلبك (PALU/PUP Style)
                    is_chinese = any(k in p['baseToken']['symbol'].lower() for k in ["pa", "pu", "jan", "shang", "dragon"])
                    tag = "🏮 *عملة بنمط صيني (فرصة عالية)*" if is_chinese else "⚡ *تسارع سيولة مكتشف*"

                    msg = (
                        f"{tag}\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"💰 الماركت كاب: ${mcap:,.0f}\n"
                        f"💧 السيولة: ${liq:,.0f}\n"
                        f"📈 نمو السعر (ساعة): %{p.get('priceChange', {}).get('h1', 0)}\n"
                        f"📊 تسارع التداول (5د): ${v5:,.0f}\n"
                        f"🛡️ الأمان: ✅ سليم | ضريبة: {sec_data.get('sell_tax', '0')}% \n"
                        f"🔒 السيولة: {'محروقة 🔥' if float(sec_data.get('lp_burned_percent', 0)) > 50 else 'مقفولة 🔒'}\n\n"
                        f"🔗 [اقتنص الفرصة من هنا](https://dexscreener.com/bsc/{addr})"
                    )
                    
                    send_telegram_msg(msg)
                    print(f"🎯 تم رصد هدف BNB: {p['baseToken']['symbol']}")
                    time.sleep(15) 
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram_msg("🏆 بدأ نظام Master Sniper V4 (تحدي BNB).. الرادار في أقصى حساسية!")
    while True:
        scan_bnb_master()
        time.sleep(10)
