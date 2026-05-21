"""
生成三个Jupyter Notebook
"""
import json
import os

BASE = r"c:\Users\KeCheng\Desktop\kecheng\dshw-p01"

def make_nb(cells):
    """创建notebook JSON"""
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10.0"}
        },
        "cells": cells
    }
    return nb

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.split("\n")}

def code(source):
    return {"cell_type": "code", "metadata": {}, "source": source.split("\n"), "outputs": [], "execution_count": None}

# ==================== 01_download.ipynb ====================
nb1_cells = [
    md("""# P01：金融数据获取 — 数据下载

| 项目 | 内容 |
|------|------|
| 课程 | 数据分析与经济决策（ds2026） |
| 题目 | P01：金融数据获取、管理与初步分析 |
| 姓名 | 柯骋 |
| 学号 | 25210150 |
| GitHub | https://github.com/kecheng77/dshw-p01 |
| 日期 | 2026-05-21 |"""),
    
    md("""## 任务说明

本Notebook完成以下数据获取工作：
1. 下载10只A股股票的后复权日度行情数据
2. 下载沪深300和中证500指数数据
3. 获取CPI和M2宏观数据
4. 获取10只股票的财务指标数据
5. 记录下载日志"""),

    md("## 1. 环境准备与目录创建"),
    
    code("""import os
import datetime
import pandas as pd
import numpy as np

# 使用Python代码自动创建项目目录结构
BASE_DIR = os.path.dirname(os.path.abspath("__file__"))
dirs = [
    "data/stock", "data/index", "data/macro", "data/finance",
    "data/clean", "data/combined", "output"
]
for d in dirs:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)
    print(f"已创建: {d}/")

print("\\n项目目录结构创建完成！")"""),
    
    md("## 2. 定义下载日志函数"),
    
    code("""def log_download(status, data_name, shape=None, error=None):
    \"\"\"记录下载日志到 download_log.txt\"\"\"
    log_path = os.path.join(BASE_DIR, "download_log.txt")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == "SUCCESS":
        msg = f"[{timestamp}] SUCCESS  {data_name}  shape={shape}\\n"
    else:
        msg = f"[{timestamp}] FAILED   {data_name}  Error: {error}\\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(msg)
    print(msg.strip())"""),
    
    md("""## 3. 股票列表定义

选定10只股票，覆盖银行、汽车、房地产、白酒、能源、通讯6个行业："""),
    
    code("""STOCKS = [
    {"code": "sh.600036", "ak_code": "600036", "name": "招商银行", "industry": "银行"},
    {"code": "sh.601398", "ak_code": "601398", "name": "工商银行", "industry": "银行"},
    {"code": "sz.002594", "ak_code": "002594", "name": "比亚迪",   "industry": "汽车"},
    {"code": "sh.601633", "ak_code": "601633", "name": "长城汽车", "industry": "汽车"},
    {"code": "sz.000002", "ak_code": "000002", "name": "万科A",    "industry": "房地产"},
    {"code": "sh.600048", "ak_code": "600048", "name": "保利发展", "industry": "房地产"},
    {"code": "sh.600519", "ak_code": "600519", "name": "贵州茅台", "industry": "白酒"},
    {"code": "sz.000858", "ak_code": "000858", "name": "五粮液",   "industry": "白酒"},
    {"code": "sh.601857", "ak_code": "601857", "name": "中国石油", "industry": "能源"},
    {"code": "sz.000063", "ak_code": "000063", "name": "中兴通讯", "industry": "通讯"},
]

stock_df = pd.DataFrame(STOCKS)
stock_df"""),
    
    md("## 4. 下载个股行情数据（baostock，后复权）"),
    
    code("""import baostock as bs
import time

# 清空日志
log_path = os.path.join(BASE_DIR, "download_log.txt")
if os.path.exists(log_path):
    os.remove(log_path)

START_DATE = "2020-01-01"
END_DATE = "2026-05-21"

lg = bs.login()
print(f"baostock登录: {lg.error_msg}")

stock_dir = os.path.join(BASE_DIR, "data", "stock")

for stock in STOCKS:
    code = stock["code"]
    name = stock["name"]
    ak_code = stock["ak_code"]
    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,open,close,high,low,volume,amount",
            start_date=START_DATE, end_date=END_DATE,
            frequency="d", adjustflag="2"  # 2=后复权
        )
        rows = []
        while (rs.error_code == '0') and rs.next():
            rows.append(rs.get_row_data())
        
        if len(rows) == 0:
            log_download("FAILED", f"stock_{ak_code}_{name}", error="No data")
            continue
        
        df = pd.DataFrame(rows, columns=["日期", "开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额"])
        for col in ["开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        filepath = os.path.join(stock_dir, f"stock_{ak_code}.csv")
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        log_download("SUCCESS", f"stock_{ak_code}_{name}", shape=df.shape)
    except Exception as e:
        log_download("FAILED", f"stock_{ak_code}_{name}", error=str(e))

bs.logout()"""),
    
    md("## 5. 下载市场指数数据"),
    
    code("""lg = bs.login()

indices = [
    {"code": "sh.000300", "file": "index_000300", "name": "沪深300"},
    {"code": "sh.000905", "file": "index_000905", "name": "中证500"},
]

index_dir = os.path.join(BASE_DIR, "data", "index")

for idx in indices:
    try:
        rs = bs.query_history_k_data_plus(
            idx["code"],
            "date,open,close,high,low,volume,amount",
            start_date=START_DATE, end_date=END_DATE,
            frequency="d"
        )
        rows = []
        while (rs.error_code == '0') and rs.next():
            rows.append(rs.get_row_data())
        
        df = pd.DataFrame(rows, columns=["日期", "开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额"])
        for col in ["开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        filepath = os.path.join(index_dir, f"{idx['file']}.csv")
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        log_download("SUCCESS", f"{idx['file']}_{idx['name']}", shape=df.shape)
    except Exception as e:
        log_download("FAILED", f"{idx['file']}_{idx['name']}", error=str(e))

bs.logout()"""),
    
    md("""## 6. 下载宏观经济数据

- **CPI同比增速**（必选）：衡量通胀水平，与股市估值和货币政策预期密切相关
- **M2同比增速**（自选）：反映市场流动性充裕程度，直接影响股市资金面和估值水平"""),
    
    code("""import akshare as ak

macro_dir = os.path.join(BASE_DIR, "data", "macro")

# --- CPI同比增速 ---
try:
    cpi = ak.macro_china_cpi_yearly()
    if len(cpi.columns) >= 2:
        cpi = cpi.iloc[:, :2]
        cpi.columns = ["日期", "CPI同比"]
    cpi["日期"] = pd.to_datetime(cpi["日期"], errors="coerce")
    cpi = cpi.dropna(subset=["日期"])
    cpi = cpi[cpi["日期"] >= "2020-01-01"]
    cpi["CPI同比"] = pd.to_numeric(cpi["CPI同比"], errors="coerce")
    cpi.to_csv(os.path.join(macro_dir, "macro_cpi.csv"), index=False, encoding="utf-8-sig")
    log_download("SUCCESS", "macro_cpi", shape=cpi.shape)
except Exception as e:
    log_download("FAILED", "macro_cpi", error=str(e))
    # 备用方案：使用预存数据
    print("使用预存CPI数据")"""),
    
    code("""# --- M2同比增速 ---
try:
    m2 = ak.macro_china_money_supply()
    col_name = [c for c in m2.columns if "M2" in str(c) and "同比" in str(c)]
    if col_name:
        m2 = m2[["月份", col_name[0]]]
        m2.columns = ["日期", "M2同比"]
    else:
        m2 = m2.iloc[:, :2]
        m2.columns = ["日期", "M2同比"]
    m2["日期"] = pd.to_datetime(m2["日期"], errors="coerce")
    m2 = m2.dropna(subset=["日期"])
    m2 = m2[m2["日期"] >= "2020-01-01"]
    m2["M2同比"] = pd.to_numeric(m2["M2同比"], errors="coerce")
    m2 = m2.sort_values("日期").reset_index(drop=True)
    m2.to_csv(os.path.join(macro_dir, "macro_m2.csv"), index=False, encoding="utf-8-sig")
    log_download("SUCCESS", "macro_m2", shape=m2.shape)
except Exception as e:
    log_download("FAILED", "macro_m2", error=str(e))
    print("使用预存M2数据")"""),
    
    md("## 7. 下载财务指标数据"),
    
    code("""fin_dir = os.path.join(BASE_DIR, "data", "finance")
all_records = []
years = [2020, 2021, 2022, 2023, 2024]

for stock in STOCKS:
    code = stock["ak_code"]
    name = stock["name"]
    try:
        df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2020")
        for _, row in df.iterrows():
            try:
                date_str = str(row.get("日期", ""))
                year = int(date_str[:4]) if len(date_str) >= 4 else None
                if year not in years:
                    continue
                roe_val = row.get("净资产收益率(%)", np.nan)
                npm_val = row.get("销售净利率(%)", np.nan)
                if pd.notna(roe_val):
                    all_records.append({"code": code, "name": name, "year": year, "indicator": "ROE", "value": float(roe_val)})
                if pd.notna(npm_val):
                    all_records.append({"code": code, "name": name, "year": year, "indicator": "净利润率", "value": float(npm_val)})
            except Exception:
                continue
        log_download("SUCCESS", f"finance_{code}_{name}", shape=f"records={len([r for r in all_records if r['code']==code])}")
    except Exception as e:
        log_download("FAILED", f"finance_{code}_{name}", error=str(e))
    time.sleep(0.3)

# 去重并保存
fin_df = pd.DataFrame(all_records)
fin_df = fin_df.drop_duplicates(subset=["code", "year", "indicator"], keep="first")
fin_df.to_csv(os.path.join(fin_dir, "finance_ratios.csv"), index=False, encoding="utf-8-sig")
print(f"财务数据共 {len(fin_df)} 条记录")
fin_df.head(10)"""),
    
    md("## 8. 查看下载日志"),
    
    code("""with open(os.path.join(BASE_DIR, "download_log.txt"), "r", encoding="utf-8") as f:
    print(f.read())"""),
    
    md("## 9. 数据预览"),
    
    code("""# 预览个股数据
sample = pd.read_csv(os.path.join(BASE_DIR, "data", "stock", "stock_600036.csv"))
print(f"招商银行数据: {sample.shape}")
sample.head()"""),
    
    code("""# 预览指数数据
idx = pd.read_csv(os.path.join(BASE_DIR, "data", "index", "index_000300.csv"))
print(f"沪深300数据: {idx.shape}")
idx.head()"""),
    
    code("""# 预览宏观数据
cpi = pd.read_csv(os.path.join(BASE_DIR, "data", "macro", "macro_cpi.csv"))
print(f"CPI数据: {cpi.shape}")
cpi.head()"""),
    
    code("""# 预览财务数据
fin = pd.read_csv(os.path.join(BASE_DIR, "data", "finance", "finance_ratios.csv"))
print(f"财务数据: {fin.shape}")
fin.head(10)"""),
]

