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

                const user = {
                    id: data.id,
                    username: data.username,
                    email: data.email,
                    is_active: data.is_active,
                    role: data.role,
                    character: data.character
                };

                login(user);

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

<div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="px-8 py-6 mt-4 text-left bg-white shadow-lg rounded-lg">
        <h3 class="text-2xl font-bold text-center">Create an account</h3>
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
                    <label class="block" for="email">Email</label>
                    <input type="email" placeholder="Email"
                           id="email"
                           class="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                           bind:value={email}
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
                <div class="mt-4">
                    <label class="block" for="confirmPassword">Confirm Password</label>
                    <input type="password" placeholder="Confirm Password"
                           id="confirmPassword"
                           class="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600"
                           bind:value={confirmPassword}
                           required>
                </div>
                {#if error}
                    <p class="text-red-500 text-xs mt-2">{error}</p>
                {/if}
                {#if successMessage}
                    <p class="text-green-500 text-xs mt-2">{successMessage}</p>
                {/if}
                <div class="flex items-baseline justify-between">
                    <button class="px-6 py-2 mt-4 text-white bg-blue-600 rounded-lg hover:bg-blue-900" disabled={!!successMessage}>Register</button>
                    <a href="/login" class="text-sm text-blue-600 hover:underline">Already have an account?</a>
                </div>
            </div>
        </form>
    </div>
</div>
