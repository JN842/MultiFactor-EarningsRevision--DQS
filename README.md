# Earnings Revision Strategy Backtesting

ทำการ backtest กลยุทธ์การลงทุนโดยใช้ปัจจัย Earnings Revision และปัจจัยอื่นๆ เพื่อคัดเลือกหุ้นที่มีแนวโน้มดี (Top Decile) และแนวโน้มไม่ดี (Bottom Decile) เปรียบเทียบกับ S&P 500

## 📋 Overview

กลยุทธ์นี้ใช้ระบบคะแนนถ่วงน้ำหนักจากปัจจัยต่างๆ ดังนี้:

- **30%** - Earnings Revision Ratio (REV_RATIO)
- **20%** - Magnitude Percentile (NTM_CHG_PCTILE)
- **20%** - Alpha Momentum (ALPHAMO)
- **10%** - 1-Month Return Reversal (ABSRET_1M_Pctile_AVG)
- **10%** - Relative Earnings Yield (FWDRELPE_Pctile)
- **10%** - Earnings Yield (FWDPE)

### Portfolio Construction
- **Top Decile**: 50 หุ้นที่มีคะแนนสูงสุด (Equal Weight 2%/ตัว)
- **Bottom Decile**: 50 หุ้นที่มีคะแนนต่ำสุด (Equal Weight 2%/ตัว)
- **Top 5th**: 25 หุ้นอันดับต้นๆ (Equal Weight 4%/ตัว)
- **Bottom 5th**: 25 หุ้นอันดับท้ายๆ (Equal Weight 4%/ตัว)
- **Rebalance**: ทุก 3 เดือน

## 🛠️ Requirements

```bash
pip install pandas numpy matplotlib yfinance python-dateutil openpyxl
```

## 📁 Project Structure

```
.
├── src/
│   ├── EarningsRevision_DQS2025.xlsx  # ข้อมูลปัจจัยจาก Bloomberg (quarterly)
│   ├── Top_Decile.csv                  # ราคาหุ้น Top 50 (จาก Bloomberg)
│   └── Bottom_Decile.csv               # ราคาหุ้น Bottom 50 (จาก Bloomberg)
├── main.py       # Main script
└── README.md
```

## 📊 Input Data

### Excel File (EarningsRevision_DQS2025.xlsx)
ไฟล์ Excel มี sheets ตามไตรมาส: `Aug25`, `May25`, `Feb25`, `Nov24`, ... `Aug20`

**Columns ที่ใช้:**
- `Bloomberg Code` - รหัสหุ้น
- `NAME` - ชื่อบริษัท
- `GICS_SECTOR_NAME` - หมวดอุตสาหกรรม
- `NTM_CHG_PCTILE` - Magnitude of earnings revision
- `ABSRET_1M_Pctile_AVG` - 1-month return percentile
- `ALPHAMO` - Alpha momentum
- `FWDPE` - Forward P/E ratio
- `FWDRELPE_Pctile` - Relative P/E percentile
- `REV_RATIO` - Earnings Revision ratio

### CSV Files (Top_Decile.csv, Bottom_Decile.csv)
**Required columns:**
- `Date` - วันที่
- `Bloomberg Code` - รหัสหุ้น
- `index` - อันดับคะแนน
- `Daily_Return` - ผลตอบแทนรายวัน

## 🚀 Usage

### 1. เตรียมข้อมูล
ดึงข้อมูลราคาหุ้นจาก Bloomberg API และบันทึกเป็น CSV:
```python
# ต้องมีการดึงข้อมูล PX_LAST จาก Bloomberg
# บันทึกเป็น Top_Decile.csv และ Bottom_Decile.csv
```

### 2. รันการ Backtest
```bash
python main.py
```

### 3. ปรับแต่งพารามิเตอร์
แก้ไขตัวแปรในโค้ด:
```python
date_as_of = "2025-10-23"           # วันที่ต้องการ backtest ถึง
start_date = date_as_of - pd.DateOffset(years=5)  # ระยะเวลา backtest
```

## 📈 Output

### 1. Performance Chart
กราฟแสดงเส้น NAV ของแต่ละ portfolio เทียบกับ S&P 500

### 2. Performance Statistics Table
```
                        Top Decile  Bottom Decile  Top 5th  Bottom 5th    SPX
Price Return (%)             X.XX           X.XX     X.XX        X.XX   X.XX
Annualized Return (%)        X.XX           X.XX     X.XX        X.XX   X.XX
Annualized Volatility       XX.XX          XX.XX    XX.XX       XX.XX  XX.XX
Sharpe Ratio                 X.XX           X.XX     X.XX        X.XX   X.XX
Max Drawdown (%)           -XX.XX         -XX.XX   -XX.XX      -XX.XX -XX.XX
```

## 🔧 Key Features

### Factor Ranking System
- **Positive ranking** (ยิ่งมากยิ่งดี): REV_RATIO, NTM_CHG_PCTILE, ALPHAMO, FWDRELPE_Pctile
- **Negative ranking** (ยิ่งน้อยยิ่งดี): ABSRET_1M_Pctile_AVG, FWDPE

### Special Handling
- **Negative P/E Treatment**: P/E ติดลบจะถูกแปลงเป็นค่าบวกเพื่อการ ranking ที่เหมาะสม
- **Equal Weight Rebalancing**: Portfolio ถูก rebalance ทุก 3 เดือนด้วยน้ำหนักเท่าๆ กัน

## 📝 Notes

1. ข้อมูลจาก Bloomberg ต้องถูกดึงล่วงหน้าและบันทึกเป็น CSV
2. Backtest period: 5 ปีย้อนหลังจาก `date_as_of`
3. Benchmark: S&P 500 Index (^SPX) จาก yfinance
4. Risk-free rate ตั้งที่ 0% (สามารถปรับได้)

---

**Last Updated:** November 2025
