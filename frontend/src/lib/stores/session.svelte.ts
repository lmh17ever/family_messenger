import { goto } from '$app/navigation';

import * as authApi from '$lib/api/auth';
import { configureAuth, uploadToS3 } from '$lib/api/client';
import * as usersApi from '$lib/api/users';
import type { TokenResponse, User } from '$lib/api/types';
import { ui } from '$lib/stores/ui.svelte';

const REFRESH_STORAGE_KEY = 'lng.refresh_token';

class SessionState {
	/** access-токен живёт только в памяти */
	accessToken = $state<string | null>(null);
	user = $state<User | null>(null);
	/** true, когда попытка восстановить сессию завершена (нужно для guard'а) */
	ready = $state(false);

	private refreshToken: string | null = null;
	private refreshInFlight: Promise<boolean> | null = null;

	get isAuthenticated(): boolean {
		return Boolean(this.user && this.accessToken);
	}

	/** Подключает клиент к хранилищу токенов (без циклических импортов) */
	init(): void {
		configureAuth({
			getAccessToken: () => this.accessToken,
			refreshAccessToken: () => this.refreshAccess(),
			onAuthFailure: () => this.handleAuthFailure()
		});
		this.refreshToken = this.readRefreshToken();
	}

	/** Восстановление сессии при запуске приложения */
	async restore(): Promise<void> {
		if (this.ready) return;
		if (!this.refreshToken) {
			this.ready = true;
			return;
		}
		const refreshed = await this.refreshAccess();
		if (refreshed) {
			try {
				this.user = await usersApi.getMe();
			} catch {
				this.clear();
			}
		}
		this.ready = true;
	}

	async login(username: string, password: string): Promise<void> {
		this.applyTokens(await authApi.login(username, password));
		this.user = await usersApi.getMe();
	}

	async register(username: string, password: string): Promise<void> {
		this.applyTokens(await authApi.register(username, password));
		this.user = await usersApi.getMe();
	}

	/** PATCH /users/me: backend возвращает новую пару токенов (ник лежит в JWT) */
	async changeUsername(username: string): Promise<void> {
		const tokens = await usersApi.updateUsername(username);
		this.applyTokens(tokens);
		if (this.user) {
			this.user = { ...this.user, username };
		}
	}

	async uploadAvatar(file: File, onProgress?: (ratio: number) => void): Promise<User> {
		const presigned = await usersApi.presignAvatar(
			file.name,
			file.type || 'image/jpeg',
			file.size
		);
		await uploadToS3(presigned.upload, file, { onProgress });
		const updated = await usersApi.confirmAvatar(presigned.avatar_key);
		this.user = updated;
		return updated;
	}

	logout(): void {
		this.clear();
		void goto('/login');
	}

	/** Single-flight обновление access-токена */
	async refreshAccess(): Promise<boolean> {
		if (this.refreshInFlight) return this.refreshInFlight;
		const refreshToken = this.refreshToken;
		if (!refreshToken) return false;

		this.refreshInFlight = (async () => {
			try {
				this.applyTokens(await authApi.refreshTokens(refreshToken));
				return true;
			} catch {
				this.clear();
				return false;
			} finally {
				this.refreshInFlight = null;
			}
		})();

		return this.refreshInFlight;
	}

	clear(): void {
		this.accessToken = null;
		this.user = null;
		this.refreshToken = null;
		try {
			sessionStorage.removeItem(REFRESH_STORAGE_KEY);
		} catch {
			// sessionStorage может быть недоступен (приватный режим)
		}
	}

	private handleAuthFailure(): void {
		if (!this.accessToken && !this.refreshToken) return;
		this.clear();
		ui.error('Сессия истекла, войдите заново');
		void goto('/login');
	}

	private applyTokens(tokens: TokenResponse): void {
		this.accessToken = tokens.access_token;
		this.refreshToken = tokens.refresh_token;
		try {
			sessionStorage.setItem(REFRESH_STORAGE_KEY, tokens.refresh_token);
		} catch {
			// игнорируем недоступное хранилище
		}
	}

	private readRefreshToken(): string | null {
		try {
			return sessionStorage.getItem(REFRESH_STORAGE_KEY);
		} catch {
			return null;
		}
	}
}

export const session = new SessionState();
