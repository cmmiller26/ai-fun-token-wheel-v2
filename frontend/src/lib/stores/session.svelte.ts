/**
 * Global session store using Svelte 5 $state runes
 */

interface TokenData {
	token_id: number;
	token_text: string;
	probability: number;
	log_probability?: number;
}

interface TokenHistoryItem {
	token_id: number;
	token_text: string;
	probability: number;
	category: string;
	selected_at: string;
	sampled_from_other?: boolean;
}

interface OtherCategory {
	total_probability: number;
	token_count: number;
	sample_tokens: TokenData[];
}

export class SessionStore {
	// Session data
	sessionId = $state<string | null>(null);
	modelName = $state<string>('gpt2');
	initialPrompt = $state<string>('');
	currentText = $state<string>('');
	tokenHistory = $state<TokenHistoryItem[]>([]);

	// Wheel data
	aboveThresholdTokens = $state<TokenData[]>([]);
	otherCategory = $state<OtherCategory>({
		total_probability: 0,
		token_count: 0,
		sample_tokens: []
	});

	// UI state
	isLoading = $state<boolean>(false);
	error = $state<string | null>(null);
	isSpinning = $state<boolean>(false);

	// Derived values using $derived
	hasSession = $derived(() => this.sessionId !== null);
	canUndo = $derived(() => this.tokenHistory.length > 0);
	generatedText = $derived(() => {
		if (!this.initialPrompt) return '';
		return this.currentText.substring(this.initialPrompt.length);
	});

	// Methods for updating state
	reset() {
		this.sessionId = null;
		this.modelName = 'gpt2';
		this.initialPrompt = '';
		this.currentText = '';
		this.tokenHistory = [];
		this.aboveThresholdTokens = [];
		this.otherCategory = {
			total_probability: 0,
			token_count: 0,
			sample_tokens: []
		};
		this.error = null;
		this.isLoading = false;
		this.isSpinning = false;
	}

	setSession(data: { session_id: string; model_name: string }) {
		this.sessionId = data.session_id;
		this.modelName = data.model_name;
	}

	setPrompt(prompt: string) {
		this.initialPrompt = prompt;
		this.currentText = prompt;
		this.tokenHistory = [];
	}

	setTokenProbabilities(data: {
		current_text: string;
		above_threshold_tokens: TokenData[];
		other_category: OtherCategory;
	}) {
		this.currentText = data.current_text;
		this.aboveThresholdTokens = data.above_threshold_tokens;
		this.otherCategory = data.other_category;
	}

	appendToken(data: { current_text: string; token_history: TokenHistoryItem[] }) {
		this.currentText = data.current_text;
		this.tokenHistory = data.token_history;
	}

	undoToken(data: { current_text: string; token_history: TokenHistoryItem[] }) {
		this.currentText = data.current_text;
		this.tokenHistory = data.token_history;
	}
}

// Export singleton instance
export const sessionStore = new SessionStore();
