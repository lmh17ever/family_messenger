<script lang="ts">
	import type { Attachment } from '$lib/api/types';
	import { isImage, isPreviewableImage } from '$lib/utils/text';
	import { formatBytes } from '$lib/utils/time';
	import Icon from './Icon.svelte';

	let {
		attachment,
		onpreview
	}: { attachment: Attachment; onpreview: (attachment: Attachment) => void } = $props();

	const previewable = $derived(isPreviewableImage(attachment));
</script>

{#if previewable}
	<button
		type="button"
		class="block overflow-hidden rounded-base"
		title="Открыть изображение"
		onclick={() => onpreview(attachment)}
	>
		<img
			src={attachment.url ?? ''}
			alt={attachment.filename}
			class="max-h-64 w-auto max-w-full object-cover"
			loading="lazy"
		/>
	</button>
{:else}
	<div
		class="flex items-center gap-2 rounded-base border border-surface-300-700 bg-surface-200-800 px-2.5 py-2"
	>
		<Icon
			name={isImage(attachment.content_type) ? 'image' : 'file'}
			size={20}
			class="shrink-0 text-primary-500"
		/>
		<div class="min-w-0">
			<p class="truncate text-xs font-medium">{attachment.filename}</p>
			<p class="text-[11px] text-surface-700-300">{formatBytes(attachment.size)}</p>
		</div>
		{#if attachment.url}
			<a
				class="ml-2 shrink-0 rounded-base p-1 text-surface-700-300 transition hover:text-primary-500"
				href={attachment.url}
				target="_blank"
				rel="noreferrer"
				download={attachment.filename}
				aria-label="Скачать файл"
			>
				<Icon name="download" size={16} />
			</a>
		{:else}
			<span class="ml-2 shrink-0 p-1 text-surface-700-300" title="Ссылка недоступна">
				<Icon name="alert" size={16} />
			</span>
		{/if}
	</div>
{/if}
