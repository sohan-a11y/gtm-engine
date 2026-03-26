import { useMutation } from "@tanstack/react-query";

import { apiFetch, ensureDemoSession, submitJson } from "@/lib/api";
import { mockOrg, mockUser } from "@/lib/mock-data";
import { useAppStore } from "@/lib/store";
import type { User } from "@/lib/types";

const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE !== "false";

type LoginRequest = {
  email: string;
  password: string;
};

type LoginResponse = {
  access_token: string;
  user: User;
  org_name?: string;
};

export function useAuth() {
  const accessToken = useAppStore((state) => state.accessToken);
  const sessionUser = useAppStore((state) => state.sessionUser);
  const orgName = useAppStore((state) => state.orgName);
  const authStatus = useAppStore((state) => state.authStatus);
  const clearSession = useAppStore((state) => state.clearSession);
  const setSession = useAppStore((state) => state.setSession);

  const loginMutation = useMutation({
    mutationFn: async (payload: LoginRequest) => {
      try {
        const result = await submitJson<LoginResponse>("/auth/login", payload);
        if (result.ok && result.data) {
          setSession({
            accessToken: result.data.access_token,
            user: result.data.user,
            orgName: result.data.org_name ?? mockOrg.name
          });
          return result.data.user;
        }

        if (!DEMO_MODE) {
          throw new Error("Login failed");
        }

        await ensureDemoSession();
        setSession({
          accessToken: "demo-access-token",
          user: mockUser,
          orgName: mockOrg.name
        });
        return mockUser;
      } catch (error) {
        if (!DEMO_MODE) {
          throw error instanceof Error ? error : new Error("Login failed");
        }

        await ensureDemoSession();
        setSession({
          accessToken: "demo-access-token",
          user: mockUser,
          orgName: mockOrg.name
        });
        return mockUser;
      }
    }
  });

  const refreshMutation = useMutation({
    mutationFn: async () => {
      await ensureDemoSession();
      return useAppStore.getState().sessionUser;
    }
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await apiFetch("/auth/logout", { method: "POST" }).catch(() => null);
      clearSession();
    }
  });

  return {
    accessToken,
    user: sessionUser,
    orgName,
    authStatus,
    isAuthenticated: Boolean(accessToken),
    login: loginMutation.mutateAsync,
    refresh: refreshMutation.mutateAsync,
    logout: logoutMutation.mutateAsync
  };
}
