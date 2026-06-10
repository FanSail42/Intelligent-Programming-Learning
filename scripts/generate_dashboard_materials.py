#!/usr/bin/env python3
"""Generate course PDF materials for dashboard demo (3 courses × 6 files)."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "root_data" / "课程资料" / "_联调演示" / "dashboard_demo"
FONT_PATH = Path("C:/Windows/Fonts/msyh.ttc")
FONT_NAME = "MSYaHei"

COURSE_MATERIALS: dict[str, list[tuple[str, str]]] = {
    "cpp": [
        ("01_线性表与链表基础.pdf", "线性表、单链表、双链表与哨兵节点。"),
        ("02_栈队列与优先队列.pdf", "STL queue/stack 与单调队列应用。"),
        ("03_二叉树与遍历.pdf", "前序、中序、后序与层序遍历。"),
        ("04_图论基础与最短路.pdf", "邻接表、BFS、Dijkstra 入门。"),
        ("05_排序与二分查找.pdf", "快排、归并与二分答案模板。"),
        ("06_动态规划入门.pdf", "状态定义、转移方程与背包问题。"),
    ],
    "python": [
        ("01_NumPy数组与向量化.pdf", "ndarray、广播机制与向量化运算。"),
        ("02_Pandas数据清洗.pdf", "缺失值、重复值与类型转换。"),
        ("03_数据透视与分组聚合.pdf", "groupby、pivot_table 实战。"),
        ("04_Matplotlib可视化.pdf", "折线图、柱状图与热力图。"),
        ("05_统计分析基础.pdf", "描述统计、相关性与假设检验简介。"),
        ("06_数据分析实战案例.pdf", "电商订单数据端到端分析流程。"),
    ],
    "java": [
        ("01_类与对象入门.pdf", "类定义、构造方法与对象生命周期。"),
        ("02_封装继承与多态.pdf", "访问控制、方法重写与向上转型。"),
        ("03_抽象类与接口.pdf", "interface 与 abstract class 对比。"),
        ("04_异常处理与集合框架.pdf", "try-catch-finally 与 ArrayList/HashMap。"),
        ("05_设计模式概述.pdf", "单例、工厂与观察者模式。"),
        ("06_面向对象综合练习.pdf", "UML 类图到代码实现演练。"),
    ],
}

COURSE_TITLES = {
    "cpp": "C++ 数据结构与算法",
    "python": "Python 数据分析",
    "java": "Java 面向对象编程",
}


def register_font() -> None:
    if FONT_PATH.is_file():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(FONT_PATH), subfontIndex=0))


def build_pdf(path: Path, course_title: str, material_title: str, summary: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm)
    title_style = ParagraphStyle(
        "title",
        fontName=FONT_NAME if FONT_PATH.is_file() else "Helvetica",
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1a365d"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "body",
        fontName=FONT_NAME if FONT_PATH.is_file() else "Helvetica",
        fontSize=11,
        leading=18,
        spaceAfter=8,
    )
    story = [
        Paragraph(course_title, title_style),
        Paragraph(material_title.replace(".pdf", ""), title_style),
        Spacer(1, 0.4 * cm),
        Paragraph(summary, body_style),
        Paragraph("本资料为慧编学伴学习仪表盘联调演示数据，可用于资料推荐与 RAG 测试。", body_style),
    ]
    doc.build(story)


def generate_all() -> dict[str, list[str]]:
    register_font()
    generated: dict[str, list[str]] = {}
    for key, items in COURSE_MATERIALS.items():
        course_title = COURSE_TITLES[key]
        paths: list[str] = []
        for filename, summary in items:
            out_path = OUT_ROOT / key / filename
            build_pdf(out_path, course_title, filename, summary)
            paths.append(str(out_path))
        generated[key] = paths
    print(f"Generated {sum(len(v) for v in generated.values())} PDFs under {OUT_ROOT}")
    return generated


if __name__ == "__main__":
    generate_all()
