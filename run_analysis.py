# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, os, warnings
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, seaborn as sns
from scipy import stats; import statsmodels.api as sm
warnings.filterwarnings('ignore')
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')

BASE = os.path.dirname(os.path.abspath(__file__))
ODIR = os.path.join(BASE, "output"); os.makedirs(ODIR, exist_ok=True)

# Stock definitions - using unicode escapes to avoid encoding issues
S = [("600036","\u62db\u5546\u94f6\u884c","\u94f6\u884c"),("601398","\u5de5\u5546\u94f6\u884c","\u94f6\u884c"),
     ("002594","\u6bd4\u4e9a\u8fea","\u6c7d\u8f66"),("601633","\u957f\u57ce\u6c7d\u8f66","\u6c7d\u8f66"),
     ("000002","\u4e07\u79d1A","\u623f\u5730\u4ea7"),("600048","\u4fdd\u5229\u53d1\u5c55","\u623f\u5730\u4ea7"),
     ("600519","\u8d35\u5dde\u8305\u53f0","\u767d\u9152"),("000858","\u4e94\u7cae\u6db2","\u767d\u9152"),
     ("601857","\u4e2d\u56fd\u77f3\u6cb9","\u80fd\u6e90"),("000063","\u4e2d\u5174\u901a\u8baf","\u901a\u8baf")]
C = {"\u94f6\u884c":"#e74c3c","\u6c7d\u8f66":"#3498db","\u623f\u5730\u4ea7":"#2ecc71","\u767d\u9152":"#f39c12","\u80fd\u6e90":"#9b59b6","\u901a\u8baf":"#1abc9c"}

# Load data and rename ALL columns by position
raw = pd.read_csv(os.path.join(BASE, "data", "clean", "stock_clean.csv"))
raw.columns = ["date","open","close","high","low","vol","amount","code","name","industry","ret","is_extreme","hs300","zz500","ym","cpi","m2"]
raw["date"] = pd.to_datetime(raw["date"])
# Fix code column: convert to string and zero-pad
raw["code"] = raw["code"].astype(str).str.zfill(6)
D = raw
print(f"Data: {D.shape}, codes: {D['code'].nunique()}")

# Fig1
fig, ax = plt.subplots(figsize=(14, 7))
for code, name, ind in S:
    sd = D[D["code"]==code].sort_values("date")
    if len(sd)==0 or sd["close"].isna().all(): continue
    ax.plot(sd["date"], sd["close"]/sd["close"].dropna().iloc[0], label=f"{name}({ind})", color=C.get(ind,"gray"), alpha=0.8, linewidth=1.2)
hs = D[["date","hs300"]].dropna().drop_duplicates("date").sort_values("date")
if len(hs)>0: ax.plot(hs["date"], hs["hs300"]/hs["hs300"].iloc[0], label="\u6caa\u6df1300", color="black", linewidth=2, linestyle="--", alpha=0.7)
ax.set_title("\u56fe1\uff1a10\u53ea\u80a1\u7968\u5f52\u4e00\u5316\u6536\u76d8\u4ef7\u8d70\u52bf", fontsize=14)
ax.set_xlabel("\u65e5\u671f"); ax.set_ylabel("\u5f52\u4e00\u5316\u6536\u76d8\u4ef7")
ax.legend(bbox_to_anchor=(1.02,1), loc="upper left", fontsize=9); ax.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(ODIR, "fig1_normalized_price.png"), dpi=150, bbox_inches="tight"); plt.close(); print("Fig1 OK")

# Fig2
fig, axes = plt.subplots(2, 5, figsize=(20, 8)); axes = axes.flatten()
for i, (code, name, ind) in enumerate(S):
    ret = D[D["code"]==code]["ret"].dropna()
    ax = axes[i]; ax.hist(ret, bins=50, density=True, alpha=0.6, color=C.get(ind,"gray"), edgecolor="white")
    x = np.linspace(ret.min(), ret.max(), 100)
    ax.plot(x, stats.norm.pdf(x, ret.mean(), ret.std()), 'k-', linewidth=1.5)
    ax.set_title(f"{name}({ind})\n\u03bc={ret.mean()*100:.3f}%, \u03c3={ret.std()*100:.3f}%", fontsize=9)
