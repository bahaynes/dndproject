<script lang="ts">
	import { login } from '$lib/auth';
	import { goto } from '$app/navigation';

	let username = '';
	let password = '';
	let error: string | null = null;

	async function handleSubmit() {
		error = null;
		try {
			// 1. Get the access token
			const tokenResponse = await fetch('/api/token', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/x-www-form-urlencoded'
				},
				body: new URLSearchParams({
					username: username,
					password: password
				})
			});

			if (!tokenResponse.ok) {
				const errorData = await tokenResponse.json();
				error = errorData.detail || 'Failed to login';
				return;
			}

			const tokenData = await tokenResponse.json();
			const accessToken = tokenData.access_token;

			// 2. Use the token to get user info
			const userResponse = await fetch('/api/users/me/', {
				headers: {
					Authorization: `Bearer ${accessToken}`
				}
			});

			if (!userResponse.ok) {
				error = 'Failed to fetch user details after login.';
				return;
			}

			const userData = await userResponse.json();

			// 3. Update the auth state
			login(userData, accessToken);

			// 4. Store the token for future sessions (e.g., in localStorage)
			if (typeof window !== 'undefined') {
				localStorage.setItem('accessToken', accessToken);
			}

			await goto('/dashboard');
		} catch (e) {
			error = 'An unexpected error occurred.';
			console.error(e);
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-gray-100">
	<div class="mt-4 rounded-lg bg-white px-8 py-6 text-left shadow-lg">
		<h3 class="text-center text-2xl font-bold">Login to your account</h3>
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
				{#if error}
					<p class="mt-2 text-xs text-red-500">{error}</p>
				{/if}
				<div class="flex items-baseline justify-between">
					<button class="mt-4 rounded-lg bg-blue-600 px-6 py-2 text-white hover:bg-blue-900"
						>Login</button
					>
					<a href="/register" class="text-sm text-blue-600 hover:underline">Register</a>
				</div>
			</div>
		</form>
	</div>
</div>
