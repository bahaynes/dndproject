<script lang="ts">
    import { login } from '$lib/auth';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { browser } from '$app/environment';

    let username = '';
    let password = '';
    let error: string | null = null;

    async function handleSubmit() {
        if (!browser) return;
        error = null;
        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                error = errorData.detail || 'Failed to login';
                return;
            }

            const tokenData = await response.json();
            const accessToken = tokenData.access_token;

            await login(accessToken);

            const redirectTo = $page.url.searchParams.get('redirectTo') || '/dashboard';
            await goto(redirectTo);

        } catch (e) {
            error = 'An unexpected error occurred.';
            console.error(e);
        }
    }
</script>

<div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="px-8 py-6 mt-4 text-left bg-white shadow-lg rounded-lg">
        <h3 class="text-2xl font-bold text-center">Login to your account</h3>
        <form on:submit|preventDefault={handleSubmit}>
            <div class="mt-4">
                <div>
                    <label class="block" for="username">Username</label>
                    <input type="text" placeholder="Username"
                           id="username"
                           class="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                           bind:value={username}
                           required>
                </div>
                <div class="mt-4">
                    <label class="block" for="password">Password</label>
                    <input type="password" placeholder="Password"
                           id="password"
                           class="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                           bind:value={password}
                           required>
                </div>
                {#if error}
                    <p class="text-red-500 text-xs mt-2">{error}</p>
                {/if}
                <div class="flex items-baseline justify-between">
                    <button class="px-6 py-2 mt-4 text-white bg-blue-600 rounded-lg hover:bg-blue-900">Login</button>
                    <a href="/register" class="text-sm text-blue-600 hover:underline">Register</a>
                </div>
            </div>
        </form>
    </div>
</div>