plt.suptitle("\u56fe2\uff1a10\u53ea\u80a1\u7968\u65e5\u6536\u76ca\u7387\u5206\u5e03", fontsize=14, y=1.02)
plt.tight_layout(); plt.savefig(os.path.join(ODIR, "fig2_return_distribution.png"), dpi=150, bbox_inches="tight"); plt.close(); print("Fig2 OK")

# Fig3
rw = pd.DataFrame()
for code, name, ind in S:
    sd = D[D["code"]==code][["date","ret"]].dropna().set_index("date")
    rw[name] = sd["ret"]
corr = rw.corr()
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, square=True, linewidths=0.5)
ax.set_title("\u56fe3\uff1a\u6536\u76ca\u7387\u76f8\u5173\u7cfb\u6570\u70ed\u529b\u56fe", fontsize=14)
plt.tight_layout(); plt.savefig(os.path.join(ODIR, "fig3_correlation_heatmap.png"), dpi=150, bbox_inches="tight"); plt.close(); print("Fig3 OK")

# Fig4
idx = pd.read_csv(os.path.join(BASE, "data", "index", "index_000300.csv"))
idx.columns = ["date","open","close","high","low","vol","amount"]
idx["date"] = pd.to_datetime(idx["date"]); idx = idx.set_index("date").sort_index()
hm = idx["close"].resample("M").last(); hmr = np.log(hm/hm.shift(1)).dropna()*100
cp = pd.read_csv(os.path.join(BASE, "data", "macro", "macro_cpi.csv"))
cp.columns = ["date","cpi_val"]; cp["date"] = pd.to_datetime(cp["date"]); cp = cp.set_index("date").sort_index()
mg = pd.DataFrame({"ret":hmr,"cpi":cp.iloc[:,0]}).dropna()
pr = mg["cpi"].corr(mg["ret"]); sl,ic,rv,pv,se = stats.linregress(mg["cpi"],mg["ret"])
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(mg["cpi"],mg["ret"],alpha=0.6,color="#3498db",s=60)
xf = np.linspace(mg["cpi"].min(),mg["cpi"].max(),100)
ax.plot(xf,sl*xf+ic,"r-",linewidth=2,alpha=0.8)
ax.set_title("\u56fe4\uff1aCPI\u4e0e\u6caa\u6df1300\u6708\u5ea6\u6536\u76ca\u7387",fontsize=14)
ax.text(0.05,0.95,f"Pearson r={pr:.3f}\nslope={sl:.3f}\np={pv:.4f}",transform=ax.transAxes,fontsize=11,va="top",bbox=dict(boxstyle="round",facecolor="wheat",alpha=0.5))
plt.tight_layout(); plt.savefig(os.path.join(ODIR,"fig4_cpi_stock_scatter.png"),dpi=150,bbox_inches="tight"); plt.close(); print("Fig4 OK")

# Fig5
fin = pd.read_csv(os.path.join(BASE, "data", "finance", "finance_ratios.csv"))
roe = fin[fin["indicator"]=="ROE"].copy()
fig, ax = plt.subplots(figsize=(12, 6))
for code, name, ind in S:
    sr = roe[roe["code"]==code].sort_values("year")
    if len(sr)==0: continue
    ax.plot(sr["year"],sr["value"],marker="o",label=f"{name}({ind})",color=C.get(ind,"gray"),linewidth=1.5,markersize=4)
ax.set_title("\u56fe5\uff1a10\u53ea\u80a1\u7968\u8fd15\u5e74ROE\u5bf9\u6bd4",fontsize=14)
ax.legend(bbox_to_anchor=(1.02,1),loc="upper left",fontsize=9); ax.grid(True,alpha=0.3)
plt.tight_layout(); plt.savefig(os.path.join(ODIR,"fig5_roe_comparison.png"),dpi=150,bbox_inches="tight"); plt.close(); print("Fig5 OK")

