# AI Token Wheel - Backend API Design

## Overview

This document describes the FastAPI backend architecture for the AI Token Wheel
educational application. The app helps students visualize how Large Language
Models (LLMs) probabilistically sample the next token from a distribution
rather than deterministically choosing it.

## Technology Stack

- **Backend Framework**: FastAPI (Python)
- **ML Framework**: HuggingFace Transformers
- **Model**: GPT-2 (initially, extensible to other models)
- **Inference**: Local model inference (no API costs)
- **Session Management**: In-memory storage (Redis optional for production)

## Core Concepts

### Dynamic Threshold Filtering

Instead of returning a fixed top-k tokens, the API uses a **dynamic threshold** approach:

- Returns all tokens with probability ≥ threshold (default: 1%)
- Groups remaining tokens into an "Other" category
- When "Other" is selected, backend randomly samples from below-threshold tokens
- Shows sample tokens from "Other" for educational purposes

**Benefits:**

- Guarantees visible wheel segments (threshold ensures minimum size)
- Demonstrates probability distribution's long tail
- Shows students that 50,000+ tokens exist below threshold
- Allows rare tokens to still be selected (via "Other" category)

### Session Management

Each student session maintains:

- Unique session ID (UUID)
- Current conversation context (prompt + generated tokens)
- Token generation history with metadata
- Model selection
- Creation and last access timestamps

Sessions are isolated, allowing multiple concurrent users.

## API Endpoints

### Base URL

```text
http://localhost:8000/api
```

### Endpoint Summary

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| POST | `/sessions` | Create new session |
| GET | `/sessions/{session_id}` | Get session state |
| POST | `/sessions/{session_id}/set-prompt` | Set/reset prompt |
| GET | `/sessions/{session_id}/next-token-probs` | Get token probabilities |
| POST | `/sessions/{session_id}/append-token` | Append selected token |
| POST | `/sessions/{session_id}/undo` | Undo last token |
| DELETE | `/sessions/{session_id}` | Delete session |
| GET | `/models` | List available models |

---

## Detailed Endpoint Specifications

### 1. Create Session

**Endpoint:** `POST /api/sessions`

**Description:** Creates a new session for a student with isolated state.

**Request Body:**

```json
{
  "model_name": "gpt2"
}
```

**Parameters:**

- `model_name` (optional, default: "gpt2"): Model to use for this session

