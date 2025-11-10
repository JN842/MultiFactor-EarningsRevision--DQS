from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

path = 'src/EarningsRevision_DQS2025.xlsx'

sheet_list = ['Aug25', 'May25', 'Feb25', 'Nov24', 'Aug24', 'May24', 'Feb24', 'Nov23', 'Aug23', 'May23', 'Feb23', 
              'Nov22', 'Aug22', 'May22', 'Feb22', 'Nov21', 'Aug21', 'May21', 'Feb21', 'Nov20', 'Aug20']

cols = ['Bloomberg Code', 'NAME', 'GICS_SECTOR_NAME', 'NTM_CHG_PCTILE', 'ABSRET_1M_Pctile_AVG',
        'ALPHAMO', 'FWDPE', 'FWDRELPE_Pctile', 'REV_RATIO']

df_top_parts, df_bottom_parts = [], []

for i in sheet_list:
    df_raw = pd.read_excel(path, sheet_name=i, header=6).drop(index=[0])
    df_time = pd.read_excel(path, sheet_name=i, header=None)
    time_name = df_time.iloc[0,1]
    
    # Add 3 months using relativedelta
    time_plus_3m = time_name + relativedelta(months=3) # Rebalance ทุก 3 เดือน

    df_factor = df_raw[cols]
    df_factor = df_factor.dropna()

    # จัดการข้อมูลที่ Forward P/E เป็นติดลบ
    def transform_pe_for_ranking(pe_series):
        positive_values = pe_series[pe_series > 0]
        negative_values = pe_series[pe_series < 0].sort_values()  # Sort from most negative to least negative
        
        transformed_series = pe_series.copy()
        
        if len(negative_values) > 0 and len(positive_values) > 0:
            max_positive = positive_values.max()
            
            # Transform negative values
            cumulative_add = 0
            for i, (idx, neg_val) in enumerate(negative_values.items()):
                if i == 0:
                    # First (most negative): make it positive and add to max positive
                    transformed_value = max_positive + abs(neg_val)
                else:
                    # Subsequent values: add the absolute value to cumulative
                    cumulative_add += abs(neg_val)
                    transformed_value = max_positive + cumulative_add
                
                transformed_series[idx] = transformed_value
        
        return transformed_series
        
    # Value ยิ่งมาก จะได้ percentile ที่สูง
    df_factor['REVRATIO_RANK'] = df_factor['REV_RATIO'].rank(pct=True)
    df_factor['MAGPCTILE_RANK'] = df_factor['NTM_CHG_PCTILE'].rank(pct=True)
    df_factor['ALPHAMO_RANK'] = df_factor['ALPHAMO'].rank(pct=True)
    df_factor['REL_ERNYLD_RANK'] = df_factor['FWDRELPE_Pctile'].rank(pct=True)

    # Value ยิ่งน้อย จะได้ percentile ที่สูง
    df_factor['RET1M_RANK'] = df_factor['ABSRET_1M_Pctile_AVG'].rank(pct=True, ascending=False)    
    df_factor['ERNYLD_RANK'] = transform_pe_for_ranking(df_factor['FWDPE']).rank(pct=True, ascending=False)

    df_factor['WGT_RANK'] = (
        0.3 * df_factor['REVRATIO_RANK'] + 
        0.2 * df_factor['MAGPCTILE_RANK'] + 
        0.2 * df_factor['ALPHAMO_RANK'] + 
        0.1 * df_factor['RET1M_RANK'] + 
        0.1 * df_factor['REL_ERNYLD_RANK'] + 
        0.1 * df_factor['ERNYLD_RANK']
    )
    
    df_sorted = df_factor.sort_values(by='WGT_RANK', ascending=False).reset_index(drop=True).reset_index() # reset 2 รอบเพราะต้องการเลข index (rank)

    df_top_decile = df_sorted[['Bloomberg Code', 'NAME', 'GICS_SECTOR_NAME', 'WGT_RANK', 'index', 'REVRATIO_RANK', 'MAGPCTILE_RANK',
                              'ALPHAMO_RANK', 'REL_ERNYLD_RANK', 'RET1M_RANK', 'ERNYLD_RANK']].iloc[0:50,:]

    df_bottom_decile = df_sorted[['Bloomberg Code', 'NAME', 'GICS_SECTOR_NAME', 'WGT_RANK', 'index', 'REVRATIO_RANK', 'MAGPCTILE_RANK',
                              'ALPHAMO_RANK', 'REL_ERNYLD_RANK', 'RET1M_RANK', 'ERNYLD_RANK']].iloc[-50:,:]
    
    df_top_parts.append(df_top_decile)
    df_bottom_parts.append(df_bottom_decile)

