<script lang="ts">
    import { goto } from '$app/navigation';
    import { setAuth } from '$lib/auth';
    import type { User } from '$lib/types';

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
            error = "Passwords do not match!";
            return;
        }

        try {
            const response = await fetch('/api/users/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    email,
                    password,
                }),
            });

            if (response.ok) {
                successMessage = "Registration successful! Logging you in...";
                const data = await response.json();
                const accessToken = data.access_token;
                const { access_token, token_type, ...userProfile } = data;

                setAuth(userProfile as User, accessToken);

                if (typeof window !== 'undefined') {
                    localStorage.setItem('accessToken', accessToken);
                }

                setTimeout(() => {
                    goto('/dashboard');
                }, 1500);
            } else {
                const errorData = await response.json();
                const detail = Array.isArray(errorData?.detail)
                    ? errorData.detail.map((d: any) => d.msg || d.detail || JSON.stringify(d)).join('; ')
                    : errorData?.detail || 'Failed to register';
                error = detail;
            }
        } catch (e) {
            error = 'An unexpected error occurred.';
            console.error(e);
        }
    }
</script>

<div class="page-container flex items-center justify-center min-h-[70vh]">
    <div class="panel w-full max-w-2xl p-8 space-y-6 glow-border">
        <div class="space-y-2 text-center">
            <div class="pill w-fit mx-auto">New recruit</div>
            <h3 class="text-3xl font-bold">Forge your adventurer profile</h3>
            <p class="muted">Claim your seat at the table and keep your quests organized.</p>
        </div>
        <form on:submit|preventDefault={handleSubmit} class="grid gap-4 md:grid-cols-2 md:gap-6">
            <div class="space-y-2 md:col-span-1">
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
            <div class="space-y-2 md:col-span-1">
                <label class="label" for="email">Email</label>
                <input
                    id="email"
                    type="email"
                    placeholder="you@realm.com"
                    class="input-field"
                    bind:value={email}
                    required
                >
            </div>
            <div class="space-y-2 md:col-span-1">
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
            <div class="space-y-2 md:col-span-1">
                <label class="label" for="confirmPassword">Confirm Password</label>
                <input
                    id="confirmPassword"
                    type="password"
                    placeholder="Match your phrase"
                    class="input-field"
                    bind:value={confirmPassword}
                    required
                >
            </div>
            <div class="md:col-span-2 space-y-2">
                {#if error}
                    <p class="text-sm text-red-300">{error}</p>
                {/if}
                {#if successMessage}
                    <p class="text-sm text-emerald-200">{successMessage}</p>
                {/if}
            </div>
            <div class="md:col-span-2 flex items-center justify-between gap-3 pt-2">
                <button class="btn btn-primary" disabled={!!successMessage}>Register</button>
                <a href="/login" class="nav-link">Already sworn in?</a>
            </div>
        </form>
    </div>
</div>
