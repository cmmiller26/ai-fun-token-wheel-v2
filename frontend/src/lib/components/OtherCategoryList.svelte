<script lang="ts">
	interface TokenData {
		token_id: number;
		token_text: string;
		probability: number;
	}

	let {
		sampleTokens = [],
		totalProbability = 0,
		tokenCount = 0
	}: {
		sampleTokens: TokenData[];
		totalProbability: number;
		tokenCount: number;
	} = $props();

	const hasOtherCategory = $derived(totalProbability > 0 && tokenCount > 0);
</script>

<div class="bg-gray-50 rounded-lg border border-gray-200 p-4">
	<h3 class="text-lg font-semibold mb-2 text-gray-900">
		<span class="inline-block w-4 h-4 bg-gray-400 rounded mr-2"></span>
		"Other" Category
	</h3>

	{#if !hasOtherCategory}
		<p class="text-sm text-gray-500">All tokens are shown on the wheel</p>
	{:else}
		<div class="mb-3 p-3 bg-white rounded border border-gray-200">
			<div class="text-sm text-gray-700">
				<strong class="text-gray-900">{tokenCount.toLocaleString()}</strong> tokens with
				<strong class="text-gray-900">{(totalProbability * 100).toFixed(1)}%</strong> total
				probability
			</div>
			<p class="text-xs text-gray-600 mt-1">
				These tokens have probabilities below the threshold
			</p>
		</div>

		{#if sampleTokens.length > 0}
			<div>
				<h4 class="text-sm font-medium text-gray-700 mb-2">Sample Tokens:</h4>
				<div class="space-y-1 max-h-48 overflow-y-auto">
					{#each sampleTokens as token}
						<div class="flex items-center justify-between p-2 bg-white rounded text-sm">
							<code class="font-mono text-gray-900">{token.token_text}</code>
							<span class="text-gray-600">{(token.probability * 100).toFixed(2)}%</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>