df_top_rebalance = pd.concat(df_top_parts, axis=0, ignore_index=True)
df_bottom_rebalance = pd.concat(df_bottom_parts, axis=0, ignore_index=True)

print(df_top_rebalance.iloc[0:5,:])
print(df_bottom_rebalance.iloc[0:5,:])

# ดึง Last Price (PX_LAST) จาก df_top_rebalance และ df_bottom_rebalance ด้วย Bloomberg API แล้วเก็บไว้ในไฟล์ .csv
# Assume ว่าดึงข้อมูลเรียบร้อยแล้ว (Top_Decile.csv, Bottom_Decile.csv)
# Top decile vs Bottom Decile (หุ้น 50 ตัว แบบ equal weight ตัวละ 2%)

date_as_of = "2025-10-23"
top_decile_path = 'src/Top_Decile.csv'
bottom_decile_path = 'src/Bottom_Decile.csv'

top_decile_rebalance = pd.read_csv(top_decile_path)  
bottom_decile_rebalance = pd.read_csv(bottom_decile_path)  

def example_backtest(data, date_as_of):             
    data['Date'] = pd.to_datetime(data['Date'])
    date_as_of = pd.to_datetime(date_as_of)
    start_date = date_as_of - pd.DateOffset(years=5) # ฺBacktest ย้อนหลัง 5 ปี
    
    mask = (data['Date'] >= start_date) & (data['Date'] <= date_as_of)
    data_x_years = data.loc[mask].copy().sort_values('Date')
    
    portfolio_return = data_x_years.groupby('Date')['Daily_Return'].mean().reset_index()    # ใช้ mean เพราะ equal weight
    portfolio_return = portfolio_return.reset_index(drop=True)    
    portfolio_return['NAV'] = 100 * ((1 + portfolio_return['Daily_Return']).cumprod())

    return portfolio_return

top_decile_nav = example_backtest(top_decile_rebalance, date_as_of)
bottom_decile_nav = example_backtest(bottom_decile_rebalance, date_as_of)

# ดู performance กับหุ้น 25 ตัวที่มีคะแนนมากและน้อยที่สุด (equal weight 4%/ตัว)
top_5th_rebalance = pd.read_csv(top_decile_path)
top_5th_rebalance = top_5th_rebalance[top_5th_rebalance['index'] < 25]
top_5th_nav = example_backtest(top_5th_rebalance, date_as_of)

bottom_5th_rebalance = pd.read_csv(bottom_decile_path)
bottom_5th_rebalance = bottom_5th_rebalance.groupby('Date').tail(25) # ใช้วิธีแบบ top_5th ไม่ได้เนื่องจากจำนวน constituent อาจไม่เท่าเดิมในทุกรอบ rebalance
bottom_5th_nav = example_backtest(bottom_5th_rebalance, date_as_of)


# ใช้ yfinance ดึงราคา benchmark (spx index) เพื่อสร้าง NAV
def benchmark_backtest(ticker):
    start_date = "2020-10-23"
    end_date_inclusive = '2025-10-23'
    
    end_date_exclusive = (pd.to_datetime(end_date_inclusive) + pd.DateOffset(days=1)).strftime('%Y-%m-%d')
    
    data = yf.download(ticker, start=start_date, end=end_date_exclusive)
    adj_close = data['Close']
    daily_returns = adj_close.pct_change()
    daily_returns.iloc[0] = 0.0
    benchmark_return = 100 * ((1 + daily_returns).cumprod())
    benchmark_return = pd.concat((benchmark_return, daily_returns), axis=1)
    benchmark_return.columns = ['NAV', 'Daily_Return']       # เปลี่ยนชื่อคอลัมน์ให้ตรงกับ portfolio
    benchmark_return = benchmark_return.reset_index()
    benchmark_return
    
    return benchmark_return
    
