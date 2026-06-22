"""
命令行入口：支持三种方式输入文本，指定抽取类型，输出结构化 JSON。

用法示例：
  # 从文件读取
  python main.py resume --file tests/resume_sample.txt

  # 直接传文本
  python main.py product --text "iPhone 15 Pro Max, Apple, 9999元, 256GB, 钛金属边框"

  # 标准输入
  echo "张三, 北京大学, 硕士, Python/Java" | python main.py resume
"""
import argparse
import json
import sys

from extractor import extract, ExtractionError


def format_output(result) -> str:
    """将 Pydantic 模型格式化为可读的 JSON 字符串"""
    return json.dumps(result.model_dump(), indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="结构化信息抽取器 — 从简历/合同/商品描述中提取结构化 JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py resume --file tests/resume_sample.txt
  python main.py contract -f tests/contract_sample.txt
  python main.py product -t "小米14 Ultra, 骁龙8Gen3, 6499元"
        """,
    )
    parser.add_argument(
        "type",
        choices=["resume", "contract", "product"],
        help="输入文本类型",
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--file", "-f",
        help="从文件读取输入文本",
    )
    input_group.add_argument(
        "--text", "-t",
        help="直接在命令行传入文本",
    )
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=3,
        help="最大重试次数（默认 3）",
    )

    args = parser.parse_args()

    # ── 获取输入文本 ──
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            print(f"❌ 文件不存在: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        # 从标准输入读取
        if sys.stdin.isatty():
            print("请输入待抽取的文本（输入完成后按 Ctrl+Z 回车 结束）:")
        text = sys.stdin.read()

    if not text.strip():
        print("❌ 输入文本为空", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 正在抽取 [{args.type}] 类型信息...", file=sys.stderr)

    try:
        result = extract(text, args.type, max_retries=args.retries)
        print(format_output(result))
    except ExtractionError as e:
        print(f"❌ 抽取失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
