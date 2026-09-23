<script lang="ts">
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api/client';
	import Logo from '$lib/components/Logo.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { ui } from '$lib/stores/ui.svelte';

	let username = $state('');
	let password = $state('');
	let busy = $state(false);
	let error = $state<string | null>(null);

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		if (busy) return;

		error = null;
		busy = true;
		try {
			await session.login(username.trim(), password);
			ui.success('Добро пожаловать!');
			await goto('/chats');
		} catch (cause) {
			error = cause instanceof ApiError ? cause.message : 'Не удалось войти';
		} finally {
			busy = false;
		}
	}
</script>

<main class="grid min-h-dvh place-items-center p-4">
	<form
		class="w-full max-w-sm rounded-container border border-surface-300-700 bg-surface-100-900 p-6 shadow-xl"
		onsubmit={submit}
	>
		<div class="mb-6 flex flex-col items-center gap-2">
			<Logo />
			<p class="text-sm text-surface-700-300">Войдите, чтобы продолжить</p>
		</div>

		<label class="mb-3 block">
			<span class="mb-1 block text-xs text-surface-700-300">Имя пользователя</span>
			<input
				class="w-full rounded-base border border-surface-300-700 bg-surface-200-800 px-3 py-2 text-sm outline-none placeholder:text-surface-700-300 focus:border-primary-500"
				bind:value={username}
				required
				autocomplete="username"
				placeholder="Ваш ник"
			/>
		</label>

		<label class="mb-4 block">
			<span class="mb-1 block text-xs text-surface-700-300">Пароль</span>
			<input
				class="w-full rounded-base border border-surface-300-700 bg-surface-200-800 px-3 py-2 text-sm outline-none placeholder:text-surface-700-300 focus:border-primary-500"
				type="password"
				bind:value={password}
				required
				autocomplete="current-password"
				placeholder="••••••"
			/>
		</label>

		{#if error}
			<p class="mb-3 text-sm text-error-500">{error}</p>
		{/if}

		<button
			class="flex w-full items-center justify-center gap-2 rounded-base bg-primary-500 px-4 py-2.5 text-sm font-semibold text-primary-contrast-500 transition hover:bg-primary-600 disabled:opacity-60"
			type="submit"
			disabled={busy}
		>
			{#if busy}<Spinner size={16} />{/if}
			Войти
		</button>

		<p class="mt-4 text-center text-sm text-surface-700-300">
			Нет аккаунта?
			<a class="text-primary-500 hover:underline" href="/register">Зарегистрироваться</a>
		</p>
	</form>
</main>