spx_nav = benchmark_backtest('^SPX')


# ---- 1) Prep & align ----
def prep(df, nav_name, ret_name):
    out = df[['Date', 'NAV', 'Daily_Return']].copy()
    out['Date'] = pd.to_datetime(out['Date'])
    out = out.sort_values('Date')
    out = out.rename(columns={'NAV': nav_name, 'Daily_Return': ret_name})
    return out

df = (
    prep(top_decile_nav,   'Top',      'Top_ret')
    .merge(prep(bottom_decile_nav, 'Bottom',   'Bottom_ret'), on='Date', how='inner')
    .merge(prep(top_5th_nav,   'Top5',     'Top5_ret'), on='Date', how='inner')
    .merge(prep(bottom_5th_nav,'Bottom5',  'Bottom5_ret'), on='Date', how='inner')
    .merge(prep(spx_nav,       'SPX',      'SPX_ret'), on='Date', how='inner')
)

# ---- 2) Plot equity curves (NAV is base 0; plot 1+NAV for an index-like curve) ----
plt.figure(figsize=(10,6))
plt.plot(df['Date'], 1 + df['Top'],     label='Top Decile', linewidth=1)
plt.plot(df['Date'], 1 + df['Bottom'],  label='Bottom Decile', linewidth=1)
plt.plot(df['Date'], 1 + df['Top5'],    label='Top 5th', linewidth=1)
plt.plot(df['Date'], 1 + df['Bottom5'], label='Bottom 5th', linewidth=1)
plt.plot(df['Date'], 1 + df['SPX'],     label='S&P 500', linewidth=1)
plt.title('Top/Bottom Deciles & 5th Portfolios vs S&P 500 (Last 5 Years)')
plt.xlabel('Date'); plt.ylabel('NAV')
plt.legend(); plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout(); plt.show()

# ---- 3) Performance stats (use provided Daily_Return) ----
TRADING_DAYS = 252
RF = 0.0  # set your annual risk-free if desired

def perf_from_returns(daily_ret: pd.Series, nav: pd.Series) -> pd.Series:
    daily_ret = daily_ret.dropna()
    # equity curve for drawdown (NAV is 0-based; convert to 1-based)
    eq = 1.0 + nav.loc[daily_ret.index].astype(float)
    # totals
    gross = (1.0 + daily_ret).prod()
    total_return = gross - 1.0
    # annualization
    n = len(daily_ret)
    ann_return = gross**(TRADING_DAYS / n) - 1.0
    ann_vol = daily_ret.std() * np.sqrt(TRADING_DAYS)
    sharpe = (ann_return - RF) / ann_vol if ann_vol > 0 else np.nan
    # max drawdown
    run_max = eq.cummax()
    drawdown = eq / run_max - 1.0
    max_dd = drawdown.min()
    return pd.Series({
        'Price Return (%)': total_return * 100,
        'Annualized Return (%)': ann_return * 100,
        'Annualized Volatility': ann_vol * 100,
        'Sharpe Ratio': sharpe,
        'Max Drawdown (%)': max_dd * 100
    })

stats = pd.DataFrame({
    'Top Decile': perf_from_returns(df['Top_ret'], df['Top']),
    'Bottom Decile': perf_from_returns(df['Bottom_ret'], df['Bottom']),
    'Top 5th': perf_from_returns(df['Top5_ret'], df['Top5']),
    'Bottom 5th': perf_from_returns(df['Bottom5_ret'], df['Bottom5']),
    'SPX': perf_from_returns(df['SPX_ret'], df['SPX']),
}).round(4)

print(stats)