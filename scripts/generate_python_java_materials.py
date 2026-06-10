#!/usr/bin/env python3
"""Generate rich Python data-analysis PDFs (3) for 课程资料/Python_数据分析."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "root_data" / "课程资料" / "Python_数据分析"
FONT_PATH = Path("C:/Windows/Fonts/msyh.ttc")
FONT_NAME = "MSYaHei"
CODE_FONT = "Courier"

REFERENCES = [
    "北京理工大学《Python 数据分析与展示》MOOC（NumPy / Pandas / Matplotlib 体系）",
    "博雅数智《Python 数据分析》课程大纲（NumPy→Pandas→可视化）",
    "LeeMeng《資料科學家的 pandas 實戰手冊》（DataFrame 清洗与汇总）",
    "pandas 官方文档：https://pandas.pydata.org/docs/",
    "NumPy 官方文档：https://numpy.org/doc/",
]

PYTHON_PDFS: list[dict] = [
    {
        "filename": "01_NumPy科学计算与数组编程.pdf",
        "title": "NumPy 科学计算与数组编程",
        "subtitle": "Python 数据分析 · 第 1 讲",
        "objectives": [
            "理解 ndarray 与 Python 列表在性能与内存上的差异",
            "掌握数组创建、索引切片、形状变换与广播机制",
            "熟练使用 ufunc、统计函数与线性代数常用操作",
            "完成 5 道 NumPy 基础练习题",
        ],
        "sections": [
            (
                "1. 为什么需要 NumPy",
                "NumPy（Numerical Python）是数据分析栈的基石。ndarray 在内存中连续存储同质数据，"
                "向量化运算由 C 实现，通常比 Python for 循环快 10～100 倍。"
                "Pandas 的底层大量依赖 NumPy 数组。",
            ),
            (
                "2. ndarray 核心概念",
                "• 维度（axis）：0 轴为行方向，1 轴为列方向\n"
                "• dtype：int64、float64、bool 等，创建后可通过 astype 转换\n"
                "• shape：各轴长度；reshape 不改变元素总数\n"
                "• 广播（broadcasting）：不同 shape 数组按规则自动扩展后运算",
            ),
            (
                "3. 常用 API 速查",
                "创建：np.array、np.zeros、np.ones、np.arange、np.linspace、np.random.randn\n"
                "索引：a[0]、a[1:4]、a[a>0] 布尔索引、a[[0,2]] 花式索引\n"
                "统计：mean、std、sum、argmax、percentile\n"
                "线性代数：np.dot、@ 运算符、np.linalg.inv（了解即可）",
            ),
        ],
        "code": """import numpy as np

# 创建与属性
a = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float64)
print(a.shape, a.ndim, a.dtype)  # (2, 3) 2 float64

# 广播：标量与数组运算
b = a * 2 + 1

# 布尔索引：筛选大于 3 的元素
mask = a > 3
print(a[mask])  # [4. 5. 6.]

# 按轴聚合
print(a.sum(axis=0))  # 每列求和
print(a.mean(axis=1)) # 每行均值

