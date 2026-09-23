<script lang="ts">
	import type { Attachment, Message } from '$lib/api/types';
	import { formatTime, toIso } from '$lib/utils/time';
	import AttachmentView from './AttachmentView.svelte';
	import Avatar from './Avatar.svelte';
	import Icon from './Icon.svelte';

	let {
		message,
		own,
		isGroup,
		senderName,
		senderAvatarUrl = null,
		showSender,
		edited,
		onedit,
		ondelete,
		onpreview
	}: {
		message: Message;
		own: boolean;
		isGroup: boolean;
		senderName: string;
		senderAvatarUrl?: string | null;
		showSender: boolean;
		edited: boolean;
		onedit: (messageId: number, text: string) => Promise<boolean>;
		ondelete: (messageId: number) => void;
		onpreview: (attachment: Attachment) => void;
	} = $props();

	let editing = $state(false);
	let draft = $state('');
	let saving = $state(false);

	function startEdit() {
		draft = message.text ?? '';
		editing = true;
	}

	async function save() {
		const text = draft.trim();
		if (!text || text === message.text) {
			editing = false;
			return;
		}
		saving = true;
		try {
			if (await onedit(message.id, text)) {
				editing = false;
			}
		} finally {
			saving = false;
		}
	}
</script>

<div class="flex gap-2 {own ? 'justify-end' : 'justify-start'}">
	{#if isGroup && !own && showSender}
		<Avatar url={senderAvatarUrl} name={senderName} size="sm" class="mt-1" />
	{:else if isGroup && !own}
		<span class="w-8 shrink-0"></span>
	{/if}

	<div class="group relative flex min-w-0 max-w-[80%] flex-col {own ? 'items-end' : 'items-start'}">
		{#if own && !editing}
			<div
				class="mb-1 flex gap-1 opacity-100 transition lg:opacity-0 lg:group-hover:opacity-100 lg:focus-within:opacity-100"
			>
				{#if message.text}
					<button
						type="button"
						class="rounded-base bg-surface-200-800 p-1 text-surface-700-300 transition hover:text-primary-500 cursor-pointer"
						title="Редактировать"
						onclick={startEdit}
					>
						<Icon name="pencil" size={14}/>
					</button>
				{/if}
				<button
					type="button"
					class="rounded-base bg-surface-200-800 p-1 text-surface-700-300 transition hover:text-error-500 cursor-pointer"
					title="Удалить"
					onclick={() => ondelete(message.id)}
				>
					<Icon name="trash" size={14} />
				</button>
			</div>
		{/if}

		{#if editing}
			<div class="w-80vw border border-primary-500 bg-surface-200-800 p-2">
				<textarea
					class="h-20 w-full resize-none rounded-base bg-surface-100-900 p-2 text-sm outline-none app-scroll"
					bind:value={draft}
					disabled={saving}
				></textarea>
				<div class="mt-2 flex justify-end gap-2">
					<button
						type="button"
						class="rounded-base px-2 py-1 text-xs text-surface-700-300 transition hover:text-surface-950-50 cursor-pointer"
						onclick={() => (editing = false)}
					>
						Отмена
					</button>
					<button
						type="button"
						class="rounded-base bg-primary-500 px-2.5 py-1 text-xs font-semibold text-primary-contrast-500 transition hover:bg-primary-600 disabled:opacity-60 cursor-pointer"
						disabled={saving || !draft.trim()}
						onclick={() => void save()}
					>
						Сохранить
					</button>
				</div>
			</div>
		{:else}
			<div
				class="app-bubble max-w-full {own
					? 'preset-filled-primary-500'
					: 'border border-surface-300-700 bg-surface-200-800'}"
			>
				{#if isGroup && !own && showSender}
					<p class="mb-0.5 text-xs font-semibold text-primary-400">{senderName}</p>
				{/if}

				{#if message.text}
					<p class="break-words">{message.text}</p>
				{/if}

				{#if message.attachments.length}
					<div class="mt-1 flex flex-col gap-1">
						{#each message.attachments as attachment (attachment.id)}
							<AttachmentView {attachment} {onpreview} />
						{/each}
					</div>
				{/if}

				<div
					class="flex items-center justify-end gap-1.5 text-[11px] {own
						? 'text-primary-contrast-500/70'
						: 'text-surface-700-300'}"
				>
					{#if edited}
						<span>изменено</span>
					{/if}
					<time datetime={toIso(message.created_at)}>{formatTime(message.created_at)}</time>
				</div>
			</div>
		{/if}
	</div>
</div>
