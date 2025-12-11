<script lang="ts">
	let { message = '' }: { message?: string } = $props();
</script>

<div class="flex items-center justify-center gap-3 p-4">
	<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
	{#if message}
		<p class="text-gray-600">{message}</p>
	{/if}
</div>