# 随机与统计
rng = np.random.default_rng(42)
samples = rng.normal(loc=0, scale=1, size=1000)
print(samples.mean(), samples.std(ddof=1))""",
        "exercises": [
            "创建 shape=(4,5) 的全 1 矩阵，并将第 2 行全部改为 0。",
            "给定 a = np.arange(12).reshape(3,4)，取出最后一列与对角线元素。",
            "对 1000 个标准正态随机数，计算均值、标准差、95% 分位数。",
            "不使用循环，将矩阵每行减去该行均值（提示：keepdims=True）。",
            "利用 np.linalg.norm 计算向量 [3,4] 的欧氏长度，验证是否为 5。",
        ],
    },
    {
        "filename": "02_Pandas数据处理与清洗实战.pdf",
        "title": "Pandas 数据处理与清洗实战",
        "subtitle": "Python 数据分析 · 第 2 讲",
        "objectives": [
            "理解 Series 与 DataFrame 的结构与索引机制",
            "掌握 CSV 读写、缺失值处理、重复值与类型转换",
            "熟练使用 groupby、pivot_table、merge 完成聚合与关联",
            "完成电商订单样例的清洗与汇总练习",
        ],
        "sections": [
            (
                "1. Pandas 在分析流程中的位置",
                "典型流程：数据获取 → 清洗 → 转换 → 聚合 → 可视化 → 结论。"
                "Pandas 负责中间 80% 的结构化表格操作，是工业界事实标准。",
            ),
            (
                "2. 数据结构",
                "Series：带标签的一维数组，可理解为 DataFrame 的一列。\n"
                "DataFrame：二维表格，行索引 Index、列名 columns、值 values（ndarray）。\n"
                "loc 按标签选取，iloc 按位置选取；避免链式赋值警告（SettingWithCopyWarning）。",
            ),
            (
                "3. 数据清洗清单",
                "• 缺失值：isna、fillna、dropna；策略有均值/中位数/众数填充或插值\n"
                "• 重复值：duplicated、drop_duplicates\n"
                "• 类型：astype、pd.to_datetime、pd.to_numeric(errors='coerce')\n"
                "• 异常值：IQR 法则或业务规则过滤",
            ),
            (
                "4. 分组与透视",
                "groupby('col').agg({'amount': 'sum', 'order_id': 'count'})\n"
                "pivot_table(index='region', columns='month', values='sales', aggfunc='sum')\n"
                "merge / concat 实现多表连接与纵向堆叠",
            ),
        ],
        "code": """import pandas as pd

df = pd.read_csv('orders.csv', parse_dates=['order_time'])
# 缺失与类型
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
df['amount'] = df['amount'].fillna(df['amount'].median())

# 去重
df = df.drop_duplicates(subset=['order_id'])

# 派生字段
df['month'] = df['order_time'].dt.to_period('M').astype(str)

# 分组聚合：各地区月度销售额
summary = (
    df.groupby(['region', 'month'], as_index=False)
      .agg(total_amount=('amount', 'sum'), order_cnt=('order_id', 'count'))
)

# 透视表
pivot = df.pivot_table(
    index='region', columns='month', values='amount', aggfunc='sum', fill_value=0
)
print(summary.head())
print(pivot)""",
        "exercises": [
            "读取 CSV 后统计每列缺失率，并删除缺失超过 50% 的列。",
            "将 user_id 转为 category 类型，比较内存占用变化（memory_usage）。",
            "按 product_category 分组，计算单价 amount/quantity 的均值与中位数。",
            "使用 merge 将订单表与用户表按 user_id 连接，输出含用户城市的汇总。",
            "对重复 order_id 保留 order_time 最新的一条记录。",
        ],
    },
    {
        "filename": "03_Matplotlib数据可视化与EDA.pdf",
        "title": "Matplotlib 数据可视化与探索性分析（EDA）",
        "subtitle": "Python 数据分析 · 第 3 讲",
        "objectives": [
            "理解 EDA 的目标：分布、关系、趋势、异常",
            "掌握折线图、柱状图、散点图、直方图与箱线图",
            "了解 Seaborn 统计图层的适用场景",
            "完成一份含 4 张图的分析小报告结构",
        ],
        "sections": [
            (
                "1. 探索性数据分析（EDA）",
                "EDA 不追求复杂模型，而是通过统计量与可视化快速理解数据。"
                "常用步骤：describe → 缺失/异常 → 单变量分布 → 双变量关系 → 时间趋势。",
            ),
            (
                "2. Matplotlib 基础",
                "Figure 与 Axes：fig, ax = plt.subplots() 推荐写法。\n"
                "折线图：趋势；柱状图：类别对比；散点图：相关；直方图/箱线图：分布。\n"
                "注意：中文标签需配置字体（如 SimHei / 微软雅黑），避免乱码。",
            ),
            (
                "3. Seaborn 补充",
                "sns.histplot、kdeplot 绘制分布；sns.heatmap 展示相关矩阵；"
                "sns.boxplot 对比组间差异。风格统一、默认配色适合报告。",
            ),
            (
                "4. 报告结构建议",
                "① 数据概览 ② 核心指标 KPI ③ 维度拆解 ④ 异常与结论 ⑤ 后续建模方向",
            ),
        ],
        "code": """import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('orders.csv', parse_dates=['order_time'])

fig, axes = plt.subplots(2, 2, figsize=(10, 8))

