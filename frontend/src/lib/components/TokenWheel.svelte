<script lang="ts">
	import { calculateWedges, wedgeToPath, type Wedge } from '$lib/utils/wheel';
	import { generateTokenColors, OTHER_COLOR, lightenColor } from '$lib/utils/colors';

	interface TokenData {
		token_id: number;
		token_text: string;
		probability: number;
	}

	interface OtherCategory {
		total_probability: number;
		token_count: number;
		sample_tokens: TokenData[];
	}

	let {
		tokens = [],
		otherCategory = { total_probability: 0, token_count: 0, sample_tokens: [] },
		onTokenSelect,
		spinning = false,
		rotation = 0
	}: {
		tokens: TokenData[];
		otherCategory: OtherCategory;
		onTokenSelect: (selection: { token_id?: number; token_text?: string; category?: string }) => void;
		spinning?: boolean;
		rotation?: number;
	} = $props();

	const centerX = 300;
	const centerY = 300;
	const radius = 250;

	let hoveredWedgeIndex = $state<number | null>(null);

	// Calculate wedges and colors reactively
	const wedges = $derived(calculateWedges(tokens, otherCategory));
	const colorMap = $derived(generateTokenColors(tokens));

	function handleWedgeClick(wedge: Wedge) {
		if (spinning) return;

		if (wedge.isOther) {
			onTokenSelect({ category: 'other' });
		} else {
			onTokenSelect({
				token_id: wedge.tokenId!,
				token_text: wedge.tokenText
			});
		}
	}

	function getWedgeColor(wedge: Wedge, index: number): string {
		const baseColor = wedge.isOther ? OTHER_COLOR : colorMap[wedge.tokenId!];
		return hoveredWedgeIndex === index ? lightenColor(baseColor, 15) : baseColor;
	}
</script>

<div class="relative flex items-center justify-center">
	<svg viewBox="0 0 600 600" class="w-full max-w-2xl">
		<g
			style="transform: rotate({rotation}deg); transform-origin: {centerX}px {centerY}px; transition: transform 2s cubic-bezier(0.25, 0.1, 0.25, 1);"
		>
			{#each wedges as wedge, i}
				<path
					d={wedgeToPath(wedge, centerX, centerY, radius)}
					fill={getWedgeColor(wedge, i)}
					stroke="#ffffff"
					stroke-width="2"
					onclick={() => handleWedgeClick(wedge)}
					onkeydown={(e) => {
						if ((e.key === 'Enter' || e.key === ' ') && !spinning) {
							e.preventDefault();
							handleWedgeClick(wedge);
						}
					}}
					onmouseenter={() => !spinning && (hoveredWedgeIndex = i)}
					onmouseleave={() => (hoveredWedgeIndex = null)}
					style="cursor: {spinning ? 'default' : 'pointer'}; transition: fill 0.2s ease;"
					role="button"
					tabindex={spinning ? -1 : 0}
					aria-label="{wedge.tokenText} - {(wedge.probability * 100).toFixed(1)}%"
				>
					<title>{wedge.tokenText} ({(wedge.probability * 100).toFixed(1)}%)</title>
				</path>
			{/each}
		</g>

		<!-- Center circle for visual appeal -->
		<circle cx={centerX} cy={centerY} r="80" fill="white" stroke="#e5e7eb" stroke-width="2" />
	</svg>

	<!-- Hover tooltip -->
	{#if hoveredWedgeIndex !== null && !spinning}
		<div
			class="absolute top-4 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-lg text-sm pointer-events-none"
		>
			<div class="font-medium">{wedges[hoveredWedgeIndex].tokenText}</div>
			<div class="text-gray-300">
				{(wedges[hoveredWedgeIndex].probability * 100).toFixed(1)}%
			</div>
		</div>
	{/if}
</div>
