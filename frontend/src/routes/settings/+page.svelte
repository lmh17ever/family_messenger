<script lang="ts">
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api/client';
	import Avatar from '$lib/components/Avatar.svelte';
	import Icon from '$lib/components/Icon.svelte';
	import Logo from '$lib/components/Logo.svelte';
	import Spinner from '$lib/components/Spinner.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { ui } from '$lib/stores/ui.svelte';

	let username = $state(session.user?.username ?? '');
	let savingUsername = $state(false);
	let uploadingAvatar = $state(false);
	let avatarProgress = $state(0);
	let avatarInput = $state<HTMLInputElement | null>(null);

	async function saveUsername(event: SubmitEvent) {
		event.preventDefault();
		const next = username.trim();
		if (!next || next === session.user?.username) return;

		savingUsername = true;
		try {
			await session.changeUsername(next);
			ui.success('Имя обновлено');
		} catch (cause) {
			ui.error(cause instanceof ApiError ? cause.message : 'Не удалось изменить имя');
			username = session.user?.username ?? '';
		} finally {
			savingUsername = false;
		}
	}

	async function uploadAvatar(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		input.value = '';
		if (!file) return;

		uploadingAvatar = true;
		avatarProgress = 0;
		try {
			await session.uploadAvatar(file, (ratio) => (avatarProgress = ratio));
			ui.success('Аватар обновлён');
		} catch (cause) {
			const message = cause instanceof ApiError ? cause.message : 'Не удалось загрузить аватар';
			ui.error(message);
		} finally {
			uploadingAvatar = false;
		}
	}
</script>

<main class="app-scroll h-dvh overflow-y-auto">
	<div class="mx-auto flex w-full max-w-2xl flex-col gap-4 p-4 lg:p-8">
		<header class="flex items-center gap-3">
			<button
				type="button"
				class="rounded-base p-2 text-surface-700-300 transition hover:bg-surface-200-800 cursor-pointer"
				title="К чатам"
				onclick={() => void goto('/chats')}
			>
				<Icon name="back" />
			</button>
			<Logo />
			<span class="ml-auto text-xs text-surface-700-300">Настройки</span>
		</header>

		{#if session.user}
			<section
				class="rounded-container border border-surface-300-700 bg-surface-100-900 p-5 shadow-lg"
			>
				<h2 class="mb-4 text-sm font-semibold">Профиль</h2>
				<div class="flex flex-col items-center gap-3 sm:flex-row sm:items-start">
					<div class="flex flex-col items-center gap-2">
						<Avatar url={session.user.avatar_url} name={session.user.username} size="xl" />
						<button
							type="button"
							class="flex items-center gap-1.5 rounded-base px-2.5 py-1.5 text-xs font-medium text-primary-500 transition hover:bg-surface-200-800 disabled:opacity-60 cursor-pointer"
							disabled={uploadingAvatar}
							onclick={() => avatarInput?.click()}
						>
							{#if uploadingAvatar}
								<Spinner size={14} />
								{Math.round(avatarProgress * 100)}%
							{:else}
								<Icon name="image" size={14} />
								Сменить аватар
							{/if}
						</button>
						<input
							bind:this={avatarInput}
							type="file"
							accept="image/jpeg,image/png,image/webp"
							class="hidden"
							onchange={uploadAvatar}
						/>
						<p class="max-w-40 text-center text-[11px] text-surface-700-300">
							JPEG, PNG или WebP
						</p>
					</div>

					<form class="flex-1" onsubmit={saveUsername}>
						<span class="mb-1 block text-xs text-surface-700-300">Имя пользователя</span>
						<div class="flex gap-2">
							<input
								class="min-w-0 flex-1 rounded-base border border-surface-300-700 bg-surface-200-800 px-3 py-2 text-sm outline-none focus:border-primary-500"
								bind:value={username}
								maxlength={30}
								required
							/>
							<button
								type="submit"
								class="flex items-center gap-2 rounded-base bg-primary-500 px-3 py-2 text-sm font-semibold text-primary-contrast-500 transition hover:bg-primary-600 disabled:opacity-60 cursor-pointer"
								disabled={savingUsername || !username.trim()}
							>
								{#if savingUsername}<Spinner size={14} />{/if}
								Сохранить
							</button>
						</div>
						<p class="mt-2 text-[11px] text-surface-700-300">
							После смены имени backend выдаёт новую пару токенов, сессия остаётся активной.
						</p>
					</form>
				</div>
			</section>

			<section
				class="rounded-container border border-surface-300-700 bg-surface-100-900 p-5 shadow-lg"
			>
				<h2 class="mb-3 text-sm font-semibold">Аккаунт</h2>
				<button
					type="button"
					class="flex w-full items-center justify-center gap-2 rounded-base border border-error-500 px-3 py-2 text-sm font-medium text-error-500 transition hover:bg-error-500 hover:text-error-contrast-500 cursor-pointer"
					onclick={() => session.logout()}
				>
					<Icon name="logout" size={18} />
					Выйти из аккаунта
				</button>
			</section>
		{:else}
			<div class="grid place-items-center py-10">
				<Spinner size={24} class="text-primary-500" />
			</div>
		{/if}
	</div>
</main>
