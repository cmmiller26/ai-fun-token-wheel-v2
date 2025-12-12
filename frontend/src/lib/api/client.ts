/**
 * API client for communicating with the FastAPI backend
 */
import type {
	AppendTokenResponse,
	CreateSessionResponse,
	DeleteSessionResponse,
	ModelsResponse,
	NextTokenProbsResponse,
	SessionStateResponse,
	SetPromptResponse,
	TokenSelection,
	UndoTokenResponse
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIError extends Error {
	statusCode: number;

	constructor(message: string, statusCode: number) {
		super(message);
		this.statusCode = statusCode;
		this.name = 'APIError';
	}
}

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		const error = await response.json().catch(() => ({ message: 'Unknown error' }));
		throw new APIError(error.message || error.detail || 'Request failed', response.status);
	}
	return response.json();
}

export async function fetchModels(): Promise<ModelsResponse> {
	const response = await fetch(`${API_BASE_URL}/api/models`);
	return handleResponse(response);
}

export async function createSession(modelName: string): Promise<CreateSessionResponse> {
	const response = await fetch(`${API_BASE_URL}/api/sessions`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ model_name: modelName })
	});
	return handleResponse(response);
}

export async function setPrompt(sessionId: string, prompt: string): Promise<SetPromptResponse> {
	const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/set-prompt`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ prompt })
	});
	return handleResponse(response);
}

export async function getNextTokenProbs(
	sessionId: string,
	threshold: number = 0.01,
	temperature: number = 1.0
): Promise<NextTokenProbsResponse> {
	const params = new URLSearchParams({
		threshold: threshold.toString(),
		temperature: temperature.toString()
	});
	const response = await fetch(
		`${API_BASE_URL}/api/sessions/${sessionId}/next-token-probs?${params}`
	);
	return handleResponse(response);
}

export async function appendToken(
	sessionId: string,
	selection: TokenSelection
): Promise<AppendTokenResponse> {
	const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/append-token`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(selection)
	});
	return handleResponse(response);
}

export async function undoToken(sessionId: string): Promise<UndoTokenResponse> {
	const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/undo`, {
		method: 'POST'
	});
	return handleResponse(response);
}

export async function deleteSession(sessionId: string): Promise<DeleteSessionResponse> {
	const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
		method: 'DELETE'
	});
	return handleResponse(response);
}

export async function getSessionState(sessionId: string): Promise<SessionStateResponse> {
	const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
	return handleResponse(response);
}
