<script lang="ts">
	import type { Snippet } from 'svelte';
	import Icon from './Icon.svelte';

	let {
		open,
		title,
		children,
		onclose,
		width = 'max-w-md'
	}: {
		open: boolean;
		title: string;
		children: Snippet;
		onclose: () => void;
		width?: string;
	} = $props();

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && open) onclose();
	}
</script>

<svelte:window onkeydown={onKeydown} />

{#if open}
	<!-- Клик по затемнению закрывает окно -->
	<div
		class="app-backdrop"
		role="presentation"
		onclick={(event) => {
			if (event.target === event.currentTarget) onclose();
		}}
	>
		<div
			class="w-full {width} overflow-hidden rounded-container border border-surface-300-700 bg-surface-100-900 shadow-2xl"
			role="dialog"
			aria-modal="true"
			aria-label={title}
		>
			<header class="flex items-center justify-between gap-4 border-b border-surface-300-700 px-4 py-3">
				<h2 class="text-base font-semibold">{title}</h2>
				<button
					type="button"
					class="rounded-base p-1 text-surface-700-300 transition hover:bg-surface-200-800 hover:text-surface-950-50"
					aria-label="Закрыть"
					onclick={onclose}
				>
					<Icon name="close" size={18} />
				</button>
			</header>
			<div class="p-4">
				{@render children()}
			</div>
		</div>
	</div>
{/if}
