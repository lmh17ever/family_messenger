<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	import { ApiError } from '$lib/api/client';
	import * as messagesApi from '$lib/api/messages';
	import type { Attachment, Message, MessageCreate } from '$lib/api/types';
	import Avatar from '$lib/components/Avatar.svelte';
	import Composer from '$lib/components/Composer.svelte';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import ImageLightbox from '$lib/components/ImageLightbox.svelte';
	import MessageList from '$lib/components/MessageList.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import { MESSAGE_PAGE_SIZE, publicFileUrl } from '$lib/config';
	import { chatSocket, closeChatSocket, openChatSocket } from '$lib/realtime/sockets';
	import { chats } from '$lib/stores/chats.svelte';
	import { editedMessages } from '$lib/stores/edits.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { ui } from '$lib/stores/ui.svelte';
	import { chatPartner, chatTitle } from '$lib/utils/text';

	const chatId = $derived(Number(page.params.id));
	const currentUserId = $derived(session.user?.id ?? 0);
	const chat = $derived(chats.items.find((item) => item.id === chatId) ?? null);
	const title = $derived(chat ? chatTitle(chat, currentUserId) : 'Чат');
	const partner = $derived(chat ? chatPartner(chat, currentUserId) : null);
	const avatarUrl = $derived(partner?.avatar_url ?? publicFileUrl(chat?.avatar_key ?? null));

	let messages = $state<Message[]>([]);
	let loading = $state(true);
	let loadingOlder = $state(false);
	let hasMore = $state(false);
	let loadError = $state<string | null>(null);

	let searchOpen = $state(false);
	let searchQuery = $state('');
	let searchResults = $state<Message[]>([]);
	let searching = $state(false);

	let confirmDeleteChat = $state(false);
	let deletingChat = $state(false);
	let lightbox = $state<Attachment | null>(null);
	let droppedFiles = $state<File[]>([]);
	let dragging = $state(false);

	function onWindowActivity() {
		if (!document.hidden) void chats.markRead(chatId);
	}

	// Загрузка чата при входе и переключении между переписками
	$effect(() => {
		const id = chatId;
		if (!Number.isFinite(id)) return;

		let cancelled = false;
		chats.activeChatId = id;
		messages = [];
		searchOpen = false;
		searchQuery = '';
		searchResults = [];
		loading = true;
		loadError = null;

		void (async () => {
			try {
				const page = await messagesApi.getMessages(id, { limit: MESSAGE_PAGE_SIZE });
				if (cancelled) return;
				messages = [...page].reverse();
				hasMore = page.length === MESSAGE_PAGE_SIZE;
				void chats.markRead(id);
			} catch (cause) {
				if (!cancelled) {
					loadError =
						cause instanceof ApiError ? cause.message : 'Не удалось загрузить сообщения';
				}
			} finally {
				if (!cancelled) loading = false;
			}
		})();

		void chats.refreshChat(id);
		openChatSocket(id);
		window.addEventListener('focus', onWindowActivity);
		document.addEventListener('visibilitychange', onWindowActivity);

		return () => {
			cancelled = true;
			closeChatSocket();
			window.removeEventListener('focus', onWindowActivity);
			document.removeEventListener('visibilitychange', onWindowActivity);
			chats.activeChatId = null;
		};
	});



	/** Добавляем/обновляем сообщение с сохранением порядка по id */
	function upsertMessage(message: Message) {
		if (message.chat_id !== chatId) return;
		const index = messages.findIndex((item) => item.id === message.id);
		if (index === -1) {
			messages = [...messages, message].sort((a, b) => a.id - b.id);
		} else {
			messages[index] = message;
		}
		if (chat && (!chat.last_message || message.id >= chat.last_message.id)) {
			chat.last_message = message;
			chat.last_message_at = message.created_at;
		}
	}

	// События сокета чата
	$effect(() => {
		return chatSocket.onEvent((event) => {
			if (event.type === 'message.created') {
				upsertMessage(event.message);
				if (event.message.sender_id !== currentUserId && !document.hidden) {
					void chats.markRead(chatId);
				}
				return;
			}
			if (event.type === 'message.updated') {
				upsertMessage(event.message);
				editedMessages.mark(event.message.id);
				return;
			}
			if (event.type === 'message.deleted') {
				messages = messages.filter((item) => item.id !== event.message_id);
				return;
			}
			if (event.type === 'error') {
				ui.error('Не удалось отправить сообщение');
			}
		});
	});

	// Поиск по сообщениям внутри чата (с задержкой на ввод)
	$effect(() => {
		const query = searchQuery.trim();
		const id = chatId;
		if (!searchOpen || !query) {
			searchResults = [];
			return;
		}

		let cancelled = false;
		const timer = setTimeout(async () => {
			searching = true;
			try {
				const found = await messagesApi.getMessages(id, { search: query, limit: 50 });
				if (!cancelled) searchResults = [...found].reverse();
			} catch (cause) {
				if (!cancelled) {
					ui.error(cause instanceof ApiError ? cause.message : 'Ошибка поиска');
				}
			} finally {
				if (!cancelled) searching = false;
			}
		}, 300);

		return () => {
			cancelled = true;
			clearTimeout(timer);
		};
	});

	async function loadOlder() {
		if (!hasMore || loadingOlder) return;
		loadingOlder = true;
		try {
			const older = await messagesApi.getMessages(chatId, {
				offset: messages.length,
				limit: MESSAGE_PAGE_SIZE
			});
			if (older.length) {
				messages = [...[...older].reverse(), ...messages];
			}
			hasMore = older.length === MESSAGE_PAGE_SIZE;
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось загрузить историю');
		} finally {
			loadingOlder = false;
		}
	}

	async function sendMessage(payload: MessageCreate): Promise<boolean> {
		try {
			upsertMessage(await messagesApi.createMessage(chatId, payload));
			return true;
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось отправить сообщение');
			return false;
		}
	}

	async function editMessage(messageId: number, text: string): Promise<boolean> {
		try {
			upsertMessage(await messagesApi.updateMessage(chatId, messageId, text));
			editedMessages.mark(messageId);
			return true;
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось изменить сообщение');
			return false;
		}
	}

	async function deleteMessage(messageId: number) {
		try {
			await messagesApi.deleteMessage(chatId, messageId);
			messages = messages.filter((item) => item.id !== messageId);
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось удалить сообщение');
		}
	}

	async function removeChat() {
		deletingChat = true;
		try {
			await chats.removeChat(chatId);
			ui.success('Чат удалён');
			await goto('/chats');
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось удалить чат');
		} finally {
			deletingChat = false;
			confirmDeleteChat = false;
		}
	}

	function onDropFiles(event: DragEvent) {
		event.preventDefault();
		dragging = false;
		const files = Array.from(event.dataTransfer?.files ?? []);
		if (files.length) droppedFiles = [...droppedFiles, ...files];
	}