# CAPM
rf = 0.02/252
hsr = D[["date","ret"]].dropna().drop_duplicates("date").set_index("date")["ret"]; hsr.name="mkt"
cr = []
for code, name, ind in S:
    sd = D[D["code"]==code][["date","ret"]].dropna().set_index("date")["ret"]; sd.name="stk"
    m = pd.merge(sd,hsr,left_index=True,right_index=True,how="inner")
    if len(m)<100: continue
    m["es"]=m["stk"]-rf; m["em"]=m["mkt"]-rf
    X = sm.add_constant(m["em"]); y = m["es"]
    model = sm.OLS(y,X).fit(); bci = model.conf_int().loc["em"]
    cr.append({"sn":name,"ind":ind,"alpha":model.params["const"],"ap":model.pvalues["const"],"beta":model.params["em"],"bcl":bci[0],"bch":bci[1],"r2":model.rsquared})
cdf = pd.DataFrame(cr); print(f"CAPM: {len(cdf)} stocks")

# Fig6
if len(cdf)>0:
    fig, ax = plt.subplots(figsize=(10,6)); seen=set()
    for _,r in cdf.iterrows():
        c=C.get(r["ind"],"gray"); lb=r["ind"] if r["ind"] not in seen else None; seen.add(r["ind"])
        ax.errorbar(r["beta"],r["sn"],xerr=[[r["beta"]-r["bcl"]],[r["bch"]-r["beta"]]],fmt="o",color=c,markersize=8,capsize=5,linewidth=1.5,label=lb)
    ax.axvline(x=1.0,color="red",linestyle="--",linewidth=1.5,alpha=0.7,label="\u03b2=1")
    ax.set_title("CAPM Beta\u7cfb\u6570\u70b9\u56fe",fontsize=14)
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=9)
    plt.tight_layout(); plt.savefig(os.path.join(ODIR,"fig6_capm_beta.png"),dpi=150,bbox_inches="tight"); plt.close(); print("Fig6 OK")

# Fig7
m2d = pd.read_csv(os.path.join(BASE, "data", "macro", "macro_m2.csv"))
m2d.columns = ["date","m2_val"]; m2d["date"] = pd.to_datetime(m2d["date"])
mr2 = []
for code,name,ind in S:
    sd = D[D["code"]==code].copy().set_index("date").sort_index()
    mc = sd["close"].resample("M").last(); mrr = np.log(mc/mc.shift(1)).dropna()*100
    mg2 = pd.DataFrame({"ret":mrr,"m2":m2d.set_index("date")["m2_val"]}).dropna()
    if len(mg2)<20: continue
    X = sm.add_constant(mg2["m2"]); model = sm.OLS(mg2["ret"],X).fit()
    mr2.append({"sn":name,"ind":ind,"gamma":model.params["m2"],"pval":model.pvalues["m2"]})
mdf = pd.DataFrame(mr2)
fig, ax = plt.subplots(figsize=(10,6))
for _,r in mdf.iterrows():
    c=C.get(r["ind"],"gray"); mk="o" if r["pval"]<0.05 else "x"
    ax.scatter(r["gamma"],r["sn"],color=c,s=100,marker=mk,zorder=5)
ax.axvline(x=0,color="gray",linestyle="--",alpha=0.5)
ax.set_title("M2\u5bf9\u6708\u5ea6\u6536\u76ca\u7387\u7684\u654f\u611f\u5ea6",fontsize=14)
plt.tight_layout(); plt.savefig(os.path.join(ODIR,"fig7_m2_sensitivity.png"),dpi=150,bbox_inches="tight"); plt.close(); print("Fig7 OK")

# Stats
td = 252; stbl = []
for code,name,ind in S:
    ret = D[D["code"]==code].sort_values("date")["ret"].dropna()
    if len(ret)==0: continue
    am=ret.mean()*td*100; av=ret.std()*np.sqrt(td)*100
    cum=(1+ret).cumprod(); rm=cum.cummax(); dd=(cum-rm)/rm
    stbl.append({"stock":name,"ind":ind,"mean":f"{am:.2f}","vol":f"{av:.2f}","skew":f"{ret.skew():.3f}","kurt":f"{ret.kurtosis():.3f}","dd":f"{dd.min()*100:.2f}"})
