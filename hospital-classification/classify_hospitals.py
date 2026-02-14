#!/usr/bin/env python3
"""
Extract hospital names from ODS files and classify them by region and city.
Uses institution codes from the ODS files to improve classification accuracy.
"""

import pandas as pd
import glob
import json
import re

# Taiwan region classification
# Based on Taiwan administrative divisions
CITY_TO_REGION = {
    # 北部 (Northern Taiwan)
    "臺北市": "北部",
    "台北市": "北部",
    "新北市": "北部",
    "基隆市": "北部",
    "桃園市": "北部",
    "新竹市": "北部",
    "新竹縣": "北部",
    "宜蘭縣": "北部",
    
    # 中部 (Central Taiwan)
    "苗栗縣": "中部",
    "臺中市": "中部",
    "台中市": "中部",
    "彰化縣": "中部",
    "南投縣": "中部",
    "雲林縣": "中部",
    
    # 南部 (Southern Taiwan)
    "嘉義市": "南部",
    "嘉義縣": "南部",
    "臺南市": "南部",
    "台南市": "南部",
    "高雄市": "南部",
    "屏東縣": "南部",
    "澎湖縣": "南部",
    
    # 東部 (Eastern Taiwan)
    "花蓮縣": "東部",
    "臺東縣": "東部",
    "台東縣": "東部",
    
    # 離島 (Offshore islands) - typically classified based on location
    "金門縣": "南部",  # Often grouped with southern region
    "連江縣": "北部",  # Matsu, often grouped with northern region
}

