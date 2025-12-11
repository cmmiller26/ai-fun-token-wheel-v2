<script lang="ts">
	let { prompt = $bindable(), onSubmit }: { prompt: string; onSubmit: () => void } = $props();

	function handleSubmit() {
		if (prompt.trim().length > 0) {
			onSubmit();
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		// Submit on Ctrl+Enter or Cmd+Enter
		if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
			handleSubmit();
		}
	}

	const isValid = $derived(prompt.trim().length > 0);
</script>

<div class="space-y-3">
	<label for="prompt-input" class="text-sm font-semibold text-gray-700">
		Enter Your Prompt
	</label>

	<textarea
		id="prompt-input"
		bind:value={prompt}
		onkeydown={handleKeyDown}
		placeholder="The cat sat on the..."
		class="w-full min-h-32 p-3 text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
		rows="4"
	></textarea>

	<div class="flex items-center justify-between">
		<p class="text-sm text-gray-600">
			Press <kbd class="px-2 py-1 bg-gray-100 rounded border">Ctrl+Enter</kbd> or click Start
		</p>
		<button
			onclick={handleSubmit}
			disabled={!isValid}
			class="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
		>
			Start
		</button>
	</div>
</div>
