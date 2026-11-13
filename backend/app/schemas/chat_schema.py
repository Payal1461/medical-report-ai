from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    report_id: int
    message: str = Field(min_length=1, max_length=1000)
    search_all_reports: bool = False


class ChatSource(BaseModel):
    report_id: int
    report_name: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource] = []
