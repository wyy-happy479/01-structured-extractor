# 项目1：结构化输出信息抽取器

> 基于 LLM 的结构化信息抽取系统，支持简历/合同/商品描述等多场景。
> Pydantic Schema 校验 + 失败重试机制，每个字段带置信度评分。
> 支持 PDF / Word / TXT 三种输入格式。

## 技术栈

- Python 3.10+
- **模型**：阿里云百炼 `qwen-max`（也可切换 DeepSeek `deepseek-chat`，OpenAI 兼容接口）
- Pydantic v2（Schema 定义 + 校验）
- pymupdf（PDF 文本提取）
- python-docx（Word 文本提取）
- 零框架依赖（不引入 LangChain），纯 API 调用

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 API Key（二选一）
#    百炼用户：
set DASHSCOPE_API_KEY=sk-your-key-here
#    DeepSeek 用户：需同时改 extractor.py 中的 base_url 和 model

# 3. 运行（支持 .txt / .pdf / .docx）
python main.py resume -f tests/resume_sample.txt
python main.py contract -f tests/contract_sample.txt
python main.py product -f tests/product_sample.txt

# 4. 直接传文本（不需要文件）
python main.py product -t "小米14 Ultra, 骁龙8Gen3, 6499元, 徕卡四摄"

# 5. 乱码输入 → 验证重试机制
python main.py resume -f tests/bad_input.txt
```

## 项目结构

```
01project/
├── schemas.py                  # Pydantic 模型定义（Resume / Contract / Product）
├── prompts.py                  # 三种输入类型的 System Prompt 模板
├── extractor.py                # 核心抽取逻辑：API 调用 → JSON 解析 → 校验 → 重试
├── reader.py                   # 文件读取器：PDF / Word / TXT → 纯文本
├── tools.py                    # 工具定义模板（6个，含风险分级，复用到项目3）
├── main.py                     # CLI 入口
├── requirements.txt
├── .gitignore
├── .env.example
├── tests/
│   ├── resume_sample.txt       # 简历测试样本
│   ├── resume_expected.json    # 简历预期输出
│   ├── contract_sample.txt     # 合同测试样本
│   ├── contract_expected.json  # 合同预期输出
│   ├── product_sample.txt      # 商品描述测试样本
│   ├── product_expected.json   # 商品描述预期输出
│   └── bad_input.txt           # 乱码输入（测试重试机制）
└── README.md
```

## 设计要点

### 1. 重试机制

```
定义 Schema → 调用模型 → 解析 JSON
    ↓ 失败
把错误信息塞回 messages → 模型看到自己的错误输出 → 重新生成
    ↓ 失败
再重试（最多 3 次）
    ↓ 仍失败
抛出 ExtractionError
```

### 2. 置信度字段

每个提取字段都有对应的 `*_confidence: 0.0~1.0`，评分标准：

- **1.0** — 从原文直接提取，完全确信（如明确写出"北京大学"）
- **0.7~0.9** — 根据原文合理推断（如从"5年后端经验"推断工作年限）
- **0.4~0.6** — 根据上下文猜测，不太确定
- **0.0** — 文本中无相关信息

### 3. 低温度策略

抽取任务使用 `temperature=0.1`，追求确定性输出，减少幻觉。

## 输出示例

```json
{
  "name": "张三",
  "name_confidence": 0.95,
  "education": "硕士",
  "education_confidence": 0.95,
  "school": "北京大学",
  "school_confidence": 0.95,
  "major": "计算机科学与技术",
  "major_confidence": 0.9,
  "skills": ["Python", "PyTorch", "TensorFlow", "LangChain", "Docker", "Kubernetes"],
  "skills_confidence": 0.9,
  "years_of_experience": 5,
  "years_of_experience_confidence": 0.8,
  "email": "zhangsan@example.com",
  "email_confidence": 1.0,
  "phone": "18612345678",
  "phone_confidence": 1.0,
  "project_names": ["AgentFlow", "RAG-Chat"],
  "project_names_confidence": 0.95,
  "project_descriptions": [
    "基于 LangGraph 的 Agent 编排框架，支持多 Agent 协作",
    "本地知识库问答系统，BM25 + 向量混合检索"
  ],
  "project_descriptions_confidence": 0.9,
  "summary": "5 年后端和 LLM 应用开发经验，专注于 Agent 架构和 RAG 系统",
  "summary_confidence": 0.85
}
```

## 验证清单

对照学习计划的 Week 2 产出要求：

- [x] GitHub repo，README 写清楚怎么用、用什么模型、输出什么
- [x] 至少 2 种输入类型的测试（简历 + 合同 + 商品描述 = 3 种）
- [x] Pydantic Schema 定义 + 失败重试逻辑（`tests/bad_input.txt` 验证）
- [x] 每个字段带 `confidence` 字段
- [x] Function Calling 工具定义模板 — `tools.py`，6 个工具 + 风险分级，可直接复用到项目3
