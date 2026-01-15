"""
宝贝视力成长跟踪系统（单文件魔法启动版 - 最终合并版）
包含：
- 魔法启动：双击 python 运行 -> subprocess 启动 streamlit run（避免 Runtime already exists）
- 阶段管理（stages.csv）：新建/启用/停用；记录自动按日期匹配阶段
- 完整检查录入：视力、远视储备、眼轴、屈光S/C/A/SE、PD、角膜曲率K1/K2、角膜散光、
  WTW、角膜厚度、瞳孔直径、眼压、双眼视觉/集合/AC/A、调节幅度、翻转拍(cpm)等
- 干预/治疗记录：阿托品/防控眼镜/捕光仪/七叶洋地参/翻转拍/其它；含频次与依从性
- 趋势图：视力（左/右/均值）+ SE（左右/均值）+ 远视储备 + 眼轴
- 汇总：阶段×干预（次数、频次均值、依从性均值、使用时平均视力/SE）
- 最近一次 A4 打印报告（建议浏览器打印：Ctrl+P，选择A4纵向）

数据文件：
- vision_data.csv：检查+干预+关键数据
- stages.csv：阶段表
"""

import os
import sys
import subprocess
from datetime import datetime

# ================== 🪄 魔法启动（subprocess 启动 streamlit） ==================
def ensure_deps():
    try:
        import streamlit  # noqa
        import pandas  # noqa
        import plotly  # noqa
        return
    except Exception:
        print("首次运行，正在安装依赖 (streamlit, pandas, plotly)...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "pandas", "plotly"])


def running_in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


def magic_launch():
    ensure_deps()
    if os.environ.get("MAGIC_LAUNCHED") == "1":
        return
    os.environ["MAGIC_LAUNCHED"] = "1"

    script_path = os.path.abspath(__file__)
    cmd = [sys.executable, "-m", "streamlit", "run", script_path]
    subprocess.Popen(cmd, close_fds=True)
    sys.exit(0)


if __name__ == "__main__":
    if not running_in_streamlit():
        magic_launch()

# ================== Streamlit APP ==================
import streamlit as st
import pandas as pd
import plotly.express as px

CSV_FILE = "vision_data.csv"
STAGE_FILE = "stages.csv"

st.set_page_config(page_title="宝贝视力成长档案", page_icon="🧸", layout="wide")

# ================== UI 美化 ==================
st.markdown(
    """
<style>
.block-container { padding-top: 1.0rem; padding-bottom: 2rem; max-width: 1250px; }
.small-hint { font-size: 12px; color: #6c757d; margin-top: -6px; }
.hero{
  padding: 14px 16px;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 14px;
  background: linear-gradient(90deg, rgba(46,134,193,.16), rgba(46,134,193,.02));
}
.hero-title{ font-size: 18px; font-weight: 900; margin: 0; }
.hero-sub{ font-size: 12px; color: #555; margin-top: 4px; }
.card{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 14px;
  padding: 12px 12px;
  background: #fff;
}
.card-title{ font-size: 13px; font-weight: 900; margin: 0 0 6px 0; }
.badge{
  display:inline-block; padding:2px 8px; border-radius:999px;
  border:1px solid rgba(0,0,0,.12); font-size:11px; color:#333;
  background: rgba(0,0,0,.02);
  margin-left: 6px;
}
[data-testid="stMetric"]{
  background: #fafbfc;
  border: 1px solid rgba(0,0,0,.08);
  padding: 10px 12px;
  border-radius: 14px;
}
.stTabs [data-baseweb="tab-list"]{ gap: 6px; }
.stTabs [data-baseweb="tab"]{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 999px;
  padding: 8px 12px;
}
.stTabs [aria-selected="true"]{
  background: rgba(46,134,193,.14);
  border-color: rgba(46,134,193,.35);
}
section[data-testid="stSidebar"] .block-container{ padding-top: .8rem; padding-bottom: .8rem; }
hr { margin: .6rem 0; }
@media print {
  header, footer, [data-testid="stSidebar"], [data-testid="stToolbar"], [data-testid="stStatusWidget"] { display:none !important; }
  .block-container { max-width: 100% !important; }
  .print-only { display:block !important; }
  .no-print { display:none !important; }
}
.print-only { display:none; }
</style>
""",
    unsafe_allow_html=True,
)

# ================== 列定义 ==================
BASE_COLUMNS = [
    "日期",
    "阶段ID",
    "阶段名称",
    "阶段主方案",
    "左眼视力",
    "右眼视力",
    "左眼远视储备",
    "右眼远视储备",
    "眼轴长度(L)",
    "眼轴长度(R)",
    "备注",
]

TREAT_COLUMNS = [
    "阿托品_是否使用", "阿托品_浓度或规格", "阿托品_频次文本", "阿托品_每周次数",
    "阿托品_开始日期", "阿托品_结束日期", "阿托品_依从性(%)", "阿托品_副作用或不适",

    "防控眼镜_是否使用", "防控眼镜_类型", "防控眼镜_每天佩戴时长(h)", "防控眼镜_每周天数",
    "防控眼镜_开始日期", "防控眼镜_结束日期", "防控眼镜_依从性(%)", "防控眼镜_不适",

    "捕光仪_是否使用", "捕光仪_方案", "捕光仪_每天时长(min)", "捕光仪_每周天数",
    "捕光仪_开始日期", "捕光仪_结束日期", "捕光仪_依从性(%)", "捕光仪_不适",

    "七叶洋地参_是否使用", "七叶洋地参_规格", "七叶洋地参_频次文本", "七叶洋地参_每日次数",
    "七叶洋地参_开始日期", "七叶洋地参_结束日期", "七叶洋地参_依从性(%)", "七叶洋地参_不适",

    "翻转拍_是否训练", "翻转拍_方案", "翻转拍_每周次数", "翻转拍_每次分钟",
    "翻转拍_开始日期", "翻转拍_结束日期", "翻转拍_依从性(%)", "翻转拍_不适或反馈",

    "其它干预_是否有", "其它干预_内容", "其它干预_频次文本", "其它干预_每周次数", "其它干预_每次分钟",
    "其它干预_开始日期", "其它干预_结束日期", "其它干预_依从性(%)", "其它干预_反馈",
]

EXAM_EXTRA_COLUMNS = [
    "右眼_S", "右眼_C", "右眼_A", "右眼_SE",
    "左眼_S", "左眼_C", "左眼_A", "左眼_SE",
    "PD(mm)",

    "右眼_K1(mm)", "右眼_K1(D)", "右眼_K1轴位",
    "右眼_K2(mm)", "右眼_K2(D)", "右眼_K2轴位",
    "右眼角膜CYL(D)", "右眼角膜CYL轴位",

    "左眼_K1(mm)", "左眼_K1(D)", "左眼_K1轴位",
    "左眼_K2(mm)", "左眼_K2(D)", "左眼_K2轴位",
    "左眼角膜CYL(D)", "左眼角膜CYL轴位",

    "右眼_WTW(mm)", "左眼_WTW(mm)",
    "右眼_角膜中央厚度(um)", "左眼_角膜中央厚度(um)",
    "右眼_最薄角膜厚度(um)", "左眼_最薄角膜厚度(um)",
    "右眼_最薄点位置(mm)", "左眼_最薄点位置(mm)",
    "右眼_瞳孔直径(mm)", "左眼_瞳孔直径(mm)",

    "右眼眼压(mmHg)", "左眼眼压(mmHg)",

    "立体视_Titmus(秒)", "融合范围(°)", "他觉斜视角(°)",
    "33cm_SC(°)", "6m_SC(°)",
    "33cm_CC(°)", "6m_CC(°)",
    "AC/A",
    "Amp_OD(D)", "Amp_OS(D)", "Amp_OU(D)",
    "Flipper_OD(cpm)", "Flipper_OS(cpm)", "Flipper_OU(cpm)",
    "Flipper_备注",
]

ALL_COLUMNS = BASE_COLUMNS + TREAT_COLUMNS + EXAM_EXTRA_COLUMNS

# ================== 阶段表 ==================
STAGE_COLUMNS = [
    "阶段ID", "阶段名称", "开始日期", "结束日期",
    "主方案", "阶段目标", "医生建议", "备注", "是否启用"
]

# ================== 工具函数 ==================
def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for c in ALL_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[ALL_COLUMNS]


def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=ALL_COLUMNS)
    df = pd.read_csv(CSV_FILE)

    date_cols = ["日期",
        "阿托品_开始日期", "阿托品_结束日期",
        "防控眼镜_开始日期", "防控眼镜_结束日期",
        "捕光仪_开始日期", "捕光仪_结束日期",
        "七叶洋地参_开始日期", "七叶洋地参_结束日期",
        "翻转拍_开始日期", "翻转拍_结束日期",
        "其它干预_开始日期", "其它干预_结束日期",
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return ensure_columns(df)


def save_data(df: pd.DataFrame) -> None:
    df.to_csv(CSV_FILE, index=False)


def load_stages() -> pd.DataFrame:
    if not os.path.exists(STAGE_FILE):
        return pd.DataFrame(columns=STAGE_COLUMNS)
    s = pd.read_csv(STAGE_FILE)
    s["开始日期"] = pd.to_datetime(s.get("开始日期"), errors="coerce")
    s["结束日期"] = pd.to_datetime(s.get("结束日期"), errors="coerce")
    if "是否启用" in s.columns:
        s["是否启用"] = s["是否启用"].astype(str).str.lower().isin(["1", "true", "yes", "是"])
    else:
        s["是否启用"] = True
    for c in STAGE_COLUMNS:
        if c not in s.columns:
            s[c] = None
    return s[STAGE_COLUMNS]


def save_stages(s: pd.DataFrame) -> None:
    s.to_csv(STAGE_FILE, index=False)


def is_yes(v) -> bool:
    return str(v).lower() in ["1", "true", "yes", "是"]


def to_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def parse_axis(s: str):
    s = (s or "").strip()
    if s == "":
        return None, None
    try:
        v = float(s)
    except ValueError:
        return None, "请输入数字"
    if not (15.0 <= v <= 30.0):
        return None, "范围应为 15.00~30.00"
    return round(v, 2), None


def parse_optional_float(s: str, min_v=None, max_v=None):
    s = (s or "").strip()
    if s == "":
        return None, None
    try:
        v = float(s)
    except ValueError:
        return None, "请输入数字"
    if min_v is not None and v < min_v:
        return None, f"不能小于 {min_v}"
    if max_v is not None and v > max_v:
        return None, f"不能大于 {max_v}"
    return v, None


def parse_optional_int(s: str, min_v=None, max_v=None):
    s = (s or "").strip()
    if s == "":
        return None, None
    try:
        v = int(float(s))
    except ValueError:
        return None, "请输入整数"
    if min_v is not None and v < min_v:
        return None, f"不能小于 {min_v}"
    if max_v is not None and v > max_v:
        return None, f"不能大于 {max_v}"
    return v, None


def match_stage_for_date(stages_df: pd.DataFrame, d: pd.Timestamp):
    if stages_df is None or stages_df.empty or pd.isna(d):
        return (None, None, None)
    s = stages_df[stages_df["是否启用"] == True].copy()
    s = s.dropna(subset=["开始日期"])
    if s.empty:
        return (None, None, None)
    end = s["结束日期"].fillna(pd.Timestamp.max)
    hit = s[(s["开始日期"] <= d) & (d <= end)]
    if hit.empty:
        return (None, None, None)
    hit = hit.sort_values("开始日期", ascending=False).iloc[0]
    return (hit.get("阶段ID"), hit.get("阶段名称"), hit.get("主方案"))


def short_tag(row: pd.Series) -> str:
    tags = []
    if is_yes(row.get("阿托品_是否使用")): tags.append("阿托品")
    if is_yes(row.get("防控眼镜_是否使用")): tags.append("防控眼镜")
    if is_yes(row.get("捕光仪_是否使用")): tags.append("捕光仪")
    if is_yes(row.get("七叶洋地参_是否使用")): tags.append("七叶洋地参")
    if is_yes(row.get("翻转拍_是否训练")): tags.append("翻转拍")
    if is_yes(row.get("其它干预_是否有")): tags.append("其它")
    return "、".join(tags) if tags else "无"


INTERVENTIONS = [
    ("阿托品", "阿托品_是否使用", ["阿托品_每周次数"], ["阿托品_依从性(%)"]),
    ("防控眼镜", "防控眼镜_是否使用", ["防控眼镜_每天佩戴时长(h)", "防控眼镜_每周天数"], ["防控眼镜_依从性(%)"]),
    ("捕光仪", "捕光仪_是否使用", ["捕光仪_每天时长(min)", "捕光仪_每周天数"], ["捕光仪_依从性(%)"]),
    ("七叶洋地参", "七叶洋地参_是否使用", ["七叶洋地参_每日次数"], ["七叶洋地参_依从性(%)"]),
    ("翻转拍", "翻转拍_是否训练", ["翻转拍_每周次数", "翻转拍_每次分钟"], ["翻转拍_依从性(%)"]),
    ("其它", "其它干预_是否有", ["其它干预_每周次数", "其它干预_每次分钟"], ["其它干预_依从性(%)"]),
]


def build_stage_intervention_summary(df_show: pd.DataFrame) -> pd.DataFrame:
    if df_show.empty:
        return pd.DataFrame()
    rows = []
    stages = sorted([x for x in df_show["阶段名称"].dropna().unique().tolist()]) or ["未匹配阶段"]
    for stage in stages:
        d0 = df_show[df_show["阶段名称"].fillna("未匹配阶段") == stage]
        for name, flag, freq_cols, adh_cols in INTERVENTIONS:
            used = d0[d0[flag].apply(is_yes)]
            if used.empty:
                continue

            v_avg = (to_numeric(used["左眼视力"]) + to_numeric(used["右眼视力"])) / 2
            se_avg = (to_numeric(used["左眼_SE"]) + to_numeric(used["右眼_SE"])) / 2

            adh = None
            for c in adh_cols:
                if c in used.columns:
                    adh = to_numeric(used[c]).mean()
                    break

            f1 = to_numeric(used[freq_cols[0]]).mean() if len(freq_cols) >= 1 and freq_cols[0] in used.columns else None
            f2 = to_numeric(used[freq_cols[1]]).mean() if len(freq_cols) >= 2 and freq_cols[1] in used.columns else None

            rows.append({
                "阶段": stage,
                "干预": name,
                "记录次数": int(len(used)),
                "平均依从性(%)": None if adh is None or pd.isna(adh) else round(float(adh), 1),
                "频次/时长均值1": None if f1 is None or pd.isna(f1) else round(float(f1), 2),
                "频次/时长均值2": None if f2 is None or pd.isna(f2) else round(float(f2), 2),
                "使用时平均视力(左右均值)": None if v_avg.dropna().empty else round(float(v_avg.mean()), 2),
                "使用时平均SE(左右均值)": None if se_avg.dropna().empty else round(float(se_avg.mean()), 2),
            })
    return pd.DataFrame(rows)


def safe_last_n_selector(label: str, df_in: pd.DataFrame, default_n: int = 10, min_n: int = 3, max_cap: int = 60):
    total = len(df_in)
    if total == 0:
        return df_in, 0, False
    nmax = min(max_cap, total)
    if total < min_n:
        st.info(f"当前记录数仅 {total} 条，已展示全部（不足 {min_n} 条时不显示滑块）。")
        return df_in, total, False
    if nmax == min_n:
        st.caption(f"当前记录数为 {min_n} 条，固定展示最近 {min_n} 条（不显示滑块）。")
        return df_in.tail(min_n), min_n, False
    n_default = min(default_n, nmax)
    n = st.slider(label, min_value=min_n, max_value=nmax, value=n_default)
    return df_in.tail(n), n, True


def fmt(v, suffix=""):
    if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and v.strip() == ""):
        return "-"
    return f"{v}{suffix}"


