# Hospital Classification by Region

This folder contains scripts and data for classifying Taiwan hospitals by geographic region and city.

## Files

- **`classify_hospitals.py`**: Main classification script
- **`hospitals_by_region.json`**: Output file with hospitals classified by region and city
- **`hospital_codes.json`**: Mapping of hospital names to NHI institution codes

## Usage

```bash
cd hospital-classification
python3 classify_hospitals.py
```

## Output Format

The script generates `hospitals_by_region.json` with the following structure:

```json
{
  "北部": {
    "臺北市": ["台大醫院", "國泰醫院", ...],
    "新北市": ["亞東醫院", ...]
  },
  "中部": { ... },
  "南部": { ... },
  "東部": { ... }
}
```

## Classification Coverage

- **北部 (Northern)**: 150 hospitals across 8 cities
- **中部 (Central)**: 91 hospitals across 5 cities  
- **南部 (Southern)**: 185 hospitals across 7 cities
- **東部 (Eastern)**: 21 hospitals across 2 cities

**Total**: 447 hospitals (100% coverage)
