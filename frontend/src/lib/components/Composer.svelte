<script lang="ts">
	import { ApiError, uploadToS3 } from '$lib/api/client';
	import * as attachmentsApi from '$lib/api/attachments';
	import type { MessageCreate } from '$lib/api/types';
	import { MESSAGE_MAX_LENGTH } from '$lib/config';
	import { ui } from '$lib/stores/ui.svelte';
	import { isImage } from '$lib/utils/text';
	import { formatBytes } from '$lib/utils/time';
	import Icon from './Icon.svelte';

	interface UploadItem {
		key: string;
		file: File;
		progress: number;
		attachmentId: number | null;
		error: string | null;
		previewUrl: string | null;
		controller: AbortController;
	}

	let {
		chatId,
		disabled = false,
		incomingFiles = [],
		onincomingconsumed,
		onsend
	}: {
		chatId: number;
		disabled?: boolean;
		/** файлы, брошенные в область сообщений: страница чата сбрасывает массив после обработки */
		incomingFiles?: File[];
		onincomingconsumed?: () => void;
		onsend: (payload: MessageCreate) => Promise<boolean>;
	} = $props();

	let text = $state('');
	let uploads = $state<UploadItem[]>([]);
	let dragging = $state(false);
	let sending = $state(false);
	let textarea = $state<HTMLTextAreaElement | null>(null);
	let fileInput = $state<HTMLInputElement | null>(null);
	let counter = 0;

	const uploading = $derived(uploads.some((item) => item.attachmentId === null && !item.error));
	const readyIds = $derived(
		uploads
			.filter((item) => item.attachmentId !== null)
			.map((item) => item.attachmentId as number)
	);
	const canSend = $derived(
		!disabled && !sending && !uploading && (text.trim().length > 0 || readyIds.length > 0)
	);

	$effect(() => {
		if (incomingFiles.length) {
			const files = [...incomingFiles];
			onincomingconsumed?.();
			void addFiles(files);
		}
	});

	async function addFiles(files: File[]) {
		const accepted = files.filter((file) => file.size > 0);
		for (const file of accepted) {
			uploads = [
				...uploads,
				{
					key: `upload-${counter++}`,
					file,
					progress: 0,
					attachmentId: null,
					error: null,
					previewUrl: isImage(file.type) ? URL.createObjectURL(file) : null,
					controller: new AbortController()
				}
			];
			// элемент берём из массива, чтобы получить рекативный прокси ($state)
			void runUpload(uploads[uploads.length - 1]);
		}
	}

	async function runUpload(item: UploadItem) {
		try {
			const presigned = await attachmentsApi.presignAttachment(chatId, item.file);
			await uploadToS3(presigned.upload, item.file, {
				signal: item.controller.signal,
				onProgress: (ratio) => {
					item.progress = ratio;
				}
			});
			const confirmed = await attachmentsApi.confirmAttachment(presigned.attachment_id);
			item.attachmentId = confirmed.id;
			item.progress = 1;
		} catch (error) {
			if (error instanceof DOMException && error.name === 'AbortError') return;
			item.error = error instanceof ApiError ? error.message : 'Не удалось загрузить файл';
			ui.error(item.error);
		}
	}

	function removeUpload(key: string) {
		const item = uploads.find((candidate) => candidate.key === key);
		item?.controller.abort();
		if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
		uploads = uploads.filter((candidate) => candidate.key !== key);
	}

	function clearUploads() {
		for (const item of uploads) {
			if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
		}
		uploads = [];
	}

	function resize() {
		const node = textarea;
		if (!node) return;
		node.style.height = 'auto';
		node.style.height = `${Math.min(node.scrollHeight, 180)}px`;
	}

	async function submit() {
		if (!canSend) return;
		sending = true;
		try {
			const ok = await onsend({
				text: text.trim() ? text.trim() : null,
				attachment_ids: readyIds
			});
			if (ok) {
				text = '';
				clearUploads();
				resize();
			}
		} finally {
			sending = false;
		}
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
			event.preventDefault();
			void submit();
		}
	}

	function onPaste(event: ClipboardEvent) {
		const files = Array.from(event.clipboardData?.files ?? []);
		if (files.length) {
			event.preventDefault();
			void addFiles(files);
		}
	}

	function onDrop(event: DragEvent) {
		event.preventDefault();
		dragging = false;
		const files = Array.from(event.dataTransfer?.files ?? []);
		if (files.length) void addFiles(files);
	}
