"""
测试 Path Intellisense 插件引用的相对路径是否能正确解析到真实文件。

在编辑器中输入 ../root_data/ 时，插件应能提示并补全路径；
本脚本用 pathlib 在运行时做等价校验。
"""
from pathlib import Path

# 与插件补全一致的相对路径（相对于本文件所在 test/ 目录）
path = "../root_data/01_慧编学伴——智能编程学习助教系统的设计与实现.pdf"


def resolve_pdf_path(relative: str) -> Path:
    """将相对路径解析为绝对路径。"""
    return (Path(__file__).resolve().parent / relative).resolve()


def test_path_exists():
    pdf = resolve_pdf_path(path)
    assert pdf.is_file(), f"路径无效或文件不存在: {pdf}"
    assert pdf.suffix.lower() == ".pdf"
    assert pdf.stat().st_size > 0, "PDF 文件为空"
    return pdf


def test_parent_dir_name():
    """root_data 目录应存在且可读。"""
    root_data = resolve_pdf_path(path).parent
    assert root_data.is_dir()
    assert root_data.name == "root_data"


if __name__ == "__main__":
    pdf = test_path_exists()
    test_parent_dir_name()
    print("Path Intellisense 路径测试通过")
    print(f"  相对路径: {path}")
    print(f"  绝对路径: {pdf}")
    print(f"  文件大小: {pdf.stat().st_size:,} bytes")
