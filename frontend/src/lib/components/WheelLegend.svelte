<script lang="ts">
	import { generateTokenColors } from '$lib/utils/colors';

	interface TokenData {
		token_id: number;
		token_text: string;
		probability: number;
	}

	let { tokens = [] }: { tokens: TokenData[] } = $props();

	const colorMap = $derived(generateTokenColors(tokens));
</script>

<div class="bg-white rounded-lg border border-gray-200 p-4">
	<h3 class="text-lg font-semibold mb-3 text-gray-900">Token Probabilities</h3>

	{#if tokens.length === 0}
		<p class="text-sm text-gray-500">No tokens to display</p>
	{:else}
		<div class="space-y-2 max-h-96 overflow-y-auto">
			{#each tokens as token}
				<div class="flex items-center gap-3 p-2 hover:bg-gray-50 rounded">
					<div
						class="w-4 h-4 rounded flex-shrink-0"
						style="background-color: {colorMap[token.token_id]}"
						aria-hidden="true"
					></div>
					<div class="flex-1 min-w-0">
						<code class="text-sm font-mono text-gray-900 break-all">{token.token_text}</code>
					</div>
					<div class="text-sm font-medium text-gray-600 flex-shrink-0">
						{(token.probability * 100).toFixed(1)}%
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
