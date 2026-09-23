import { request } from './client';
import type { TokenResponse } from './types';

/** POST /auth/token — OAuth2PasswordRequestForm (form-urlencoded) */
export function login(username: string, password: string): Promise<TokenResponse> {
	return request<TokenResponse>('/auth/token', {
		method: 'POST',
		form: { username, password },
		auth: false
	});
}

/** POST /auth/register — сразу возвращает пару токенов */
export function register(username: string, password: string): Promise<TokenResponse> {
	return request<TokenResponse>('/auth/register', {
		method: 'POST',
		body: { username, password },
		auth: false
	});
}

/** POST /auth/token/refresh */
export function refreshTokens(refreshToken: string): Promise<TokenResponse> {
	return request<TokenResponse>('/auth/token/refresh', {
		method: 'POST',
		body: { refresh_token: refreshToken },
		auth: false
	});
}
