<script lang="ts">
    import { setAuth } from '$lib/auth';
    import type { User } from '$lib/types';
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
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password,
                }),
            });

            if (!tokenResponse.ok) {
                const errorData = await tokenResponse.json();
                const detail = Array.isArray(errorData?.detail)
                    ? errorData.detail.map((d: any) => d.msg || d.detail || JSON.stringify(d)).join('; ')
                    : errorData?.detail || 'Failed to login';
                error = detail;
                return;
            }

            const tokenData = await tokenResponse.json();
            const accessToken = tokenData.access_token;

            // 2. Use the token to get user info
            const userResponse = await fetch('/api/users/me/', {
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (!userResponse.ok) {
                const errorData = await userResponse.json();
                const detail = errorData?.detail || 'Failed to fetch user details after login.';
                error = detail;
                return;
            }

            const userData: User = await userResponse.json();

            // 3. Update the auth state
            setAuth(userData, accessToken);

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