**Response:** `201 Created`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_name": "gpt2",
  "created_at": "2025-12-11T10:30:00Z"
}
```

**Error Responses:**

- `400 Bad Request`: Invalid model name
- `503 Service Unavailable`: Model failed to load

---

### 2. Get Session State

**Endpoint:** `GET /api/sessions/{session_id}`

**Description:** Retrieves current state of a session.

**Response:** `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "model_name": "gpt2",
  "initial_prompt": "The cat sat on the",
  "current_text": "The cat sat on the mat",
  "token_history": [
    {
      "token_id": 2214,
      "token_text": " mat",
      "probability": 0.18,
      "category": "above_threshold",
      "selected_at": "2025-12-11T10:31:15Z"
    }
  ],
  "generation_count": 1,
  "created_at": "2025-12-11T10:30:00Z",
  "last_accessed": "2025-12-11T10:31:15Z"
}
```

**Error Responses:**

- `404 Not Found`: Session does not exist

---

### 3. Set Prompt

**Endpoint:** `POST /api/sessions/{session_id}/set-prompt`

**Description:** Sets or resets the initial prompt for the session.

**Request Body:**

```json
{
  "prompt": "The cat sat on the"
}
```

**Parameters:**

- `prompt` (required): Initial text prompt

**Response:** `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_text": "The cat sat on the",
  "token_count": 4,
  "message": "Prompt set successfully"
}
```

**Error Responses:**

- `404 Not Found`: Session does not exist
- `400 Bad Request`: Empty or invalid prompt

---

### 4. Get Next Token Probabilities

**Endpoint:** `GET /api/sessions/{session_id}/next-token-probs`

**Description:** Returns probability distribution for the next token using
dynamic threshold filtering. This is the core endpoint for the probability
wheel visualization.

**Query Parameters:**

- `threshold` (optional, default: 0.01): Minimum probability threshold
  (range: 0.0 to 1.0)
- `other_top_k` (optional, default: 10): Number of sample tokens to show
  from "Other" category
- `temperature` (optional, default: 1.0): Temperature for probability
  adjustment

**Response:** `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_text": "The cat sat on the",
  "threshold": 0.01,
  "temperature": 1.0,
  "above_threshold_tokens": [
    {
      "token_id": 2214,
      "token_text": " mat",
      "probability": 0.18,
      "log_probability": -1.71
    },
    {
      "token_id": 4675,
      "token_text": " floor",
      "probability": 0.12,
      "log_probability": -2.12
    },
    {
      "token_id": 3038,
      "token_text": " table",
      "probability": 0.09,
      "log_probability": -2.41
    },
    {
      "token_id": 2166,
      "token_text": " bed",
      "probability": 0.05,
      "log_probability": -2.99
    },
    {
      "token_id": 5118,
      "token_text": " couch",
      "probability": 0.03,
      "log_probability": -3.51
    }
  ],
  "other_category": {
    "total_probability": 0.53,
    "token_count": 50251,
    "sample_tokens": [
      {
        "token_id": 8421,
        "token_text": " roof",
        "probability": 0.008,
        "log_probability": -4.83
      },
      {
        "token_id": 2166,
        "token_text": " chair",
        "probability": 0.007,
        "log_probability": -4.96
      },
      {
        "token_id": 9414,
        "token_text": " windowsill",
        "probability": 0.003,
        "log_probability": -5.81
      }
    ]
  },
  "total_above_threshold_probability": 0.47,
  "vocabulary_size": 50257
}
```

**Response Fields:**

- `above_threshold_tokens`: All tokens with probability ≥ threshold
- `other_category.total_probability`: Combined probability of all
  below-threshold tokens
- `other_category.token_count`: Number of tokens below threshold
  (educational!)
- `other_category.sample_tokens`: Top-k tokens from "Other" to show low
  probabilities
- `total_above_threshold_probability`: Sum of visible token probabilities

**Frontend Use:**

The wheel visualization should create:

1. One segment per token in `above_threshold_tokens` (sized by probability)
2. One "Other" segment (sized by `other_category.total_probability`)

**Error Responses:**

- `404 Not Found`: Session does not exist
- `400 Bad Request`: No prompt set yet or invalid parameters

---

### 5. Append Token

**Endpoint:** `POST /api/sessions/{session_id}/append-token`

**Description:** Appends a selected token to the conversation context. Handles
both explicit token selection and "Other" category selection with backend
sampling.

**Request Body (Explicit Token):**

```json
{
  "token_id": 2214,
  "token_text": " mat"
}
```

**Request Body (Other Category):**

```json
{
  "category": "other"
}
```

**Parameters:**

- `token_id` (optional): Token ID to append
- `token_text` (optional): Token text to append (alternative to token_id)
- `category` (optional): Set to "other" for backend sampling from
  below-threshold tokens

**Response (Normal Token):** `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_text": "The cat sat on the",
  "appended_token": {
    "token_id": 2214,
    "token_text": " mat",
    "probability": 0.18,
    "category": "above_threshold"
  },
  "current_text": "The cat sat on the mat",
  "token_history": [
    {
      "token_id": 2214,
      "token_text": " mat",
      "probability": 0.18,
      "category": "above_threshold",
      "selected_at": "2025-12-11T10:31:15Z"
    }
  ]
}
```

**Response (Other Category):** `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_text": "The cat sat on the",
  "appended_token": {
    "token_id": 9414,
    "token_text": " windowsill",
    "probability": 0.003,
    "category": "other",
    "sampled_from_other": true
  },
  "current_text": "The cat sat on the windowsill",
  "other_category_info": {
    "total_probability": 0.53,
    "token_count": 50251,
    "selected_token_rank": 43
  },
  "token_history": [
    {
      "token_id": 9414,
      "token_text": " windowsill",
      "probability": 0.003,
      "category": "other",
      "sampled_from_other": true,
      "selected_at": "2025-12-11T10:31:15Z"
    }
  ]
}
```

**Backend Logic for "Other" Selection:**

```python
# 1. Get all tokens below threshold with their probabilities
below_threshold_mask = probabilities < threshold
below_threshold_probs = probabilities[below_threshold_mask]

# 2. Renormalize probabilities (so they sum to 1.0 within "Other")
renormalized_probs = below_threshold_probs / below_threshold_probs.sum()

# 3. Sample from the distribution
sampled_token_idx = torch.multinomial(renormalized_probs, num_samples=1)
```

**Error Responses:**

- `404 Not Found`: Session does not exist
- `400 Bad Request`: Invalid token_id or no prompt set

---

### 6. Undo Last Token

**Endpoint:** `POST /api/sessions/{session_id}/undo`

**Description:** Removes the last generated token and reverts to the previous
state. Does not remove tokens from the initial prompt.

**Request Body:** None

**Response:** `200 OK`

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_text": "The cat sat on the mat",
  "removed_token": {
    "token_id": 2214,
    "token_text": " mat",
    "probability": 0.18,
    "category": "above_threshold"
  },
  "current_text": "The cat sat on the",
  "token_history": [],
  "message": "Last token removed successfully"
}
```