def a4_report_html(latest: pd.Series) -> str:
    # 关键字段抓取（你后续想再加项，直接在这里追加）
    def g(k):
        return latest.get(k, None)

    dt = g("日期")
    dt_str = dt.strftime("%Y-%m-%d") if pd.notnull(dt) else "未知"

    stage = g("阶段名称") or "未匹配阶段"
    plan = g("阶段主方案") or "-"

    tag = short_tag(latest)

    # 组装表格：尽量一页A4
    rows = []

    # 视功能
    rows += [
        ("左眼视力", fmt(g("左眼视力")) , "右眼视力", fmt(g("右眼视力"))),
        ("左眼远视储备(D)", fmt(g("左眼远视储备")), "右眼远视储备(D)", fmt(g("右眼远视储备"))),
        ("左眼眼轴(mm)", fmt(g("眼轴长度(L)")), "右眼眼轴(mm)", fmt(g("眼轴长度(R)"))),
    ]

    # 屈光
    rows += [
        ("OD S/C/A/SE", f"{fmt(g('右眼_S'))}/{fmt(g('右眼_C'))}/{fmt(g('右眼_A'))}/{fmt(g('右眼_SE'))}",
         "OS S/C/A/SE", f"{fmt(g('左眼_S'))}/{fmt(g('左眼_C'))}/{fmt(g('左眼_A'))}/{fmt(g('左眼_SE'))}"),
        ("PD(mm)", fmt(g("PD(mm)")), "IOP OD/OS(mmHg)", f"{fmt(g('右眼眼压(mmHg)'))}/{fmt(g('左眼眼压(mmHg)'))}"),
    ]

    # 角膜曲率
    rows += [
        ("OD K1(mm/D/轴)", f"{fmt(g('右眼_K1(mm)'))}/{fmt(g('右眼_K1(D)'))}/{fmt(g('右眼_K1轴位'))}",
         "OD K2(mm/D/轴)", f"{fmt(g('右眼_K2(mm)'))}/{fmt(g('右眼_K2(D)'))}/{fmt(g('右眼_K2轴位'))}"),
        ("OS K1(mm/D/轴)", f"{fmt(g('左眼_K1(mm)'))}/{fmt(g('左眼_K1(D)'))}/{fmt(g('左眼_K1轴位'))}",
         "OS K2(mm/D/轴)", f"{fmt(g('左眼_K2(mm)'))}/{fmt(g('左眼_K2(D)'))}/{fmt(g('左眼_K2轴位'))}"),
        ("角膜CYL OD(D/轴)", f"{fmt(g('右眼角膜CYL(D)'))}/{fmt(g('右眼角膜CYL轴位'))}",
         "角膜CYL OS(D/轴)", f"{fmt(g('左眼角膜CYL(D)'))}/{fmt(g('左眼角膜CYL轴位'))}"),
    ]

    # WTW/厚度/瞳孔
    rows += [
        ("WTW OD/OS(mm)", f"{fmt(g('右眼_WTW(mm)'))}/{fmt(g('左眼_WTW(mm)'))}",
         "瞳孔 OD/OS(mm)", f"{fmt(g('右眼_瞳孔直径(mm)'))}/{fmt(g('左眼_瞳孔直径(mm)'))}"),
        ("CCT OD/OS(um)", f"{fmt(g('右眼_角膜中央厚度(um)'))}/{fmt(g('左眼_角膜中央厚度(um)'))}",
         "最薄 OD/OS(um)", f"{fmt(g('右眼_最薄角膜厚度(um)'))}/{fmt(g('左眼_最薄角膜厚度(um)'))}"),
        ("最薄点 OD/OS(mm)", f"{fmt(g('右眼_最薄点位置(mm)'))}/{fmt(g('左眼_最薄点位置(mm)'))}",
         "融合范围(°)", fmt(g("融合范围(°)"))),
    ]

    # 双眼视觉/集合/调节/翻转拍
    rows += [
        ("立体视 Titmus(秒)", fmt(g("立体视_Titmus(秒)")), "他觉斜视角(°)", fmt(g("他觉斜视角(°)"))),
        ("SC 33cm/6m(°)", f"{fmt(g('33cm_SC(°)'))}/{fmt(g('6m_SC(°)'))}",
         "CC 33cm/6m(°)", f"{fmt(g('33cm_CC(°)'))}/{fmt(g('6m_CC(°)'))}"),
        ("AC/A", fmt(g("AC/A")),
         "Amp OD/OS/OU(D)", f"{fmt(g('Amp_OD(D)'))}/{fmt(g('Amp_OS(D)'))}/{fmt(g('Amp_OU(D)'))}"),
        ("Flipper OD/OS/OU(cpm)", f"{fmt(g('Flipper_OD(cpm)'))}/{fmt(g('Flipper_OS(cpm)'))}/{fmt(g('Flipper_OU(cpm)'))}",
         "Flipper备注", fmt(g("Flipper_备注"))),
    ]

    # 干预频次摘要（尽量简短）
    def yesno(k): return "是" if is_yes(g(k)) else "否"
    lines = []
    if is_yes(g("阿托品_是否使用")):
        lines.append(f"阿托品：{fmt(g('阿托品_浓度或规格'))}；频次：{fmt(g('阿托品_频次文本'))}；每周{fmt(g('阿托品_每周次数'))}次；依从性{fmt(g('阿托品_依从性(%)'))}%")
    if is_yes(g("防控眼镜_是否使用")):
        lines.append(f"眼镜：{fmt(g('防控眼镜_类型'))}；每天{fmt(g('防控眼镜_每天佩戴时长(h)'))}h；每周{fmt(g('防控眼镜_每周天数'))}天；依从性{fmt(g('防控眼镜_依从性(%)'))}%")
    if is_yes(g("捕光仪_是否使用")):
        lines.append(f"捕光仪：{fmt(g('捕光仪_方案'))}；每天{fmt(g('捕光仪_每天时长(min)'))}min；每周{fmt(g('捕光仪_每周天数'))}天；依从性{fmt(g('捕光仪_依从性(%)'))}%")
    if is_yes(g("七叶洋地参_是否使用")):
        lines.append(f"七叶洋地参：{fmt(g('七叶洋地参_规格'))}；频次：{fmt(g('七叶洋地参_频次文本'))}；每日{fmt(g('七叶洋地参_每日次数'))}次；依从性{fmt(g('七叶洋地参_依从性(%)'))}%")
    if is_yes(g("翻转拍_是否训练")):
        lines.append(f"翻转拍：{fmt(g('翻转拍_方案'))}；每周{fmt(g('翻转拍_每周次数'))}次；每次{fmt(g('翻转拍_每次分钟'))}min；依从性{fmt(g('翻转拍_依从性(%)'))}%")
    if is_yes(g("其它干预_是否有")):
        lines.append(f"其它：{fmt(g('其它干预_频次文本'))}；每周{fmt(g('其它干预_每周次数'))}次；每次{fmt(g('其它干预_每次分钟'))}min")

    treat_block = "<br/>".join(lines) if lines else "无"

    # HTML
    html = f"""
<div class="print-only" style="font-family:Arial, 'Microsoft YaHei';">
  <h2 style="margin:0 0 6px 0;">宝贝视力检查报告（最近一次）</h2>
  <div style="font-size:12px;color:#333;margin-bottom:10px;">
    日期：<b>{dt_str}</b> ｜ 阶段：<b>{stage}</b> ｜ 主方案：<b>{plan}</b> ｜ 当前干预：<b>{tag}</b>
  </div>

  <table style="width:100%; border-collapse:collapse; font-size:12px;">
    <tbody>
      {''.join([f"<tr>"
               f"<td style='border:1px solid #999;padding:6px;width:18%;background:#f5f7fb;'><b>{a}</b></td>"
               f"<td style='border:1px solid #999;padding:6px;width:32%;'>{b}</td>"
               f"<td style='border:1px solid #999;padding:6px;width:18%;background:#f5f7fb;'><b>{c}</b></td>"
               f"<td style='border:1px solid #999;padding:6px;width:32%;'>{d}</td>"
               f"</tr>" for a,b,c,d in rows])}
    </tbody>
  </table>

  <div style="margin-top:10px; font-size:12px;">
    <b>干预/治疗频次摘要：</b><br/>{treat_block}
  </div>

  <div style="margin-top:10px; font-size:12px;">
    <b>备注：</b><br/>{fmt(g("备注"))}
  </div>

  <div style="margin-top:10px; font-size:11px; color:#666;">
    提示：本页为打印版，浏览器 Ctrl+P 选择 A4 纵向即可。
  </div>
</div>
"""
    return html


