import requests
import json
import pandas as pd
import time
import os
from datetime import datetime

# ==================== 設定 ====================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 公司名單（可以改成讀取外部檔案）
COMPANY_NAMES = [
    "上海新阳", "江化微", "晶瑞电材", "格林达", "中巨芯",
    "兴福电子", "润玛股份", "达诺尔", "华特气体", "南大光电",
    "飞凯材料", "安集科技", "鼎龙股份", "容大感光", "广信材料",
    "永光化学", "利绅科技", "长兴材料", "三福化工", "胜一化工",
    "李長榮化工", "中華化學", "台硝", "大立高分子"
]

def search_company_email(company_name):
    """用 DeepSeek API 搜尋公司 Email"""
    
    prompt = f"""
請幫我找出以下化工公司的業務聯絡 Email 和官方網站：

公司名稱：{company_name}

請以 JSON 格式回覆，包含以下欄位：
- website: 官方網站網址
- email: 主要的業務聯絡信箱
- phone: 聯絡電話（有的話）

如果找不到，website 和 email 都回傳空字串。

只回傳 JSON，不要有其他文字。
"""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是化工行業資料收集助手，只回傳 JSON。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # 清理 JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            data = json.loads(content)
            return data
        else:
            print(f"API 錯誤: {response.status_code}")
            return {"website": "", "email": "", "phone": ""}
            
    except Exception as e:
        print(f"錯誤: {e}")
        return {"website": "", "email": "", "phone": ""}

def generate_html(results):
    """生成 HTML 報表"""
    
    html_template = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>化工電子郵件採集結果 | 台灣盛世國際化學</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .card {{
            background: white;
            border-radius: 2rem;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #0f2b3d 100%);
            color: white;
            padding: 2rem;
        }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .update-time {{ opacity: 0.8; font-size: 0.9rem; }}
        .content {{ padding: 2rem; }}
        .stats {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: #f8fafc;
            border-radius: 1rem;
            padding: 1rem 1.5rem;
            text-align: center;
            flex: 1;
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #1e3a5f;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
        }}
        .email {{ color: #3b82f6; font-family: monospace; }}
        .badge {{
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-success {{ background: #dcfce7; color: #166534; }}
        .badge-warning {{ background: #fee2e2; color: #991b1b; }}
        .footer {{
            text-align: center;
            padding: 1.5rem;
            color: #64748b;
            font-size: 0.8rem;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="header">
            <h1>🕷️ 化工電子郵件採集系統</h1>
            <p>台灣盛世國際化學 · 自動化供應商開發</p>
            <div class="update-time">📅 更新時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
        <div class="content">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(results)}</div>
                    <div>總公司數</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(1 for r in results if r['email'])}</div>
                    <div>已採集 Email</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{sum(1 for r in results if r['website'])}</div>
                    <div>已找到官網</div>
                </div>
            </div>
            
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr><th>公司名稱</th><th>官方網站</th><th>Email</th><th>電話</th></tr>
                    </thead>
                    <tbody>
                        {"".join([f"""
                        <tr>
                            <td style="font-weight:500;">{r['company']}</td>
                            <td>{f'<a href="{r["website"]}" target="_blank">{r["website"]}</a>' if r["website"] else "—"}</td>
                            <td class="email">{r["email"] if r["email"] else "<span class='badge badge-warning'>未找到</span>"}</td>
                            <td>{r["phone"] if r["phone"] else "—"}</td>
                        </tr>
                        """ for r in results])}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="footer">
            <span>⚡ 由 DeepSeek API 自動採集 · 每日更新</span>
        </div>
    </div>
</div>
</body>
</html>'''
    
    return html_template

def main():
    print("開始採集化工公司聯絡資訊...")
    print("="*60)
    
    results = []
    
    for i, company in enumerate(COMPANY_NAMES, 1):
        print(f"[{i}/{len(COMPANY_NAMES)}] 處理中: {company}")
        
        info = search_company_email(company)
        
        results.append({
            'company': company,
            'website': info.get('website', ''),
            'email': info.get('email', ''),
            'phone': info.get('phone', '')
        })
        
        time.sleep(1)  # 避免 API 限流
    
    # 生成 HTML
    html_content = generate_html(results)
    
    # 儲存檔案
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # 也存一份 CSV 備份
    df = pd.DataFrame(results)
    df.to_csv(os.path.join(output_dir, "results.csv"), index=False, encoding='utf-8-sig')
    
    print("\n" + "="*60)
    print(f"✅ 完成！共處理 {len(results)} 家公司")
    print(f"📧 找到 Email: {sum(1 for r in results if r['email'])} 家")
    print(f"📁 輸出檔案: output/index.html 和 output/results.csv")

if __name__ == "__main__":
    main()