</script>

<div
	role="presentation"
	class="relative border-t border-surface-300-700 bg-surface-100-900 px-3 py-3 lg:px-6"
	ondragover={(event) => {
		event.preventDefault();
		dragging = true;
	}}
	ondragleave={() => (dragging = false)}
	ondrop={onDrop}
>
	{#if dragging}
		<div
			class="pointer-events-none absolute inset-2 z-10 grid place-items-center rounded-container border-2 border-dashed border-primary-500 bg-surface-100-900/90 text-sm text-primary-500"
		>
			Отпустите файлы, чтобы прикрепить
		</div>
	{/if}

	{#if uploads.length}
		<ul class="mb-2 flex flex-wrap gap-2">
			{#each uploads as item (item.key)}
				<li
					class="flex w-52 flex-col gap-1 rounded-base border border-surface-300-700 bg-surface-200-800 p-2"
				>
					<div class="flex items-center gap-2">
						{#if item.previewUrl}
							<img src={item.previewUrl} alt="" class="h-8 w-8 shrink-0 rounded-base object-cover" />
						{:else}
							<span
								class="grid h-8 w-8 shrink-0 place-items-center rounded-base bg-surface-300-700 text-primary-500"
							>
								<Icon name="file" size={16} />
							</span>
						{/if}
						<div class="min-w-0 flex-1">
							<p class="truncate text-[11px] font-medium">{item.file.name}</p>
							<p class="text-[10px] text-surface-700-300">{formatBytes(item.file.size)}</p>
						</div>
						<button
							type="button"
							class="shrink-0 rounded-base p-0.5 text-surface-700-300 transition hover:text-error-500"
							title={item.attachmentId === null && !item.error ? 'Отменить загрузку' : 'Убрать'}
							onclick={() => removeUpload(item.key)}
						>
							<Icon name="close" size={14} />
						</button>
					</div>
					{#if item.error}
						<p class="text-[10px] text-error-500">{item.error}</p>
					{:else if item.attachmentId === null}
						<div class="app-progress">
							<div
								class="app-progress-bar"
								style={`width:${Math.round(item.progress * 100)}%`}
							></div>
						</div>
					{:else}
						<p class="text-[10px] text-success-500">Готово к отправке</p>
					{/if}
				</li>
			{/each}
		</ul>
	{/if}

	<div class="flex items-end gap-2">
		<button
			type="button"
			class="grid h-10 w-10 shrink-0 place-items-center rounded-base text-surface-700-300 transition hover:bg-surface-200-800 hover:text-primary-500 disabled:opacity-50 cursor-pointer"
			title="Прикрепить файлы"
			{disabled}
			onclick={() => fileInput?.click()}
		>
			<Icon name="paperclip" />
		</button>
		<input
			bind:this={fileInput}
			type="file"
			multiple
			class="hidden"
			onchange={(event) => {
				const files = Array.from(event.currentTarget.files ?? []);
				event.currentTarget.value = '';
				if (files.length) void addFiles(files);
			}}
		/>

		<textarea
			bind:this={textarea}
			bind:value={text}
			rows="1"
			{disabled}
			maxlength={MESSAGE_MAX_LENGTH}
			placeholder="Сообщение…"
			class="app-scroll max-h-44 min-h-10 flex-1 resize-none rounded-container border border-surface-300-700 bg-surface-200-800 px-3 py-2 text-sm outline-none placeholder:text-surface-700-300 focus:border-primary-500 disabled:opacity-60"
			oninput={resize}
			onkeydown={onKeydown}
			onpaste={onPaste}
		></textarea>

		<button
			type="button"
			class="grid h-10 w-10 shrink-0 place-items-center rounded-base bg-primary-500 text-primary-contrast-500 transition hover:bg-primary-600 disabled:opacity-50 cursor-pointer"
			title="Отправить (Enter)"
			disabled={!canSend}
			onclick={() => void submit()}
		>
			<Icon name="send" class="translate-x-[-1px] translate-y-[1px]"/>
		</button>
	</div>

	<p class="mt-1 px-1 text-[11px] text-surface-700-300">
		Enter — отправить, Shift+Enter — новая строка
	</p>
</div>
