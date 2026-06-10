import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Table,
    JSON,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import Base


def gen_id():
    return uuid.uuid4().hex


class PaperStatus(enum.Enum):
    PENDING_PARSING = "PENDING_PARSING"
    PARSING = "PARSING"
    PENDING_EXTRACTION = "PENDING_EXTRACTION"
    EXTRACTING = "EXTRACTING"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class TaskType(enum.Enum):
    PDF_PARSE = "PDF_PARSE"
    LLM_EXTRACT = "LLM_EXTRACT"


class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Association table for many-to-many Paper <-> Tag
paper_tag = Table(
    "paper_tag",
    Base.metadata,
    Column("paper_id", String(64), ForeignKey("paper.id"), primary_key=True),
    Column("tag_id", String(64), ForeignKey("tag.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "user"

    id = Column(String(64), primary_key=True, default=gen_id)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Avatar fields: store disk path and a URL path mounted under /uploads
    avatar_path = Column(String(1024), nullable=True)
    avatar_url = Column(String(1024), nullable=True)

    papers = relationship("Paper", back_populates="user")


class Folder(Base):
    __tablename__ = "folder"

    id = Column(String(64), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    user_id = Column(String(64), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User")
    papers = relationship("Paper", back_populates="folder")


class Paper(Base):
    __tablename__ = "paper"

    id = Column(String(64), primary_key=True, default=gen_id)
    title = Column(String(1024), nullable=False)
    authors = Column(Text, nullable=True)
    abstract = Column(Text, nullable=True)
    doi = Column(String(255), unique=True, nullable=True)
    year = Column(Integer, nullable=True)
    source = Column(String(512), nullable=True)  # 论文出处（期刊/会议名称）
    pdf_path = Column(String(1024), nullable=True)
    md5_hash = Column(String(64), nullable=True)
    file_size = Column(Integer, nullable=True)
    full_text = Column(Text, nullable=True)  # PDF 完整文本内容（用于全文搜索）
    user_id = Column(String(64), ForeignKey("user.id"), nullable=False)
    folder_id = Column(String(64), ForeignKey("folder.id"), nullable=True)
    status = Column(SAEnum(PaperStatus), nullable=False, server_default=PaperStatus.PENDING_PARSING.value)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="papers")
    key_points = relationship("KeyPoints", uselist=False, back_populates="paper")
    folder = relationship("Folder", back_populates="papers")
    tags = relationship("Tag", secondary=paper_tag, back_populates="papers")
    embedding_row = relationship("PaperEmbedding", uselist=False, back_populates="paper")

    #联合唯一约束（user_id + md5_hash）
    __table_args__ = (
        UniqueConstraint("user_id", "md5_hash", name="uix_user_md5"),
    )


class PaperEmbedding(Base):
    """论文向量（Embedding API 结果），存 MySQL JSON，与 paper.id 一对一。"""

    __tablename__ = "paper_embedding"

    paper_id = Column(String(64), ForeignKey("paper.id"), primary_key=True)
    embedding = Column(JSON, nullable=False)
    model_name = Column(String(128), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    paper = relationship("Paper", back_populates="embedding_row")


class KeyPoints(Base):
    __tablename__ = "keypoints"

    id = Column(String(64), primary_key=True, default=gen_id)
    paper_id = Column(String(64), ForeignKey("paper.id"), unique=True, nullable=False)
    background = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    innovation = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    is_confirmed = Column(Boolean, nullable=False, server_default="0")
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    paper = relationship("Paper", back_populates="key_points")


class Tag(Base):
    __tablename__ = "tag"

    id = Column(String(64), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)

    papers = relationship("Paper", secondary=paper_tag, back_populates="tags")


class LLMProvider(Base):
    """LLM 提供商配置：支持全局或用户级别的模型配置存储。"""

    __tablename__ = "llm_provider"

    id = Column(String(64), primary_key=True, default=gen_id)
    name = Column(String(128), nullable=False)
    provider = Column(String(64), nullable=False)
    base_url = Column(String(512), nullable=True)
    api_key = Column(String(1024), nullable=True)
    default_model = Column(String(128), nullable=True)
    enabled = Column(Boolean, nullable=False, server_default="1")
    user_id = Column(String(64), ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User")


class Task(Base):
    __tablename__ = "task"

    id = Column(String(64), primary_key=True, default=gen_id)
    type = Column(SAEnum(TaskType), nullable=False)
    status = Column(SAEnum(TaskStatus), nullable=False, server_default=TaskStatus.PENDING.value)
    paper_id = Column(String(64), ForeignKey("paper.id"), nullable=True)
    progress = Column(Integer, nullable=False, server_default="0")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class PaperNote(Base):
    """论文笔记表"""
    __tablename__ = "paper_note"

    id = Column(String(64), primary_key=True, default=gen_id)
    paper_id = Column(String(64), ForeignKey("paper.id"), nullable=False)
    # 兼容旧字段：保留 `content`（可选），推荐使用 `content_html` 存储富文本
    content = Column(Text, nullable=True)
    # 新增富文本与标题字段
    title = Column(String(255), nullable=True)
    content_html = Column(Text, nullable=True)
    content_format = Column(String(20), nullable=False, server_default='html')
    # 抽取的纯文本，用于搜索索引或生成 note_search
    content_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)  # 笔记关联的页码
    selected_text = Column(Text, nullable=True)  # 选中的文本片段
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    paper = relationship("Paper", backref="notes")
    images = relationship("NoteImage", back_populates="note", order_by="NoteImage.order_index")


class NoteImage(Base):
    __tablename__ = 'note_image'

    id = Column(String(64), primary_key=True, default=gen_id)
    note_id = Column(String(64), ForeignKey('paper_note.id'), nullable=False, index=True)
    url = Column(String(1024), nullable=False)
    mime_type = Column(String(50), nullable=True)
    filename = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    note = relationship('PaperNote', back_populates='images')


class NoteSearch(Base):
    __tablename__ = 'note_search'

    note_id = Column(String(64), ForeignKey('paper_note.id'), primary_key=True)
    paper_id = Column(String(64), nullable=False, index=True)
    note_title = Column(String(255), nullable=True)
    paper_title = Column(String(1024), nullable=True)
    content_text = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class GraphNode(Base):
    """自定义图谱节点表"""
    __tablename__ = "graph_node"

    id = Column(String(64), primary_key=True, default=gen_id)
    user_id = Column(String(64), ForeignKey("user.id"), nullable=False, index=True)
    paper_id = Column(String(64), ForeignKey("paper.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False, server_default="custom")
    category = Column(Integer, nullable=False, server_default="0")
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    paper = relationship("Paper")
    outgoing_edges = relationship("GraphEdge", foreign_keys="GraphEdge.source_id", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("GraphEdge", foreign_keys="GraphEdge.target_id", back_populates="target_node", cascade="all, delete-orphan")


class GraphEdge(Base):
    """自定义图谱边表"""
    __tablename__ = "graph_edge"

    id = Column(String(64), primary_key=True, default=gen_id)
    user_id = Column(String(64), ForeignKey("user.id"), nullable=False, index=True)
    source_id = Column(String(64), ForeignKey("graph_node.id"), nullable=False, index=True)
    target_id = Column(String(64), ForeignKey("graph_node.id"), nullable=False, index=True)
    relation_type = Column(String(50), nullable=False, server_default="related")
    label = Column(String(255), nullable=True)
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    source_node = relationship("GraphNode", foreign_keys=[source_id], back_populates="outgoing_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_id], back_populates="incoming_edges")

class GraphLLMCache(Base):
    """存储 LLM 生成的原始图谱结构"""
    __tablename__ = "graph_llm_cache"

    id = Column(String(64), primary_key=True, default=gen_id)
    user_id = Column(String(64), ForeignKey("user.id"), nullable=False, index=True)
    folder_id = Column(String(64), nullable=True, index=True)
    papers_hash = Column(String(64), nullable=False)          # 论文 ID 排序后 MD5
    clusters = Column(JSON, nullable=False)                   # 聚类信息
    nodes = Column(JSON, nullable=False)                      # 原始节点列表（论文节点）
    edges = Column(JSON, nullable=False)                      # 原始边列表（系统边）
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")