</script>

<div class="flex h-full min-h-0 flex-1 flex-col">
	<header
		class="flex items-center gap-2 border-b border-surface-300-700 bg-surface-100-900 px-3 py-2.5 lg:px-6"
	>
		<button
			type="button"
			class="rounded-base p-2 text-surface-700-300 transition hover:bg-surface-200-800 lg:hidden"
			title="К списку чатов"
			onclick={() => void goto('/chats')}
		>
			<Icon name="back" />
		</button>

		<Avatar url={avatarUrl} name={title} />

		<div class="min-w-0 flex-1">
			<p class="truncate text-sm font-semibold">{title}</p>
			{#if chat?.type === 'group'}
				<p class="truncate text-[11px] text-surface-700-300">
					{chat.participants.length} участников
				</p>
			{/if}
		</div>

		<button
			type="button"
			class="rounded-base cursor-pointer p-2 text-surface-700-300 transition hover:bg-surface-200-800 hover:text-primary-500 {searchOpen
				? 'text-primary-500'
				: ''}"
			title="Поиск по сообщениям"
			onclick={() => {
				searchOpen = !searchOpen;
				searchQuery = '';
			}}
		>
			<Icon name="search" />
		</button>

		<button
			type="button"
			class="rounded-base p-2 text-surface-700-300 transition hover:bg-surface-200-800 hover:text-error-500 cursor-pointer"
			title="Удалить чат"
			onclick={() => (confirmDeleteChat = true)}
		>
			<Icon name="trash" />
		</button>
	</header>

	{#if searchOpen}
		<div class="border-b border-surface-300-700 bg-surface-100-900 px-3 py-2 lg:px-6">
			<input
				class="w-full rounded-base border border-surface-300-700 bg-surface-200-800 px-3 py-2 text-sm outline-none placeholder:text-surface-700-300 focus:border-primary-500"
				placeholder="Поиск по сообщениям в этом чате"
				bind:value={searchQuery}
				autocomplete="off"
			/>
		</div>
	{/if}

	{#if loading}
		<div class="grid flex-1 place-items-center">
			<Spinner size={24} class="text-primary-500" />
		</div>
	{:else if loadError}
		<p class="grid flex-1 place-items-center p-6 text-center text-sm text-error-500">{loadError}</p>
	{:else if !chat}
		<div class="grid flex-1 place-items-center">
			<Spinner size={24} class="text-primary-500" />
		</div>
	{:else if searchOpen}
		{#if searching}
			<div class="grid flex-1 place-items-center">
				<Spinner size={20} class="text-primary-500" />
			</div>
		{:else if searchResults.length === 0}
			<div class="grid flex-1 place-items-center p-6 text-sm text-surface-700-300">
				{searchQuery.trim() ? 'Ничего не найдено' : 'Введите текст для поиска'}
			</div>
		{:else}
			<MessageList
				messages={searchResults}
				{chat}
				{currentUserId}
				onloadolder={async () => {}}
				onedit={editMessage}
				ondelete={deleteMessage}
				onpreview={(attachment) => (lightbox = attachment)}
			/>
		{/if}
	{:else}
		<div class="relative flex min-h-0 flex-1 flex-col">
			<div
				role="presentation"
				class="relative flex min-h-0 flex-1 flex-col"
				ondragover={(event) => {
					event.preventDefault();
					dragging = true;
				}}
				ondragleave={() => (dragging = false)}
				ondrop={onDropFiles}
			>
				<MessageList
					{messages}
					{chat}
					{currentUserId}
					{loadingOlder}
					{hasMore}
					onloadolder={loadOlder}
					onedit={editMessage}
					ondelete={deleteMessage}
					onpreview={(attachment) => (lightbox = attachment)}
				/>
				{#if dragging}
					<div
						class="pointer-events-none absolute inset-2 z-10 grid place-items-center rounded-container border-2 border-dashed border-primary-500 bg-surface-100-900/80 text-sm text-primary-500"
					>
						Отпустите файлы, чтобы прикрепить
					</div>
				{/if}
			</div>

			<Composer
				{chatId}
				incomingFiles={droppedFiles}
				onincomingconsumed={() => (droppedFiles = [])}
				onsend={sendMessage}
			/>
		</div>
	{/if}
</div>

<ConfirmDialog
	open={confirmDeleteChat}
	title="Удалить чат"
	text="Чат будет удалён у всех участников вместе с сообщениями. Действие необратимо."
	confirmLabel="Удалить"
	danger
	busy={deletingChat}
	onconfirm={() => void removeChat()}
	oncancel={() => (confirmDeleteChat = false)}
/>

{#if lightbox}
	<ImageLightbox
		src={lightbox.url ?? ''}
		alt={lightbox.filename}
		onclose={() => (lightbox = null)}
	/>
{/if}