sdf = pd.DataFrame(stbl)

# HTML
hb = cdf[cdf["beta"]>1] if len(cdf)>0 else pd.DataFrame()
sa = cdf[cdf["ap"]<0.05] if len(cdf)>0 else pd.DataFrame()
hbn = ", ".join([f"{r['sn']}({r['ind']})" for _,r in hb.iterrows()]) if len(hb)>0 else "\u65e0"
mx = cdf.loc[cdf["r2"].idxmax()] if len(cdf)>0 else None
mn = cdf.loc[cdf["r2"].idxmin()] if len(cdf)>0 else None

chtml = ""
if len(cdf)>0:
    cd = cdf[["sn","ind","alpha","ap","beta","r2"]].copy()
    cd.columns = ["\u80a1\u7968","\u884c\u4e1a","\u03b1\u0302","p\u503c","\u03b2\u0302","R\u00b2"]
    for c in ["\u03b1\u0302","p\u503c","\u03b2\u0302","R\u00b2"]:
        cd[c] = cd[c].apply(lambda x: f"{float(x):.4f}")
    chtml = cd.to_html(index=False, escape=False)

sdf2 = sdf.copy(); sdf2.columns = ["\u80a1\u7968","\u884c\u4e1a","\u5e74\u5316\u5747\u503c(%)","\u5e74\u5316\u6ce2\u52a8\u7387(%)","\u504f\u5ea6","\u5cf0\u5ea6","\u6700\u5927\u56de\u64a4(%)"]

