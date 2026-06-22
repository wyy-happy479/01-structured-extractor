"""
工具定义模板：OpenAI/DeepSeek Function Calling 格式的 Tool Schema。

每个工具包含三个核心字段：
  - name:        工具名（模型用它来决定"该调哪个"）
  - description: 工具描述（写清楚什么时候用、什么时候不用）
  - parameters:  JSON Schema 格式的参数定义

设计原则（面试常考）：
  ✅ 单一职责 — 一个工具只做一件事
  ✅ 名称明确 — 动词+名词，如 query_order / cancel_order
  ✅ 参数尽量少 — 必填参数 ≤3 个
  ✅ 返回结构化 — 成功/失败统一格式
  ✅ description 写清楚边界 — "什么时候用，什么时候别用"

这些模板可直接复用到项目3（工具调用型客服 Agent）。
"""

# ──────────────────────────────────────────────────
# 工具 1：订单查询
# ──────────────────────────────────────────────────

QUERY_ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "query_order",
        "description": (
            "查询用户的订单详情。当用户询问订单状态、订单内容、物流进度时使用。"
            "需要提供订单号来精确定位。如果没有订单号，先用 query_order_list 查找。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单号，格式如 ORD-20240601-001",
                },
            },
            "required": ["order_id"],
        },
    },
}

# ──────────────────────────────────────────────────
# 工具 2：物流查询
# ──────────────────────────────────────────────────

QUERY_LOGISTICS_TOOL = {
    "type": "function",
    "function": {
        "name": "query_logistics",
        "description": (
            "查询订单的物流状态和快递轨迹。适用于用户问'我的快递到哪了'、"
            "'什么时候发货'、'物流单号是多少'等情况。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "订单号，格式如 ORD-20240601-001",
                },
                "tracking_number": {
                    "type": "string",
                    "description": "快递单号（可选），如果用户已提供快递单号",
                },
            },
            "required": ["order_id"],
        },
    },
}

# ──────────────────────────────────────────────────
# 工具 3：退款政策查询（RAG 检索）
# ──────────────────────────────────────────────────

SEARCH_REFUND_POLICY_TOOL = {
    "type": "function",
    "function": {
        "name": "search_refund_policy",
        "description": (
            "在知识库中检索退款政策、退换货规则、售后流程。"
            "当用户问'能不能退''怎么退货''退款什么时候到账'时使用。"
            "不要用于常规的订单状态查询——那种情况用 query_order。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用户的原始问题或改写后的检索关键词",
                },
                "product_type": {
                    "type": "string",
                    "description": "商品类别（可选），用于缩小检索范围，如'电子产品''服装'",
                },
            },
            "required": ["query"],
        },
    },
}

# ──────────────────────────────────────────────────
# 工具 4：创建售后工单
# ──────────────────────────────────────────────────

CREATE_TICKET_TOOL = {
    "type": "function",
    "function": {
        "name": "create_ticket",
        "description": (
            "为用户创建售后工单（退换货/维修/投诉）。"
            "使用前提：用户明确表达了售后诉求，且已经确认了订单号和问题描述。"
            "注意：创建工单是写入操作，不可撤销，务必在调用前与用户确认关键信息。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "关联的订单号",
                },
                "ticket_type": {
                    "type": "string",
                    "enum": ["refund", "exchange", "repair", "complaint"],
                    "description": "工单类型：退款/换货/维修/投诉",
                },
                "reason": {
                    "type": "string",
                    "description": "问题描述，用户原话或摘要",
                },
            },
            "required": ["order_id", "ticket_type", "reason"],
        },
    },
}

# ──────────────────────────────────────────────────
# 工具 5：取消订单（高风险 — 需要二次确认）
# ──────────────────────────────────────────────────

CANCEL_ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "cancel_order",
        "description": (
            "取消指定的订单。⚠️ 高风险操作！调用前必须满足以下条件：\n"
            "1. 用户明确表示要取消订单\n"
            "2. 已经告知用户该操作不可撤销\n"
            "3. 已确认订单当前状态允许取消（未发货/未处理）\n"
            "4. 用户再次确认后才可以真正执行\n"
            "如果不满足以上任一条件，不要调用此工具，改为向用户说明情况并请求确认。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "要取消的订单号",
                },
                "reason": {
                    "type": "string",
                    "description": "取消原因（用于记录和后续分析）",
                },
                "user_confirmed": {
                    "type": "boolean",
                    "description": (
                        "用户是否已经明确二次确认。"
                        "必须为 true 才执行取消，false 时不执行只提示。"
                    ),
                },
            },
            "required": ["order_id", "reason", "user_confirmed"],
        },
    },
}

# ──────────────────────────────────────────────────
# 工具 6：搜索 FAQ
# ──────────────────────────────────────────────────

SEARCH_FAQ_TOOL = {
    "type": "function",
    "function": {
        "name": "search_faq",
        "description": (
            "搜索常见问题库（FAQ）。用于回答'怎么修改地址''支持哪些支付方式'"
            "'会员等级怎么升级'等标准问题。FAQ 覆盖账户、支付、配送、会员等通用话题。"
            "注意：FAQ 不包含实时订单状态和个性化退款政策，那种情况用对应专用工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用户的原始问题",
                },
                "category": {
                    "type": "string",
                    "enum": ["account", "payment", "delivery", "membership", "general"],
                    "description": "可选的问题分类，用于缩小匹配范围",
                },
            },
            "required": ["query"],
        },
    },
}

# ──────────────────────────────────────────────────
# 工具注册表：所有工具统一管理
# ──────────────────────────────────────────────────

TOOL_REGISTRY = [
    QUERY_ORDER_TOOL,
    QUERY_LOGISTICS_TOOL,
    SEARCH_REFUND_POLICY_TOOL,
    CREATE_TICKET_TOOL,
    CANCEL_ORDER_TOOL,
    SEARCH_FAQ_TOOL,
]

# ──────────────────────────────────────────────────
# 风险等级分类（用于权限控制）
# ──────────────────────────────────────────────────

TOOL_RISK_LEVELS = {
    "query_order":            "read",      # 只读
    "query_logistics":        "read",      # 只读
    "search_refund_policy":   "read",      # 只读
    "search_faq":             "read",      # 只读
    "create_ticket":          "write",     # 写入
    "cancel_order":           "high_risk", # 高风险
}

# ──────────────────────────────────────────────────
# 使用示例（项目3 会用到）
# ──────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("工具定义模板 — 验证")
    print("=" * 60)

    for tool in TOOL_REGISTRY:
        name = tool["function"]["name"]
        risk = TOOL_RISK_LEVELS.get(name, "unknown")
        required = tool["function"]["parameters"].get("required", [])
        print(f"\n🔧 {name}")
        print(f"   风险等级: {risk}")
        print(f"   必填参数: {required}")

    print(f"\n✅ 共注册 {len(TOOL_REGISTRY)} 个工具\n")

    # 演示：把工具列表传给 API 的格式
    # response = client.chat.completions.create(
    #     model="qwen-max",
    #     messages=[...],
    #     tools=TOOL_REGISTRY,          # <-- 就是这里
    #     tool_choice="auto",
    # )