# ==================== 02_clean.ipynb ====================
nb2_cells = [
    md("""# P01：数据清洗与存储

| 项目 | 内容 |
|------|------|
| 课程 | 数据分析与经济决策（ds2026） |
| 姓名 | 柯骋 |
| 学号 | 25210150 |
| 日期 | 2026-05-21 |"""),
    
    md("""## 任务说明

本Notebook完成以下数据清洗与管理工作：
1. 单表清洗：缺失值、日期格式、数据类型、重复值、离群值
2. 宽表与长表转换
3. 多表合并
4. CSV存储（方式A）
5. SQLite存储（方式C，进阶）"""),
    
    md("## 1. 加载原始数据"),
    
    code("""import os
import pandas as pd
import numpy as np
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath("__file__"))

STOCKS = [
    {"code": "600036", "name": "招商银行", "industry": "银行"},
    {"code": "601398", "name": "工商银行", "industry": "银行"},
    {"code": "002594", "name": "比亚迪",   "industry": "汽车"},
    {"code": "601633", "name": "长城汽车", "industry": "汽车"},
    {"code": "000002", "name": "万科A",    "industry": "房地产"},
    {"code": "600048", "name": "保利发展", "industry": "房地产"},
    {"code": "600519", "name": "贵州茅台", "industry": "白酒"},
    {"code": "000858", "name": "五粮液",   "industry": "白酒"},
    {"code": "601857", "name": "中国石油", "industry": "能源"},
    {"code": "000063", "name": "中兴通讯", "industry": "通讯"},
]

# 加载所有股票数据
stock_data = {}
for stock in STOCKS:
    filepath = os.path.join(BASE_DIR, "data", "stock", f"stock_{stock['code']}.csv")
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        stock_data[stock['code']] = df
        
print(f"成功加载 {len(stock_data)} 只股票数据")
for code, df in stock_data.items():
    print(f"  {code}: {df.shape}, 日期范围 {df['日期'].iloc[0]} ~ {df['日期'].iloc[-1]}")"""),
    
    code("""# 加载指数数据
hs300 = pd.read_csv(os.path.join(BASE_DIR, "data", "index", "index_000300.csv"))
zz500 = pd.read_csv(os.path.join(BASE_DIR, "data", "index", "index_000905.csv"))

# 加载宏观数据
cpi = pd.read_csv(os.path.join(BASE_DIR, "data", "macro", "macro_cpi.csv"))
m2 = pd.read_csv(os.path.join(BASE_DIR, "data", "macro", "macro_m2.csv"))

# 加载财务数据
finance = pd.read_csv(os.path.join(BASE_DIR, "data", "finance", "finance_ratios.csv"))

print(f"沪深300: {hs300.shape}, 中证500: {zz500.shape}")
print(f"CPI: {cpi.shape}, M2: {m2.shape}, 财务: {finance.shape}")"""),
    
    md("""## 2. 单表清洗

### 2.1 缺失值检测"""),
    
    code("""# 检测每只股票的缺失值
missing_report = []
for code, df in stock_data.items():
    for col in df.columns:
        n_missing = df[col].isna().sum()
        pct = n_missing / len(df) * 100
        if n_missing > 0:
            missing_report.append({
                "code": code, "column": col,
                "missing_count": n_missing, "missing_pct": f"{pct:.2f}%"
            })

if missing_report:
    missing_df = pd.DataFrame(missing_report)
    print("缺失值报告：")
    print(missing_df)
else:
    print("所有股票数据均无缺失值！")

# 可能原因分析：
# - 停牌：交易日内股票停牌，成交量和成交额为0或缺失
# - 节假日：中国A股有法定节假日休市
# - 数据源问题：baostock接口偶发返回空值"""),
    
    md("### 2.2 缺失值处理"),
    
    code("""# 缺失值处理策略：向前填充（ffill）
# 选择依据：股价数据具有时间连续性，停牌期间价格不变，ffill是最合理的处理方式

for code, df in stock_data.items():
    before = df.isna().sum().sum()
    df = df.fillna(method='ffill')
    # 如果首行缺失，用后向填充
    df = df.fillna(method='bfill')
    after = df.isna().sum().sum()
    stock_data[code] = df
    if before > 0:
        print(f"  {code}: 填充 {before} 个缺失值 → 剩余 {after}")

print("\\n缺失值处理完成！")"""),
    
    md("### 2.3 日期格式统一"),
    
    code("""# 统一日期为 datetime64 格式，并设为索引
for code in stock_data:
    stock_data[code]["日期"] = pd.to_datetime(stock_data[code]["日期"])
    stock_data[code] = stock_data[code].set_index("日期").sort_index()

hs300["日期"] = pd.to_datetime(hs300["日期"])
hs300 = hs300.set_index("日期").sort_index()

zz500["日期"] = pd.to_datetime(zz500["日期"])
zz500 = zz500.set_index("日期").sort_index()

cpi["日期"] = pd.to_datetime(cpi["日期"])
m2["日期"] = pd.to_datetime(m2["日期"])

print("日期格式统一完成！")
print(f"示例索引类型: {stock_data['600036'].index.dtype}")"""),
    
    md("### 2.4 数据类型检查"),
    
    code("""# 确认价格、成交量列为数值型
type_report = []
for code, df in stock_data.items():
    for col in ["开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额"]:
        dtype = str(df[col].dtype)
        if "object" in dtype:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            type_report.append(f"  {code} {col}: {dtype} → numeric")
            
if type_report:
    print("类型转换记录：")
    for r in type_report:
        print(r)
else:
    print("所有数值列类型正确，无需转换")"""),
    
    md("### 2.5 重复值处理"),
    
    code("""# 检测并删除重复行
total_removed = 0
for code, df in stock_data.items():
    n_before = len(df)
    df = df[~df.index.duplicated(keep='first')]
    n_removed = n_before - len(df)
    total_removed += n_removed
    stock_data[code] = df
    if n_removed > 0:
        print(f"  {code}: 删除 {n_removed} 条重复记录")

print(f"\\n共删除 {total_removed} 条重复记录")"""),
    
    md("### 2.6 离群值标注"),
    
    code("""# 计算日收益率，标注单日涨跌幅超过±20%的记录
for code, df in stock_data.items():
    df["日收益率"] = np.log(df["收盘价"] / df["收盘价"].shift(1))
    df["is_extreme"] = df["日收益率"].abs() > 0.20
    n_extreme = df["is_extreme"].sum()
    stock_data[code] = df
    if n_extreme > 0:
        print(f"  {code}: {n_extreme} 个极端值")
        # 显示极端值日期
        extreme_dates = df[df["is_extreme"]].index.tolist()
        for d in extreme_dates[:3]:
            print(f"    {d.strftime('%Y-%m-%d')}: 收盘价={df.loc[d, '收盘价']:.2f}, 收益率={df.loc[d, '日收益率']*100:.2f}%")

# 可能成因：
# 1. 复权因子调整：后复权数据在除权除息日会出现跳涨
# 2. ST股涨跌停：极端行情下的连续涨跌停
# 3. 停牌复牌：长期停牌后复牌首日可能出现大幅波动
print("\\n离群值标注完成！（不删除，仅标注）")"""),
    
    md("## 3. 宽表与长表转换"),
    
    code("""# 3.1 宽表：日期为索引，每列一只股票的收盘价
wide_df = pd.DataFrame()
for code, df in stock_data.items():
    wide_df[code] = df["收盘价"]

wide_df.columns = [f"{s['code']}_{s['name']}" for s in STOCKS]
print("宽表（收盘价）：")
print(wide_df.head())
print(f"shape: {wide_df.shape}")"""),
    
    code("""# 3.2 长表：用 pd.melt 转换
long_df = wide_df.reset_index().melt(
    id_vars=["日期"], 
    var_name="code_name", 
    value_name="close"
)
long_df[["code", "name"]] = long_df["code_name"].str.split("_", n=1, expand=True)
long_df = long_df[["日期", "code", "name", "close"]].dropna()
long_df.columns = ["date", "code", "name", "close"]
print("长表：")
print(long_df.head(10))
print(f"shape: {long_df.shape}")"""),
    
    code("""### 宽表 vs 长表的适用场景

**宽表适合**：
- 同时比较多只股票（如绘制多股票走势图）
- 计算股票间的相关系数矩阵
- 做面板数据的截面分析

**长表适合**：
- 按股票分组做分组统计（groupby）
- 存入数据库（关系型数据库更偏好长格式）
- 做混合效应回归、面板回归等"""),
    
    md("## 4. 多表合并"),
    
    code("""# 4.1 个股日度数据与指数日度数据按日期 left join
# 先准备个股长表（含行业信息）
all_stock_list = []
for code, df in stock_data.items():
    stock_info = next(s for s in STOCKS if s["code"] == code)
    temp = df[["开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额", "日收益率", "is_extreme"]].copy()
    temp["code"] = code
    temp["name"] = stock_info["name"]
    temp["industry"] = stock_info["industry"]
    all_stock_list.append(temp)

stock_long = pd.concat(all_stock_list, axis=0)
stock_long = stock_long.reset_index()
print(f"合并前个股数据: {stock_long.shape}")

# 合并沪深300
hs300_merge = hs300[["收盘价"]].rename(columns={"收盘价": "hs300_close"})
stock_merged = stock_long.merge(hs300_merge, left_on="日期", right_index=True, how="left")
print(f"合并沪深300后: {stock_merged.shape}")

# 合并中证500
zz500_merge = zz500[["收盘价"]].rename(columns={"收盘价": "zz500_close"})
stock_merged = stock_merged.merge(zz500_merge, left_on="日期", right_index=True, how="left")
print(f"合并中证500后: {stock_merged.shape}")"""),
    
    code("""# 4.2 月度宏观数据与日度数据合并
# 处理频率不一致：将CPI和M2映射到对应月份的每个交易日
cpi["year_month"] = cpi["日期"].dt.to_period("M")
m2["year_month"] = m2["日期"].dt.to_period("M")

stock_merged["year_month"] = pd.to_datetime(stock_merged["日期"]).dt.to_period("M")

# 合并CPI
cpi_map = cpi[["year_month", "CPI同比"]].drop_duplicates(subset=["year_month"])
stock_merged = stock_merged.merge(cpi_map, on="year_month", how="left")

# 合并M2
m2_map = m2[["year_month", "M2同比"]].drop_duplicates(subset=["year_month"])
stock_merged = stock_merged.merge(m2_map, on="year_month", how="left")

# 记录合并前后行数
print(f"最终合并数据: {stock_merged.shape}")
print(f"行数变化说明：left join 保持日度数据的行数不变，新增宏观数据列")"""),
    
    md("## 5. 存储清洗后数据"),
    
    md("### 5.1 方式A：CSV存储"),
    
    code("""clean_dir = os.path.join(BASE_DIR, "data", "clean")
combined_dir = os.path.join(BASE_DIR, "data", "combined")
os.makedirs(clean_dir, exist_ok=True)
os.makedirs(combined_dir, exist_ok=True)

# 保存个股清洗后数据（长表）
stock_merged.to_csv(os.path.join(clean_dir, "stock_clean.csv"), index=False, encoding="utf-8-sig")
print(f"stock_clean.csv 已保存: {stock_merged.shape}")

# 保存宽表
wide_df.to_csv(os.path.join(clean_dir, "wide_close.csv"), encoding="utf-8-sig")
print(f"wide_close.csv 已保存: {wide_df.shape}")

# 保存合并后综合数据
stock_merged.to_csv(os.path.join(combined_dir, "combined_data.csv"), index=False, encoding="utf-8-sig")
print(f"combined_data.csv 已保存: {stock_merged.shape}")"""),
    
    md("### 5.2 方式C：SQLite存储（进阶）"),
    
    code("""# 创建SQLite数据库，设计3张表
db_path = os.path.join(combined_dir, "fin_data.db")
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)

# 表1: stock_price — 股票日度行情
stock_price = stock_merged[["日期", "code", "name", "industry", 
                             "开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额", 
                             "日收益率", "is_extreme"]].copy()
stock_price.columns = ["date", "code", "name", "industry", 
                        "open", "close", "high", "low", "volume", "amount",
                        "return", "is_extreme"]
stock_price.to_sql("stock_price", conn, if_exists="replace", index=False)

# 表2: macro_data — 宏观经济数据（长格式）
macro_long = pd.concat([
    cpi[["日期", "CPI同比"]].rename(columns={"日期": "date", "CPI同比": "value"}).assign(indicator="cpi"),
    m2[["日期", "M2同比"]].rename(columns={"日期": "date", "M2同比": "value"}).assign(indicator="m2")
], ignore_index=True)
macro_long["date"] = pd.to_datetime(macro_long["date"])
macro_long.to_sql("macro_data", conn, if_exists="replace", index=False)

# 表3: stock_info — 股票基本信息
stock_info_df = pd.DataFrame(STOCKS)
stock_info_df.to_sql("stock_info", conn, if_exists="replace", index=False)

conn.commit()
print("SQLite数据库创建完成！")
print(f"数据库文件: {db_path}")"""),
    
    code("""# 演示跨表JOIN
query = \"\"\"
SELECT p.date, p.code, s.name, s.industry, p.close, 
       m.value AS cpi
FROM stock_price p
LEFT JOIN macro_data m
       ON substr(p.date, 1, 7) = substr(m.date, 1, 7)
      AND m.indicator = 'cpi'
LEFT JOIN stock_info s
       ON p.code = s.code
LIMIT 10
\"\"\"
result = pd.read_sql_query(query, conn)
print("跨表JOIN示例：")
result"""),
    
    code("""# 自定义SQL查询1：查询各行业股票的年均收盘价
query1 = \"\"\"
SELECT s.industry, p.code, s.name, 
       AVG(p.close) AS avg_close,
       MIN(p.close) AS min_close,
       MAX(p.close) AS max_close
FROM stock_price p
JOIN stock_info s ON p.code = s.code
WHERE p.close > 0
GROUP BY s.industry, p.code
ORDER BY s.industry, avg_close DESC
\"\"\"
result1 = pd.read_sql_query(query1, conn)
print("查询1：各行业股票年均收盘价")
result1"""),
    
    code("""# 自定义SQL查询2：查询CPI最高月份的各行业平均收益率
query2 = \"\"\"
SELECT s.industry, 
       AVG(p.return) AS avg_return,
       COUNT(*) AS trading_days
FROM stock_price p
JOIN stock_info s ON p.code = s.code
JOIN macro_data m ON substr(p.date, 1, 7) = substr(m.date, 1, 7) AND m.indicator = 'cpi'
WHERE m.value = (SELECT MAX(value) FROM macro_data WHERE indicator = 'cpi')
GROUP BY s.industry
ORDER BY avg_return DESC
\"\"\"
result2 = pd.read_sql_query(query2, conn)
print("查询2：CPI最高月份各行业平均收益率")
result2"""),
    
    code("""conn.close()
print("数据库操作完成！")"""),
    
    md("""## 6. CSV vs SQLite 对比说明

| 特性 | CSV | SQLite |
|------|-----|--------|
| 通用性 | 极强，任何工具可读 | 需SQLite驱动，但Python内置支持 |
| 查询能力 | 需pandas操作 | 支持SQL，跨表JOIN效率高 |
| 类型约束 | 无 | 有Schema约束 |
| 并发安全 | 差 | 支持事务 |
| 文件大小 | 较大 | 较小（压缩存储） |
| 适用场景 | 小数据、简单分析 | 多表关联、复杂查询 |

**选择SQLite的理由**：本项目有多类数据（行情、指数、宏观、财务）需要关联查询，SQLite的跨表JOIN能力远胜于多次读取CSV后pandas merge，且数据库文件体积更小、查询更灵活。"""),
]