# Institution code (first 4 digits) to city mapping
# Based on Taiwan NHI administrative area codes
CODE_TO_CITY = {
    # Taipei City
    "0101": "臺北市",  # Taipei Municipal (臺北市聯醫)
    "0401": "臺北市",  # NTU Hospital (台大醫院)
    "0501": "臺北市",  # Military General Hospital (三軍總醫院)
    "0601": "臺北市",  # Taipei Veterans (臺北榮總)
    "0901": "臺北市",  # 中山醫院, 郵政醫院, 西園醫院
    "1101": "臺北市",  # Cathay (國泰), Mackay (馬偕)
    "1301": "臺北市",  # Wanfang (萬芳), TMU (台北醫大)
    "1401": "臺北市",  # 仁濟醫院
    "1533": "臺北市",  # 大安醫院 (大安 is Taipei district)
    
    # New Taipei City
    "0131": "新北市",  # New Taipei Municipal (新北市聯醫), 部台北, 部八里
    "0931": "新北市",  # Board hospitals (板英 = 板橋)
    "1131": "新北市",  # Far Eastern (亞東), Tzu Chi (慈濟), Mackay Tamsui (淡水)
    "1231": "新北市",  # Cathay (耕莘)
    "1441": "新北市",  # 仁馨醫院
    "1531": "新北市",  # Board hospitals (板新, 板橋)
    
    # Keelung City
    "0211": "基隆市",  # Keelung Municipal
    "0511": "基隆市",  # Military Keelung
    
    # Taoyuan City
    "0132": "桃園市",  # 部桃園, 桃療, 桃園新屋
    "0532": "桃園市",  # Military Taoyuan
    "0632": "桃園市",  # Veterans Taoyuan
    "0932": "桃園市",  # Tiancheng (天晟)
    "1132": "桃園市",  # Linkou Chang Gung (林口長庚), 桃園長庚
    "1532": "桃園市",  # Minsheng (敏盛), Landseed (聯新)
    
    # Hsinchu City/County
    "0412": "新竹市",  # NTU Hsinchu
    "0933": "新竹縣",  # Oriental (東元), 竹北新仁
    "1112": "新竹市",  # Mackay Hsinchu, Cathay Hsinchu
    
    # Yilan County
    "0651": "宜蘭縣",  # Veterans Yuanshan
    "1134": "宜蘭縣",  # Luodong (羅東博愛), St. Mary (聖母), 宜蘭仁愛
    
    # Miaoli County
    "0935": "苗栗縣",  # 大千, 李綜合苑裡
    "1535": "苗栗縣",  # 協和, 大千, 通霄光田
    
    # Taichung City
    "0517": "臺中市",  # Military Taichung (國軍中清分)
    "0536": "臺中市",  # Military Taichung
    "0617": "臺中市",  # Taichung Veterans
    "0936": "臺中市",  # Kuang Tien (光田), Tung's (童綜合)
    "1303": "臺中市",  # CMU (中國兒童醫, 中醫大市醫, 亞洲大學附)
    "1317": "臺中市",  # CSMU (中山附醫), CMU (中國附醫)
    "1517": "臺中市",  # Cheng Ching (澄清)
    
    # Changhua County
    "0937": "彰化縣",  # Show Chwan (秀傳), Tao Zhou (道周), Yuanlin (員榮)
    "1137": "彰化縣",  # Christian Hospital (彰基), Show Chwan (秀傳)
    
    # Nantou County
    "1537": "南投縣",  # 信生, 冠華, 成美
    
    # Yunlin County
    "0439": "雲林縣",  # NTU Yunlin
    "1139": "雲林縣",  # Tzu Chi Douliu (斗六慈濟), St. Joseph (若瑟)
    
    # Chiayi City/County
    "0622": "嘉義縣",  # Veterans Chiayi
    "0922": "嘉義市",  # Chen Jen-Te (陳仁德), Qingsheng (慶昇)
    
    # Tainan City
    "0141": "臺南市",  # 部新營, 部臺南新化
    "0421": "臺南市",  # NCKU Hospital (成大醫院)
    "1141": "臺南市",  # Chi Mei (奇美)
    "1521": "臺南市",  # Kuo General (郭綜合)
    "1522": "臺南市",  # Yanming (陽明), Lu Ya-Ren (盧亞人)
    
    # Kaohsiung City
    "0102": "高雄市",  # Kaohsiung Municipal (市立), Kaohsiung Min-Sheng (民生)
    "0602": "高雄市",  # Kaohsiung Veterans
    "1107": "高雄市",  # E-Da (義大), Catholic (天主教聖功)
    "1142": "高雄市",  # Kaohsiung Chang Gung (高雄長庚), E-Da (義大)
    "1502": "高雄市",  # 正大, 馨蕙馨, 柏仁
    "1503": "高雄市",  # 杏豐, 漢忠
    "1507": "高雄市",  # 新高鳳, 博愛蕙馨
    "1536": "高雄市",  # 豐安, 祥恩
    "1542": "高雄市",  # 大東, 惠德, 新上琳
    "1543": "高雄市",  # 國仁, 民眾
    
    # Pingtung County
    "0943": "屏東縣",  # 寶建, 安泰
    "1143": "屏東縣",  # 屏基, 恆春基督教
    
    # Penghu County
    "0544": "澎湖縣",  # Military Penghu
    
    # Hualien County
    "0145": "花蓮縣",  # 花蓮醫院, 玉里醫院
    "0146": "臺東縣",  # 部東醫院, 成功分院
    "0645": "花蓮縣",  # Veterans Hualien
    "0905": "花蓮縣",  # 吉安醫院 (Ji'an is in Hualien)
    "1145": "花蓮縣",  # Tzu Chi (慈濟), Mennonite (門諾)
    
    # Taitung County
    "0641": "臺東縣",  # Veterans Taitung
    "1146": "臺東縣",  # Mackay Taitung (台東馬偕)
    
    # Lienchiang County (Matsu)
    "0291": "連江縣",  # Lienchiang Hospital
    
    # Additional codes based on analysis
    "0717": "臺中市",  # 培德醫院
    "0907": "高雄市",  # 燕巢靜和醫, 高雄秀傳
    "0911": "臺中市",  # 維德醫院
    "0917": "臺中市",  # 林新醫院 (famous Taichung hospital)
    "0934": "嘉義市",  # 海天醫院
    "0939": "嘉義市",  # 信安醫院
    "0941": "高雄市",  # 新興, 永達, 晉生 (新興 is Kaohsiung district)
    "1103": "臺北市",  # 佛教正德醫
    "1144": "臺南市",  # 惠民醫院
    "1202": "新北市",  # 基督教信義
    "1411": "新北市",  # 臺灣礦工 (Ruifang, New Taipei)
    "1412": "新北市",  # 新生醫院
    "1417": "新北市",  # 靜和醫院
    "1442": "嘉義縣",  # 慈惠醫院
    "1501": "臺北市",  # 博仁, 培靈, 秀傳, 協和婦女, 景美 (景美 is Taipei district)
    "1505": "臺北市",  # 璟馨, 大安婦幼醫, 陳澤彥 (大安 is Taipei district)
    "1511": "嘉義市",  # 新昆明, 暘基 (暘基 is in Chiayi)
    "1512": "臺北市",  # 南門, 新中興 (南門 is Taipei area)
    "1538": "臺南市",  # 曾漢棋綜合, 惠和, 東華
    "1539": "臺南市",  # 洪揚, 安生, 全生, 蔡, 諸元
    "1541": "高雄市",  # 營新, 信一骨科, 宏科
    "1701": "臺北市",  # 德威國際牙
}

