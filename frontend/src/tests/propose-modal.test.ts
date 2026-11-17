import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import ProposeModal from '../lib/components/ProposeModal.svelte';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
	api: vi.fn(() => Promise.resolve({}))
}));

const sampleProps = {
	open: true,
	sessionId: 4,
	missions: [
		{
			id: 5,
			name: 'Sunken Vault',
			tier: 'Tier 1',
			status: 'Available',
			cooldown_days: 7,
			is_retired: false,
			is_discoverable: true,
			rewards: [],
			players: []
		}
	],
	hexes: [{ id: 9, q: 1, r: 2, terrain: 'swamp', linked_location_name: 'Bog Shrine' }]
};

describe('ProposeModal', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	test('submits a Posted Quest proposal', async () => {
		render(ProposeModal, { props: sampleProps });
		await fireEvent.click(screen.getByText('Propose'));
		await waitFor(() =>
			expect(api).toHaveBeenCalledWith('POST', '/sessions/proposals', {
				session_id: 4,
				mission_id: 5
			})
		);
	});

	test('submits a Discovered Hex proposal', async () => {
		render(ProposeModal, { props: sampleProps });
		await fireEvent.click(screen.getByText('Discovered Hex'));
		await fireEvent.click(screen.getByText('Propose'));
		await waitFor(() =>
			expect(api).toHaveBeenCalledWith('POST', '/sessions/proposals', {
				session_id: 4,
				hex_id: 9
			})
		);
	});
});
