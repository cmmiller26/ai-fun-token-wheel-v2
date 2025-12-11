/**
 * Utility functions for wheel spinning logic
 */

import type { Wedge } from './wheel';

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

export interface SelectedToken {
	token_id?: number;
	token_text?: string;
	probability: number;
	isOther: boolean;
	wedge?: Wedge;
}

/**
 * Randomly select a token based on probability distribution
 */
export function selectRandomToken(
	tokens: TokenData[],
	otherCategory: OtherCategory,
	wedges: Wedge[]
): SelectedToken {
	// Create weighted array
	const allTokens: SelectedToken[] = [
		...tokens.map((t, i) => ({
			token_id: t.token_id,
			token_text: t.token_text,
			probability: t.probability,
			isOther: false,
			wedge: wedges[i]
		})),
		{
			probability: otherCategory.total_probability,
			isOther: true,
			wedge: wedges[tokens.length] // Last wedge is "Other"
		}
	];

	// Random number between 0 and 1
	const random = Math.random();

	// Find selected token by cumulative probability
	let cumulative = 0;
	for (const token of allTokens) {
		cumulative += token.probability;
		if (random <= cumulative) {
			return token;
		}
	}

	// Fallback to last token (should rarely happen)
	return allTokens[allTokens.length - 1];
}

/**
 * Calculate total rotation angle for spin animation
 * Includes multiple full rotations plus the target angle
 */
export function calculateSpinRotation(selectedWedge: Wedge, spins: number = 3): number {
	// Calculate angle to middle of selected wedge
	const targetAngle = (selectedWedge.startAngle + selectedWedge.endAngle) / 2;

	// Add multiple full rotations for dramatic effect
	// We add 360 degrees per spin, then add the target angle
	const totalRotation = spins * 360 + targetAngle;

	return totalRotation;
}

/**
 * Animate a value over time using easing
 */
export function easeOutCubic(t: number): number {
	return 1 - Math.pow(1 - t, 3);
}
