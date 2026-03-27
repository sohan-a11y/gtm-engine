import { useMutation } from "@tanstack/react-query";
import { apiFetch, submitJson } from "@/lib/api";
import { backendUserToFrontend } from "@/lib/transforms";
import { useAppStore } from "@/lib/store";
import type { User } from "@/lib/types";

type LoginRequest = { email: string; password: string };
type RegisterRequest = { email: string; password: string; full_name?: string; org_name?: string };

type BackendAuthResponse = {
  access_token?: string;
  tokens?: { access_token: string };
  user: {
    id: string;
    email: string;
    full_name?: string | null;
    org_id: string;
    role: string;
    permissions?: string[];
  };
};

function extractSession(data: BackendAuthResponse) {
  const token = data.access_token ?? data.tokens?.access_token ?? "";
  const user = backendUserToFrontend(data.user);
  return { accessToken: token, user };
}

export function useAuth() {
  const accessToken = useAppStore((state) => state.accessToken);
  const sessionUser = useAppStore((state) => state.sessionUser);
  const orgName = useAppStore((state) => state.orgName);
  const authStatus = useAppStore((state) => state.authStatus);
  const clearSession = useAppStore((state) => state.clearSession);
  const setSession = useAppStore((state) => state.setSession);

  const loginMutation = useMutation({
    mutationFn: async (payload: LoginRequest) => {
      const result = await submitJson<BackendAuthResponse>("/auth/login", payload);
      if (!result.ok || !result.data) {
        throw new Error("Login failed. Check your email and password.");
      }
      const { accessToken: token, user } = extractSession(result.data);
      setSession({ accessToken: token, user });
      return user;
    },
  });

  const registerMutation = useMutation({
    mutationFn: async (payload: RegisterRequest) => {
      const result = await submitJson<BackendAuthResponse>("/auth/register", payload);
      if (!result.ok || !result.data) {
        throw new Error("Registration failed.");
      }
      const { accessToken: token, user } = extractSession(result.data);
      setSession({ accessToken: token, user });
      return user;
    },
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await apiFetch("/auth/logout", { method: "POST" }).catch(() => null);
      clearSession();
    },
  });

  return {
    accessToken,
    user: sessionUser,
    orgName,
    authStatus,
    isAuthenticated: Boolean(accessToken),
    login: loginMutation.mutateAsync,
    loginError: loginMutation.error,
    register: registerMutation.mutateAsync,
    registerError: registerMutation.error,
    logout: logoutMutation.mutateAsync,
  };
}
