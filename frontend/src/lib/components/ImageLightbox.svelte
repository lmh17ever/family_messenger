<script lang="ts">
	import Icon from './Icon.svelte';

	let { src, alt, onclose }: { src: string; alt: string; onclose: () => void } = $props();

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') onclose();
	}
</script>

<svelte:window onkeydown={onKeydown} />

<div
	class="app-backdrop"
	role="presentation"
	onclick={(event) => {
		if (event.target === event.currentTarget) onclose();
	}}
>
	<figure class="flex max-h-full max-w-full flex-col items-center gap-2">
		<img {src} {alt} class="max-h-[85vh] max-w-full rounded-container object-contain" />
		<figcaption class="text-xs text-surface-700-300">{alt}</figcaption>
	</figure>
	<button
		type="button"
		class="absolute top-4 right-4 rounded-base bg-surface-100-900/80 p-2 text-surface-950-50 transition hover:bg-surface-100-900"
		aria-label="Закрыть просмотр"
		onclick={onclose}
	>
		<Icon name="close" />
	</button>
</div>
