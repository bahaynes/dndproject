<script lang="ts">
	import { auth } from '$lib/auth';
	import { goto } from '$app/navigation';
	import { ADMIN_NAV } from '$lib/navigation';
	import SubNav from '$lib/components/SubNav.svelte';

	$: if ($auth.isAuthenticated && $auth.user?.role !== 'admin') {
		goto('/dashboard');
	}
</script>

<div class="page-container">
	<SubNav items={ADMIN_NAV} />
	<slot />
</div>
