import { create } from "zustand";

import type { ApprovalItem, Campaign, Lead, User } from "@/lib/types";

type AuthStatus = "anonymous" | "authenticating" | "authenticated";

type AppState = {
  accessToken: string | null;
  sessionUser: User | null;
  orgName: string;
  authStatus: AuthStatus;
  selectedApprovalId: string | null;
  sidebarCollapsed: boolean;
  leadSearch: string;
  campaignSearch: string;
  setSession: (payload: { accessToken: string; user: User; orgName?: string }) => void;
  clearSession: () => void;
  setAuthStatus: (status: AuthStatus) => void;
  selectApproval: (id: string | null) => void;
  toggleSidebar: () => void;
  setLeadSearch: (value: string) => void;
  setCampaignSearch: (value: string) => void;
  hydrateApprovalSelection: (items: ApprovalItem[]) => void;
  currentLead: (items: Lead[]) => Lead | undefined;
  currentCampaign: (items: Campaign[]) => Campaign | undefined;
};

export const useAppStore = create<AppState>((set, get) => ({
  accessToken: null,
  sessionUser: null,
  orgName: "Artifex",
  authStatus: "anonymous",
  selectedApprovalId: null,
  sidebarCollapsed: false,
  leadSearch: "",
  campaignSearch: "",
  setSession: ({ accessToken, user, orgName }) =>
    set({
      accessToken,
      sessionUser: user,
      orgName: orgName ?? "Artifex",
      authStatus: "authenticated"
    }),
  clearSession: () =>
    set({
      accessToken: null,
      sessionUser: null,
      authStatus: "anonymous"
    }),
  setAuthStatus: (status) => set({ authStatus: status }),
  selectApproval: (id) => set({ selectedApprovalId: id }),
  toggleSidebar: () =>
    set((state) => ({
      sidebarCollapsed: !state.sidebarCollapsed
    })),
  setLeadSearch: (value) => set({ leadSearch: value }),
  setCampaignSearch: (value) => set({ campaignSearch: value }),
  hydrateApprovalSelection: (items) => {
    const { selectedApprovalId } = get();
    if (!selectedApprovalId && items.length > 0) {
      set({ selectedApprovalId: items[0].id });
    }
  },
  currentLead: (items) => items[0],
  currentCampaign: (items) => items[0]
}));
