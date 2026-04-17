import requests
import time

# --- إعدادات المستخدم ---
TELEGRAM_TOKEN = 'TELEGRAM_TOKEN'
TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'
CHECK_INTERVAL = 30  # الفحص كل 30 ثانية
MIN_VOLUME_H1 = 5000  # الحد الأدنى لحجم التداول في الساعة للاهتمام بالعملة
CHAIN_ID = "56" # كود شبكة BSC (الموجودة في صورك)

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        print("خطأ في إرسال رسالة تليجرام")

def check_security_and_whales(token_address):
    """يفحص أمان العقد وتوزيع المحفظات"""
    url = f"https://api.gopluslabs.io/api/v1/token_security/{CHAIN_ID}?contract_addresses={token_address}"
    try:
        res = requests.get(url).json()
        if res['message'] == 'OK':
            data = res['result'][token_address.lower()]
            
            # 1. فحص المصيدة
            if data.get('is_honeypot') == '1': return False, "🚫 مصيدة (Honeypot)"
            
            # 2. فحص كبار الملاك (Whale Concentration)
            # إذا كان كبار الملاك يملكون أكثر من 25% من العملة خارج السيولة، فهي خطر
            holders = data.get('holders', [])
            top_holdings = sum([float(h.get('percent', 0)) for h in holders[:3]])
            if top_holdings > 0.25: return False, f"⚠️ تركيز عالي للملاك ({int(top_holdings*100)}%)"
            
            # 3. فحص قفل السيولة
            if data.get('lp_locked') == '1' or float(data.get('lp_burned_percent', 0)) > 50:
                return True, "✅ سيولة آمنة وملاك موزعون"
        return False, "❌ فحص الأمان لم يكتمل"
    except:
        return False, "⚙️ خطأ في فحص الأمان"

def scan_alpha():
    print("🚀 جاري فحص رادار 'الفا' بحثاً عن انفجارات قادمة...")
    # جلب العملات التي بدأت تحصل على "دعم" أو ترند (Trending/Boosted)
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    
    try:
        boosted_tokens = requests.get(url).json()
        for item in boosted_tokens:
            addr = item.get('tokenAddress')
            
            # جلب بيانات السوق الحقيقية
            market_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}").json()
            pairs = market_res.get('pairs')
            if not pairs: continue
            
            p = pairs[0]
            vol = p.get('volume', {})
            v5 = vol.get('m5', 0) # حجم آخر 5 دقائق
            h1 = vol.get('h1', 0) # حجم آخر ساعة
            
            # الاستراتيجية: إذا دخلت سيولة مفاجئة (30% من الساعة في آخر 5 دقائق)
            if h1 > MIN_VOLUME_H1 and (v5 / h1) > 0.3:
                # التحقق من الأمان وتتبع الملاك قبل الإرسال
                is_safe, security_note = check_security_and_whales(addr)
                
                if is_safe:
                    msg = (
                        f"🌟 *إشارة Alpha قبل الانفجار!*\n\n"
                        f"💎 العملة: {p['baseToken']['symbol']}\n"
                        f"💰 السعر: ${p['priceUsd']}\n"
                        f"📊 نشاط لحظي ضخم: {int((v5/h1)*100)}% من سيولة الساعة\n"
                        f"🛡️ الأمان: {security_note}\n"
                        f"👥 الملاك: توزيع صحي (تحت المراقبة)\n\n"
                        f"🔗 [رابط الشراء والتفاصيل](https://dexscreener.com/bsc/{addr})"
                    )
                    send_telegram_msg(msg)
                    print(f"✅ تم إرسال تنبيه لعملة {p['baseToken']['symbol']}")
                    time.sleep(2) # لتجنب حظر الـ API
    except Exception as e:
        print(f"حدث خطأ في المسح: {e}")

if __name__ == "__main__":
    send_telegram_msg("🤖 بدأ بوت 'الفا' بالعمل.. رادار الانفجارات مفعل!")
    while True:
        scan_alpha()
        time.sleep(CHECK_INTERVAL)