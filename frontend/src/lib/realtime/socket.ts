import { currentAccessToken } from '$lib/api/client';
import { WS_PING_INTERVAL, WS_URL } from '$lib/config';
import { session } from '$lib/stores/session.svelte';

export type SocketStatus = 'connecting' | 'open' | 'closed';

interface SocketOptions<TEvent extends { type: string }> {
	/** Путь относительно /api/v1. null — соединение открывать не нужно. */
	path: () => string | null;
	/** Вызывается после установки соединения (в том числе при переподключении) */
	onOpen?: (socket: RealtimeSocket<TEvent>) => void;
}

/**
 * WebSocket-клиент с авто-переподключением (экспоненциальная задержка до 30 с)
 * и ping'ами. Токен передаётся query-параметром, как ожидает backend.
 */
export class RealtimeSocket<TEvent extends { type: string }> {
	private socket: WebSocket | null = null;
	private pingTimer: ReturnType<typeof setInterval> | null = null;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	private attempts = 0;
	private running = false;

	private readonly eventHandlers = new Set<(event: TEvent) => void>();
	private readonly statusHandlers = new Set<(status: SocketStatus) => void>();
	private readonly options: SocketOptions<TEvent>;

	constructor(options: SocketOptions<TEvent>) {
		this.options = options;
	}

	onEvent(handler: (event: TEvent) => void): () => void {
		this.eventHandlers.add(handler);
		return () => {
			this.eventHandlers.delete(handler);
		};
	}

	onStatus(handler: (status: SocketStatus) => void): () => void {
		this.statusHandlers.add(handler);
		return () => {
			this.statusHandlers.delete(handler);
		};
	}

	start(): void {
		if (this.running) {
			this.restart();
			return;
		}
		this.running = true;
		this.attempts = 0;
		this.open();
	}

	stop(): void {
		this.running = false;
		this.clearTimers();
		this.closeSocket();
		this.emitStatus('closed');
	}

	restart(): void {
		if (!this.running) return;
		this.clearTimers();
		this.closeSocket();
		this.open();
	}

	send(event: unknown): boolean {
		if (this.socket && this.socket.readyState === WebSocket.OPEN) {
			this.socket.send(JSON.stringify(event));
			return true;
		}
		return false;
	}

	private open(): void {
		const path = this.options.path();
		if (!this.running || !path) return;

		const token = currentAccessToken();
		if (!token) {
			this.scheduleReconnect();
			return;
		}

		this.emitStatus('connecting');
		const socket = new WebSocket(`${WS_URL}${path}?token=${encodeURIComponent(token)}`);
		this.socket = socket;

		socket.addEventListener('open', () => {
			if (this.socket !== socket) return;
			this.attempts = 0;
			this.startPing();
			this.emitStatus('open');
			this.options.onOpen?.(this);
		});

		socket.addEventListener('message', (event) => {
			let payload: TEvent;
			try {
				payload = JSON.parse(String(event.data)) as TEvent;
			} catch {
				return;
			}
			for (const handler of this.eventHandlers) {
				handler(payload);
			}
		});

		socket.addEventListener('close', (event) => {
			// Соединение уже заменено/закрыто нами — реакция не нужна
			if (this.socket !== socket) return;
			this.socket = null;
			this.stopPing();
			this.emitStatus('closed');
			if (!this.running) return;

			if (event.code === 1008) {
				// backend закрыл соединение из-за токена — обновляем и пробуем снова
				void session.refreshAccess().then(() => this.scheduleReconnect());
				return;
			}
			this.scheduleReconnect();
		});

		socket.addEventListener('error', () => {
			socket.close();
		});
	}

	private scheduleReconnect(): void {
		if (!this.running || this.reconnectTimer) return;
		const delay = Math.min(30_000, 1000 * 2 ** Math.min(this.attempts, 5));
		this.attempts += 1;
		this.reconnectTimer = setTimeout(() => {
			this.reconnectTimer = null;
			this.open();
		}, delay);
	}

	private startPing(): void {
		this.stopPing();
		this.pingTimer = setInterval(() => this.send({ type: 'ping' }), WS_PING_INTERVAL);
	}

	private stopPing(): void {
		if (this.pingTimer) {
			clearInterval(this.pingTimer);
			this.pingTimer = null;
		}
	}

	private clearTimers(): void {
		this.stopPing();
		if (this.reconnectTimer) {
			clearTimeout(this.reconnectTimer);
			this.reconnectTimer = null;
		}
	}

	private closeSocket(): void {
		const socket = this.socket;
		this.socket = null;
		if (socket && socket.readyState !== WebSocket.CLOSED) {
			socket.close();
		}
	}

	private emitStatus(status: SocketStatus): void {
		for (const handler of this.statusHandlers) {
			handler(status);
		}
	}
}
