<script lang="ts">
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session.svelte';

	// Точка входа: после восстановления сессии уходим в чаты или на вход
	$effect(() => {
		if (!session.ready) return;
		void goto(session.isAuthenticated ? '/chats' : '/login', { replaceState: true });
	});
</script>

<div class="grid h-dvh place-items-center"></div>