# ================== 主程序 ==================
def app_main():
    st.markdown(
        """
<div class="hero">
  <div class="hero-title">🧸 宝贝视力成长跟踪系统（阶段管理 + 完整录入）</div>
  <div class="hero-sub">记录：检查结果 + 干预方案（含频次/依从性）+ 医生关心参数，并按阶段对比效果。</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.write("")

    stages = load_stages()
    df = load_data()
    if not df.empty:
        df = df.sort_values("日期")

    # 每次运行：把阶段匹配写回历史数据（阶段调整后会自动刷新归属）
    if not df.empty:
        sid_list, sname_list, splan_list = [], [], []
        for _, row in df.iterrows():
            sid, sn, sp = match_stage_for_date(stages, row["日期"])
            sid_list.append(sid)
            sname_list.append(sn if sn else "未匹配阶段")
            splan_list.append(sp)
        df["阶段ID"] = sid_list
        df["阶段名称"] = sname_list
        df["阶段主方案"] = splan_list
        df = ensure_columns(df)
        save_data(df)

    df_show = df.copy()
    if not df_show.empty:
        df_show = df_show.sort_values("日期")
        df_show["干预标签"] = df_show.apply(short_tag, axis=1)
        df_show["阶段名称"] = df_show["阶段名称"].fillna("未匹配阶段")

    # ================== Sidebar：阶段管理 + 完整录入 ==================
    with st.sidebar:
        st.header("🧩 阶段管理")

        with st.expander("新建阶段", expanded=False):
            with st.form("stage_form", clear_on_submit=True):
                stage_name = st.text_input("阶段名称（如：阿托品+眼镜阶段）", value="")
                start_d = st.date_input("开始日期", value=datetime.now().date())
                end_d = st.date_input("结束日期（可选，留空=至今）", value=None)
                main_plan = st.text_input("主方案（如：0.01%阿托品+防控眼镜）", value="")
                goal = st.text_area("阶段目标（可选）", value="", height=70)
                advice = st.text_area("医生建议（可选）", value="", height=70)
                memo = st.text_area("备注（可选）", value="", height=60)
                enable = st.checkbox("启用", value=True)
                stage_submit = st.form_submit_button("➕ 保存阶段")

                if stage_submit:
                    if not stage_name.strip():
                        st.error("阶段名称不能为空")
                        st.stop()
                    ymd = pd.to_datetime(start_d).strftime("%Y%m%d")
                    existing = stages[stages["阶段ID"].astype(str).str.startswith(ymd)]
                    idx = len(existing) + 1
                    stage_id = f"{ymd}-{idx:02d}"

                    new_row = pd.DataFrame([{
                        "阶段ID": stage_id,
                        "阶段名称": stage_name.strip(),
                        "开始日期": pd.to_datetime(start_d),
                        "结束日期": pd.to_datetime(end_d) if end_d else pd.NaT,
                        "主方案": main_plan.strip() or None,
                        "阶段目标": goal.strip() or None,
                        "医生建议": advice.strip() or None,
                        "备注": memo.strip() or None,
                        "是否启用": bool(enable),
                    }])
                    stages2 = pd.concat([stages, new_row], ignore_index=True) if not stages.empty else new_row
                    save_stages(stages2)
                    st.success(f"✅ 已新增阶段：{stage_id}")
                    st.rerun()

        with st.expander("查看/管理阶段（启用/停用）", expanded=False):
            if stages.empty:
                st.info("暂无阶段。")
            else:
                show_cols = ["阶段ID", "阶段名称", "开始日期", "结束日期", "主方案", "是否启用"]
                st.dataframe(stages[show_cols].sort_values("开始日期", ascending=False), use_container_width=True)

                ids = stages["阶段ID"].astype(str).tolist()
                sel_id = st.selectbox("选择阶段ID", ids, index=0)
                cA, cB = st.columns(2)
                if cA.button("✅ 启用"):
                    stages.loc[stages["阶段ID"] == sel_id, "是否启用"] = True
                    save_stages(stages)
                    st.rerun()
                if cB.button("⛔ 停用"):
                    stages.loc[stages["阶段ID"] == sel_id, "是否启用"] = False
                    save_stages(stages)
                    st.rerun()

        st.divider()
        st.header("📝 新增检查 + 干预（完整版）")

        with st.form("entry_form", clear_on_submit=True):
            date_input = st.date_input("检查日期", datetime.now().date())

            auto_sid, auto_sname, auto_splan = match_stage_for_date(stages, pd.to_datetime(date_input))
            stage_options = ["自动匹配"] + stages[stages["是否启用"] == True]["阶段ID"].astype(str).tolist()
            sel_stage = st.selectbox("阶段归属", options=stage_options, index=0)

            if sel_stage == "自动匹配":
                stage_id, stage_name, stage_plan = auto_sid, auto_sname, auto_splan
            else:
                row = stages[stages["阶段ID"].astype(str) == sel_stage].iloc[0]
                stage_id, stage_name, stage_plan = row["阶段ID"], row["阶段名称"], row["主方案"]

            st.caption(f"归属阶段：**{stage_name or '未匹配阶段'}** | 主方案：**{stage_plan or '-'}**")

            st.markdown("### ① 视功能（必填项为主）")
            c1, c2 = st.columns(2)
            l_vision = c1.number_input("左眼视力 (L)", min_value=0.1, max_value=2.0, value=1.0, step=0.1, format="%.1f")
            r_vision = c2.number_input("右眼视力 (R)", min_value=0.1, max_value=2.0, value=1.0, step=0.1, format="%.1f")

            c3, c4 = st.columns(2)
            l_reserve = c3.number_input("左眼远视储备 (D)", min_value=-10.0, max_value=10.0, value=0.0, step=0.25, format="%.2f")
            r_reserve = c4.number_input("右眼远视储备 (D)", min_value=-10.0, max_value=10.0, value=0.0, step=0.25, format="%.2f")

            c5, c6 = st.columns(2)
            l_axis_text = c5.text_input("左眼眼轴(mm，可留空 15~30)", value="")
            r_axis_text = c6.text_input("右眼眼轴(mm，可留空 15~30)", value="")
            l_axis, l_axis_err = parse_axis(l_axis_text)
            r_axis, r_axis_err = parse_axis(r_axis_text)
            if l_axis_err: c5.error(l_axis_err)
            if r_axis_err: c6.error(r_axis_err)

            st.markdown("### ② 屈光/验光（可留空）")
            r1, r2, r3, r4 = st.columns(4)
            OD_S = r1.text_input("OD S", value="")
            OD_C = r2.text_input("OD C", value="")
            OD_A = r3.text_input("OD A", value="")
            OD_SE = r4.text_input("OD SE", value="")

            l1, l2, l3, l4 = st.columns(4)
            OS_S = l1.text_input("OS S", value="")
            OS_C = l2.text_input("OS C", value="")
            OS_A = l3.text_input("OS A", value="")
            OS_SE = l4.text_input("OS SE", value="")

            # PD：用可留空文本输入，避免 below-min 报错
            pd_col = st.text_input("PD(mm)（可留空，范围 40~80）", value="")
            PD, PD_err = parse_optional_float(pd_col, 40.0, 80.0)
            if PD_err: st.error(f"PD：{PD_err}")

            st.markdown("### ③ 角膜曲率/K值（可留空）")
            k1, k2, k3 = st.columns(3)
            OD_K1_mm = k1.text_input("OD K1(mm)", value="")
            OD_K1_D = k2.text_input("OD K1(D)", value="")
            OD_K1_axis = k3.text_input("OD K1轴位", value="")

            k4, k5, k6 = st.columns(3)
            OD_K2_mm = k4.text_input("OD K2(mm)", value="")
            OD_K2_D = k5.text_input("OD K2(D)", value="")
            OD_K2_axis = k6.text_input("OD K2轴位", value="")

            k7, k8 = st.columns(2)
            OD_cyl = k7.text_input("OD 角膜CYL(D)", value="")
            OD_cyl_axis = k8.text_input("OD 角膜CYL轴位", value="")

            k9, k10, k11 = st.columns(3)
            OS_K1_mm = k9.text_input("OS K1(mm)", value="")
            OS_K1_D = k10.text_input("OS K1(D)", value="")
            OS_K1_axis = k11.text_input("OS K1轴位", value="")

            k12, k13, k14 = st.columns(3)
            OS_K2_mm = k12.text_input("OS K2(mm)", value="")
            OS_K2_D = k13.text_input("OS K2(D)", value="")
            OS_K2_axis = k14.text_input("OS K2轴位", value="")

            k15, k16 = st.columns(2)
            OS_cyl = k15.text_input("OS 角膜CYL(D)", value="")
            OS_cyl_axis = k16.text_input("OS 角膜CYL轴位", value="")

            st.markdown("### ④ WTW/角膜厚度/瞳孔/眼压（可留空）")
            x1, x2 = st.columns(2)
            OD_WTW = x1.text_input("OD WTW(mm)", value="")
            OS_WTW = x2.text_input("OS WTW(mm)", value="")

            t1, t2, t3 = st.columns(3)
            OD_CCT = t1.text_input("OD 角膜中央厚度(um)", value="")
            OS_CCT = t2.text_input("OS 角膜中央厚度(um)", value="")
            OD_thinnest = t3.text_input("OD 最薄角膜厚度(um)", value="")

            t4, t5, t6 = st.columns(3)
            OS_thinnest = t4.text_input("OS 最薄角膜厚度(um)", value="")
            OD_thinnest_pos = t5.text_input("OD 最薄点位置(mm)", value="")
            OS_thinnest_pos = t6.text_input("OS 最薄点位置(mm)", value="")

            p1, p2, p3, p4 = st.columns(4)
            OD_pupil = p1.text_input("OD 瞳孔直径(mm)", value="")
            OS_pupil = p2.text_input("OS 瞳孔直径(mm)", value="")
            OD_iop = p3.text_input("OD 眼压(mmHg)", value="")
            OS_iop = p4.text_input("OS 眼压(mmHg)", value="")

            st.markdown("### ⑤ 双眼视觉/集合/调节/翻转拍（可留空）")
            b1, b2, b3 = st.columns(3)
            Titmus = b1.text_input("立体视 Titmus(秒)", value="")
            Fusion = b2.text_input("融合范围(°)", value="")
            Tropia = b3.text_input("他觉斜视角(°)", value="")

            csc1, csc2, ccc1, ccc2 = st.columns(4)
            SC_33 = csc1.text_input("33cm_SC(°)", value="")
            SC_6m = csc2.text_input("6m_SC(°)", value="")
            CC_33 = ccc1.text_input("33cm_CC(°)", value="")
            CC_6m = ccc2.text_input("6m_CC(°)", value="")

            a1, a2, a3, a4 = st.columns(4)
            ACA = a1.text_input("AC/A", value="")
            Amp_OD = a2.text_input("Amp_OD(D)", value="")
            Amp_OS = a3.text_input("Amp_OS(D)", value="")
            Amp_OU = a4.text_input("Amp_OU(D)", value="")

            f1, f2, f3, f4 = st.columns(4)
            Fl_OD = f1.text_input("Flipper_OD(cpm)", value="")
            Fl_OS = f2.text_input("Flipper_OS(cpm)", value="")
            Fl_OU = f3.text_input("Flipper_OU(cpm)", value="")
            Fl_note = f4.text_input("Flipper_备注", value="")

            st.divider()
            st.markdown("### ⑥ 干预/治疗（含频次与依从性）")
            st.markdown('<div class="small-hint">建议每次复查把“当前阶段正在执行的方案”勾选并写清楚频次，便于对比效果。</div>', unsafe_allow_html=True)

            # 阿托品
            use_atropine = st.checkbox("低浓度阿托品")
            atropine_spec = atropine_freq = ""
            atropine_week = None
            atropine_start = atropine_end = None
            atropine_ad = None
            atropine_se = ""
            if use_atropine:
                atropine_spec = st.text_input("阿托品浓度/规格（如：0.01%）", value="")
                atropine_freq = st.text_input("阿托品频次（文本）（如：每晚1次）", value="")
                wtxt = st.text_input("阿托品每周次数（数字，可留空）", value="")
                atropine_week, err = parse_optional_int(wtxt, 0, 14)
                if err: st.error(f"阿托品每周次数：{err}")
                a1c, a2c = st.columns(2)
                atropine_start = a1c.date_input("阿托品开始日期", value=date_input)
                atropine_end = a2c.date_input("阿托品结束日期（可选）", value=None)
                atropine_ad = st.slider("阿托品依从性(%)", 0, 100, 80, 5)
                atropine_se = st.text_area("阿托品副作用/不适（可选）", value="", height=60)

            # 眼镜
            use_glasses = st.checkbox("防控眼镜")
            glasses_type = ""
            glasses_hours = None
            glasses_days = None
            glasses_start = glasses_end = None
            glasses_ad = None
            glasses_dis = ""
            if use_glasses:
                glasses_type = st.text_input("眼镜类型（如：离焦/周边离焦等，自填）", value="")
                glasses_hours = st.number_input("每天佩戴时长(h)", min_value=0.0, max_value=24.0, value=8.0, step=0.5)
                dtxt = st.text_input("每周佩戴天数（0~7，可留空）", value="")
                glasses_days, err = parse_optional_int(dtxt, 0, 7)
                if err: st.error(f"每周佩戴天数：{err}")
                g1c, g2c = st.columns(2)
                glasses_start = g1c.date_input("眼镜开始日期", value=date_input)
                glasses_end = g2c.date_input("眼镜结束日期（可选）", value=None)
                glasses_ad = st.slider("眼镜依从性(%)", 0, 100, 85, 5)
                glasses_dis = st.text_area("眼镜不适/反馈（可选）", value="", height=60)

            # 捕光仪
            use_light = st.checkbox("捕光仪/光照类")
            light_plan = ""
            light_minutes = None
            light_days = None
            light_start = light_end = None
            light_ad = None
            light_dis = ""
            if use_light:
                light_plan = st.text_input("方案/型号/规则（自填）", value="")
                light_minutes = st.number_input("每天时长(min)", min_value=0, max_value=300, value=30, step=5)
                ldtxt = st.text_input("每周使用天数（0~7，可留空）", value="")
                light_days, err = parse_optional_int(ldtxt, 0, 7)
                if err: st.error(f"每周使用天数：{err}")
                l1c, l2c = st.columns(2)
                light_start = l1c.date_input("捕光仪开始日期", value=date_input)
                light_end = l2c.date_input("捕光仪结束日期（可选）", value=None)
                light_ad = st.slider("捕光仪依从性(%)", 0, 100, 80, 5)
                light_dis = st.text_area("捕光仪不适/反馈（可选）", value="", height=60)

            # 七叶洋地参
            use_qiye = st.checkbox("七叶洋地参滴眼液（仅记录）")
            qiye_spec = qiye_freq = ""
            qiye_day = None
            qiye_start = qiye_end = None
            qiye_ad = None
            qiye_dis = ""
            if use_qiye:
                qiye_spec = st.text_input("规格/品牌（自填）", value="")
                qiye_freq = st.text_input("频次（文本）（如：每日2次）", value="")
                qtxt = st.text_input("每日次数（0~10，可留空）", value="")
                qiye_day, err = parse_optional_int(qtxt, 0, 10)
                if err: st.error(f"每日次数：{err}")
                q1c, q2c = st.columns(2)
                qiye_start = q1c.date_input("开始日期", value=date_input)
                qiye_end = q2c.date_input("结束日期（可选）", value=None)
                qiye_ad = st.slider("依从性(%)", 0, 100, 80, 5)
                qiye_dis = st.text_area("不适/反馈（可选）", value="", height=60)

            # 翻转拍
            use_flip = st.checkbox("翻转拍/训练")
            flip_plan = ""
            flip_perweek = None
            flip_minutes = None
            flip_start = flip_end = None
            flip_ad = None
            flip_fb = ""
            if use_flip:
                flip_plan = st.text_input("训练方案（自填）", value="")
                fptxt = st.text_input("每周次数（0~21，可留空）", value="")
                flip_perweek, err = parse_optional_int(fptxt, 0, 21)
                if err: st.error(f"每周次数：{err}")
                fmtxt = st.text_input("每次分钟（0~180，可留空）", value="")
                flip_minutes, err = parse_optional_int(fmtxt, 0, 180)
                if err: st.error(f"每次分钟：{err}")
                f1c, f2c = st.columns(2)
                flip_start = f1c.date_input("训练开始日期", value=date_input)
                flip_end = f2c.date_input("训练结束日期（可选）", value=None)
                flip_ad = st.slider("训练依从性(%)", 0, 100, 70, 5)
                flip_fb = st.text_area("训练反馈/不适（可选）", value="", height=60)

            # 其它
            use_other = st.checkbox("其它干预（自定义）")
            other_content = ""
            other_freqtxt = ""
            other_perweek = None
            other_minutes = None
            other_start = other_end = None
            other_ad = None
            other_fb = ""
            if use_other:
                other_content = st.text_area("其它干预内容（写清：是什么、怎么做、频次等）", value="", height=80)
                other_freqtxt = st.text_input("频次（文本）（如：每天一次/隔天一次等）", value="")
                optxt = st.text_input("每周次数（0~21，可留空）", value="")
                other_perweek, err = parse_optional_int(optxt, 0, 21)
                if err: st.error(f"每周次数：{err}")
                omtxt = st.text_input("每次分钟（0~180，可留空）", value="")
                other_minutes, err = parse_optional_int(omtxt, 0, 180)
                if err: st.error(f"每次分钟：{err}")
                o1c, o2c = st.columns(2)
                other_start = o1c.date_input("其它干预开始日期", value=date_input)
                other_end = o2c.date_input("其它干预结束日期（可选）", value=None)
                other_ad = st.slider("其它干预依从性(%)", 0, 100, 70, 5)
                other_fb = st.text_area("其它干预反馈（可选）", value="", height=60)

            st.divider()
            note = st.text_area("备注（医院/验光方式/医生建议/用眼情况等）", value="", height=120)

            submitted = st.form_submit_button("💾 保存记录（完整版）")

            if submitted:
                # 校验关键可选数值
                if l_axis_err or r_axis_err:
                    st.error("❌ 眼轴输入有误，请修正后再保存")
                    st.stop()
                if PD_err:
                    st.error("❌ PD 输入有误，请修正后再保存")
                    st.stop()

                # 入库
                new_entry = {
                    "日期": pd.to_datetime(date_input),
                    "阶段ID": stage_id,
                    "阶段名称": stage_name if stage_name else "未匹配阶段",
                    "阶段主方案": stage_plan,

                    "左眼视力": float(l_vision),
                    "右眼视力": float(r_vision),
                    "左眼远视储备": float(l_reserve),
                    "右眼远视储备": float(r_reserve),
                    "眼轴长度(L)": None if l_axis is None else float(l_axis),
                    "眼轴长度(R)": None if r_axis is None else float(r_axis),
                    "备注": note,

                    # 屈光
                    "右眼_S": OD_S or None, "右眼_C": OD_C or None, "右眼_A": OD_A or None, "右眼_SE": OD_SE or None,
                    "左眼_S": OS_S or None, "左眼_C": OS_C or None, "左眼_A": OS_A or None, "左眼_SE": OS_SE or None,
                    "PD(mm)": None if PD is None else float(PD),

                    # K
                    "右眼_K1(mm)": OD_K1_mm or None, "右眼_K1(D)": OD_K1_D or None, "右眼_K1轴位": OD_K1_axis or None,
                    "右眼_K2(mm)": OD_K2_mm or None, "右眼_K2(D)": OD_K2_D or None, "右眼_K2轴位": OD_K2_axis or None,
                    "右眼角膜CYL(D)": OD_cyl or None, "右眼角膜CYL轴位": OD_cyl_axis or None,

                    "左眼_K1(mm)": OS_K1_mm or None, "左眼_K1(D)": OS_K1_D or None, "左眼_K1轴位": OS_K1_axis or None,
                    "左眼_K2(mm)": OS_K2_mm or None, "左眼_K2(D)": OS_K2_D or None, "左眼_K2轴位": OS_K2_axis or None,
                    "左眼角膜CYL(D)": OS_cyl or None, "左眼角膜CYL轴位": OS_cyl_axis or None,

                    # WTW/厚度/瞳孔/眼压
                    "右眼_WTW(mm)": OD_WTW or None, "左眼_WTW(mm)": OS_WTW or None,
                    "右眼_角膜中央厚度(um)": OD_CCT or None, "左眼_角膜中央厚度(um)": OS_CCT or None,
                    "右眼_最薄角膜厚度(um)": OD_thinnest or None, "左眼_最薄角膜厚度(um)": OS_thinnest or None,
                    "右眼_最薄点位置(mm)": OD_thinnest_pos or None, "左眼_最薄点位置(mm)": OS_thinnest_pos or None,
                    "右眼_瞳孔直径(mm)": OD_pupil or None, "左眼_瞳孔直径(mm)": OS_pupil or None,
                    "右眼眼压(mmHg)": OD_iop or None, "左眼眼压(mmHg)": OS_iop or None,

                    # 双眼视觉/集合/调节/翻转拍
                    "立体视_Titmus(秒)": Titmus or None,
                    "融合范围(°)": Fusion or None,
                    "他觉斜视角(°)": Tropia or None,
                    "33cm_SC(°)": SC_33 or None, "6m_SC(°)": SC_6m or None,
                    "33cm_CC(°)": CC_33 or None, "6m_CC(°)": CC_6m or None,
                    "AC/A": ACA or None,
                    "Amp_OD(D)": Amp_OD or None, "Amp_OS(D)": Amp_OS or None, "Amp_OU(D)": Amp_OU or None,
                    "Flipper_OD(cpm)": Fl_OD or None, "Flipper_OS(cpm)": Fl_OS or None, "Flipper_OU(cpm)": Fl_OU or None,
                    "Flipper_备注": Fl_note or None,

                    # 干预
                    "阿托品_是否使用": bool(use_atropine),
                    "阿托品_浓度或规格": atropine_spec if use_atropine else None,
                    "阿托品_频次文本": atropine_freq if use_atropine else None,
                    "阿托品_每周次数": atropine_week if use_atropine else None,
                    "阿托品_开始日期": pd.to_datetime(atropine_start) if use_atropine and atropine_start else None,
                    "阿托品_结束日期": pd.to_datetime(atropine_end) if use_atropine and atropine_end else None,
                    "阿托品_依从性(%)": int(atropine_ad) if use_atropine and atropine_ad is not None else None,
                    "阿托品_副作用或不适": atropine_se if use_atropine else None,

                    "防控眼镜_是否使用": bool(use_glasses),
                    "防控眼镜_类型": glasses_type if use_glasses else None,
                    "防控眼镜_每天佩戴时长(h)": float(glasses_hours) if use_glasses and glasses_hours is not None else None,
                    "防控眼镜_每周天数": glasses_days if use_glasses else None,
                    "防控眼镜_开始日期": pd.to_datetime(glasses_start) if use_glasses and glasses_start else None,
                    "防控眼镜_结束日期": pd.to_datetime(glasses_end) if use_glasses and glasses_end else None,
                    "防控眼镜_依从性(%)": int(glasses_ad) if use_glasses and glasses_ad is not None else None,
                    "防控眼镜_不适": glasses_dis if use_glasses else None,

                    "捕光仪_是否使用": bool(use_light),
                    "捕光仪_方案": light_plan if use_light else None,
                    "捕光仪_每天时长(min)": int(light_minutes) if use_light and light_minutes is not None else None,
                    "捕光仪_每周天数": light_days if use_light else None,
                    "捕光仪_开始日期": pd.to_datetime(light_start) if use_light and light_start else None,
                    "捕光仪_结束日期": pd.to_datetime(light_end) if use_light and light_end else None,
                    "捕光仪_依从性(%)": int(light_ad) if use_light and light_ad is not None else None,
                    "捕光仪_不适": light_dis if use_light else None,

                    "七叶洋地参_是否使用": bool(use_qiye),
                    "七叶洋地参_规格": qiye_spec if use_qiye else None,
                    "七叶洋地参_频次文本": qiye_freq if use_qiye else None,
                    "七叶洋地参_每日次数": qiye_day if use_qiye else None,
                    "七叶洋地参_开始日期": pd.to_datetime(qiye_start) if use_qiye and qiye_start else None,
                    "七叶洋地参_结束日期": pd.to_datetime(qiye_end) if use_qiye and qiye_end else None,
                    "七叶洋地参_依从性(%)": int(qiye_ad) if use_qiye and qiye_ad is not None else None,
                    "七叶洋地参_不适": qiye_dis if use_qiye else None,

                    "翻转拍_是否训练": bool(use_flip),
                    "翻转拍_方案": flip_plan if use_flip else None,
                    "翻转拍_每周次数": flip_perweek if use_flip else None,
                    "翻转拍_每次分钟": flip_minutes if use_flip else None,
                    "翻转拍_开始日期": pd.to_datetime(flip_start) if use_flip and flip_start else None,
                    "翻转拍_结束日期": pd.to_datetime(flip_end) if use_flip and flip_end else None,
                    "翻转拍_依从性(%)": int(flip_ad) if use_flip and flip_ad is not None else None,
                    "翻转拍_不适或反馈": flip_fb if use_flip else None,

                    "其它干预_是否有": bool(use_other),
                    "其它干预_内容": other_content if use_other else None,
                    "其它干预_频次文本": other_freqtxt if use_other else None,
                    "其它干预_每周次数": other_perweek if use_other else None,
                    "其它干预_每次分钟": other_minutes if use_other else None,
                    "其它干预_开始日期": pd.to_datetime(other_start) if use_other and other_start else None,
                    "其它干预_结束日期": pd.to_datetime(other_end) if use_other and other_end else None,
                    "其它干预_依从性(%)": int(other_ad) if use_other and other_ad is not None else None,
                    "其它干预_反馈": other_fb if use_other else None,
                }

                new_df = pd.DataFrame([new_entry])
                df2 = pd.concat([df, new_df], ignore_index=True) if not df.empty else new_df
                df2["日期"] = pd.to_datetime(df2["日期"], errors="coerce")
                df2 = df2.sort_values("日期")
                df2 = ensure_columns(df2)
                save_data(df2)

                st.success("✅ 已保存（完整版+阶段）")
                st.rerun()

    # ================== 主页面展示 ==================
    if df_show.empty:
        st.info("👋 欢迎！请在左侧录入第一次检查数据。")
        return

    df_show = df_show.sort_values("日期").copy()
    latest = df_show.iloc[-1]
    latest_date_str = latest["日期"].strftime("%Y-%m-%d") if pd.notnull(latest["日期"]) else "未知日期"

    st.markdown(
        f"""
<div class="card">
  <div class="card-title">🔍 最近一次记录
    <span class="badge">{latest_date_str}</span>
    <span class="badge">阶段：{latest.get("阶段名称","未匹配阶段")}</span>
    <span class="badge">干预：{short_tag(latest)}</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("左眼视力", latest.get("左眼视力", ""))
    k2.metric("右眼视力", latest.get("右眼视力", ""))
    k3.metric("左眼远视储备", f"{latest.get('左眼远视储备', 0):+}D")
    k4.metric("右眼远视储备", f"{latest.get('右眼远视储备', 0):+}D")

    # A4 打印版报告（隐藏打印按钮区域）
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    with st.expander("🖨️ 最近一次检查报告（A4一页打印版）", expanded=False):
        st.info("打开后按 Ctrl+P（打印），选择 A4 纵向；系统会自动只打印报告内容。")
        st.markdown(a4_report_html(latest), unsafe_allow_html=True)
        st.caption("提示：如果你想把报告导出 PDF，打印时选择“另存为PDF”。")
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📈 趋势", "🧩 阶段×干预汇总", "🧾 最近一次明细清单", "📑 全部数据"])

    with tab1:
        stage_list = ["全部"] + sorted(df_show["阶段名称"].fillna("未匹配阶段").unique().tolist())
        sel_stage = st.selectbox("阶段过滤", stage_list, index=0)

        dfp = df_show.copy()
        dfp["阶段名称"] = dfp["阶段名称"].fillna("未匹配阶段")
        if sel_stage != "全部":
            dfp = dfp[dfp["阶段名称"] == sel_stage]

        if dfp.empty:
            st.warning("该阶段暂无数据。")
        else:
            df_tail, n_used, _ = safe_last_n_selector("显示最近 N 次", dfp, default_n=12, min_n=3, max_cap=80)
            df_tail = df_tail.copy()

            # 平均视力 / 平均SE
            df_tail["平均视力"] = (to_numeric(df_tail["左眼视力"]) + to_numeric(df_tail["右眼视力"])) / 2
            df_tail["平均SE"] = (to_numeric(df_tail["左眼_SE"]) + to_numeric(df_tail["右眼_SE"])) / 2

            cA, cB = st.columns(2)

            with cA:
                long_v = df_tail.melt(
                    id_vars=["日期", "阶段名称", "阶段主方案"],
                    value_vars=["左眼视力", "右眼视力", "平均视力"],
                    var_name="指标",
                    value_name="值",
                ).dropna(subset=["日期", "值"])
                fig1 = px.line(long_v, x="日期", y="值", color="指标", markers=True, hover_data=["阶段名称", "阶段主方案"])
                st.plotly_chart(fig1, use_container_width=True)

            with cB:
                long_se = df_tail.melt(
                    id_vars=["日期", "阶段名称", "阶段主方案"],
                    value_vars=["左眼_SE", "右眼_SE", "平均SE"],
                    var_name="指标",
                    value_name="值",
                ).dropna(subset=["日期", "值"])
                if long_se.empty:
                    st.info("SE 数据为空（请在录入时填写 S/C/A/SE 或 SE）。")
                else:
                    fig2 = px.line(long_se, x="日期", y="值", color="指标", markers=True, hover_data=["阶段名称", "阶段主方案"])
                    st.plotly_chart(fig2, use_container_width=True)

            cC, cD = st.columns(2)
            with cC:
                long_r = df_tail.melt(
                    id_vars=["日期", "阶段名称"],
                    value_vars=["左眼远视储备", "右眼远视储备"],
                    var_name="指标",
                    value_name="值",
                ).dropna(subset=["日期", "值"])
                fig3 = px.line(long_r, x="日期", y="值", color="指标", markers=True, hover_data=["阶段名称"])
                st.plotly_chart(fig3, use_container_width=True)

            with cD:
                long_ax = df_tail.melt(
                    id_vars=["日期", "阶段名称"],
                    value_vars=["眼轴长度(L)", "眼轴长度(R)"],
                    var_name="指标",
                    value_name="值",
                ).dropna(subset=["日期", "值"])
                if long_ax.empty:
                    st.info("眼轴数据为空（可留空，也可后续补录）。")
                else:
                    fig4 = px.line(long_ax, x="日期", y="值", color="指标", markers=True, hover_data=["阶段名称"])
                    st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        summary = build_stage_intervention_summary(df_show)
        if summary.empty:
            st.info("暂无可汇总数据（请先录入干预勾选/频次/依从性）。")
        else:
            st.dataframe(summary.sort_values(["阶段", "干预"]), use_container_width=True)
            st.caption("说明：频次/时长均值1、2 对应各干预的核心频次字段（如眼镜=每天佩戴时长/每周天数）。")

    with tab3:
        st.markdown("### 🧾 最近一次检查项目清单（可打印/可复制）")
        st.markdown(a4_report_html(latest), unsafe_allow_html=True)
        st.caption("提示：该页面在打印时会自动只打印报告内容（隐藏侧栏与控件）。")

    with tab4:
        front_cols = [
            "日期", "阶段名称", "阶段主方案", "干预标签",
            "左眼视力", "右眼视力", "左眼远视储备", "右眼远视储备",
            "眼轴长度(L)", "眼轴长度(R)",
            "右眼_S","右眼_C","右眼_A","右眼_SE","左眼_S","左眼_C","左眼_A","左眼_SE",
            "PD(mm)", "右眼眼压(mmHg)", "左眼眼压(mmHg)",
            "备注"
        ]
        rest_cols = [c for c in df_show.columns if c not in front_cols]
        st.dataframe(df_show[front_cols + rest_cols].sort_values("日期"), use_container_width=True)


app_main()
