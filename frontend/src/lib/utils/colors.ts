/**
 * Utility functions for generating colors for token wedges
 */

/**
 * Generate distinct colors for tokens using HSL color space
 */
export function generateTokenColors(tokens: { token_id: number }[]): Record<number, string> {
	const colorMap: Record<number, string> = {};

	if (tokens.length === 0) return colorMap;

	// Use HSL for evenly distributed colors
	const hueStep = 360 / tokens.length;

	tokens.forEach((token, index) => {
		const hue = (index * hueStep) % 360;
		const saturation = 70; // Vibrant colors
		const lightness = 55; // Medium brightness

		colorMap[token.token_id] = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
	});

	return colorMap;
}

/**
 * Gray color for "Other" category
 */
export const OTHER_COLOR = '#9ca3af';

/**
 * Lighten a color for hover effects
 */
export function lightenColor(color: string, amount: number = 10): string {
	// If it's an HSL color, adjust lightness
	if (color.startsWith('hsl')) {
		const match = color.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
		if (match) {
			const h = match[1];
			const s = match[2];
			const l = Math.min(100, parseInt(match[3]) + amount);
			return `hsl(${h}, ${s}%, ${l}%)`;
		}
	}

	// If it's a hex color
	if (color.startsWith('#')) {
		const num = parseInt(color.slice(1), 16);
		const r = Math.min(255, ((num >> 16) & 255) + amount);
		const g = Math.min(255, ((num >> 8) & 255) + amount);
		const b = Math.min(255, (num & 255) + amount);
		return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
	}

	return color;
}
