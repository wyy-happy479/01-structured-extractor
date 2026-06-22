"""
文件读取器：将 PDF / Word / TXT 文件提取为纯文本字符串。

项目1 的"输入层"——不管什么格式进来，出来的都是 extract() 能吃的纯文本。
"""

from pathlib import Path


def read_file(file_path: str) -> str:
    """根据文件后缀自动选择读取方式，返回纯文本"""
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return _read_pdf(file_path)
    elif suffix in (".docx", ".doc"):
        return _read_docx(file_path)
    else:
        # 默认当纯文本读（.txt / .md / .json 等）
        return _read_txt(file_path)


def _read_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def _read_pdf(file_path: str) -> str:
    import fitz  # pymupdf

    doc = fitz.open(file_path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    doc.close()
    return "\n".join(texts)


def _read_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)
