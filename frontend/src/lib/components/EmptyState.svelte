<script lang="ts">
	import Icon from './Icon.svelte';

	let {
		title,
		text = '',
		icon = 'message'
	}: { title: string; text?: string; icon?: string } = $props();
</script>

<div class="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
	<span class="grid h-14 w-14 place-items-center rounded-full bg-surface-200-800 text-primary-500">
		<Icon name={icon} size={26} />
	</span>
	<p class="text-base font-semibold">{title}</p>
	{#if text}
		<p class="max-w-sm text-sm text-surface-700-300">{text}</p>
	{/if}
</div>
