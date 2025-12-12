/**
 * TypeScript types for API request/response models
 * Matches the Pydantic models from backend/app/models.py
 */

export interface TokenData {
	token_id: number;
	token_text: string;
	probability: number;
	log_probability?: number;
}

export interface TokenHistoryItem {
	token_id: number;
	token_text: string;
	probability: number;
	category: string;
	selected_at: string;
	sampled_from_other?: boolean;
}

export interface OtherCategoryInfo {
	total_probability: number;
	token_count: number;
	sample_tokens: TokenData[];
}

export interface OtherCategorySelectionInfo {
	total_probability: number;
	token_count: number;
	selected_token_rank: number;
}

export interface ModelInfo {
	id: string;
	name: string;
	description: string;
	parameters: string;
	default: boolean;
}

export interface ModelsResponse {
	models: ModelInfo[];
}

export interface CreateSessionResponse {
	session_id: string;
	model_name: string;
	created_at: string;
}

export interface SessionStateResponse {
	session_id: string;
	model_name: string;
	initial_prompt: string;
	current_text: string;
	token_history: TokenHistoryItem[];
	generation_count: number;
	created_at: string;
	last_accessed: string;
}

export interface SetPromptResponse {
	session_id: string;
	current_text: string;
	token_count: number;
	message: string;
}

export interface NextTokenProbsResponse {
	session_id: string;
	current_text: string;
	threshold: number;
	temperature: number;
	above_threshold_tokens: TokenData[];
	other_category: OtherCategoryInfo;
	total_above_threshold_probability: number;
	vocabulary_size: number;
}

export interface AppendedTokenInfo {
	token_id: number;
	token_text: string;
	probability: number;
	category: string;
	sampled_from_other?: boolean;
}

export interface AppendTokenResponse {
	session_id: string;
	previous_text: string;
	appended_token: AppendedTokenInfo;
	current_text: string;
	token_history: TokenHistoryItem[];
	other_category_info?: OtherCategorySelectionInfo;
}

export interface UndoTokenResponse {
	session_id: string;
	previous_text: string;
	removed_token: AppendedTokenInfo;
	current_text: string;
	token_history: TokenHistoryItem[];
	message: string;
}

export interface DeleteSessionResponse {
	message: string;
	session_id: string;
}

export interface TokenSelection {
	token_id?: number;
	token_text?: string;
	category?: string;
}