**Error Responses:**

- `404 Not Found`: Session does not exist
- `400 Bad Request`: No generated tokens to remove (only initial prompt
  remains)

```json
{
  "error": "Cannot undo",
  "message": "No generated tokens to remove. Only initial prompt remains.",
  "current_text": "The cat sat on the"
}
```

---

### 7. Delete Session

**Endpoint:** `DELETE /api/sessions/{session_id}`

**Description:** Deletes a session and cleans up resources.

**Response:** `200 OK`

```json
{
  "message": "Session deleted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

- `404 Not Found`: Session does not exist

---

### 8. List Available Models

**Endpoint:** `GET /api/models`

**Description:** Returns list of available models for session creation.

**Response:** `200 OK`

```json
{
  "models": [
    {
      "id": "gpt2",
      "name": "GPT-2 (124M)",
      "description": "Base GPT-2 model with 124M parameters",
      "parameters": "124M",
      "default": true
    },
    {
      "id": "gpt2-medium",
      "name": "GPT-2 Medium (355M)",
      "description": "Medium-sized GPT-2 model",
      "parameters": "355M",
      "default": false
    },
    {
      "id": "gpt2-large",
      "name": "GPT-2 Large (774M)",
      "description": "Large GPT-2 model",
      "parameters": "774M",
      "default": false
    }
  ]
}
```

---

## Design Decisions

### Why Dynamic Threshold?

1. **Guaranteed Visibility**: Ensures all wheel segments are visible
   (minimum 1% by default)
2. **Educational Value**: Shows the long tail of probability distribution
3. **Flexible Control**: Threshold can be adjusted for different lesson plans
4. **Realistic Sampling**: Still allows rare tokens to be selected via "Other"

### Why Backend Sampling for "Other"?

1. **Simplicity**: Frontend doesn't need to handle 50,000+ tokens
2. **Performance**: Reduces payload size dramatically
3. **Security**: Token sampling logic stays on backend
4. **Accuracy**: Ensures proper probability-weighted sampling

### Session Management Strategy

- **In-Memory Storage**: Fast access, simple implementation
- **TTL (Time-To-Live)**: Auto-cleanup of inactive sessions (1 hour)
- **Stateful Sessions**: Each session maintains full context
- **Concurrent Safe**: Each session is independent

### Temperature Parameter

Temperature adjusts the probability distribution:

- **T = 1.0** (default): True model probabilities
- **T > 1.0**: Flattened distribution (more random)
- **T < 1.0**: Sharpened distribution (more deterministic)

Formula: `probabilities = softmax(logits / temperature)`

---

## Educational Benefits

This API design provides excellent pedagogical value:

### 1. Visualizes Probability Distribution

Students see:

- A small number of high-probability tokens (5-10 tokens covering ~50% probability)
- A large "Other" category containing 50,000+ tokens
- The long tail nature of language model distributions

### 2. Demonstrates Sampling vs. Argmax

Students learn the difference between:

- **Argmax**: Always pick the highest probability token (deterministic)
- **Sampling**: Randomly select based on probabilities (probabilistic)

### 3. Shows Rare Events

When "Other" is selected and generates an unexpected token:

- Teaches that low-probability events can still occur
- Demonstrates the difference between probability and possibility
- Shows the model's creativity/diversity

### 4. Configurable Difficulty

Instructors can adjust threshold to modify lesson complexity:

- **High threshold (0.05)**: More uniform wheel, frequent "Other" selections
- **Low threshold (0.001)**: Fewer tokens in "Other", more predictable

### 5. Interactive Learning

The undo feature allows students to:

- Experiment with different choices
- See how different tokens lead to different continuations
- Learn through trial and error

---

## Example User Flow

### Scenario: Student generates text from "The cat sat on the"

1. **Create Session**

   ```http
   POST /api/sessions
   → Returns session_id: "abc-123"
   ```

2. **Set Initial Prompt**

   ```http
   POST /api/sessions/abc-123/set-prompt
   Body: {"prompt": "The cat sat on the"}
   ```

3. **Get Token Probabilities**

   ```http
   GET /api/sessions/abc-123/next-token-probs?threshold=0.01
   → Returns:
     - " mat" (18%)
     - " floor" (12%)
     - " table" (9%)
     - " bed" (5%)
     - " couch" (3%)
     - "Other" (53%, containing 50,251 tokens)
   ```

4. **Spin Wheel → Lands on "Other"**

   ```http
   POST /api/sessions/abc-123/append-token
   Body: {"category": "other"}
   → Backend samples: " windowsill" (0.3%)
   → Returns: "The cat sat on the windowsill"
   ```

5. **Student Thinks "That's Weird!" → Undo**

   ```http
   POST /api/sessions/abc-123/undo
   → Returns: "The cat sat on the"
   ```

6. **Get Probabilities Again (Same Distribution)**

   ```http
   GET /api/sessions/abc-123/next-token-probs?threshold=0.01
   → Returns same distribution as step 3
   ```

7. **Spin Wheel → Lands on " mat"**

   ```http
   POST /api/sessions/abc-123/append-token
   Body: {"token_id": 2214, "token_text": " mat"}
   → Returns: "The cat sat on the mat"
   ```

8. **Continue Generating...**

9. **Done → Clean Up**

   ```http
   DELETE /api/sessions/abc-123
   ```

---

## Implementation Notes

### HuggingFace Transformers Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load model once at startup
model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2")
tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
model.eval()  # Set to evaluation mode

# Get token probabilities
def get_next_token_probabilities(text, threshold=0.01):
    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[:, -1, :]  # Last token logits

    # Apply softmax to get probabilities
    probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]

    # Filter by threshold
    above_threshold_mask = probabilities >= threshold
    above_threshold_tokens = torch.where(above_threshold_mask)[0]
    above_threshold_probs = probabilities[above_threshold_tokens]

    # Get "Other" category
    below_threshold_mask = ~above_threshold_mask
    other_total_prob = probabilities[below_threshold_mask].sum().item()

    return {
        "above_threshold_tokens": above_threshold_tokens,
        "above_threshold_probs": above_threshold_probs,
        "other_total_prob": other_total_prob,
        "vocabulary_size": len(probabilities)
    }
```

