import { render, screen } from '@testing-library/svelte';
import { describe, test, expect } from 'vitest';
import PrivacyPage from '../routes/privacy/+page.svelte';
import TermsPage from '../routes/terms/+page.svelte';
import { LAST_UPDATED } from '../lib/legal';

describe('legal pages', () => {
	test('privacy page shows required sections and links to terms', () => {
		render(PrivacyPage);
		expect(screen.getByRole('heading', { name: 'Privacy Policy' })).toBeTruthy();
		expect(screen.getByText(`Last updated ${LAST_UPDATED}`)).toBeTruthy();
		for (const h of [
			'What we collect',
			'Your Discord access token',
			'Where it is kept',
			'Who can see it',
			'How long we keep it, and deletion'
		]) {
			expect(screen.getByRole('heading', { name: h })).toBeTruthy();
		}
		expect(screen.getByRole('link', { name: 'Terms of Service' }).getAttribute('href')).toBe(
			'/terms'
		);
		expect(screen.getByRole('link', { name: 'email admin@bahaynes.com' })).toHaveAttribute(
			'href',
			'mailto:admin@bahaynes.com'
		);
	});

	test('terms page shows date and links to privacy', () => {
		render(TermsPage);
		expect(screen.getByRole('heading', { name: 'Terms of Service' })).toBeTruthy();
		expect(screen.getByText(`Last updated ${LAST_UPDATED}`)).toBeTruthy();
		const privacyLinks = screen.getAllByRole('link', { name: 'Privacy Policy' });
		expect(privacyLinks.every((a) => a.getAttribute('href') === '/privacy')).toBe(true);
	});
});
