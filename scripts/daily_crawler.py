import requests
import json
import os
from datetime import datetime

# DeepSeek API 設定
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def fetch_futures_prices():
    """
    抓取期貨價格
    目前使用模擬資料，之後可改成真實爬蟲
    """
    # TODO: 改成真實爬蟲
    # 目標網站：大連商品交易所、鄭州商品交易所
    
    return {
        "PP": {"price": 7850, "change": 3.2, "unit": "元/噸", "trend": "up"},
        "PE": {"price": 8120, "change": 0.5, "unit": "元/噸", "trend": "flat"},
        "ABS": {"price": 11250, "change": -1.8, "unit": "元/噸", "trend": "down"},
        "PVC": {"price": 5980, "change": -0.3, "unit": "元/噸", "trend": "down"}
    }

def get_price_reason(product, change):
    """根據產品和漲跌生成原因"""
    reasons = {
        "PP": {">0": "上游丙烯缺貨", "<0": "下游需求疲軟"},
        "PE": {">0": "原油上漲帶動", "<0": "庫存過高"},
        "ABS": {">0": "家電訂單增加", "<0": "中國新產能開出"},
        "PVC": {">0": "基建需求增加", "<0": "房地產低迷"}
    }
    if change > 0:
        return reasons.get(product, {}).get(">0", "市場看好")
    elif change < 0:
        return reasons.get(product, {}).get("<0", "市場看淡")
    return "供需平衡"

def analyze_with_deepseek(prices):
    """用 DeepSeek 分析趨勢（可選，也可用規則）"""
    
    prompt = f"""
今天塑膠原料價格：
- PP：{prices['PP']['price']} 元/噸，漲跌 {prices['PP']['change']:.1f}%
- PE：{prices['PE']['price']} 元/噸，漲跌 {prices['PE']['change']:.1f}%
- ABS：{prices['ABS']['price']} 元/噸，漲跌 {prices['ABS']['change']:.1f}%
- PVC：{prices['PVC']['price']} 元/噸，漲跌 {prices['PVC']['change']:.1f}%

請根據以上數據，用以下格式輸出（不要有其他內容）：
📈 價格動態：
├── PP：【漲/跌/持平】【百分比】（【簡短原因】）
├── PE：【漲/跌/持平】【百分比】（【簡短原因】）
├── ABS：【漲/跌/持平】【百分比】（【簡短原因】）
└── PVC：【漲/跌/持平】【百分比】（【簡短原因】）

🎯 今日行動建議：
├── PP：【買進/賣出/觀望】（【理由一句】）
├── PE：【買進/賣出/觀望】（【理由一句】）
├── ABS：【買進/賣出/觀望】（【理由一句】）
└── PVC：【買進/賣出/觀望】（【理由一句】）

⚠️ 注意事項：
└── 【一條重要提醒，字數不超過15字】
"""
    
    if not DEEPSEEK_API_KEY:
        # 沒有 API Key 時用規則生成
        return generate_report_by_rules(prices)
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API 失敗: {e}")
    
    return generate_report_by_rules(prices)

def generate_report_by_rules(prices):
    """用規則生成報告（無 API 時的備案）"""
    lines = []
    lines.append("📈 價格動態：")
    
    for product, data in prices.items():
        change = data['change']
        if change > 0:
            trend = "漲"
        elif change < 0:
            trend = "跌"
        else:
            trend = "持平"
        
        reason = get_price_reason(product, change)
        lines.append(f"├── {product}：{trend} {abs(change):.1f}%（{reason}）")
    
    lines.append("\n🎯 今日行動建議：")
    
    suggestions = {
        "PP": ("買進", "漲勢確立"),
        "PE": ("觀望", "波動不大"),
        "ABS": ("等待", "還會再跌"),
        "PVC": ("觀望", "需求疲軟")
    }
    
    for product, (action, reason) in suggestions.items():
        lines.append(f"├── {product}：{action}（{reason}）")
    
    lines.append("\n⚠️ 注意事項：")
    lines.append("└── 國際油價波動加大，留意成本變化")
    
    return "\n".join(lines)

def generate_html(report, date_str):
    """產生 today.html 完整內容"""
    
    return f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日重點 | 台灣盛世國際化學</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', 'Courier New', monospace;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .container {{
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
        }}
        .report-box {{
            background: #0f172a;
            border: 2px solid #334155;
            border-radius: 1.5rem;
            padding: 2rem;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }}
        pre {{
            color: #e2e8f0;
            font-size: 0.95rem;
            font-family: 'Courier New', 'Segoe UI', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.6;
            margin: 0;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #334155;
        }}
        .header h1 {{
            color: #fbbf24;
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 0.8rem;
        }}
        .footer {{
            text-align: center;
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid #334155;
            color: #475569;
            font-size: 0.7rem;
        }}
        .footer a {{
            color: #64748b;
            text-decoration: none;
        }}
        .footer a:hover {{
            color: #94a3b8;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .report-box {{ padding: 1rem; }}
            pre {{ font-size: 0.8rem; }}
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="report-box">
        <div class="header">
            <h1>🏭 台灣盛世國際化學</h1>
            <p>每日情報重點｜{date_str}</p>
        </div>
        <pre>{report}</pre>
        <div class="footer">
            <a href="/chemical-email-collector/index.html">📊 完整戰情室</a> | 
            <a href="/chemical-email-collector/intelligence.html">📈 產業報告庫</a>
        </div>
    </div>
</div>
</body>
</html>'''

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 開始產生每日報告 - {date_str}")
    
    # 1. 抓取價格
    print("📡 抓取期貨價格...")
    prices = fetch_futures_prices()
    
    # 2. 生成分析報告
    print("🤖 AI 分析中...")
    report = analyze_with_deepseek(prices)
    
    # 3. 產生 HTML
    print("📄 產生 today.html...")
    html = generate_html(report, date_str)
    
    # 4. 儲存檔案
    with open("today.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ 完成！today.html 已更新")

if __name__ == "__main__":
    main()
