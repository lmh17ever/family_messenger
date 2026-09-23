<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Spinner from '$lib/components/Spinner.svelte';
	import Toaster from '$lib/components/Toaster.svelte';
	import { userSocket } from '$lib/realtime/sockets';
	import { chats } from '$lib/stores/chats.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { ui } from '$lib/stores/ui.svelte';
	import type { UserRealtimeEvent } from '$lib/api/types';
	import {
		requestNotificationPermission,
		setUnreadBadge,
		showSystemNotification
	} from '$lib/utils/notifications';
	import { playNotificationSound, unlockAudio } from '$lib/utils/sound';

	let { children } = $props();
	let started = false;

	const authenticated = $derived(session.isAuthenticated);

	// Однократная инициализация сессии
	$effect(() => {
		if (started) return;
		started = true;
		session.init();
		void session.restore();
	});

	// Guard: неавторизованных — на вход, авторизованных со страниц входа — в чаты
	$effect(() => {
		if (!session.ready) return;
		const path = page.url.pathname;
		const isPublicPage = path === '/login' || path === '/register';

		if (!authenticated && !isPublicPage) {
			void goto('/login');
			return;
		}
		if (authenticated && isPublicPage) {
			void goto('/chats');
		}
	});

	// Персональный сокет поднимаем только для авторизованного пользователя
	$effect(() => {
		if (authenticated) {
			userSocket.start();
			void requestNotificationPermission();
			return () => userSocket.stop();
		}
		userSocket.stop();
		return;
	});

	// Счётчик непрочитанных в заголовке вкладки
	$effect(() => {
		setUnreadBadge(chats.totalUnread);
	});

	function handleRealtimeEvent(event: UserRealtimeEvent) {
		if (event.type === 'chat.updated') {
			void chats.refreshChat(event.chat_id);
			return;
		}
		if (event.type !== 'notification.new_message') return;

		if (!chats.applyNotification(event)) return;

		playNotificationSound();
		const title = event.sender?.username ?? 'Новое сообщение';
		const body = event.text?.trim() || 'Вложение';
		ui.info(`${title}: ${body}`);
		showSystemNotification(title, body, `chat-${event.chat_id}`);
	}

	// Подписка на события сокета + разблокировка звука по первому действию пользователя
	$effect(() => {
		const stopEvents = userSocket.onEvent(handleRealtimeEvent);

		const onFirstInteraction = () => {
			unlockAudio();
			void requestNotificationPermission();
		};
		window.addEventListener('click', onFirstInteraction, { once: true });
		window.addEventListener('keydown', onFirstInteraction, { once: true });

		return () => {
			stopEvents();
			window.removeEventListener('click', onFirstInteraction);
			window.removeEventListener('keydown', onFirstInteraction);
		};
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if session.ready}
	{@render children()}
{:else}
	<div class="grid h-dvh place-items-center">
		<Spinner size={28} class="text-primary-500" />
	</div>
{/if}

<Toaster />
