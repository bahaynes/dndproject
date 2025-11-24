import { vi } from 'vitest';

vi.hoisted(() => {
	vi.mock('$app/environment', () => ({
		browser: true
	}));

	vi.mock('$app/navigation', () => ({
		goto: vi.fn()
	}));
});
