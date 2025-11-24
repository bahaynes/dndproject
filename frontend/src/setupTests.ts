import '@testing-library/jest-dom';
import { vi } from 'vitest';

Object.defineProperty(window, 'EventSource', {
	writable: true,
	value: vi.fn().mockImplementation(() => ({
		addEventListener: vi.fn(),
		close: vi.fn()
	}))
});
