import { render } from '@testing-library/svelte';
import Layout from '../routes/+layout.svelte';

describe('+layout.svelte', () => {
	it('renders without crashing', () => {
		const { container } = render(Layout);
		expect(container).toBeTruthy();
	});
});
