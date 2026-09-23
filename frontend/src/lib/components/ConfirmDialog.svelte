<script lang="ts">
	import Modal from './Modal.svelte';

	let {
		open,
		title,
		text,
		confirmLabel = 'Подтвердить',
		danger = false,
		busy = false,
		onconfirm,
		oncancel
	}: {
		open: boolean;
		title: string;
		text: string;
		confirmLabel?: string;
		danger?: boolean;
		busy?: boolean;
		onconfirm: () => void;
		oncancel: () => void;
	} = $props();
</script>

<Modal {open} {title} onclose={oncancel}>
	<p class="text-sm text-surface-700-300">{text}</p>
	<div class="mt-5 flex justify-end gap-2">
		<button
			type="button"
			class="rounded-base px-3 py-2 text-sm font-medium text-surface-700-300 transition hover:bg-surface-200-800 hover:text-surface-950-50 cursor-pointer"
			onclick={oncancel}
		>
			Отмена
		</button>
		<button
			type="button"
			class="rounded-base cursor-pointer px-3 py-2 text-sm font-semibold transition disabled:opacity-60 {danger
				? 'bg-error-500 text-error-contrast-500 hover:bg-error-600'
				: 'bg-primary-500 text-primary-contrast-500 hover:bg-primary-600'}"
			disabled={busy}
			onclick={onconfirm}
		>
			{confirmLabel}
		</button>
	</div>
</Modal>