### Session Storage

```python
from datetime import datetime, timedelta
from uuid import uuid4

# In-memory session store
sessions = {}

class Session:
    def __init__(self, model_name="gpt2"):
        self.session_id = str(uuid4())
        self.model_name = model_name
        self.initial_prompt = ""
        self.token_history = []
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()

    @property
    def current_text(self):
        text = self.initial_prompt
        for token in self.token_history:
            text += token["token_text"]
        return text

    def is_expired(self, ttl_hours=1):
        expiry = self.last_accessed + timedelta(hours=ttl_hours)
        return datetime.utcnow() > expiry
```

### Background Cleanup Task

```python
import asyncio

async def cleanup_expired_sessions():
    """Background task to remove expired sessions"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes

        expired_sessions = [
            sid for sid, session in sessions.items()
            if session.is_expired()
        ]

        for sid in expired_sessions:
            del sessions[sid]
            print(f"Cleaned up expired session: {sid}")
```

---

## Security Considerations

1. **Rate Limiting**: Implement per-session rate limits to prevent abuse
2. **Input Validation**: Sanitize all user inputs (prompts, token selections)
3. **Session Limits**: Maximum number of concurrent sessions per IP
4. **Timeout**: Auto-delete sessions after inactivity
5. **Resource Limits**: Maximum prompt length, maximum generation length

---

## Future Enhancements

### Potential Additional Endpoints

1. `GET /api/sessions/{session_id}/statistics`

   - Average token probability
   - "Other" selection frequency
   - Generation statistics

2. `POST /api/sessions/{session_id}/fork`

   - Create a new session from current state
   - Allows students to explore different paths

3. `POST /api/sessions/{session_id}/compare`
   - Compare sampling vs. greedy decoding
   - Educational: show both paths side-by-side

### Additional Models

- GPT-Neo (125M, 1.3B, 2.7B)
- GPT-J (6B)
- DistilGPT-2 (smaller, faster)
- Custom fine-tuned models

### Advanced Features

- Adjustable temperature per request
- Nucleus (top-p) sampling option
- Token frequency visualization
- Export generation history (JSON, CSV)

---

## Appendix: HTTP Status Codes

| Code | Meaning | Usage |
| ---- | ------- | ----- |
| 200 | OK | Successful GET, POST, DELETE |
| 201 | Created | Successful session creation |
| 400 | Bad Request | Invalid input, validation error |
| 404 | Not Found | Session does not exist |
| 500 | Internal Server Error | Model error, unexpected failure |
| 503 | Service Unavailable | Model not loaded, server overload |
