"""
Session management API endpoints.
"""
import torch
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.models import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionStateResponse,
    SetPromptRequest,
    SetPromptResponse,
    NextTokenProbsResponse,
    AppendTokenRequest,
    AppendTokenResponse,
    UndoTokenResponse,
    DeleteSessionResponse,
    TokenData,
    OtherCategoryInfo,
    AppendedTokenInfo,
    OtherCategorySelectionInfo,
    TokenHistoryItem,
)
from app.utils.session_manager import session_manager, TokenInfo
from app.utils.model_loader import load_model, MODEL_IDS

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse, status_code=201)
async def create_session(request: CreateSessionRequest):
    """Create a new session for a student with isolated state."""
    # Validate model name
    if request.model_name not in MODEL_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name. Available models: {list(MODEL_IDS.keys())}",
        )

    # Try to load the model to ensure it's available
    try:
        load_model(request.model_name)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model failed to load: {str(e)}")

    # Create session
    session = session_manager.create_session(model_name=request.model_name)

    return CreateSessionResponse(
        session_id=session.session_id,
        model_name=session.model_name,
        created_at=session.created_at.isoformat() + "Z",
    )


@router.get("/{session_id}", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Retrieve current state of a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")

    return SessionStateResponse(**session.to_dict())


@router.post("/{session_id}/set-prompt", response_model=SetPromptResponse)
async def set_prompt(session_id: str, request: SetPromptRequest):
    """Set or reset the initial prompt for the session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Empty or invalid prompt")

    # Get tokenizer to count tokens
    _, tokenizer = load_model(session.model_name)
    tokens = tokenizer.encode(request.prompt)

    # Set the prompt
    session.set_prompt(request.prompt)

    return SetPromptResponse(
        session_id=session.session_id,
        current_text=session.current_text,
        token_count=len(tokens),
        message="Prompt set successfully",
    )


@router.get("/{session_id}/next-token-probs", response_model=NextTokenProbsResponse)
async def get_next_token_probs(
    session_id: str,
    threshold: float = 0.01,
    other_top_k: int = 10,
    temperature: float = 1.0,
):
    """
    Returns probability distribution for the next token using dynamic threshold filtering.
    This is the core endpoint for the probability wheel visualization.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")

    if not session.initial_prompt:
        raise HTTPException(status_code=400, detail="No prompt set yet")

    # Validate parameters
    if not 0.0 <= threshold <= 1.0:
        raise HTTPException(status_code=400, detail="Threshold must be between 0.0 and 1.0")

    if temperature <= 0:
        raise HTTPException(status_code=400, detail="Temperature must be greater than 0")

    # Load model and tokenizer
    model, tokenizer = load_model(session.model_name)

    # Get current text
    current_text = session.current_text

    # Tokenize input
    inputs = tokenizer(current_text, return_tensors="pt")

    # Get model predictions
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[:, -1, :]  # Last token logits

    # Apply temperature
    logits = logits / temperature

    # Apply softmax to get probabilities
    probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]

    # Get log probabilities
    log_probs = torch.nn.functional.log_softmax(logits, dim=-1)[0]

    # Filter by threshold
    above_threshold_mask = probabilities >= threshold
    above_threshold_indices = torch.where(above_threshold_mask)[0]
    above_threshold_probs = probabilities[above_threshold_indices]

    # Sort above threshold tokens by probability (descending)
    sorted_indices = torch.argsort(above_threshold_probs, descending=True)
    above_threshold_indices = above_threshold_indices[sorted_indices]
    above_threshold_probs = above_threshold_probs[sorted_indices]

    # Create above threshold tokens list
    above_threshold_tokens = []
    for idx, prob in zip(above_threshold_indices, above_threshold_probs):
        token_id = int(idx)
        token_text = tokenizer.decode([token_id])
        above_threshold_tokens.append(
            TokenData(
                token_id=token_id,
                token_text=token_text,
                probability=float(prob),
                log_probability=float(log_probs[idx]),
            )
        )

    # Get "Other" category
    below_threshold_mask = ~above_threshold_mask
    below_threshold_indices = torch.where(below_threshold_mask)[0]
    below_threshold_probs = probabilities[below_threshold_indices]

    other_total_prob = float(below_threshold_probs.sum())
    other_token_count = len(below_threshold_indices)

    # Get sample tokens from "Other" category
    sample_indices = torch.argsort(below_threshold_probs, descending=True)[:other_top_k]
    sample_tokens = []
    for idx in sample_indices:
        token_idx = below_threshold_indices[idx]
        token_id = int(token_idx)
        token_text = tokenizer.decode([token_id])
        sample_tokens.append(
            TokenData(
                token_id=token_id,
                token_text=token_text,
                probability=float(probabilities[token_idx]),
                log_probability=float(log_probs[token_idx]),
            )
        )

    # Calculate total above threshold probability
    total_above_threshold_prob = float(above_threshold_probs.sum())

    return NextTokenProbsResponse(
        session_id=session.session_id,
        current_text=current_text,
        threshold=threshold,
        temperature=temperature,
        above_threshold_tokens=above_threshold_tokens,
        other_category=OtherCategoryInfo(
            total_probability=other_total_prob,
            token_count=other_token_count,
            sample_tokens=sample_tokens,
        ),
        total_above_threshold_probability=total_above_threshold_prob,
        vocabulary_size=len(probabilities),
    )


