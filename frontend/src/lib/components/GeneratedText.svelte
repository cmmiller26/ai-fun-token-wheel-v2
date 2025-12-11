<script lang="ts">
	let {
		prompt = '',
		currentText = ''
	}: {
		prompt: string;
		currentText: string;
	} = $props();

	const generatedText = $derived(() => {
		if (!prompt) return '';
		return currentText.substring(prompt.length);
	});
</script>

<div class="bg-white rounded-lg border-2 border-gray-300 p-6 shadow-sm">
	<h2 class="text-sm font-semibold text-gray-600 mb-3">Generated Text</h2>

	<div class="text-xl leading-relaxed">
		{#if currentText}
			<span class="text-gray-900">{prompt}</span><span class="text-blue-600 font-medium"
				>{generatedText()}</span
			>
			<span class="inline-block w-1 h-6 bg-blue-600 animate-pulse ml-1"></span>
		{:else}
			<span class="text-gray-400 italic">No text generated yet</span>
		{/if}
	</div>

	{#if generatedText()}
		<div class="mt-4 pt-4 border-t border-gray-200 flex items-center gap-4 text-sm text-gray-600">
			<div>
				<strong>Prompt:</strong>
				{prompt.length} chars
			</div>
			<div>
				<strong>Generated:</strong>
				{generatedText().length} chars
			</div>
			<div>
				<strong>Total:</strong>
				{currentText.length} chars
			</div>
		</div>
	{/if}
</div>
