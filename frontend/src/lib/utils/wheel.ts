/**
 * Utility functions for calculating wheel geometry
 */

export interface Wedge {
	tokenId: number | null;
	tokenText: string;
	probability: number;
	startAngle: number;
	endAngle: number;
	isOther: boolean;
}

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

/**
 * Calculate wedge positions based on token probabilities
 */
export function calculateWedges(tokens: TokenData[], otherCategory: OtherCategory): Wedge[] {
	const wedges: Wedge[] = [];
	let currentAngle = -90; // Start at top (12 o'clock)

	// Above threshold tokens
	for (const token of tokens) {
		const angleSize = token.probability * 360;
		wedges.push({
			tokenId: token.token_id,
			tokenText: token.token_text,
			probability: token.probability,
			startAngle: currentAngle,
			endAngle: currentAngle + angleSize,
			isOther: false
		});
		currentAngle += angleSize;
	}

	// "Other" category
	if (otherCategory && otherCategory.total_probability > 0) {
		const angleSize = otherCategory.total_probability * 360;
		wedges.push({
			tokenId: null,
			tokenText: 'Other',
			probability: otherCategory.total_probability,
			startAngle: currentAngle,
			endAngle: currentAngle + angleSize,
			isOther: true
		});
	}

	return wedges;
}

/**
 * Convert wedge to SVG path string
 */
export function wedgeToPath(
	wedge: Wedge,
	centerX: number,
	centerY: number,
	radius: number
): string {
	const { startAngle, endAngle } = wedge;

	const startRad = (startAngle * Math.PI) / 180;
	const endRad = (endAngle * Math.PI) / 180;

	const x1 = centerX + radius * Math.cos(startRad);
	const y1 = centerY + radius * Math.sin(startRad);
	const x2 = centerX + radius * Math.cos(endRad);
	const y2 = centerY + radius * Math.sin(endRad);

	const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;

	return `
    M ${centerX} ${centerY}
    L ${x1} ${y1}
    A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
    Z
  `.trim();
}

/**
 * Calculate text position for label in the middle of a wedge
 */
export function getWedgeLabelPosition(
	wedge: Wedge,
	centerX: number,
	centerY: number,
	radius: number
): { x: number; y: number; angle: number } {
	const midAngle = (wedge.startAngle + wedge.endAngle) / 2;
	const midRad = (midAngle * Math.PI) / 180;
	const labelRadius = radius * 0.7; // 70% of radius for label position

	const x = centerX + labelRadius * Math.cos(midRad);
	const y = centerY + labelRadius * Math.sin(midRad);

	return { x, y, angle: midAngle };
}
