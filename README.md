# Hospital Nursing Dataset in Taiwan

## 資料來源 / Data Source

護病比資料來自 `nurse-to-patient-ratios-by-shift/` 目錄中的 ODS 檔案。

## 醫院地區分類 / Hospital Regional Classification

執行 `classify_hospitals.py` 可將所有醫院依照地區分類：

```bash
python3 classify_hospitals.py
```

輸出檔案：`hospitals_by_region.json`

### 分類結構 / Classification Structure

醫院分為四大區域：北部、中部、南部、東部，並依縣市細分：

```json
{
  "北部": {
    "臺北市": ["台大醫院", "..."],
    "新北市": ["亞東醫院", "..."],
    ...
  },
  "中部": {
    "臺中市": ["中山附醫", "..."],
    ...
  },
  "南部": {
    "高雄市": ["高雄長庚", "..."],
    ...
  },
  "東部": {
    "花蓮縣": ["慈濟醫院", "..."],
    ...
  }
}
```

### 統計資料 / Statistics

- **北部 (Northern)**: 150 家醫院，涵蓋 8 個縣市
- **中部 (Central)**: 91 家醫院，涵蓋 5 個縣市  
- **南部 (Southern)**: 186 家醫院，涵蓋 7 個縣市
- **東部 (Eastern)**: 20 家醫院，涵蓋 2 個縣市

**總計**: 447 家醫院 (100% 分類完成)
