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

<div class="page-container flex items-center justify-center min-h-[70vh]">
    <div class="panel w-full max-w-xl p-8 space-y-6 glow-border">
        <div class="space-y-2 text-center">
            <div class="pill w-fit mx-auto">Welcome back</div>
            <h3 class="text-3xl font-bold">Log in to your guild tools</h3>
            <p class="muted">Sign in to manage your character, track quests, and rally your party.</p>
        </div>
        <form on:submit|preventDefault={handleSubmit} class="space-y-4">
            <div class="space-y-2">
                <label class="label" for="username">Username</label>
                <input
                    id="username"
                    type="text"
                    placeholder="Your handle"
                    class="input-field"
                    bind:value={username}
                    required
                >
            </div>
            <div class="space-y-2">
                <label class="label" for="password">Password</label>
                <input
                    id="password"
                    type="password"
                    placeholder="Secret phrase"
                    class="input-field"
                    bind:value={password}
                    required
                >
            </div>
            {#if error}
                <p class="text-sm text-red-300">{error}</p>
            {/if}
            <div class="flex items-center justify-between gap-3 pt-2">
                <button class="btn btn-primary">Login</button>
                <a href="/register" class="nav-link">Register</a>
            </div>
        </form>
    </div>
</div>
