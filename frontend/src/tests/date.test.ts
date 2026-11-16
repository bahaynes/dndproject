import { describe, expect, test } from 'vitest';
import { parseUtcDate, toLocalDateTimeInput } from '../lib/date';

describe('date helpers', () => {
	test('parseUtcDate treats naive ISO strings as UTC', () => {
		const naive = parseUtcDate('2026-11-30T23:30:00');
		const explicit = parseUtcDate('2026-11-30T23:30:00Z');
		expect(naive.getTime()).toBe(explicit.getTime());
	});

	test('parseUtcDate preserves explicit timezone offsets', () => {
		const offset = parseUtcDate('2026-11-30T18:30:00-05:00');
		const utc = parseUtcDate('2026-11-30T23:30:00Z');
		expect(offset.getTime()).toBe(utc.getTime());
	});

	test('toLocalDateTimeInput formats valid dates as YYYY-MM-DDTHH:mm', () => {
		const val = toLocalDateTimeInput('2026-11-30T23:30:00');
		expect(val).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
	});
});
