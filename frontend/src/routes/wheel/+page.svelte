<script lang="ts">
	import { goto } from '$app/navigation';
	import TokenWheel from '$lib/components/TokenWheel.svelte';
	import WheelLegend from '$lib/components/WheelLegend.svelte';
	import OtherCategoryList from '$lib/components/OtherCategoryList.svelte';
	import GeneratedText from '$lib/components/GeneratedText.svelte';
	import SpinButton from '$lib/components/SpinButton.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import { sessionStore } from '$lib/stores/session.svelte';
	import { appendToken, getNextTokenProbs, undoToken } from '$lib/api/client';
	import { selectRandomToken, calculateSpinRotation } from '$lib/utils/spinner';
	import { calculateWedges } from '$lib/utils/wheel';

	let rotation = $state(0);

	// Redirect if no active session (reactively monitors session state)
	$effect(() => {
		if (!sessionStore.hasSession) {
			void goto('/');
		}
	});

	async function handleTokenSelect(selection: {
		token_id?: number;
		token_text?: string;
		category?: string;
	}) {
		sessionStore.isLoading = true;
		sessionStore.error = null;

		try {
			const data = await appendToken(sessionStore.sessionId!, selection);
			sessionStore.appendToken(data);

			const probData = await getNextTokenProbs(sessionStore.sessionId!);
			sessionStore.setTokenProbabilities(probData);
		} catch (error) {
			sessionStore.error = error instanceof Error ? error.message : 'Failed to select token';
		} finally {
			sessionStore.isLoading = false;
		}
	}

	async function handleSpin() {
		sessionStore.isSpinning = true;
		sessionStore.error = null;

		// Calculate wedges for selection
		const wedges = calculateWedges(sessionStore.aboveThresholdTokens, sessionStore.otherCategory);

		// Select random token
		const selectedToken = selectRandomToken(
			sessionStore.aboveThresholdTokens,
			sessionStore.otherCategory,
			wedges
		);

		// Calculate and apply rotation
		if (selectedToken.wedge) {
			const spinRotation = calculateSpinRotation(selectedToken.wedge, 3);
			rotation = spinRotation;
		}

		// Wait for animation to complete
		await new Promise((resolve) => setTimeout(resolve, 2000));

		// Select the token
		sessionStore.isSpinning = false;

		if (selectedToken.isOther) {
			await handleTokenSelect({ category: 'other' });
		} else {
			await handleTokenSelect({
				token_id: selectedToken.token_id,
				token_text: selectedToken.token_text
			});
		}

		// Reset rotation for next spin
		rotation = 0;
	}

	async function handleUndo() {
		sessionStore.isLoading = true;
		sessionStore.error = null;

		try {
			const data = await undoToken(sessionStore.sessionId!);
			sessionStore.undoToken(data);

			const probData = await getNextTokenProbs(sessionStore.sessionId!);
			sessionStore.setTokenProbabilities(probData);
		} catch (error) {
			sessionStore.error = error instanceof Error ? error.message : 'Failed to undo';
		} finally {
			sessionStore.isLoading = false;
		}
	}

	function handleNewPrompt() {
		sessionStore.reset();
		void goto('/');
	}
</script>

<svelte:head>
	<title>AI Token Wheel - Generation</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
	<div class="container mx-auto px-4 max-w-7xl">
		<!-- Header Actions -->
		<div class="flex items-center justify-between mb-6">
			<button
				onclick={handleNewPrompt}
				class="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M10 19l-7-7m0 0l7-7m-7 7h18"
					/>
				</svg>
				New Prompt
			</button>

			<div class="flex items-center gap-3">
				<button
					onclick={handleUndo}
					disabled={!sessionStore.canUndo || sessionStore.isLoading || sessionStore.isSpinning}
					class="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
						/>
					</svg>
					Undo Last Token
				</button>
			</div>
		</div>

		<!-- Generated Text Display -->
		<div class="mb-8">
			<GeneratedText prompt={sessionStore.initialPrompt} currentText={sessionStore.currentText} />
		</div>

		<!-- Error Display -->
		{#if sessionStore.error}
			<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
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

		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
			<!-- Wheel Column (2/3) -->
			<div class="lg:col-span-2">
				<div class="bg-white rounded-2xl shadow-xl p-8">
					{#if sessionStore.isLoading && !sessionStore.isSpinning}
						<LoadingSpinner message="Processing..." />
					{:else}
						<div class="relative">
							<TokenWheel
								tokens={sessionStore.aboveThresholdTokens}
								otherCategory={sessionStore.otherCategory}
								onTokenSelect={handleTokenSelect}
								spinning={sessionStore.isSpinning}
								{rotation}
							/>
							<SpinButton
								onSpin={handleSpin}
								disabled={sessionStore.isLoading}
								spinning={sessionStore.isSpinning}
							/>
						</div>

						{#if sessionStore.isSpinning}
							<div class="text-center mt-4 text-gray-600 font-medium animate-pulse">
								Spinning...
							</div>
						{/if}
					{/if}
				</div>
			</div>

			<!-- Sidebar Column (1/3) -->
			<div class="lg:col-span-1 space-y-6">
				<WheelLegend tokens={sessionStore.aboveThresholdTokens} />

				<OtherCategoryList
					sampleTokens={sessionStore.otherCategory.sample_tokens}
					totalProbability={sessionStore.otherCategory.total_probability}
					tokenCount={sessionStore.otherCategory.token_count}
				/>
			</div>
		</div>
	</div>
</div>
