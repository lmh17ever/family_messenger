<script lang="ts">
	import { APP_NAME } from '$lib/config';

	let { compact = false }: { compact?: boolean } = $props();
</script>

<span class="inline-flex items-center gap-2 select-none">
	<span
		class="grid h-8 w-8 place-items-center rounded-base bg-primary-500 text-xs font-black tracking-tight text-primary-contrast-500"
	>LNG</span
	>
	{#if !compact}
		<span class="text-lg font-semibold tracking-tight">{APP_NAME}</span>
	{/if}
</span>
