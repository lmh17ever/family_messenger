// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

interface ImportMetaEnv {
	readonly PUBLIC_API_BASE_URL?: string;
	readonly PUBLIC_S3_BASE_URL?: string;
	readonly PUBLIC_S3_PUBLIC_BUCKET?: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}

export {};
