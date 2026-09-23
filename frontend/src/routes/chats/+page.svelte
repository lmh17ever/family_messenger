<script lang="ts">
	import EmptyState from '$lib/components/EmptyState.svelte';
</script>

<section class="hidden flex-1 items-center justify-center lg:flex">
	<EmptyState
		title="Выберите чат"
		text="Слева — список переписок. Кнопка «+» открывает поиск пользователей и новый диалог."
		icon="message"
	/>
</section>
