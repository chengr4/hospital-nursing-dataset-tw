from curl_cffi import requests
from bs4 import BeautifulSoup
import os
import re
import json
import sys

# 配置資訊
URL = "https://www.nhi.gov.tw/ch/cp-15138-b2fee-3669-1.html"
BASE_URL = "https://www.nhi.gov.tw"
TARGET_DIR = "."  # 存放檔案的資料夾
HISTORY_FILE = "download_history.json"  # 記錄下載歷史
HEADERS = {
    "Referer": "https://www.nhi.gov.tw/"
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def download_ods():
    # 0. 載入歷史紀錄
    history = load_history()
    
    try:
        response = requests.get(URL, headers=HEADERS, timeout=30, impersonate="chrome")
        response.raise_for_status()
    except Exception as e:
        print(f"無法存取目標網頁: {e}")
        sys.exit(1)

    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. 找出所有項目並提取年份
    items = soup.select('div.download_list ul li') # 根據實際 HTML 層級調整
    if not items:
        # 備用選擇器：針對截圖中顯示的結構
        items = soup.find_all('li', text=re.compile(r'\d+年')) 
        # 如果 li 裡面包著文字，BS4 可能需要特定寫法，改用抓取所有 li 再過濾
        items = [li for li in soup.find_all('li') if '各醫院三班護病比' in li.get_text()]

    if not items:
        print("錯誤：在網頁上找不到任何資料項，可能是網頁結構已改變。")
        sys.exit(1)

    target_files = []
    max_year = 0

    for li in items:
        text = li.get_text() # 例如：113年11月各醫院三班護病比（114.01.21更新）
        match = re.search(r'(\d+)年', text)
        if match:
            year = int(match.group(1))
            ods_link = li.find('a', string=re.compile(r'ods', re.I))
            
            if ods_link:
                href = ods_link.get('href')
                full_url = BASE_URL + href if href.startswith('/') else href
                
                # 建立檔名，例如：114年9月_三班護病比.ods
                clean_title = text.split('（')[0].strip() # 移除括號後的日期
                file_name = f"{clean_title}.ods"
                
                # 提取更新日期作為版本號 (若無括號日期，預設為 'initial')
                date_match = re.search(r'（(.+?)更新）', text)
                version_date = date_match.group(1) if date_match else "initial"
                
                target_files.append({
                    "year": year,
                    "url": full_url,
                    "name": file_name,
                    "version": version_date
                })
                if year > max_year:
                    max_year = year

    if not target_files:
        print("錯誤：找到項目但找不到任何 ODS 下載連結。")
        sys.exit(1)

    # 2. 顯示最新年份
    print(f"偵測到最新年份為：{max_year}年")

    # 3. 執行下載 (只下載符合 max_year 的檔案，且檢查更新)
    has_downloaded = False
    for file in target_files:
        if file['year'] == max_year:
            file_name = file['name']
            server_version = file['version']
            
            # 檢查是否需要下載：歷史紀錄不存在 OR 版本號不同
            local_version = history.get(file_name)
            
            if local_version != server_version:
                print(f"發現新版本或新檔案：{file_name} (版本: {server_version})")
                print(f"正在下載...")
                
                try:
                    f_resp = requests.get(file['url'], headers=HEADERS, timeout=30, impersonate="chrome")
                    f_resp.raise_for_status()
                    file_path = os.path.join(TARGET_DIR, file_name)
                    with open(file_path, 'wb') as f:
                        f.write(f_resp.content)
                    
                    # 更新紀錄
                    history[file_name] = server_version
                    has_downloaded = True
                except Exception as e:
                    print(f"下載失敗 {file_name}: {e}")
            else:
                print(f"已是最新，跳過：{file_name}")

    # 4. 只有在有下載時才寫入紀錄檔，減少 IO
    if has_downloaded:
        save_history(history)
        print("下載與紀錄更新完成！")
    else:
        print("所有檔案皆為最新，無需下載。")

if __name__ == "__main__":
    download_ods()