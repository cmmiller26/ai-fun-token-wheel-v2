<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchModels } from '$lib/api/client';

	interface ModelInfo {
		id: string;
		name: string;
		description: string;
		parameters: string;
		default: boolean;
	}

	let { selectedModel = $bindable() }: { selectedModel: string } = $props();

	let models = $state<ModelInfo[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		try {
			const data = await fetchModels();
			models = data.models;
			loading = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load models';
			loading = false;
		}
	});
</script>

<div class="space-y-3">
	<div class="text-sm font-semibold text-gray-700">Select Model</div>

	{#if loading}
		<div class="text-sm text-gray-500">Loading models...</div>
	{:else if error}
		<div class="text-sm text-red-600">{error}</div>
	{:else if models.length === 0}
		<div class="text-sm text-gray-500">No models available</div>
	{:else}
		<div class="space-y-2">
			{#each models as model (model.id)}
				<label
					class="flex items-start gap-3 rounded-lg border border-gray-200 p-3 hover:bg-gray-50 cursor-pointer transition-colors"
				>
					<input
						type="radio"
						bind:group={selectedModel}
						value={model.id}
						class="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500"
					/>
					<div class="flex-1">
						<div class="font-medium text-gray-900">{model.name}</div>
						<div class="text-sm text-gray-600">{model.description}</div>
					</div>
				</label>
			{/each}
		</div>
	{/if}
</div>
