"""
数据库模型包。

这里放 SQLAlchemy 模型，也就是“数据在数据库里怎么存”。
如果一段代码定义的是表、字段、外键、关系，应优先放在这里。

为了减少调用方的导入复杂度，这个入口统一导出当前项目常用的模型类。
"""

# 制度知识库主档与版本模型
from app.models.policy_document import PolicyDocument
from app.models.policy_version import PolicyVersion

# 制度正文与检索内容模型
from app.models.policy_section import PolicySection
from app.models.policy_chunk import PolicyChunk
from app.models.policy_block import PolicyBlock

__all__ = [
    "PolicyDocument",
    "PolicyVersion",
    "PolicySection",
    "PolicyChunk",
    "PolicyBlock",
]
