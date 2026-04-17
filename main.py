import requests
import time
import os

# --- الإعدادات (سحب آمن من Railway) ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- معايير القناص المحترف ---
NETWORKS = ["solana", "base", "bsc"] # الشبكات المستهدفة
MIN_LIQUIDITY = 3000                 # الحد الأدنى للسيولة
MAX_MARKET_CAP = 300000              # أقصى ماركت كاب لاقتناص العملة وهي رخيصة
CHECK_INTERVAL = 10                  # سرعة المسح (ثواني)

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except: pass

def get_security_report(chain, address):
    """فحص أمان متطور حسب الشبكة"""
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain}?contract_addresses={address}"
        res = requests.get(url, timeout=5).json()
        return res.get('result', {}).get(address.lower(), {})
    except: return {}

def scan_multi_chain_alpha():
    # استخدام API الـ Boosts لجلب العملات التي بدأت تحصل على زخم (Trending)
    url = "https://api.dexscreener.com/token-boosts/latest/v1"
    try:
        tokens = requests.get(url, timeout=10).json()
        
        # نركز على أول 15 عملة حصلت على دعم مؤخراً
        for item in tokens[:15]:
            chain_id = item.get('chainId')
            if chain_id not in NETWORKS: continue
            
            addr = item.get('tokenAddress')
            m_res = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addr}", timeout=10).json()
            pairs = m_res.get('pairs')
            if not pairs: continue
            
            # فلترة الأزواج بناءً على السيولة والماركت كاب
            for p in pairs:
                if p.get('chainId') not in NETWORKS: continue
                
                mcap = float(p.get('fdv', 0))
                liq = float(p.get('liquidity', {}).get('usd', 0))
                vol_5m = float(p.get('volume', {}).get('m5', 0))
                
                # الفلتر الذهبي: ماركت كاب منخفض + سيولة جيدة + تداول نشط جداً
                if 5000 < mcap < MAX_MARKET_CAP and liq > MIN_LIQUIDITY and vol_5m > 500:
                    
                    # الفحص الأمني قبل الإرسال
                    sec = get_security_report(chain_id, addr)
                    if sec.get('is_honeypot') == '1': continue # استبعاد المصائد
                    
                    # التحقق من نسبة كبار الملاك (Whales)
                    top_holders = sec.get('holders', [])
                    whale_risk = "⚠️ خطر" if any(float(h.get('percent', 0)) > 0.15 for h in top_holders[:3]) else "✅ آمن"

                    msg = (
                        f"🚀 *Alpha Sniper: {chain_id.upper()}* 🚀\n\n"
                        f"💎 العملة: `{p['baseToken']['symbol']}`\n"
                        f"💵 الماركت كاب: ${mcap:,.0f}\n"
                        f"💧 السيولة: ${liq:,.0f}\n"
                        f"🔥 حجم (5د): ${vol_5m:,.0f}\n"
                        f"🛡️ الأمان: {'سليم ✅' if sec.get('is_open_source') == '1' else 'غير موثق ⚠️'}\n"
                        f"🐋 الحيتان: {whale_risk}\n\n"
                        f"🔗 [افتح الرسم البياني للشراء](https://dexscreener.com/{chain_id}/{addr})"
                    )
                    
                    send_telegram_msg(msg)
                    print(f"🎯 تم صيد فرصة على {chain_id}: {p['baseToken']['symbol']}")
                    time.sleep(10) # منع التكرار
                    break 
    except Exception as e:
        print(f"خطأ في المسح: {e}")

if __name__ == "__main__":
    send_telegram_msg("🕵️‍♂️ القناص المتعدد (Solana, Base, BSC) بدأ العمل الآن...")
    while True:
        scan_multi_chain_alpha()
        time.sleep(CHECK_INTERVAL)