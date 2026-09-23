<script lang="ts">
	import * as usersApi from '$lib/api/users';
	import type { User } from '$lib/api/types';
	import { ApiError } from '$lib/api/client';
	import Avatar from './Avatar.svelte';
	import Icon from './Icon.svelte';
	import Modal from './Modal.svelte';
	import Spinner from './Spinner.svelte';

	let {
		open,
		onclose,
		onselect
	}: { open: boolean; onclose: () => void; onselect: (user: User) => void } = $props();

	let query = $state('');
	let results = $state<User[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);

	$effect(() => {
		const search = query;
		if (!open) return;

		let cancelled = false;
		const timer = setTimeout(async () => {
			loading = true;
			error = null;
			try {
				const users = await usersApi.searchUsers(search);
				if (!cancelled) results = users;
			} catch (cause) {
				if (!cancelled) {
					error = cause instanceof ApiError ? cause.message : 'Не удалось загрузить список';
				}
			} finally {
				if (!cancelled) loading = false;
			}
		}, 250);

		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	});
</script>

<Modal {open} title="Новый чат" onclose={onclose}>
	<label class="label">
		<span class="mb-1 block text-xs text-surface-700-300">Поиск пользователя по имени</span>
		<span class="relative block">
			<Icon
				name="search"
				size={16}
				class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-surface-700-300"
			/>
			<input
				class="input w-full rounded-base border border-surface-300-700 bg-surface-200-800 py-2 pr-3 pl-9 text-sm outline-none placeholder:text-surface-700-300 focus:border-primary-500"
				placeholder="Например: anna"
				bind:value={query}
				autocomplete="off"
			/>
		</span>
	</label>

	<div class="mt-3 flex max-h-72 flex-col gap-1 overflow-y-auto app-scroll">
		{#if loading}
			<div class="flex items-center gap-2 px-2 py-3 text-sm text-surface-700-300">
				<Spinner size={16} />
				<span>Поиск…</span>
			</div>
		{:else if error}
			<p class="px-2 py-3 text-sm text-error-500">{error}</p>
		{:else if results.length === 0}
			<p class="px-2 py-3 text-sm text-surface-700-300">Ничего не найдено</p>
		{:else}
			{#each results as user (user.id)}
				<button
					type="button"
					class="flex items-center gap-3 rounded-base px-2 py-2 text-left transition hover:bg-surface-200-800 cursor-pointer"
					onclick={() => onselect(user)}
				>
					<Avatar url={user.avatar_url} name={user.username} size="sm" />
					<span class="truncate text-sm">{user.username}</span>
				</button>
			{/each}
		{/if}
	</div>
</Modal>
