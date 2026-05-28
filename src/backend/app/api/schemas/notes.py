from typing import Optional
from pydantic import BaseModel


class CreateNoteRequest(BaseModel):
    paperId: str
    title: Optional[str] = None
    contentHtml: Optional[str] = None
    contentFormat: Optional[str] = "html"


class UpdateNoteRequest(BaseModel):
    title: Optional[str] = None
    contentHtml: Optional[str] = None
    contentFormat: Optional[str] = None
