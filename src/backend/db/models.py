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
    pdf_path = Column(String(1024), nullable=True)
    md5_hash = Column(String(64), unique=True, nullable=True)
    file_size = Column(Integer, nullable=True)
    user_id = Column(String(64), ForeignKey("user.id"), nullable=False)
    folder_id = Column(String(64), ForeignKey("folder.id"), nullable=True)
    status = Column(SAEnum(PaperStatus), nullable=False, server_default=PaperStatus.PENDING_PARSING.value)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="papers")
    key_points = relationship("KeyPoints", uselist=False, back_populates="paper")
    folder = relationship("Folder", back_populates="papers")
    tags = relationship("Tag", secondary=paper_tag, back_populates="papers")


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