# Specific hospital to city mapping for precise classification
# Only use this for hospitals that cannot be classified by code or name patterns
SPECIFIC_HOSPITALS = {
    # Note: Most hospitals are classified by their NHI institution codes.
    # Only add entries here if absolutely necessary (not covered by codes or patterns).
    
    # Major hospitals that might need explicit mapping
    "台北長庚": "臺北市",
    "林口長庚": "桃園市",
    "長庚醫院": "桃園市",
    
    # Hospitals needing specific classification
    "輔大附醫": "新北市",
    "東元法人": "新竹市",
    "湖口仁慈": "新竹縣",
    "竹北新仁醫": "新竹縣",
    "員山榮民醫": "宜蘭縣",
    "蘇澳榮民醫": "宜蘭縣",
    "李綜合苑裡": "苗栗縣",
    "中國北港醫": "雲林縣",
    "潮州安泰醫": "屏東縣",
    "屏榮龍泉分": "屏東縣",
    "屏安醫療社": "屏東縣",
    "北榮鳳林": "花蓮縣",
    "豐濱原住民": "花蓮縣",
}

# Hospital name patterns to city mapping
# This helps identify city from hospital name
HOSPITAL_PATTERNS = {
    # 臺北市/台北市
    r"台大|臺大|北醫|萬芳|和平|中興|仁愛|忠孝|陽明|關渡|台北馬偕|臺北馬偕|台北市立|臺北市立|台北長庚|臺北長庚": "臺北市",
    
    # 新北市
    r"新北|板橋|新店|淡水|汐止|雙和|亞東|耕莘|恩主公|三峽|樹林|永和|中和|土城|新莊|泰山|蘆洲|三重|樂生|瑞芳": "新北市",
    
    # 基隆市
    r"基隆|長庚情人湖|三總附基隆": "基隆市",
    
    # 桃園市
    r"桃園|桃新|林口長庚|中壢|龜山|天成|怡仁|聯新|敏盛|壢新|大園|龍潭": "桃園市",
    
    # 新竹市/縣
    r"新竹|台大竹東|臺大竹東|生醫竹北|馬偕新竹|竹北|竹東|竹信|湖口": "新竹市",
    
    # 宜蘭縣
    r"宜蘭|羅東|陽大|蘭陽|員山|蘇澳": "宜蘭縣",
    
    # 苗栗縣
    r"苗栗|為恭|大千|通霄|苑裡": "苗栗縣",
    
    # 臺中市/台中市
    r"台中|臺中|中山附|中國附|中國台中|中國臺中|中榮|澄清|童綜合|仁愛亞太|豐原|大里|沙鹿|梧棲|大甲|東勢|烏日|太平": "臺中市",
    
    # 彰化縣
    r"彰化|彰基|員林|秀傳|鹿港|二林|溪洲|員榮|員郭|伸港": "彰化縣",
    
    # 南投縣
    r"南投|草屯|竹山|埔里|佑民|祐民": "南投縣",
    
    # 雲林縣
    r"雲林|斗六|北港|台大雲林|臺大雲林|成大斗六|若瑟": "雲林縣",
    
    # 嘉義市/縣
    r"嘉義|聖馬|陽明嘉義|慶升|嘉基|大林|朴子|暘基": "嘉義市",
    
    # 臺南市/台南市
    r"台南|臺南|成大|郭綜合|新樓|奇美|柳營|麻豆|永康|安南|新營|善化|佳里": "臺南市",
    
    # 高雄市
    r"高雄|高醫|高榮|長庚高雄|小港|義大|民生|聯合|阮綜合|市立大同|旗山|岡山|鳳山|左營|前鎮|七賢|燕巢|旗津|路竹": "高雄市",
    
    # 屏東縣
    r"屏東|寶建|恆春|枋寮|輔英|潮州|屏基|屏榮|屏安": "屏東縣",
    
    # 澎湖縣
    r"澎湖|三軍澎湖": "澎湖縣",
    
    # 花蓮縣
    r"花蓮|慈濟|門諾|玉里|鳳林|吉安|豐濱": "花蓮縣",
    
    # 臺東縣/台東縣
    r"台東|臺東|馬偕台東|關山": "臺東縣",
    
    # 金門縣
    r"金門": "金門縣",
    
    # 連江縣
    r"連江|馬祖": "連江縣",
}

