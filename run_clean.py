# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))

STOCKS = [
    {"code": "600036", "name": "招商银行", "industry": "银行"},
    {"code": "601398", "name": "工商银行", "industry": "银行"},
    {"code": "002594", "name": "比亚迪", "industry": "汽车"},
    {"code": "601633", "name": "长城汽车", "industry": "汽车"},
    {"code": "000002", "name": "万科A", "industry": "房地产"},
    {"code": "600048", "name": "保利发展", "industry": "房地产"},
    {"code": "600519", "name": "贵州茅台", "industry": "白酒"},
    {"code": "000858", "name": "五粮液", "industry": "白酒"},
    {"code": "601857", "name": "中国石油", "industry": "能源"},
    {"code": "000063", "name": "中兴通讯", "industry": "通讯"},
]

all_data = []
for stock in STOCKS:
    filepath = os.path.join(BASE, "data", "stock", f"stock_{stock['code']}.csv")
    df = pd.read_csv(filepath)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期")
    df["code"] = stock["code"]
    df["name"] = stock["name"]
    df["industry"] = stock["industry"]
    df["日收益率"] = np.log(df["收盘价"] / df["收盘价"].shift(1))
    df["is_extreme"] = df["日收益率"].abs() > 0.20
    df = df.fillna(method="ffill").fillna(method="bfill")
    all_data.append(df)

stock_merged = pd.concat(all_data, ignore_index=True)

hs300 = pd.read_csv(os.path.join(BASE, "data", "index", "index_000300.csv"))
hs300["日期"] = pd.to_datetime(hs300["日期"])
hs300 = hs300.set_index("日期").sort_index()[["收盘价"]].rename(columns={"收盘价": "hs300_close"})

zz500 = pd.read_csv(os.path.join(BASE, "data", "index", "index_000905.csv"))
zz500["日期"] = pd.to_datetime(zz500["日期"])
zz500 = zz500.set_index("日期").sort_index()[["收盘价"]].rename(columns={"收盘价": "zz500_close"})

stock_merged = stock_merged.merge(hs300, left_on="日期", right_index=True, how="left")
stock_merged = stock_merged.merge(zz500, left_on="日期", right_index=True, how="left")

cpi = pd.read_csv(os.path.join(BASE, "data", "macro", "macro_cpi.csv"))
cpi["日期"] = pd.to_datetime(cpi["日期"])
cpi["year_month"] = cpi["日期"].dt.to_period("M")

m2 = pd.read_csv(os.path.join(BASE, "data", "macro", "macro_m2.csv"))
m2["日期"] = pd.to_datetime(m2["日期"])
m2["year_month"] = m2["日期"].dt.to_period("M")

stock_merged["year_month"] = stock_merged["日期"].dt.to_period("M")

cpi_map = cpi[["year_month", "CPI同比"]].drop_duplicates(subset=["year_month"])
stock_merged = stock_merged.merge(cpi_map, on="year_month", how="left")

m2_map = m2[["year_month", "M2同比"]].drop_duplicates(subset=["year_month"])
stock_merged = stock_merged.merge(m2_map, on="year_month", how="left")

os.makedirs(os.path.join(BASE, "data", "clean"), exist_ok=True)
os.makedirs(os.path.join(BASE, "data", "combined"), exist_ok=True)

stock_merged.to_csv(os.path.join(BASE, "data", "clean", "stock_clean.csv"), index=False, encoding="utf-8-sig")
stock_merged.to_csv(os.path.join(BASE, "data", "combined", "combined_data.csv"), index=False, encoding="utf-8-sig")

db_path = os.path.join(BASE, "data", "combined", "fin_data.db")
if os.path.exists(db_path):
    os.remove(db_path)
conn = sqlite3.connect(db_path)

sp = stock_merged[["日期", "code", "name", "industry", "开盘价", "收盘价", "最高价", "最低价", "成交量", "成交额", "日收益率", "is_extreme"]].copy()
sp.columns = ["date", "code", "name", "industry", "open", "close", "high", "low", "volume", "amount", "return", "is_extreme"]
sp.to_sql("stock_price", conn, if_exists="replace", index=False)

macro_long = pd.concat([
    cpi[["日期", "CPI同比"]].rename(columns={"日期": "date", "CPI同比": "value"}).assign(indicator="cpi"),
    m2[["日期", "M2同比"]].rename(columns={"日期": "date", "M2同比": "value"}).assign(indicator="m2")
], ignore_index=True)
macro_long["date"] = pd.to_datetime(macro_long["date"])
macro_long.to_sql("macro_data", conn, if_exists="replace", index=False)

pd.DataFrame(STOCKS).to_sql("stock_info", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print(f"清洗后数据: {stock_merged.shape}")
print(f"SQLite数据库: {db_path}")
print("数据清洗和存储完成！")
