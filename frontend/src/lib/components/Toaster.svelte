<script lang="ts">
	import { ui } from '$lib/stores/ui.svelte';
	import Icon from './Icon.svelte';

	const ICON_BY_KIND: Record<string, string> = {
		info: 'message',
		success: 'check',
		error: 'alert'
	};

	const COLOR_BY_KIND: Record<string, string> = {
		info: 'text-primary-500',
		success: 'text-success-500',
		error: 'text-error-500'
	};
</script>

<div
	class="pointer-events-none fixed top-4 right-4 z-[100] flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2"
>
	{#each ui.toasts as toast (toast.id)}
		<div
			class="app-bubble-new pointer-events-auto flex items-start gap-2 rounded-container border border-surface-300-700 bg-surface-100-900 px-3 py-2 shadow-xl"
		>
			<Icon name={ICON_BY_KIND[toast.kind] ?? 'message'} class={COLOR_BY_KIND[toast.kind] ?? ''} />
			<p class="flex-1 text-sm break-words">{toast.text}</p>
			<button
				type="button"
				class="rounded-base p-0.5 text-surface-700-300 transition hover:text-surface-950-50"
				aria-label="Закрыть уведомление"
				onclick={() => ui.dismiss(toast.id)}
			>
				<Icon name="close" size={16} />
			</button>
		</div>
	{/each}
</div>
