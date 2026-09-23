<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	import { ApiError } from '$lib/api/client';
	import Avatar from '$lib/components/Avatar.svelte';
	import ChatListItem from '$lib/components/ChatListItem.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import Logo from '$lib/components/Logo.svelte';
	import NewChatDialog from '$lib/components/NewChatDialog.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import { chats } from '$lib/stores/chats.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { ui } from '$lib/stores/ui.svelte';
	import { chatTitle } from '$lib/utils/text';

	let { children } = $props();

	let search = $state('');
	let newChatOpen = $state(false);
	let listError = $state<string | null>(null);

	const currentUserId = $derived(session.user?.id ?? 0);
	/** id активного чата берём из маршрута /chats/[id] */
	const activeChatId = $derived(page.params.id ? Number(page.params.id) : null);
	const filteredChats = $derived(
		search.trim()
			? chats.items.filter((chat) =>
					chatTitle(chat, currentUserId)
						.toLowerCase()
						.includes(search.trim().toLowerCase())
				)
			: chats.items
	);

	$effect(() => {
		if (!session.isAuthenticated || chats.loaded || chats.loading) return;
		void loadChats();
	});

	async function loadChats() {
		listError = null;
		try {
			await chats.load();
		} catch (cause) {
			listError = cause instanceof ApiError ? cause.message : 'Не удалось загрузить чаты';
		}
	}

	async function openUser(userId: number) {
		newChatOpen = false;
		try {
			const chat = await chats.openDirect(userId);
			await goto(`/chats/${chat.id}`);
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось открыть чат');
		}
	}
</script>

<div class="flex h-dvh overflow-hidden">
	<!-- Рейл с профилем -->
	<nav
		class="hidden w-[68px] shrink-0 flex-col items-center gap-3 border-r border-surface-300-700 bg-surface-100-900 py-4 lg:flex"
	>
		<Logo compact />
		{#if session.user}
			<a
				class="rounded-full transition hover:ring-2 hover:ring-primary-500"
				href="/settings"
				title="Настройки профиля"
			>
				<Avatar url={session.user.avatar_url} name={session.user.username} />
			</a>
		{/if}
		<div class="mt-auto flex flex-col items-center gap-1">
			<a
				class="rounded-base p-2 text-surface-700-300 transition hover:bg-surface-200-800 hover:text-primary-500"
				href="/settings"
				title="Настройки"
			>
				<Icon name="cog" />
			</a>
			<button
				type="button"
				class="rounded-base p-2 text-surface-700-300 transition hover:bg-surface-200-800 hover:text-error-500 cursor-pointer"
				title="Выйти из аккаунта"
				onclick={() => session.logout()}
			>
				<Icon name="logout" />
			</button>
		</div>
	</nav>

	<!-- Список чатов -->
	<section
		class="w-full flex-col border-r border-surface-300-700 bg-surface-100-900 lg:w-[340px] lg:shrink-0 {activeChatId !==
		null
			? 'hidden lg:flex'
			: 'flex'}"
	>
		<header class="flex items-center gap-2 border-b border-surface-300-700 px-3 py-3">
			<span class="lg:hidden">
				<a href="/settings" title="Настройки"><Logo compact /></a>
			</span>
			<div class="relative flex-1">
				<Icon
					name="search"
					size={16}
					class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-surface-700-300"
				/>
				<input
					class="w-full rounded-base border border-surface-300-700 bg-surface-200-800 py-2 pr-3 pl-9 text-sm outline-none placeholder:text-surface-700-300 focus:border-primary-500"
					placeholder="Поиск по чатам"
					bind:value={search}
					autocomplete="off"
				/>
			</div>
			<button
				type="button"
				class="rounded-base p-2 text-surface-700-300 transition hover:bg-surface-200-800 hover:text-primary-500 cursor-pointer"
				title="Новый чат"
				onclick={() => (newChatOpen = true)}
			>
				<Icon name="plus" />
			</button>
		</header>

		<div class="app-scroll min-h-0 flex-1 overflow-y-auto">
			{#if chats.loading && !chats.loaded}
				<div class="flex justify-center py-6 text-surface-700-300">
					<Spinner size={20} />
				</div>
			{:else if listError}
				<p class="p-4 text-sm text-error-500">{listError}</p>
			{:else if filteredChats.length === 0}
				<p class="p-4 text-sm text-surface-700-300">
					{search.trim() ? 'Ничего не найдено' : 'Пока нет чатов. Начните с кнопки «+».'}
				</p>
			{:else}
				{#each filteredChats as chat (chat.id)}
					<ChatListItem
						{chat}
						{currentUserId}
						active={chat.id === activeChatId}
						onselect={(id) => void goto(`/chats/${id}`)}
					/>
				{/each}
			{/if}
		</div>
	</section>

	<!-- Область переписки -->
	<section class="min-w-0 flex-1 {activeChatId === null ? 'hidden lg:flex' : 'flex'} flex-col">
		{@render children()}
	</section>
</div>

<NewChatDialog
	open={newChatOpen}
	onclose={() => (newChatOpen = false)}
	onselect={(user) => void openUser(user.id)}
/>
