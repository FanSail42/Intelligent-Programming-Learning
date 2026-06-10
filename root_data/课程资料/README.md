# 课程资料目录说明

本目录按**课程类型**分门别类存放教学资料，供慧编学伴资料仓库、RAG 检索与学习仪表盘演示使用。

## 目录结构

```
课程资料/
├── README.md                    # 本说明
├── C++_竞赛算法/                # C++ 数据结构与算法竞赛向 PDF（10 讲）
├── Python_数据分析/             # Python 数据分析 PDF 讲义（含 NumPy/Pandas/可视化）
├── Java_面向对象编程/           # Java OOP Markdown 讲义（含练习题）
└── _联调演示/                   # 仪表盘三类课程联调用简短演示资料
    └── dashboard_demo/
        ├── cpp/   (6 份 PDF)
        ├── python/ (6 份 PDF)
        └── java/   (6 份 PDF)
```

## 三类代表课程对应关系

| 课程名称 | 资料目录 | 格式 | 说明 |
|----------|----------|------|------|
| C++ 数据结构与算法 | `C++_竞赛算法/` | PDF | 01～10 讲，竞赛/STL/算法专题 |
| Python 数据分析 | `Python_数据分析/` | PDF | NumPy、Pandas、Matplotlib/EDA |
| Java 面向对象编程 | `Java_面向对象编程/` | Markdown | 封装、继承多态、抽象接口 |

## 生成与更新

```bash
# Python 数据分析 PDF（3 份详细讲义）
cd backend
python ../scripts/generate_python_java_materials.py

# C++ 竞赛 10 讲 PDF
python ../scripts/generate_cpp_course_pdfs.py

# 仪表盘联调演示数据（47 条错题 + 18 份短 PDF）
python ../scripts/seed_dashboard_demo.py
```

## 参考资料来源（摘要）

- **Python**：[北理 MOOC 数据分析与展示](https://www.bilibili.com/video/BV1L64y1X7om/)、[博雅数智课程大纲](http://boyaidata.com/enterprise_dynamics/26)、[pandas 实战手册](https://leemeng.tw/practical-pandas-tutorial-for-aspiring-data-scientists.html)、pandas/NumPy 官方文档  
- **Java**：[Oracle Java Tutorial](https://docs.oracle.com/javase/tutorial/)、[极客时间 设计模式之美·OOP](https://time.geekbang.org/column/article/161114)、[阿里云 OOP 回顾](https://developer.aliyun.com/article/1614252)