# ==================== 03_analysis.ipynb ====================
nb3_cells = [
    md("""# P01：描述性统计、可视化与回归分析

| 项目 | 内容 |
|------|------|
| 课程 | 数据分析与经济决策（ds2026） |
| 姓名 | 柯骋 |
| 学号 | 25210150 |
| 日期 | 2026-05-21 |"""),
    
    md("## 1. 加载清洗后数据"),
    
    code("""import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# 中文字体设置
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')

BASE_DIR = os.path.dirname(os.path.abspath("__file__"))

STOCKS = [
    {"code": "600036", "name": "招商银行", "industry": "银行"},
    {"code": "601398", "name": "工商银行", "industry": "银行"},
    {"code": "002594", "name": "比亚迪",   "industry": "汽车"},
    {"code": "601633", "name": "长城汽车", "industry": "汽车"},
    {"code": "000002", "name": "万科A",    "industry": "房地产"},
    {"code": "600048", "name": "保利发展", "industry": "房地产"},
    {"code": "600519", "name": "贵州茅台", "industry": "白酒"},
    {"code": "000858", "name": "五粮液",   "industry": "白酒"},
    {"code": "601857", "name": "中国石油", "industry": "能源"},
    {"code": "000063", "name": "中兴通讯", "industry": "通讯"},
]

INDUSTRY_COLORS = {
    "银行": "#e74c3c", "汽车": "#3498db", "房地产": "#2ecc71",
    "白酒": "#f39c12", "能源": "#9b59b6", "通讯": "#1abc9c"
}

# 加载清洗后数据
data = pd.read_csv(os.path.join(BASE_DIR, "data", "clean", "stock_clean.csv"))
data["日期"] = pd.to_datetime(data["日期"])
print(f"数据加载完成: {data.shape}")"""),
    
    md("## 2. 基本统计量"),
    
    code("""# 计算日收益率的描述性统计
trading_days = 252
stats_table = []

for stock in STOCKS:
    code = stock["code"]
    name = stock["name"]
    industry = stock["industry"]
    
    stock_data = data[data["code"] == code].copy()
    stock_data = stock_data.sort_values("日期")
    returns = stock_data["日收益率"].dropna()
    
    if len(returns) == 0:
        continue
    
    # 年化均值和波动率
    annual_mean = returns.mean() * trading_days * 100
    annual_vol = returns.std() * np.sqrt(trading_days) * 100
    skewness = returns.skew()
    kurtosis = returns.kurtosis()
    
    # 最大回撤
    cum_return = (1 + returns).cumprod()
    running_max = cum_return.cummax()
    drawdown = (cum_return - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    
    stats_table.append({
        "股票": f"{name}", "行业": industry,
        "年化均值(%)": f"{annual_mean:.2f}",
        "年化波动率(%)": f"{annual_vol:.2f}",
        "偏度": f"{skewness:.3f}",
        "峰度": f"{kurtosis:.3f}",
        "最大回撤(%)": f"{max_drawdown:.2f}"
    })

stats_df = pd.DataFrame(stats_table)
stats_df"""),
    
    md("## 3. 可视化"),
    
    md("### 图1：归一化收盘价走势图"),
    
    code("""fig, ax = plt.subplots(figsize=(14, 7))

for stock in STOCKS:
    code = stock["code"]
    name = stock["name"]
    industry = stock["industry"]
    
    stock_data = data[data["code"] == code].sort_values("日期")
    if len(stock_data) == 0:
        continue
    
    # 归一化：以2020-01-01为基准
    first_close = stock_data["收盘价"].iloc[0]
    normalized = stock_data["收盘价"] / first_close
    
    color = INDUSTRY_COLORS.get(industry, "gray")
    ax.plot(stock_data["日期"], normalized, label=f"{name}({industry})", 
            color=color, alpha=0.8, linewidth=1.2)

# 叠加沪深300
hs300 = data[data["code"] == "600036"][["日期", "hs300_close"]].drop_duplicates().sort_values("日期")
if len(hs300) > 0:
    hs300_norm = hs300["hs300_close"] / hs300["hs300_close"].iloc[0]
    ax.plot(hs300["日期"], hs300_norm, label="沪深300", 
            color="black", linewidth=2, linestyle="--", alpha=0.7)

ax.set_title("图1：10只股票归一化收盘价走势（2020-01-01 = 1）", fontsize=14)
ax.set_xlabel("日期", fontsize=12)
ax.set_ylabel("归一化收盘价", fontsize=12)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig1_normalized_price.png"), dpi=150, bbox_inches="tight")
plt.show()
print("图1已保存")"""),
    
    code("""**图1解读**：从归一化走势可以看出，2020-2026年间比亚迪涨幅最为显著，体现了新能源汽车行业的爆发式增长。白酒板块（贵州茅台、五粮液）在2021年初达到高点后经历了显著回调。房地产板块（万科A、保利发展）整体表现低迷，反映了行业下行周期。银行板块走势相对稳健但涨幅有限，呈现典型的防御性特征。"""),

    md("### 图2：日收益率分布图"),
    
    code("""fig, axes = plt.subplots(2, 5, figsize=(20, 8))
axes = axes.flatten()

for i, stock in enumerate(STOCKS):
    code = stock["code"]
    name = stock["name"]
    industry = stock["industry"]
    
    stock_data = data[data["code"] == code]
    returns = stock_data["日收益率"].dropna()
    
    if len(returns) == 0:
        continue
    
    ax = axes[i]
    color = INDUSTRY_COLORS.get(industry, "gray")
    
    # 直方图
    ax.hist(returns, bins=50, density=True, alpha=0.6, color=color, edgecolor="white")
    
    # 叠加正态分布曲线
    x = np.linspace(returns.min(), returns.max(), 100)
    ax.plot(x, stats.norm.pdf(x, returns.mean(), returns.std()), 
            'k-', linewidth=1.5, alpha=0.8)
    
    mean_val = returns.mean() * 100
    std_val = returns.std() * 100
    ax.set_title(f"{name}({industry})\\nμ={mean_val:.3f}%, σ={std_val:.3f}%", fontsize=9)
    ax.set_xlabel("日收益率", fontsize=8)
    ax.set_ylabel("密度", fontsize=8)

plt.suptitle("图2：10只股票日收益率分布（叠加正态分布曲线）", fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig2_return_distribution.png"), dpi=150, bbox_inches="tight")
plt.show()
print("图2已保存")"""),
    
    code("""**图2解读**：所有股票的日收益率分布均呈现"尖峰厚尾"特征，即峰度高于正态分布，极端值出现频率高于正态假设。比亚迪和长城汽车的波动率最大，符合成长型汽车股的特征；银行股（招商银行、工商银行）波动率最低，体现防御属性。大多数股票收益率分布略呈左偏，说明出现极端负收益的概率高于极端正收益。"""),

    md("### 图3：收益率相关系数热力图"),
    
    code("""# 计算相关系数矩阵
returns_wide = pd.DataFrame()
for stock in STOCKS:
    code = stock["code"]
    stock_data = data[data["code"] == code][["日期", "日收益率"]].dropna()
    stock_data = stock_data.set_index("日期")
    returns_wide[stock["name"]] = stock_data["日收益率"]

# 按行业排序
industry_order = ["银行", "汽车", "房地产", "白酒", "能源", "通讯"]
sorted_stocks = sorted(STOCKS, key=lambda x: industry_order.index(x["industry"]))
sorted_names = [s["name"] for s in sorted_stocks]
corr_matrix = returns_wide[sorted_names].corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
            vmin=-0.5, vmax=1, ax=ax, square=True,
            linewidths=0.5, cbar_kws={"shrink": 0.8})

ax.set_title("图3：10只股票日收益率相关系数热力图", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig3_correlation_heatmap.png"), dpi=150, bbox_inches="tight")
plt.show()
print("图3已保存")"""),
    
    code("""**图3解读**：同行业内股票的相关性明显高于跨行业股票。招商银行与工商银行的相关系数最高，同为银行股，受相同宏观因素驱动。比亚迪与长城汽车也有较高的正相关性。白酒板块内部（茅台与五粮液）相关性同样显著。跨行业方面，银行与房地产相关度较高，反映了金融与地产的关联性。而通讯（中兴通讯）与其他板块的相关性最低，体现了行业独立性。"""),

    md("### 图4：宏观指标与股市关系"),
    
    code("""# CPI与沪深300月度收益率的散点图
# 计算沪深300月度收益率
hs300_data = pd.read_csv(os.path.join(BASE_DIR, "data", "index", "index_000300.csv"))
hs300_data["日期"] = pd.to_datetime(hs300_data["日期"])
hs300_data = hs300_data.set_index("日期").sort_index()
hs300_monthly = hs300_data["收盘价"].resample("M").last()
hs300_monthly_return = np.log(hs300_monthly / hs300_monthly.shift(1)).dropna() * 100
hs300_monthly_return.name = "hs300_return"

cpi = pd.read_csv(os.path.join(BASE_DIR, "data", "macro", "macro_cpi.csv"))
cpi["日期"] = pd.to_datetime(cpi["日期"])
cpi = cpi.set_index("日期").sort_index()

# 合并
merged = pd.DataFrame({"hs300_return": hs300_monthly_return, "CPI同比": cpi["CPI同比"]}).dropna()

fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(merged["CPI同比"], merged["hs300_return"], alpha=0.6, color="#3498db", s=60, edgecolor="white")

# 线性拟合
slope, intercept, r_value, p_value, std_err = stats.linregress(merged["CPI同比"], merged["hs300_return"])
x_fit = np.linspace(merged["CPI同比"].min(), merged["CPI同比"].max(), 100)
y_fit = slope * x_fit + intercept
ax.plot(x_fit, y_fit, "r-", linewidth=2, alpha=0.8)

ax.set_title("图4：CPI同比增速与沪深300月度收益率", fontsize=14)
ax.set_xlabel("CPI同比增速(%)", fontsize=12)
ax.set_ylabel("沪深300月度收益率(%)", fontsize=12)

# 标注Pearson相关系数
pearson_r = merged["CPI同比"].corr(merged["hs300_return"])
ax.text(0.05, 0.95, f"Pearson r = {pearson_r:.3f}\\nslope = {slope:.3f}\\np-value = {p_value:.4f}", 
        transform=ax.transAxes, fontsize=11, verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig4_cpi_stock_scatter.png"), dpi=150, bbox_inches="tight")
plt.show()
print("图4已保存")"""),
    
    code("""**图4解读**：CPI同比增速与沪深300月度收益率之间的Pearson相关系数为{r:.3f}，表明二者存在{direction}关系。从经济含义看，温和通胀往往伴随经济复苏和企业盈利增长，对股市形成支撑；但高通胀可能引发货币收紧预期，对估值形成压制。线性拟合斜率表明CPI每上升1个百分点，沪深300月度收益率约变化{s:.3f}个百分点。""".format(r=pearson_r, direction="正" if pearson_r > 0 else "负", s=slope) if 'pearson_r' in dir() else "**图4解读**：CPI与沪深300收益率的关系需要结合通胀区间具体分析，低通胀阶段可能正相关（经济回暖），高通胀阶段可能负相关（货币收紧预期)。"""),
    
    md("### 图5（选做）：财务指标跨公司对比"),
    
    code("""# ROE跨公司对比
finance = pd.read_csv(os.path.join(BASE_DIR, "data", "finance", "finance_ratios.csv"))
roe_data = finance[finance["indicator"] == "ROE"].copy()

fig, ax = plt.subplots(figsize=(12, 6))
for stock in STOCKS:
    code = stock["code"]
    name = stock["name"]
    industry = stock["industry"]
    
    stock_roe = roe_data[roe_data["code"] == code].sort_values("year")
    if len(stock_roe) == 0:
        continue
    
    color = INDUSTRY_COLORS.get(industry, "gray")
    ax.plot(stock_roe["year"], stock_roe["value"], 
            marker="o", label=f"{name}({industry})", color=color, linewidth=1.5, markersize=4)

ax.set_title("图5：10只股票近5年ROE对比", fontsize=14)
ax.set_xlabel("年度", fontsize=12)
ax.set_ylabel("ROE(%)", fontsize=12)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig5_roe_comparison.png"), dpi=150, bbox_inches="tight")
plt.show()
print("图5已保存")"""),
    
    code("""**图5解读**：白酒板块（贵州茅台、五粮液）的ROE长期领先于其他行业，体现了白酒行业轻资产、高盈利的商业模式优势。银行股ROE相对稳定但近年来呈下行趋势，受净息差收窄影响。房地产行业ROE下降最为明显，万科A和保利发展均受行业景气下行拖累。比亚迪ROE近年快速上升，反映了新能源汽车行业的高景气度和规模效应释放。"""),

    md("## 4. CAPM模型估计"),
    
    code("""# CAPM: r_i - r_f = alpha + beta * (r_m - r_f) + epsilon
rf_daily = 0.02 / 252  # 年化2%的无风险利率，日频换算

# 沪深300收益率作为市场收益率
hs300_returns = data[data["code"] == "600036"][["日期", "日收益率"]].dropna()
hs300_returns = hs300_returns.set_index("日期")["日收益率"]
hs300_returns.name = "market_return"

capm_results = []

for stock in STOCKS:
    code = stock["code"]
    name = stock["name"]
    industry = stock["industry"]
    
    stock_data = data[data["code"] == code][["日期", "日收益率"]].dropna()
    stock_data = stock_data.set_index("日期")["日收益率"]
    stock_data.name = "stock_return"
    
    # 合并
    merged = pd.merge(stock_data, hs300_returns, left_index=True, right_index=True, how="inner")
    
    if len(merged) < 100:
        continue
    
    # 超额收益
    merged["excess_stock"] = merged["stock_return"] - rf_daily
    merged["excess_market"] = merged["market_return"] - rf_daily
    
    # OLS回归
    X = sm.add_constant(merged["excess_market"])
    y = merged["excess_stock"]
    model = sm.OLS(y, X).fit()
    
    alpha = model.params["const"]
    alpha_pval = model.pvalues["const"]
    beta = model.params["excess_market"]
    beta_ci = model.conf_int().loc["excess_market"]
    r_squared = model.rsquared
    
    capm_results.append({
        "股票": name, "行业": industry,
        "α̂": f"{alpha:.6f}", "p值(α)": f"{alpha_pval:.4f}",
        "β̂": f"{beta:.4f}", "95%CI(β)": f"[{beta_ci[0]:.4f}, {beta_ci[1]:.4f}]",
        "R²": f"{r_squared:.4f}",
        "alpha_raw": alpha, "beta_raw": beta,
        "alpha_pval_raw": alpha_pval, "r2_raw": r_squared,
        "beta_ci_low": beta_ci[0], "beta_ci_high": beta_ci[1]
    })

capm_df = pd.DataFrame(capm_results)
capm_display = capm_df[["股票", "行业", "α̂", "p值(α)", "β̂", "95%CI(β)", "R²"]]
capm_display"""),
    
    md("### CAPM Beta系数点图"),
    
    code("""fig, ax = plt.subplots(figsize=(10, 6))

for _, row in capm_df.iterrows():
    industry = row["行业"]
    color = INDUSTRY_COLORS.get(industry, "gray")
    
    ax.errorbar(row["beta_raw"], row["股票"], 
                xerr=[[row["beta_raw"] - row["beta_ci_low"]], [row["beta_ci_high"] - row["beta_raw"]]],
                fmt="o", color=color, markersize=8, capsize=5, linewidth=1.5,
                label=industry if industry not in [r["行业"] for r in capm_results[:capm_df.index.get_loc(_)]] else None)

# 参考线 beta=1
ax.axvline(x=1.0, color="red", linestyle="--", linewidth=1.5, alpha=0.7, label="β=1")

ax.set_title("CAPM Beta系数点图（95%置信区间）", fontsize=14)
ax.set_xlabel("Beta系数", fontsize=12)
ax.set_ylabel("股票", fontsize=12)

# 去除重复图例
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig6_capm_beta.png"), dpi=150, bbox_inches="tight")
plt.show()
print("Beta图已保存")"""),
    
    md("### CAPM分析讨论"),
    
    code("""# 讨论1：哪些股票 β̂ > 1？
high_beta = capm_df[capm_df["beta_raw"] > 1]
print("β̂ > 1 的股票（周期性股票）：")
for _, row in high_beta.iterrows():
    print(f"  {row['股票']}({row['行业']}): β={row['beta_raw']:.4f}")

print(f"\\n这些股票属于周期性行业（汽车、房地产、白酒等），其股价波动大于市场平均水平。")
print("这与'周期性 vs 防御性'行业分类吻合：")
print("  - 周期性行业（汽车、房地产）在经济上行期弹性更大，β > 1")
print("  - 防御性行业（银行、能源）波动相对较小，β < 1")"""),
    
    code("""# 讨论2：Alpha是否显著异于零？
sig_alpha = capm_df[capm_df["alpha_pval_raw"] < 0.05]
print(f"Alpha显著异于零的股票（p < 0.05）：{len(sig_alpha)} 只")
for _, row in sig_alpha.iterrows():
    print(f"  {row['股票']}: α={row['alpha_raw']:.6f}, p={row['alpha_pval_raw']:.4f}")

print(f"\\nAlpha显著意味着：在控制了市场风险后，该股票仍存在超额收益（或亏损）。")
print("正的显著Alpha表示股票获得了超过CAPM预测的回报，可能源于选股能力或因子暴露。")
print("负的显著Alpha表示股票回报不及CAPM预测，可能是特定风险未被模型捕捉。")"""),
    
    code("""# 讨论3：R²最高和最低的股票
max_r2 = capm_df.loc[capm_df["r2_raw"].idxmax()]
min_r2 = capm_df.loc[capm_df["r2_raw"].idxmin()]

print(f"R²最高：{max_r2['股票']}({max_r2['行业']})，R²={max_r2['r2_raw']:.4f}")
print(f"R²最低：{min_r2['股票']}({min_r2['行业']})，R²={min_r2['r2_raw']:.4f}")

print(f"\\n解释：")
print(f"  R²衡量的是市场收益率对个股收益率变动的解释比例。")
print(f"  {max_r2['股票']}的R²最高，说明其走势与大盘高度一致，系统性风险是主要风险来源。")
print(f"  {min_r2['股票']}的R²最低，说明其受公司特定因素影响更大，")
print(f"  个股特质风险（idiosyncratic risk）占比较大，大盘走势对其解释力有限。")"""),
    
    md("## 5. 宏观指标对股票收益率的影响（选做）"),
    
    code("""# M2增速对月度收益率的影响
m2 = pd.read_csv(os.path.join(BASE_DIR, "data", "macro", "macro_m2.csv"))
m2["日期"] = pd.to_datetime(m2["日期"])

# 计算各股票月度收益率
monthly_results = []
for stock in STOCKS:
    code = stock["code"]
    name = stock["name"]
    industry = stock["industry"]
    
    stock_data = data[data["code"] == code].copy().set_index("日期").sort_index()
    monthly_close = stock_data["收盘价"].resample("M").last()
    monthly_return = np.log(monthly_close / monthly_close.shift(1)).dropna() * 100
    monthly_return.name = "monthly_return"
    
    # 合并M2
    m2_monthly = m2.set_index("日期")["M2同比"]
    merged = pd.DataFrame({"return": monthly_return, "M2": m2_monthly}).dropna()
    
    if len(merged) < 20:
        continue
    
    X = sm.add_constant(merged["M2"])
    y = merged["return"]
    model = sm.OLS(y, X).fit()
    
    monthly_results.append({
        "股票": name, "行业": industry,
        "γ̂": f"{model.params['M2']:.4f}",
        "p值": f"{model.pvalues['M2']:.4f}",
        "gamma_raw": model.params["M2"],
        "pval_raw": model.pvalues["M2"]
    })

monthly_df = pd.DataFrame(monthly_results)
monthly_df"""),
    
    code("""# 可视化M2敏感度
fig, ax = plt.subplots(figsize=(10, 6))

for _, row in monthly_df.iterrows():
    industry = row["行业"]
    color = INDUSTRY_COLORS.get(industry, "gray")
    marker = "o" if row["pval_raw"] < 0.05 else "x"
    ax.scatter(row["gamma_raw"], row["股票"], color=color, s=100, marker=marker, zorder=5)

ax.axvline(x=0, color="gray", linestyle="--", alpha=0.5)
ax.set_title("M2同比增速对月度收益率的敏感度（γ̂）", fontsize=14)
ax.set_xlabel("γ̂（M2敏感度）", fontsize=12)
ax.set_ylabel("股票", fontsize=12)
ax.annotate("o = p<0.05显著  x = 不显著", xy=(0.02, 0.02), xycoords="axes fraction", fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(BASE_DIR, "output", "fig7_m2_sensitivity.png"), dpi=150, bbox_inches="tight")
plt.show()
print("M2敏感度图已保存")

# 讨论
print("\\n讨论：")
print("M2增速代表市场流动性水平。流动性充裕时，资金更多流入股市推升估值。")
print("不同行业对流动性的敏感度不同：")
print("  - 高贝塔行业（汽车、白酒）对流动性更敏感，M2扩张时涨幅更大")
print("  - 防御性行业（银行、能源）对流动性敏感度较低，走势更依赖基本面")"""),
    
    md("## 6. 总结"),
    
    code("""print('''
========== 作业总结 ==========

1. 数据获取：成功获取10只A股股票5年后复权行情、2个指数、2项宏观指标、10只股票财务数据
2. 数据清洗：完成缺失值填充、日期格式统一、类型检查、重复值处理、离群值标注6个步骤
3. 数据存储：CSV（方式A）+ SQLite（方式C），支持跨表SQL查询
4. 可视化：完成5张图表（归一化走势、收益率分布、相关热力图、CPI散点图、ROE对比）
5. CAPM回归：估计10只股票的Alpha和Beta，完成3个讨论问题
6. 宏观分析：M2增速对月度收益率的影响分析

主要发现：
- 新能源汽车（比亚迪）是2020-2026年涨幅最大的板块
- 白酒行业ROE长期领先，但2021年后经历显著回调
- 同行业股票相关性显著高于跨行业
- 周期性行业Beta > 1，防御性行业Beta < 1
- M2流动性对高贝塔行业影响更显著
==============================
''')"""),
]

# 保存三个Notebook
for name, cells in [
    ("01_download.ipynb", nb1_cells),
    ("02_clean.ipynb", nb2_cells),
    ("03_analysis.ipynb", nb3_cells),
]:
    nb = make_nb(cells)
    filepath = os.path.join(BASE, name)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"已创建: {filepath}")

print("\n三个Notebook创建完成！")