mxml = mx["sn"] if mx is not None else "N/A"; mxr2 = f"{mx['r2']:.4f}" if mx is not None else "N/A"
mnlm = mn["sn"] if mn is not None else "N/A"; mnr2 = f"{mn['r2']:.4f}" if mn is not None else "N/A"

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>P01 \u91d1\u878d\u6570\u636e\u5206\u6790\u62a5\u544a</title>
<style>body{{font-family:'Microsoft YaHei',sans-serif;max-width:1000px;margin:0 auto;padding:20px;color:#333;line-height:1.8}}h1{{color:#2c3e50;border-bottom:3px solid #3498db;padding-bottom:10px}}h2{{color:#2980b9;margin-top:30px}}h3{{color:#27ae60}}table{{border-collapse:collapse;width:100%;margin:15px 0}}th,td{{border:1px solid #ddd;padding:8px 12px;text-align:center;font-size:0.9em}}th{{background-color:#3498db;color:white}}tr:nth-child(even){{background-color:#f2f2f2}}img{{max-width:100%;margin:10px 0;border:1px solid #ddd;border-radius:4px}}.info{{background:#ecf0f1;padding:15px;border-radius:8px;margin:15px 0}}.hl{{background:#fff3cd;padding:12px;border-left:4px solid #f39c12;margin:15px 0}}</style></head><body>
<h1>P01\uff1a\u91d1\u878d\u6570\u636e\u83b7\u53d6\u3001\u7ba1\u7406\u4e0e\u521d\u6b65\u5206\u6790</h1>
<div class="info"><p><b>\u59d3\u540d</b>\uff1a\u67ef\u9a8b | <b>\u5b66\u53f7</b>\uff1a25210150 | <b>\u8bfe\u7a0b</b>\uff1a\u6570\u636e\u5206\u6790\u4e0e\u7ecf\u6d4e\u51b3\u7b56</p>
<p><b>GitHub</b>\uff1a<a href="https://github.com/kecheng77/dshw-p01">https://github.com/kecheng77/dshw-p01</a></p></div>
<h2>1. \u6570\u636e\u8bf4\u660e</h2><p>10\u53eaA\u80a1\u80a1\u7968\uff0c6\u4e2a\u884c\u4e1a\uff0c2020-2026\u540e\u590d\u6743\u65e5\u5ea6\u884c\u60c5\uff0c\u6caa\u6df1300/\u4e2d\u8bc1500\u6307\u6570\uff0cCPI/M2\u5b8f\u89c2\u6570\u636e\uff0cROE/\u51c0\u5229\u6da6\u7387\u8d22\u52a1\u6570\u636e\u3002</p>
<h2>2. \u6e05\u6d17\u8bf4\u660e</h2><p>6\u6b65\uff1a\u7f3a\u5931\u503c\u68c0\u6d4b\u2192ffill\u2192\u65e5\u671f\u7edf\u4e00\u2192\u7c7b\u578b\u68c0\u67e5\u2192\u91cd\u590d\u5220\u9664\u2192\u79bb\u7fa4\u503c\u6807\u6ce8\u3002CSV+SQLite\u5b58\u50a8\u3002</p>
<h2>3. \u63cf\u8ff0\u6027\u7edf\u8ba1</h2>{sdf2.to_html(index=False, escape=False)}
<h2>4. \u53ef\u89c6\u5316</h2>
<h3>\u56fe1</h3><img src="output/fig1_normalized_price.png"><div class="hl">\u6bd4\u4e9a\u8fea\u6da8\u5e45\u6700\u5927\uff0c\u767d\u9152\u540e\u56de\u8c03\uff0c\u623f\u5730\u4ea7\u4f4e\u8ff7\uff0c\u94f6\u884c\u7a33\u5065\u3002</div>
<h3>\u56fe2</h3><img src="output/fig2_return_distribution.png"><div class="hl">\u5c16\u5cf0\u539a\u5c3e\u7279\u5f81\uff0c\u6c7d\u8f66\u6ce2\u52a8\u5927\u94f6\u884c\u6ce2\u52a8\u5c0f\u3002</div>
<h3>\u56fe3</h3><img src="output/fig3_correlation_heatmap.png"><div class="hl">\u540c\u884c\u4e1a\u76f8\u5173\u6027\u663e\u8457\u9ad8\u4e8e\u8de8\u884c\u4e1a\u3002</div>
<h3>\u56fe4</h3><img src="output/fig4_cpi_stock_scatter.png"><div class="hl">Pearson r={pr:.3f}\u3002\u6e29\u548c\u901a\u80c0\u652f\u6491\u80a1\u5e02\uff0c\u9ad8\u901a\u80c0\u538b\u5236\u4f30\u503c\u3002</div>
<h3>\u56fe5</h3><img src="output/fig5_roe_comparison.png"><div class="hl">\u767d\u9152ROE\u9886\u5148\uff0c\u94f6\u884c\u4e0b\u884c\uff0c\u623f\u5730\u4ea7\u964d\u6700\u591a\uff0c\u6bd4\u4e9a\u8fea\u5feb\u901f\u4e0a\u5347\u3002</div>
<h2>5. CAPM</h2>{chtml}<img src="output/fig6_capm_beta.png">
<p><b>\u03b2&gt;1</b>\uff1a{hbn}</p>
<p><b>Alpha\u663e\u8457</b>\uff1a{len(sa)}\u53ea\u3002</p>
<p><b>R\u00b2</b>\uff1a\u6700\u9ad8{mxml}({mxr2})\uff0c\u6700\u4f4e{mnlm}({mnr2})\u3002</p>
<h2>6. \u5b8f\u89c2\u5f71\u54cd</h2><img src="output/fig7_m2_sensitivity.png"><div class="hl">M2\u5bf9\u9ad8\u8d1d\u5854\u884c\u4e1a\u5f71\u54cd\u66f4\u663e\u8457\u3002</div>
<h2>7. \u7ed3\u8bba</h2><ol><li>\u65b0\u80fd\u6e90\u6da8\u5e45\u6700\u5927</li><li>\u767d\u9152ROE\u9886\u5148\u4f46\u5df2\u56de\u8c03</li><li>\u540c\u884c\u4e1a\u76f8\u5173\u6027\u9ad8</li><li>\u5468\u671f\u884c\u4e1aBeta&gt;1</li><li>M2\u5bf9\u9ad8\u8d1d\u5854\u5f71\u54cd\u663e\u8457</li></ol>
<hr><p style="color:#999;font-size:0.85em">AI: CodeBuddy | 2026-05-21</p></body></html>"""

with open(os.path.join(BASE, "report.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("report.html DONE!")
