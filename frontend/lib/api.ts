import { mockOrg, mockUser } from "@/lib/mock-data";
import { useAppStore } from "@/lib/store";
import type { User } from "@/lib/types";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api").replace(/\/$/, "");
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

type ApiResult<T> = {
  ok: boolean;
  status: number;
  data: T | null;
};

function buildUrl(path: string) {
  if (path.startsWith("http")) {
    return path;
  }

  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${cleanPath}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}

async function refreshAccessToken() {
  try {
    const response = await fetch(buildUrl("/auth/refresh"), {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) {
      throw new Error("refresh failed");
    }

    const payload = (await parseResponse<{ access_token: string; user: User; org_name?: string }>(response)) ?? null;
    if (!payload?.access_token || !payload.user) {
      throw new Error("invalid refresh payload");
    }

    useAppStore.getState().setSession({
      accessToken: payload.access_token,
      user: payload.user,
      orgName: payload.org_name ?? mockOrg.name
    });

    return payload.access_token;
  } catch {
    if (DEMO_MODE) {
      useAppStore.getState().setSession({
        accessToken: "demo-access-token",
        user: mockUser,
        orgName: mockOrg.name
      });
      return "demo-access-token";
    }

    useAppStore.getState().clearSession();
    return null;
  }
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = useAppStore.getState().accessToken;

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const requestInit: RequestInit = {
    ...init,
    credentials: "include",
    headers
  };

  let response = await fetch(buildUrl(path), requestInit);
  if (response.status !== 401) {
    return response;
  }

  const refreshed = await refreshAccessToken();
  if (!refreshed) {
    return response;
  }

  headers.set("Authorization", `Bearer ${refreshed}`);
  response = await fetch(buildUrl(path), {
    ...requestInit,
    headers
  });

  return response;
}

export async function fetchJson<T>(path: string, fallback: T, init: RequestInit = {}): Promise<T> {
  try {
    const response = await apiFetch(path, init);
    if (!response.ok) {
      return fallback;
    }

    return await parseResponse<T>(response);
  } catch {
    return fallback;
  }
}

export async function submitJson<T>(path: string, payload: unknown, init: RequestInit = {}): Promise<ApiResult<T>> {
  const response = await apiFetch(path, {
    ...init,
    method: init.method ?? "POST",
    body: JSON.stringify(payload)
  });

  return {
    ok: response.ok,
    status: response.status,
    data: response.ok ? await parseResponse<T>(response) : null
  };
}

export async function ensureDemoSession() {
  if (useAppStore.getState().accessToken) {
    return useAppStore.getState().accessToken;
  }

  return refreshAccessToken();
}
