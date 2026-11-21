import { describe, it, expect } from 'vitest';
import { safeExternalUrl, safeInternalPath } from '$lib/utils/url';

describe('URL sanitization utilities', () => {
	it('allows valid http and https external URLs', () => {
		expect(safeExternalUrl('https://www.dndbeyond.com/characters/123')).toBe(
			'https://www.dndbeyond.com/characters/123'
		);
		expect(safeExternalUrl('  http://foundry.local:30000/sheet  ')).toBe(
			'http://foundry.local:30000/sheet'
		);
	});

	it('rejects javascript:, data:, vbscript:, relative, and empty external URLs', () => {
		expect(safeExternalUrl('javascript:alert(1)')).toBeNull();
		expect(safeExternalUrl('JAVASCRIPT:alert(1)')).toBeNull();
		expect(safeExternalUrl('data:text/html,<script>alert(1)</script>')).toBeNull();
		expect(safeExternalUrl('vbscript:msgbox(1)')).toBeNull();
		expect(safeExternalUrl('/characters/1')).toBeNull();
		expect(safeExternalUrl('   ')).toBeNull();
		expect(safeExternalUrl(null)).toBeNull();
		expect(safeExternalUrl(undefined)).toBeNull();
	});

	it('allows safe internal relative paths', () => {
		expect(safeInternalPath('/sessions')).toBe('/sessions');
		expect(safeInternalPath('  /maps?layer=topo  ')).toBe('/maps?layer=topo');
	});

	it('rejects protocol-relative, external, backslash, and control-char internal paths', () => {
		expect(safeInternalPath('//evil.example/phish')).toBeNull();
		expect(safeInternalPath('https://evil.example')).toBeNull();
		expect(safeInternalPath('javascript:alert(1)')).toBeNull();
		expect(safeInternalPath('/foo\\bar')).toBeNull();
		expect(safeInternalPath('/foo\nbar')).toBeNull();
		expect(safeInternalPath('')).toBeNull();
		expect(safeInternalPath(null)).toBeNull();
	});
});
