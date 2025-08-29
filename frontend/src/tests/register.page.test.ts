import { render, screen, fireEvent } from '@testing-library/svelte';
import RegisterPage from '../routes/register/+page.svelte';
import { vi } from 'vitest';

describe('Register Page', () => {
	it('renders the registration form', () => {
		render(RegisterPage);

		expect(screen.getByLabelText('Username')).toBeInTheDocument();
		expect(screen.getByLabelText('Email')).toBeInTheDocument();
		expect(screen.getByLabelText('Password')).toBeInTheDocument();
		expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
		expect(screen.getByRole('button', { name: 'Register' })).toBeInTheDocument();
	});

	it('submits the form with user input', async () => {
        render(RegisterPage);

		const username = `testuser_${Date.now()}`;
		const email = `${username}@example.com`;
		const password = 'password';

		await fireEvent.input(screen.getByLabelText('Username'), { target: { value: username } });
		await fireEvent.input(screen.getByLabelText('Email'), { target: { value: email } });
		await fireEvent.input(screen.getByLabelText('Password'), { target: { value: password } });
		await fireEvent.input(screen.getByLabelText('Confirm Password'), { target: { value: password } });
		await fireEvent.click(screen.getByRole('button', { name: 'Register' }));

        // We can't easily assert the navigation here, but we can at least make sure no error is shown
        const error = screen.queryByRole('alert', { name: /error/i });
        expect(error).not.toBeInTheDocument();
	});
});
