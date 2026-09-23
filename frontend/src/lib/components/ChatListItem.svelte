<script lang="ts">
	import type { Chat } from '$lib/api/types';
	import { publicFileUrl } from '$lib/config';
	import { chatPartner, chatTitle, describeMessage } from '$lib/utils/text';
	import { formatDate } from '$lib/utils/time';
	import Avatar from './Avatar.svelte';

	let {
		chat,
		currentUserId,
		active = false,
		onselect
	}: {
		chat: Chat;
		currentUserId: number;
		active?: boolean;
		onselect: (chatId: number) => void;
	} = $props();

	const title = $derived(chatTitle(chat, currentUserId));
	const partner = $derived(chatPartner(chat, currentUserId));
	const avatarUrl = $derived(partner?.avatar_url ?? publicFileUrl(chat.avatar_key));
	const preview = $derived(describeMessage(chat.last_message, currentUserId));
	const dateLabel = $derived(chat.last_message_at ? formatDate(chat.last_message_at) : '');
</script>

<button
	type="button"
	class="flex w-full items-center gap-3 border-l-2 px-3 py-2.5 text-left transition {active
		? 'border-primary-500 bg-surface-200-800'
		: 'border-transparent hover:bg-surface-200-800 cursor-pointer'}"
	onclick={() => onselect(chat.id)}
>
	<Avatar url={avatarUrl} name={title} />
	<div class="min-w-0 flex-1">
		<div class="flex items-baseline justify-between gap-2">
			<p class="truncate text-sm font-semibold">{title}</p>
			<span class="shrink-0 text-[11px] text-surface-700-300">{dateLabel}</span>
		</div>
		<div class="mt-0.5 flex items-center justify-between gap-2">
			<p class="truncate text-xs text-surface-700-300">{preview}</p>
			{#if chat.unread_count > 0}
				<span
					class="grid min-w-5 shrink-0 place-items-center rounded-full bg-primary-500 px-1 py-0.5 text-[11px] font-bold text-primary-contrast-500"
				>
					{chat.unread_count}
				</span>
			{/if}
		</div>
	</div>
</button>
