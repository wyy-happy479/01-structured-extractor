"""
Pydantic Schema 定义：简历、合同、商品描述三种输入类型的结构化输出格式。

每个字段都有一个对应的 `_confidence` 字段（0.0~1.0），
表示模型对自己提取结果的置信度。
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── 简历 ──────────────────────────────────────────

class Resume(BaseModel):
    """简历信息抽取结果"""
    name: str = Field(default="", description="姓名")
    name_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="姓名提取置信度")

    education: str = Field(default="", description="最高学历，如：本科/硕士/博士")
    education_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="学历提取置信度")

    school: str = Field(default="", description="毕业院校")
    school_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="院校提取置信度")

    major: str = Field(default="", description="专业")
    major_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="专业提取置信度")

    skills: list[str] = Field(default_factory=list, description="技能列表")
    skills_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="技能提取置信度")

    years_of_experience: Optional[int] = Field(default=None, description="工作年限")
    years_of_experience_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="工作年限提取置信度")

    email: str = Field(default="", description="电子邮箱")
    email_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="邮箱提取置信度")

    phone: str = Field(default="", description="电话号码")
    phone_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="电话提取置信度")

    summary: str = Field(default="", description="一句话总结候选人背景")
    summary_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="总结置信度")


# ── 合同 ──────────────────────────────────────────

class Contract(BaseModel):
    """合同关键信息抽取结果"""
    party_a: str = Field(default="", description="甲方（第一方）")
    party_a_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    party_b: str = Field(default="", description="乙方（第二方）")
    party_b_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    contract_type: str = Field(default="", description="合同类型，如：劳动合同/采购合同/租赁合同")
    contract_type_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    amount: Optional[float] = Field(default=None, description="合同金额（元）")
    amount_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    start_date: str = Field(default="", description="合同开始日期，格式 YYYY-MM-DD")
    start_date_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    end_date: str = Field(default="", description="合同结束日期，格式 YYYY-MM-DD")
    end_date_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    key_terms: list[str] = Field(default_factory=list, description="关键条款摘要列表")
    key_terms_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    governing_law: str = Field(default="", description="适用法律/管辖地")
    governing_law_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ── 商品描述 ──────────────────────────────────────

class Product(BaseModel):
    """商品描述信息抽取结果"""
    product_name: str = Field(default="", description="商品名称")
    product_name_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    category: str = Field(default="", description="商品类别，如：电子产品/服装/食品")
    category_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    brand: str = Field(default="", description="品牌")
    brand_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    price: Optional[float] = Field(default=None, description="价格（元）")
    price_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    specifications: dict[str, str] = Field(default_factory=dict, description="规格参数，如：{\"尺寸\": \"15.6英寸\", \"重量\": \"1.8kg\"}")
    specifications_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    features: list[str] = Field(default_factory=list, description="商品特色/卖点列表")
    features_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    suitable_for: str = Field(default="", description="适用人群/场景")
    suitable_for_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Schema 注册表 ─────────────────────────────────

SCHEMA_MAP = {
    "resume": Resume,
    "contract": Contract,
    "product": Product,
}
