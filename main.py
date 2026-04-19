import requests
import time
import os

# --- الإعدادات ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code
    except: return None

def scan_now():
    # استخدام API الـ Pairs المباشر لأكثر العملات تداولاً على BSC
    url = "https://api.dexscreener.com/token-boosts/latest/v1"
    try:
        response = requests.get(url, timeout=10).json()
        
        for item in response[:40]:
            if item.get('chainId') != "bsc": continue
            
            addr = item.get('tokenAddress')
            # جلب البيانات اللحظية
            res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            # --- فلاتر مرنة جداً لمطابقة الصورة ---
            mcap = float(p.get('fdv', 0))
            h1_change = float(p.get('priceChange', {}).get('h1', 0))
            
            # إذا صعدت العملة أكثر من 5% في الساعة، أرسلها فوراً
            if h1_change > 5 and 10000 < mcap < 10000000:
                msg = (
                    f"🔔 *إشارة فورية (BNB Smart Chain)*\n\n"
                    f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                    f"📈 صعود الساعة: %{h1_change}\n"
                    f"💰 الماركت كاب: ${mcap:,.0f}\n"
                    f"📊 السعر: ${p.get('priceUsd')}\n\n"
                    f"🔗 [الشارت](https://dexscreener.com/bsc/{addr})\n"
                    f"🛒 [شراء مباشر](https://pancakeswap.finance/swap?outputCurrency={addr})"
                )
                send_telegram_msg(msg)
                print(f"Done: {p['baseToken']['symbol']}")
                time.sleep(10) # انتظار بسيط
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # هذه الرسالة يجب أن تصلك فور تشغيل البوت لتتأكد أنه يعمل
    test_status = send_telegram_msg("✅ *تم تفعيل القناص بنجاح!* جاري فحص عملات الترند الصينية الآن...")
    if test_status != 200:
        print("خطأ: لم يتمكن البوت من الإرسال لتليجرام. تأكد من الـ Token والـ Chat ID.")
    
    while True:
        scan_now()
        time.sleep(15)
