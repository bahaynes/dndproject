function hasControlChars(value: string): boolean {
	for (let i = 0; i < value.length; i += 1) {
		const code = value.charCodeAt(i);
		if (code < 0x20 || code === 0x7f) {
			return true;
		}
	}
	return false;
}

/**
 * Validates external URLs for anchor tags, permitting only http: and https: protocols.
 */
export function safeExternalUrl(url: string | null | undefined): string | null {
	if (!url) return null;
	const trimmed = url.trim();
	if (!trimmed || hasControlChars(trimmed)) return null;
	try {
		const parsed = new URL(trimmed);
		if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
			return trimmed;
		}
		return null;
	} catch {
		return null;
	}
}

/**
 * Validates internal relative paths for anchor tags, rejecting protocol-relative URLs,
 * backslashes, and control characters.
 */
export function safeInternalPath(path: string | null | undefined): string | null {
	if (!path) return null;
	const trimmed = path.trim();
	if (!trimmed) return null;
	if (!trimmed.startsWith('/') || trimmed.startsWith('//')) return null;
	if (trimmed.includes('\\') || hasControlChars(trimmed)) return null;
	return trimmed;
}
