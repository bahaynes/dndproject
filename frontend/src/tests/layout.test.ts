import { render } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';
import { vi } from 'vitest';

vi.mock('svelte', async (importOriginal) => {
    const svelte = await importOriginal();
    return {
        ...svelte,
        onMount: vi.fn(),
    };
});

describe('+layout.svelte', () => {
	it('renders without crashing', () => {
		const { container } = render(Layout);
		expect(container).toBeTruthy();
	});
});