# 趋势
daily = df.groupby(df['order_time'].dt.date)['amount'].sum()
axes[0,0].plot(daily.index, daily.values)
axes[0,0].set_title('日销售额趋势')

# 类别柱状
cat = df.groupby('category')['amount'].sum().sort_values(ascending=False)
axes[0,1].bar(cat.index, cat.values)
axes[0,1].tick_params(axis='x', rotation=30)

# 散点：数量 vs 金额
axes[1,0].scatter(df['quantity'], df['amount'], alpha=0.5, s=10)

# 箱线图：各地区金额分布
sns.boxplot(data=df, x='region', y='amount', ax=axes[1,1])

plt.tight_layout()
plt.savefig('eda_report.png', dpi=150)""",
        "exercises": [
            "绘制某列的直方图与核密度曲线，并标注均值线。",
            "用 heatmap 展示数值型字段的相关矩阵，隐藏上三角。",
            "按 weekday 聚合订单量，绘制柱状图并添加数据标签。",
            "发现 3 个可能的异常点（IQR 法），在散点图中高亮。",
            "撰写 200 字 EDA 小结：数据质量、主要发现、后续建议。",
        ],
    },
]


def register_font() -> None:
    if FONT_PATH.is_file():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH), subfontIndex=0))


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_styles() -> dict[str, ParagraphStyle]:
    fn = FONT_NAME if FONT_PATH.is_file() else "Helvetica"
    return {
        "title": ParagraphStyle("title", fontName=fn, fontSize=20, leading=26, spaceAfter=10, textColor=colors.HexColor("#1a365d")),
        "subtitle": ParagraphStyle("subtitle", fontName=fn, fontSize=12, leading=18, spaceAfter=14, textColor=colors.HexColor("#4a5568")),
        "heading": ParagraphStyle("heading", fontName=fn, fontSize=13, leading=18, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#2d3748")),
        "body": ParagraphStyle("body", fontName=fn, fontSize=10.5, leading=16, spaceAfter=6),
        "bullet": ParagraphStyle("bullet", fontName=fn, fontSize=10.5, leading=16, leftIndent=12, spaceAfter=3),
        "ref": ParagraphStyle("ref", fontName=fn, fontSize=9, leading=14, textColor=colors.HexColor("#718096")),
    }


def code_block(text: str) -> list:
    return [
        Preformatted(
            text.rstrip(),
            ParagraphStyle("pre", fontName=CODE_FONT, fontSize=8, leading=10, backColor=colors.HexColor("#f7fafc"), borderPadding=6),
        ),
        Spacer(1, 0.2 * cm),
    ]


def build_pdf(spec: dict) -> Path:
    styles = build_styles()
    out = OUT_DIR / spec["filename"]
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm)
    story: list = []

    story.append(Paragraph(esc(spec["title"]), styles["title"]))
    story.append(Paragraph(esc(spec["subtitle"]), styles["subtitle"]))
    story.append(Paragraph(esc("慧编学伴 · Python 数据分析课程资料"), styles["ref"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(esc("学习目标"), styles["heading"]))
    for obj in spec["objectives"]:
        story.append(Paragraph(f"• {esc(obj)}", styles["bullet"]))

    for heading, body in spec["sections"]:
        story.append(Paragraph(esc(heading), styles["heading"]))
        for para in body.split("\n"):
            if para.strip():
                story.append(Paragraph(esc(para.strip()), styles["body"]))

    story.append(Paragraph(esc("代码示例"), styles["heading"]))
    story.extend(code_block(spec["code"]))

    story.append(PageBreak())
    story.append(Paragraph(esc("练习题"), styles["heading"]))
    for i, ex in enumerate(spec["exercises"], 1):
        story.append(Paragraph(f"{i}. {esc(ex)}", styles["bullet"]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(esc("参考资料"), styles["heading"]))
    for ref in REFERENCES:
        story.append(Paragraph(f"• {esc(ref)}", styles["ref"]))

    doc.build(story)
    return out


def generate_python_pdfs() -> list[Path]:
    register_font()
    paths = [build_pdf(spec) for spec in PYTHON_PDFS]
    print(f"Generated {len(paths)} Python PDFs -> {OUT_DIR}")
    return paths


if __name__ == "__main__":
    generate_python_pdfs()
