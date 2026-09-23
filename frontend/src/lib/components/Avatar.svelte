<script lang="ts">
	import { initials } from '$lib/utils/text';

	let {
		url = null,
		name,
		size = 'md',
		class: className = ''
	}: {
		url?: string | null;
		name: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		class?: string;
	} = $props();

	const SIZE_CLASSES: Record<string, string> = {
		sm: 'h-8 w-8 text-[11px]',
		md: 'h-10 w-10 text-xs',
		lg: 'h-14 w-14 text-base',
		xl: 'h-24 w-24 text-2xl'
	};

	let failed = $state(false);

	// при смене ссылки пробуем показать картинку заново
	$effect(() => {
		url;
		failed = false;
	});

	const sizeClass = $derived(SIZE_CLASSES[size]);
	const label = $derived(initials(name));
	const showImage = $derived(Boolean(url) && !failed);
</script>

<span
	class="relative inline-grid shrink-0 place-items-center overflow-hidden rounded-full bg-surface-300-700 font-semibold text-surface-950-50 select-none {sizeClass} {className}"
	title={name}
>
	<span>{label}</span>
	{#if showImage}
		<img
			src={url}
			alt={name}
			loading="lazy"
			class="absolute inset-0 h-full w-full object-cover"
			onerror={() => (failed = true)}
		/>
	{/if}
</span>
