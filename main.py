import requests
import time
import os

# --- الإعدادات الآمنة ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- معايير قناص بينانس (BNB) ---
TARGET_CHAIN = "bsc"         # التركيز حصراً على شبكة بينانس
MIN_LIQUIDITY = 5000         # الحد الأدنى للسيولة (دولار) لضمان الأمان
MAX_MARKET_CAP = 500000      # اقتناص العملة قبل أن تصبح ضخمة جداً
CHECK_INTERVAL = 15          # فحص كل 15 ثانية

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except: pass

def get_bnb_security(address):
    """فحص أمان متقدم لعملات شبكة بينانس"""
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/56?contract_addresses={address}"
        res = requests.get(url, timeout=5).json()
        return res.get('result', {}).get(address.lower(), {})
    except: return {}

def scan_bnb_only():
    # جلب العملات النشطة حالياً (Trending/Boosted)
    url = "https://api.dexscreener.com/token-boosts/latest/v1"
    try:
        tokens = requests.get(url, timeout=10).json()
        
        for item in tokens[:20]:
            chain_id = item.get('chainId')
            
            # فلتر الشبكة: نتجاهل أي شيء ليس BNB
            if chain_id != TARGET_CHAIN: continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            # تحليل بيانات الزوج الأساسي على شبكة BNB
            for p in pairs:
                if p.get('chainId') != TARGET_CHAIN: continue
                
                mcap = float(p.get('fdv', 0))
                liq = float(p.get('liquidity', {}).get('usd', 0))
                vol_h1 = float(p.get('volume', {}).get('h1', 0))
                
                # استراتيجية الاقتناص: سيولة جيدة + ماركت كاب منخفض + حجم تداول نشط
                if 10000 < mcap < MAX_MARKET_CAP and liq > MIN_LIQUIDITY and vol_h1 > 2000:
                    
                    # الفحص الأمني (GoPlus)
                    sec = get_bnb_security(addr)
                    if sec.get('is_honeypot') == '1': continue
                    
                    # التحقق من قفل السيولة (مهم جداً في BNB)
                    lp_status = "🔒 مقفولة/محروقة" if sec.get('lp_burned_percent') and float(sec.get('lp_burned_percent')) > 50 else "⚠️ غير مؤكدة"

                    msg = (
                        f"🟡 *قناص بينانس (BNB Chain)* 🟡\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"💰 الماركت كاب: ${mcap:,.0f}\n"
                        f"💧 السيولة: ${liq:,.0f}\n"
                        f"📊 حجم (ساعة): ${vol_h1:,.0f}\n"
                        f"🛡️ الأمان: {'✅ سليم' if sec.get('is_open_source') == '1' else '⚠️ عقد غير موثق'}\n"
                        f"🔑 السيولة: {lp_status}\n\n"
                        f"🔗 [شراء عبر PancakeSwap / Dex](https://dexscreener.com/bsc/{addr})"
                    )
                    
                    send_telegram_msg(msg)
                    print(f"🎯 تم صيد عملة BNB: {p['baseToken']['symbol']}")
                    time.sleep(10) 
                    break 
    except Exception as e:
        print(f"خطأ في مسح BNB: {e}")

if __name__ == "__main__":
    send_telegram_msg("🟡 رادار 'بينانس' (BNB Only) نشط الآن.. جاري البحث عن الفرص!")
    while True:
        scan_bnb_only()
        time.sleep(CHECK_INTERVAL)