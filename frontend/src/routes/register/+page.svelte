<script lang="ts">
	import { goto } from '$app/navigation';
	import { login } from '$lib/auth';

	let username = '';
	let email = '';
	let password = '';
	let confirmPassword = '';
	let error: string | null = null;
	let successMessage: string | null = null;

	async function handleSubmit() {
		error = null;
		successMessage = null;

		if (password !== confirmPassword) {
			error = 'Passwords do not match!';
			return;
		}

		try {
			const response = await fetch('/api/users/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					username,
					email,
					password
				})
			});

			if (response.ok) {
				successMessage = 'Registration successful! Logging you in...';
				const data = await response.json();
				const user = {
					id: data.id,
					username: data.username,
					email: data.email,
					is_active: data.is_active,
					role: data.role,
					character: data.character
				};

				login(user, data.access_token);

				if (typeof window !== 'undefined') {
					localStorage.setItem('accessToken', data.access_token);
				}

				setTimeout(() => {
					goto('/dashboard');
				}, 1500);
			} else {
				const errorData = await response.json();
				error = errorData.detail || 'Failed to register';
			}
		} catch (e) {
			error = 'An unexpected error occurred.';
			console.error(e);
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-gray-100">
	<div class="mt-4 rounded-lg bg-white px-8 py-6 text-left shadow-lg">
		<h3 class="text-center text-2xl font-bold">Create an account</h3>
		<form on:submit|preventDefault={handleSubmit}>
			<div class="mt-4">
				<div>
					<label class="block" for="username">Username</label>
					<input
						type="text"
						placeholder="Username"
						id="username"
						class="mt-2 w-full rounded-md border px-4 py-2 focus:ring-1 focus:ring-blue-600 focus:outline-none"
						bind:value={username}
						required
					/>
				</div>
				<div class="mt-4">
					<label class="block" for="email">Email</label>
					<input
						type="email"
						placeholder="Email"
						id="email"
						class="mt-2 w-full rounded-md border px-4 py-2 focus:ring-1 focus:ring-blue-600 focus:outline-none"
						bind:value={email}
						required
					/>
				</div>
				<div class="mt-4">
					<label class="block" for="password">Password</label>
					<input
						type="password"
						placeholder="Password"
						id="password"
						class="mt-2 w-full rounded-md border px-4 py-2 focus:ring-1 focus:ring-blue-600 focus:outline-none"
						bind:value={password}
						required
					/>
				</div>
				<div class="mt-4">
					<label class="block" for="confirmPassword">Confirm Password</label>
					<input
						type="password"
						placeholder="Confirm Password"
						id="confirmPassword"
						class="mt-2 w-full rounded-md border px-4 py-2 focus:ring-1 focus:ring-blue-600 focus:outline-none"
						bind:value={confirmPassword}
						required
					/>
				</div>
				{#if error}
					<p class="mt-2 text-xs text-red-500">{error}</p>
				{/if}
				{#if successMessage}
					<p class="mt-2 text-xs text-green-500">{successMessage}</p>
				{/if}
				<div class="flex items-baseline justify-between">
					<button
						class="mt-4 rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-900"
						disabled={!!successMessage}>Register</button
					>
					<a href="/login" class="text-sm text-blue-600 hover:underline">Already have an account?</a
					>
				</div>
			</div>
		</form>
	</div>
</div>
