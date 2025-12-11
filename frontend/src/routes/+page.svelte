<script lang="ts">
	import { goto } from '$app/navigation';
	import ModelSelector from '$lib/components/ModelSelector.svelte';
	import PromptInput from '$lib/components/PromptInput.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import { sessionStore } from '$lib/stores/session.svelte';
	import { createSession, setPrompt, getNextTokenProbs } from '$lib/api/client';

	let selectedModel = $state('gpt2');
	let prompt = $state('');

	async function handleStart() {
		sessionStore.isLoading = true;
		sessionStore.error = null;

		try {
			// Create session
			const sessionData = await createSession(selectedModel);
			sessionStore.setSession(sessionData);

			// Set prompt
			await setPrompt(sessionStore.sessionId!, prompt);
			sessionStore.setPrompt(prompt);

			// Get initial probabilities
			const probData = await getNextTokenProbs(sessionStore.sessionId!);
			sessionStore.setTokenProbabilities(probData);

			// Navigate to wheel
			goto('/wheel');
		} catch (error) {
			sessionStore.error = error instanceof Error ? error.message : 'An error occurred';
		} finally {
			sessionStore.isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>AI Token Wheel - Home</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
	<div class="container mx-auto px-4 py-8 max-w-4xl">
		<!-- Header -->
		<header class="text-center mb-12">
			<h1 class="text-5xl font-bold text-gray-900 mb-4">
				🎲 AI Token Wheel
			</h1>
			<p class="text-xl text-gray-700 max-w-2xl mx-auto">
				Visualize how Large Language Models probabilistically sample the next token.
				An interactive educational tool for understanding LLM generation.
			</p>
		</header>

		<!-- Main Form -->
		<div class="bg-white rounded-2xl shadow-xl p-8 space-y-8">
			{#if sessionStore.isLoading}
				<LoadingSpinner message="Creating session and initializing model..." />
			{:else}
				<ModelSelector bind:selectedModel />

				<div class="border-t border-gray-200"></div>

				<PromptInput bind:prompt onSubmit={handleStart} />

				{#if sessionStore.error}
					<div class="p-4 bg-red-50 border border-red-200 rounded-lg">
						<div class="flex items-start gap-3">
							<svg
								class="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"
								fill="currentColor"
								viewBox="0 0 20 20"
							>
								<path
									fill-rule="evenodd"
									d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
									clip-rule="evenodd"
								/>
							</svg>
							<div class="flex-1">
								<h3 class="text-sm font-medium text-red-900">Error</h3>
								<p class="text-sm text-red-700 mt-1">{sessionStore.error}</p>
							</div>
						</div>
					</div>
				{/if}
			{/if}
		</div>

		<!-- Info Section -->
		<div class="mt-8 text-center text-sm text-gray-600">
			<p>
				This tool demonstrates the probabilistic nature of language model generation.
				Each "spin" of the wheel samples from the probability distribution of possible next tokens.
			</p>
		</div>
	</div>
</div>
