<script lang="ts">
	import { ICONS } from './icons';

	let {
		name,
		size = 20,
		class: className = ''
	}: { name: string; size?: number; class?: string } = $props();

	const body = $derived(ICONS[name] ?? '');
</script>

<svg
	xmlns="http://www.w3.org/2000/svg"
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	stroke="currentColor"
	stroke-width="1.8"
	stroke-linecap="round"
	stroke-linejoin="round"
	class={className}
	aria-hidden="true"
>
	{@html body}
</svg>
