<script lang="ts">
	import type { Attachment, Chat, Message } from '$lib/api/types';
	import { editedMessages } from '$lib/stores/edits.svelte';
	import { userById } from '$lib/utils/text';
	import { dayKey, formatDate } from '$lib/utils/time';
	import MessageBubble from './MessageBubble.svelte';
	import Spinner from './Spinner.svelte';

	let {
		messages,
		chat,
		currentUserId,
		loadingOlder = false,
		hasMore = false,
		onloadolder,
		onedit,
		ondelete,
		onpreview
	}: {
		/** Сообщения в порядке возрастания (старые сверху) */
		messages: Message[];
		chat: Chat;
		currentUserId: number;
		loadingOlder?: boolean;
		hasMore?: boolean;
		onloadolder: () => Promise<void>;
		onedit: (messageId: number, text: string) => Promise<boolean>;
		ondelete: (messageId: number) => void;
		onpreview: (attachment: Attachment) => void;
	} = $props();

	let container = $state<HTMLDivElement | null>(null);
	let stickToBottom = true;
	let lastRenderedId = 0;
	let initialized = false;

	const isGroup = $derived(chat.type === 'group');

	function scrollToBottom(smooth = false) {
		const node = container;
		if (!node) return;
		node.scrollTo({ top: node.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
	}

	// первый рендер — сразу вниз; новые сообщения — вниз, если пользователь не листает историю
	$effect(() => {
		const list = messages;
		const node = container;
		if (!node || list.length === 0) return;

		const lastId = list[list.length - 1].id;
		if (!initialized) {
			initialized = true;
			lastRenderedId = lastId;
			scrollToBottom();
			return;
		}
		if (lastId !== lastRenderedId) {
			lastRenderedId = lastId;
			if (stickToBottom) scrollToBottom(true);
		}
	});

	async function handleScroll() {
		const node = container;
		if (!node) return;

		stickToBottom = node.scrollHeight - node.scrollTop - node.clientHeight < 120;

		if (node.scrollTop < 120 && hasMore && !loadingOlder) {
			const previousHeight = node.scrollHeight;
			const previousTop = node.scrollTop;
			await onloadolder();
			requestAnimationFrame(() => {
				const current = container;
				if (!current) return;
				current.scrollTop = previousTop + (current.scrollHeight - previousHeight);
			});
		}
	}
</script>

<div
	class="app-scroll min-h-0 flex-1 overflow-y-auto px-3 py-4 lg:px-6"
	bind:this={container}
	onscroll={handleScroll}
>
	{#if loadingOlder}
		<div class="flex justify-center py-2 text-surface-700-300">
			<Spinner size={18} />
		</div>
	{/if}

	<div class="flex flex-col gap-1.5">
		{#each messages as message, index (message.id)}
			{@const previous = index > 0 ? messages[index - 1] : null}
			{@const newDay = !previous || dayKey(previous.created_at) !== dayKey(message.created_at)}
			{@const sender = userById(chat, message.sender_id)}
			{@const showSender =
				isGroup &&
				message.sender_id !== currentUserId &&
				(!previous || previous.sender_id !== message.sender_id || newDay)}
			{#if newDay}
				<div class="my-3 flex items-center justify-center">
					<span class="rounded-full bg-surface-200-800 px-2.5 py-0.5 text-[11px] text-surface-700-300">
						{formatDate(message.created_at)}
					</span>
				</div>
			{/if}
			<MessageBubble
				{message}
				own={message.sender_id === currentUserId}
				{isGroup}
				senderName={sender?.username ?? 'Пользователь'}
				senderAvatarUrl={sender?.avatar_url ?? null}
				{showSender}
				edited={editedMessages.has(message.id)}
				{onedit}
				{ondelete}
				{onpreview}
			/>
		{/each}
	</div>
</div>
