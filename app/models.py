from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    filename: str
    heading: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


@dataclass
class OrderResult:
    found: bool
    order_id: str
    status: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    estimated_delivery: str | None = None
    message: str | None = None
    error: str | None = None


@dataclass
class ToolCallRecord:
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass
class AgentResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    human_handoff: bool = False
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)