def extract_hospitals_from_ods():
    """Extract all unique hospital names and their codes from ODS files."""
    ods_files = glob.glob("../nurse-to-patient-ratios-by-shift/*.ods")
    hospital_to_code = {}
    
    for file_path in sorted(ods_files):
        try:
            df = pd.read_excel(file_path, engine='odf', header=None)
            # Skip the first 3 rows (title, subtitle, and header)
            df_data = df.iloc[3:]
            # Column index 3 is "機構代號", 4 is "機構名稱"
            for idx, row in df_data.iterrows():
                if pd.notna(row[3]) and pd.notna(row[4]):
                    code = str(row[3])
                    name = row[4]
                    # Store the most recent code for each hospital
                    hospital_to_code[name] = code
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return hospital_to_code

def classify_hospital_by_code(code):
    """Classify a hospital to a city based on institution code."""
    if not code:
        return None
    
    # Check first 4 digits
    prefix4 = code[:4]
    if prefix4 in CODE_TO_CITY:
        return CODE_TO_CITY[prefix4]
    
    # Check first 2 digits for general patterns
    prefix2 = code[:2]
    if prefix2 in CODE_TO_CITY:
        return CODE_TO_CITY[prefix2]
    
    return None

def classify_hospital(hospital_name, hospital_code=None):
    """Classify a hospital to a city based on code and name patterns."""
    # First try to classify by institution code
    if hospital_code:
        city = classify_hospital_by_code(hospital_code)
        if city:
            return city
    
    # Then check specific hospital mappings
    if hospital_name in SPECIFIC_HOSPITALS:
        return SPECIFIC_HOSPITALS[hospital_name]
    
    # Finally check pattern matching
    for pattern, city in HOSPITAL_PATTERNS.items():
        if re.search(pattern, hospital_name):
            return city
    
    # If no pattern matches, return None
    return None

def classify_hospitals_by_region():
    """Classify all hospitals by region and city."""
    hospital_to_code = extract_hospitals_from_ods()
    
    # Initialize result structure
    result = {
        "北部": {},
        "中部": {},
        "南部": {},
        "東部": {}
    }
    
    unclassified = []
    
    for hospital, code in hospital_to_code.items():
        city = classify_hospital(hospital, code)
        
        if city and city in CITY_TO_REGION:
            region = CITY_TO_REGION[city]
            
            # Initialize city list if not exists
            if city not in result[region]:
                result[region][city] = []
            
            result[region][city].append(hospital)
        else:
            unclassified.append(hospital)
    
    # Sort hospitals within each city
    for region in result:
        for city in result[region]:
            result[region][city].sort()
    
    return result, unclassified

def main():
    """Main function to classify hospitals and save to JSON."""
    print("Extracting and classifying hospitals...")
    result, unclassified = classify_hospitals_by_region()
    
    # Save to JSON file
    output_file = "hospitals_by_region.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nClassification complete!")
    print(f"Output saved to: {output_file}")
    
    # Print statistics
    total_classified = 0
    for region, cities in result.items():
        region_count = sum(len(hospitals) for hospitals in cities.values())
        total_classified += region_count
        print(f"\n{region}: {region_count} hospitals in {len(cities)} cities")
        for city, hospitals in sorted(cities.items()):
            print(f"  {city}: {len(hospitals)} hospitals")
    
    print(f"\nTotal classified: {total_classified}")
    print(f"Unclassified: {len(unclassified)}")
    
    if unclassified:
        print(f"\nUnclassified hospitals (first 20):")
        for hospital in unclassified[:20]:
            print(f"  - {hospital}")
        
        # Save unclassified to a separate file
        with open("unclassified_hospitals.txt", 'w', encoding='utf-8') as f:
            for hospital in sorted(unclassified):
                f.write(f"{hospital}\n")
        print(f"\nFull list of unclassified hospitals saved to: unclassified_hospitals.txt")
    else:
        # Remove unclassified file if all hospitals are classified
        import os
        if os.path.exists("unclassified_hospitals.txt"):
            os.remove("unclassified_hospitals.txt")
        print("\n✓ All hospitals successfully classified!")

if __name__ == "__main__":
    main()
