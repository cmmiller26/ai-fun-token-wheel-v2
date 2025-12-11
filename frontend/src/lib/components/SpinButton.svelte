<script lang="ts">
	let {
		onSpin,
		disabled = false,
		spinning = false
	}: {
		onSpin: () => void;
		disabled?: boolean;
		spinning?: boolean;
	} = $props();
</script>

<div class="absolute inset-0 flex items-center justify-center pointer-events-none">
	<button
		onclick={onSpin}
		disabled={disabled || spinning}
		class="pointer-events-auto w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 text-white font-bold text-xl shadow-2xl hover:from-blue-600 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95"
		aria-label="Spin the wheel"
	>
		{#if spinning}
			<div class="animate-spin">🎲</div>
		{:else}
			<div>SPIN</div>
		{/if}
	</button>
</div>
