"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, ConfigDict, Field


# Request Models
class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    model_config = ConfigDict(protected_namespaces=())

    model_name: str = Field(default="gpt2", description="Model to use for this session")


class SetPromptRequest(BaseModel):
    """Request to set the initial prompt."""

    prompt: str = Field(..., min_length=1, description="Initial text prompt")


class AppendTokenRequest(BaseModel):
    """Request to append a token to the conversation."""

    token_id: int | None = Field(None, description="Token ID to append")
    token_text: str | None = Field(None, description="Token text to append")
    category: str | None = Field(
        None, description="Set to 'other' for backend sampling"
    )


# Response Models
class TokenData(BaseModel):
    """Information about a token."""

    token_id: int
    token_text: str
    probability: float
    log_probability: float | None = None


class TokenHistoryItem(BaseModel):
    """Historical token selection."""

    token_id: int
    token_text: str
    probability: float
    category: str
    selected_at: str
    sampled_from_other: bool | None = None


class OtherCategoryInfo(BaseModel):
    """Information about the 'Other' category."""

    total_probability: float
    token_count: int
    sample_tokens: list[TokenData]


class OtherCategorySelectionInfo(BaseModel):
    """Information about a token selected from 'Other' category."""

    total_probability: float
    token_count: int
    selected_token_rank: int


class CreateSessionResponse(BaseModel):
    """Response from creating a session."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    model_name: str
    created_at: str


class SessionStateResponse(BaseModel):
    """Current state of a session."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    model_name: str
    initial_prompt: str
    current_text: str
    token_history: list[TokenHistoryItem]
    generation_count: int
    created_at: str
    last_accessed: str


class SetPromptResponse(BaseModel):
    """Response from setting a prompt."""

    session_id: str
    current_text: str
    token_count: int
    message: str


class NextTokenProbsResponse(BaseModel):
    """Response with next token probabilities."""

    session_id: str
    current_text: str
    threshold: float
    temperature: float
    above_threshold_tokens: list[TokenData]
    other_category: OtherCategoryInfo
    total_above_threshold_probability: float
    vocabulary_size: int


class AppendedTokenInfo(BaseModel):
    """Information about the appended token."""

    token_id: int
    token_text: str
    probability: float
    category: str
    sampled_from_other: bool | None = None


class AppendTokenResponse(BaseModel):
    """Response from appending a token."""

    session_id: str
    previous_text: str
    appended_token: AppendedTokenInfo
    current_text: str
    token_history: list[TokenHistoryItem]
    other_category_info: OtherCategorySelectionInfo | None = None


class UndoTokenResponse(BaseModel):
    """Response from undoing a token."""

    session_id: str
    previous_text: str
    removed_token: AppendedTokenInfo
    current_text: str
    token_history: list[TokenHistoryItem]
    message: str


class DeleteSessionResponse(BaseModel):
    """Response from deleting a session."""

    message: str
    session_id: str


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    name: str
    description: str
    parameters: str
    default: bool


class ModelsResponse(BaseModel):
    """Response with available models."""

    models: list[ModelInfo]


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    timestamp: str


class ReadyResponse(BaseModel):
    """Readiness check response."""

    status: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    message: str
    current_text: str | None = None