@router.post("/{session_id}/append-token", response_model=AppendTokenResponse)
async def append_token(session_id: str, request: AppendTokenRequest):
    """
    Appends a selected token to the conversation context.
    Handles both explicit token selection and "Other" category selection with backend sampling.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")

    if not session.initial_prompt:
        raise HTTPException(status_code=400, detail="No prompt set")

    # Load model and tokenizer
    model, tokenizer = load_model(session.model_name)

    # Get current probabilities
    current_text = session.current_text
    inputs = tokenizer(current_text, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[:, -1, :]

    probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]

    previous_text = current_text
    other_category_info = None

    # Handle "Other" category selection
    if request.category == "other":
        # Sample from below threshold tokens
        threshold = 0.01  # Use default threshold
        below_threshold_mask = probabilities < threshold
        below_threshold_probs = probabilities[below_threshold_mask]
        below_threshold_indices = torch.where(below_threshold_mask)[0]

        if len(below_threshold_probs) == 0:
            raise HTTPException(
                status_code=400, detail="No tokens available in 'Other' category"
            )

        # Renormalize probabilities
        renormalized_probs = below_threshold_probs / below_threshold_probs.sum()

        # Sample from the distribution
        sampled_idx = torch.multinomial(renormalized_probs, num_samples=1)
        token_idx = below_threshold_indices[sampled_idx]
        token_id = int(token_idx)
        token_text = tokenizer.decode([token_id])
        probability = float(probabilities[token_idx])

        # Find rank of selected token
        sorted_indices = torch.argsort(probabilities, descending=True)
        rank = int((sorted_indices == token_idx).nonzero()[0]) + 1

        # Create token info
        token_info = TokenInfo(
            token_id=token_id,
            token_text=token_text,
            probability=probability,
            category="other",
            sampled_from_other=True,
        )

        other_category_info = OtherCategorySelectionInfo(
            total_probability=float(below_threshold_probs.sum()),
            token_count=len(below_threshold_indices),
            selected_token_rank=rank,
        )

    else:
        # Explicit token selection
        if request.token_id is not None:
            token_id = request.token_id
            token_text = tokenizer.decode([token_id])
        elif request.token_text is not None:
            token_text = request.token_text
            # Find token_id from text
            token_ids = tokenizer.encode(token_text, add_special_tokens=False)
            if len(token_ids) != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Token text must correspond to exactly one token",
                )
            token_id = token_ids[0]
        else:
            raise HTTPException(
                status_code=400,
                detail="Either token_id or token_text must be provided",
            )

        probability = float(probabilities[token_id])

        # Determine category
        threshold = 0.01
        category = "above_threshold" if probability >= threshold else "other"

        token_info = TokenInfo(
            token_id=token_id,
            token_text=token_text,
            probability=probability,
            category=category,
            sampled_from_other=False,
        )

    # Append token to session
    session.append_token(token_info)

    # Build response
    response_data = {
        "session_id": session.session_id,
        "previous_text": previous_text,
        "appended_token": AppendedTokenInfo(**token_info.to_dict()),
        "current_text": session.current_text,
        "token_history": [TokenHistoryItem(**t.to_dict()) for t in session.token_history],
    }

    if other_category_info:
        response_data["other_category_info"] = other_category_info

    return AppendTokenResponse(**response_data)


@router.post("/{session_id}/undo", response_model=UndoTokenResponse)
async def undo_last_token(session_id: str):
    """
    Removes the last generated token and reverts to the previous state.
    Does not remove tokens from the initial prompt.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")

    previous_text = session.current_text
    removed_token = session.undo_last_token()

    if removed_token is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot undo. No generated tokens to remove. Only initial prompt remains.",
        )

    return UndoTokenResponse(
        session_id=session.session_id,
        previous_text=previous_text,
        removed_token=AppendedTokenInfo(**removed_token.to_dict()),
        current_text=session.current_text,
        token_history=[TokenHistoryItem(**t.to_dict()) for t in session.token_history],
        message="Last token removed successfully",
    )


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str):
    """Deletes a session and cleans up resources."""
    deleted = session_manager.delete_session(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Session does not exist")

    return DeleteSessionResponse(
        message="Session deleted successfully",
        session_id=session_id,
    )
