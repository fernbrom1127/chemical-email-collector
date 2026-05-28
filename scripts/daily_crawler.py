import requests
import re
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

# ==================== 商品對照表 ====================
PRODUCTS = {
    "PP": {
        "name_cn": "聚丙烯",
        "shengweishe_id": "pp",
        "dce_symbol": "pp",
        "dce_code": "pp"
    },
    "LLDPE": {
        "name_cn": "線性低密度聚乙烯",
        "shengweishe_id": "lldpe",
        "dce_symbol": "l",
        "dce_code": "l"
    },
    "ABS": {
        "name_cn": "ABS樹脂",
        "shengweishe_id": "abs",
        "dce_symbol": None,
        "dce_code": None
    },
    "PVC": {
        "name_cn": "聚氯乙烯",
        "shengweishe_id": "pvc",
        "dce_symbol": "v",
        "dce_code": "v"
    },
    "PC": {
        "name_cn": "聚碳酸酯",
        "shengweishe_id": "pc",
        "dce_symbol": None,
        "dce_code": None
    }
}

# ==================== 生意社爬蟲 ====================
def fetch_shengweishe_price(product_id):
    """
    從生意社抓取現貨價格
    網址格式：https://www.100ppi.com/price/detail/{product_id}
    """
    url = f"https://www.100ppi.com/price/detail/{product_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.100ppi.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 方法1：找價格所在的 span 或 div
        # 常見 class: .price, .c_price, .pri_big, #pri_big
        price_selectors = [
            '#pri_big',           # 大數字價格
            '.pri_big',           # 大數字價格
            '.price',             # 通用價格
            '.c_price',           # 行情價格
            'span.price',         # span 下的價格
            'div.price'           # div 下的價格
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                # 提取數字（含小數點）
                match = re.search(r'([\d,]+\.?\d*)', price_text)
                if match:
                    price = match.group(1).replace(',', '')
                    return float(price)
        
        # 方法2：從頁面標題或 meta 中抓取
        # 有些頁面價格在 title 或 description 中
        title = soup.find('title')
        if title:
            match = re.search(r'(\d{3,5})[\s]*元', title.text)
            if match:
                return float(match.group(1))
        
        print(f"⚠️ 生意社 {product_id} 未找到價格")
        return None
        
    except Exception as e:
        print(f"❌ 生意社爬取失敗 {product_id}: {e}")
        return None

# ==================== 大商所期貨爬蟲 ====================
def fetch_dce_futures(symbol_code):
    """
    從大商所抓取期貨主力合約價格
    使用大商所官網報價 API
    """
    if not symbol_code:
        return None
    
    # 大商所主力合約報價接口
    # 注意：實際 API 需要確認，這裡使用公開行情接口
    urls = [
        f"https://www.dce.com.cn/public/quote/quoteDetail.shtml?symbol={symbol_code.upper()}",
        f"http://www.dce.com.cn/dalianshangpin/quote/{symbol_code.upper()}.html"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尋找最新價（最新價、現價、last price）
            price_selectors = [
                '#lastPrice',           # ID
                '.lastPrice',           # Class
                '.last-price',          # Class
                'td:contains("最新價") + td',  # 表格
                'td:contains("最新") + td',    # 表格
                '.quote-last',          # 行情區
                'span.last'             # span 最後價
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    price_text = elem.get_text().strip()
                    match = re.search(r'([\d,]+\.?\d*)', price_text)
                    if match:
                        price = match.group(1).replace(',', '')
                        if float(price) > 0:
                            return float(price)
            
            # 嘗試從表格中找價格
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    for i, cell in enumerate(cells):
                        if '最新' in cell.get_text() or '最新價' in cell.get_text():
                            if i + 1 < len(cells):
                                price_text = cells[i+1].get_text().strip()
                                match = re.search(r'([\d,]+\.?\d*)', price_text)
                                if match:
                                    price = match.group(1).replace(',', '')
                                    if float(price) > 0:
                                        return float(price)
            
        except Exception as e:
            print(f"⚠️ 大商所 {symbol_code} 嘗試 {url} 失敗: {e}")
            continue
    
    print(f"⚠️ 大商所 {symbol_code} 未找到價格")
    return None

# ==================== 備用：生意社API ====================
def fetch_shengweishe_api(product_id):
    """
    備用方案：使用生意社的內部 API（如果有）
    """
    # 生意社可能有隱藏 API，需要抓包才能知道
    # 這裡預留位置，後續可補充
    return None

# ==================== 生成 HTML ====================
def generate_html(price_data, update_time):
    """生成 today.html"""
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>化工現貨/期貨報價 | 台灣盛世國際化學</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
        }}
        .header p {{ color: #94a3b8; font-size: 0.9rem; }}
        
        .card {{
            background: #1e293b;
            border-radius: 1rem;
            padding: 1.5rem;
            border: 1px solid #334155;
            margin-bottom: 1.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #334155;
        }}
        th {{ color: #fbbf24; font-weight: 600; }}
        td {{ color: #e2e8f0; }}
        .spot-price {{ color: #3b82f6; font-weight: bold; }}
        .futures-price {{ color: #10b981; font-weight: bold; }}
        .basis-positive {{ color: #ef4444; }}
        .basis-negative {{ color: #10b981; }}
        .na {{ color: #64748b; font-style: italic; }}
        
        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #334155;
            color: #475569;
            font-size: 0.7rem;
        }}
        .update-time {{
            text-align: right;
            color: #64748b;
            font-size: 0.7rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🏭 台灣盛世國際化學</h1>
        <p>塑膠原料 現貨 vs 期貨 報價表</p>
    </div>
    
    <div class="update-time">📅 更新時間：{update_time}</div>
    
    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>商品</th>
                    <th>中文名稱</th>
                    <th>生意社現貨 (元/噸)</th>
                    <th>大商所期貨 (元/噸)</th>
                    <th>基差 (現貨-期貨)</th>
                </tr>
            </thead>
            <tbody>
'''
    
    for p in price_data:
        spot_display = f'<span class="spot-price">{p["spot"]:,.0f}</span>' if p["spot"] else '<span class="na">未取得</span>'
        futures_display = f'<span class="futures-price">{p["futures"]:,.0f}</span>' if p["futures"] else '<span class="na">無期貨</span>'
        
        if p["basis"] is not None:
            basis_class = "basis-positive" if p["basis"] > 0 else "basis-negative"
            basis_display = f'<span class="{basis_class}">{p["basis"]:+,.0f}</span>'
        else:
            basis_display = '<span class="na">無法計算</span>'
        
        html += f"""
                <tr>
                    <td><strong>{p["code"]}</strong></td>
                    <td>{p["name_cn"]}</td>
                    <td>{spot_display}</td>
                    <td>{futures_display}</td>
                    <td>{basis_display}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        📊 資料來源：生意社 (現貨) | 大連商品交易所 (期貨)
    </div>
</div>
</body>
</html>"""
    
    return html

# ==================== 主程式 ====================
def main():
    print("🚀 開始爬取真實價格數據...")
    print(f"📅 執行時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    price_data = []
    
    for code, info in PRODUCTS.items():
        print(f"\n📡 處理商品：{code} ({info['name_cn']})")
        
        # 爬生意社現貨
        spot_price = None
        if info.get("shengweishe_id"):
            print(f"   → 爬取生意社現貨...")
            spot_price = fetch_shengweishe_price(info["shengweishe_id"])
            if spot_price:
                print(f"   ✅ 現貨價格：{spot_price} 元/噸")
            else:
                print(f"   ⚠️ 未取得現貨價格")
        
        # 爬大商所期貨
        futures_price = None
        if info.get("dce_symbol"):
            print(f"   → 爬取大商所期貨...")
            futures_price = fetch_dce_futures(info["dce_symbol"])
            if futures_price:
                print(f"   ✅ 期貨價格：{futures_price} 元/噸")
            else:
                print(f"   ⚠️ 未取得期貨價格")
        
        # 計算基差
        basis = None
        if spot_price and futures_price:
            basis = spot_price - futures_price
            print(f"   📊 基差：{basis:+.0f} 元/噸")
        
        price_data.append({
            "code": code,
            "name_cn": info["name_cn"],
            "spot": spot_price,
            "futures": futures_price,
            "basis": basis
        })
        
        # 避免請求過快
        time.sleep(1)
    
    print("\n" + "-" * 50)
    print("📄 生成 today.html...")
    
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content = generate_html(price_data, update_time)
    
    with open("today.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ today.html 已更新！")
    print("\n📊 價格摘要：")
    for p in price_data:
        spot_str = f"{p['spot']:,.0f}" if p['spot'] else "未取得"
        fut_str = f"{p['futures']:,.0f}" if p['futures'] else "無期貨"
        print(f"   {p['code']}: 現貨={spot_str}, 期貨={fut_str}")

if __name__ == "__main__":
    main()
