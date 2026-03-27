/**
 * Transforms backend API responses (snake_case, paginated) to frontend types (camelCase).
 */

import type { AgentRun, AgentSummary, AnalyticsSnapshot, ApprovalItem, ApprovalVariant, Campaign, Company, Lead, User } from "@/lib/types";

// Backend paginated response wrapper
export type Paginated<T> = { items: T[]; total: number; page: number; page_size: number };

// Unwrap paginated response or return items array directly
export function unwrapItems<T>(data: Paginated<T> | T[] | null | undefined): T[] {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items ?? [];
}

// Backend API lead/contact shape
type BackendLead = {
  id: string;
  org_id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  title?: string | null;
  status?: string;
  icp_score?: number | null;
  icp_score_reason?: string | null;
  fit_signals?: string[];
  gap_signals?: string[];
  enrichment_status?: string;
  enrichment_data?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export function backendLeadToFrontend(lead: BackendLead): Lead {
  const ed = (lead.enrichment_data ?? {}) as Record<string, unknown>;
  const firstName = lead.first_name ?? "";
  const lastName = lead.last_name ?? "";
  const name = [firstName, lastName].filter(Boolean).join(" ") || lead.email;
  return {
    id: lead.id,
    name,
    title: lead.title ?? "",
    company: (ed.company_name as string) ?? "",
    email: lead.email,
    status: (lead.status as Lead["status"]) ?? "new",
    icpScore: lead.icp_score ?? 0,
    emailRisk: 0,
    owner: "",
    lastTouchedAt: lead.updated_at,
    city: (ed.city as string) ?? "",
    notes: (ed.notes as string) ?? "",
    enrichment: {
      source: (ed.source as string) ?? "manual",
      employees: (ed.employees as number) ?? 0,
      revenue: (ed.revenue as string) ?? "",
      technologies: (ed.technologies as string[]) ?? [],
    },
  };
}

type BackendCampaign = {
  id: string;
  org_id: string;
  name: string;
  tone?: string | null;
  product_value_prop?: string | null;
  brand_voice?: string | null;
  target_icp?: Record<string, unknown>;
  active?: boolean;
  status?: string;
  sequences?: unknown[];
  created_at: string;
  updated_at: string;
};

export function backendCampaignToFrontend(campaign: BackendCampaign): Campaign {
  const isActive = campaign.active ?? true;
  const status: Campaign["status"] = campaign.status === "paused" ? "paused" : isActive ? "active" : "draft";
  return {
    id: campaign.id,
    name: campaign.name,
    goal: "",
    status,
    tone: campaign.tone ?? "professional",
    valueProp: campaign.product_value_prop ?? "",
    icpMinScore: 0,
    sent: 0,
    openRate: 0,
    replyRate: 0,
    createdAt: campaign.created_at,
  };
}

type BackendApproval = {
  id: string;
  org_id: string;
  target_type?: string;
  target_id?: string;
  title: string;
  body: string;
  status?: string;
  reviewer_id?: string | null;
  reviewed_at?: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export function backendApprovalToFrontend(item: BackendApproval): ApprovalItem {
  const variant: ApprovalVariant = {
    id: item.id,
    subject: item.title,
    body: item.body,
    hookType: "outbound",
    confidence: 0.8,
  };
  const stub: Lead = {
    id: item.target_id ?? item.id,
    name: "",
    title: "",
    company: "",
    email: "",
    status: "pending_approval",
    icpScore: 0,
    emailRisk: 0,
    owner: "",
    lastTouchedAt: item.created_at,
    city: "",
    notes: "",
    enrichment: { source: "", employees: 0, revenue: "", technologies: [] },
  };
  return {
    id: item.id,
    lead: stub,
    campaign: "",
    status: (item.status as ApprovalItem["status"]) ?? "pending_approval",
    createdAt: item.created_at,
    variants: [variant],
    reviewReason: undefined,
  };
}

type BackendCompany = {
  id: string;
  org_id: string;
  name: string;
  domain?: string | null;
  industry?: string | null;
  employee_count?: number | null;
  health_score?: number | null;
  icp_score?: number | null;
  enrichment_data?: Record<string, unknown>;
  last_synced_at?: string | null;
  created_at: string;
  updated_at: string;
};

export function backendCompanyToFrontend(c: BackendCompany): Company {
  const ed = (c.enrichment_data ?? {}) as Record<string, unknown>;
  return {
    id: c.id,
    name: c.name,
    domain: c.domain ?? "",
    industry: c.industry ?? "",
    stage: (ed.stage as string) ?? "prospect",
    healthScore: c.health_score ?? 0,
    owner: "",
    employees: c.employee_count ?? 0,
    revenue: (ed.revenue as string) ?? "",
    lastSyncAt: c.last_synced_at ?? c.updated_at,
  };
}

type BackendUser = {
  id: string;
  email: string;
  full_name?: string | null;
  org_id: string;
  role: string;
  permissions?: string[];
  is_active?: boolean;
};

export function backendUserToFrontend(u: BackendUser): User {
  return {
    id: u.id,
    name: u.full_name ?? u.email.split("@")[0],
    email: u.email,
    role: (u.role as User["role"]) ?? "member",
    orgId: u.org_id,
    avatarUrl: `https://api.dicebear.com/8.x/initials/svg?seed=${encodeURIComponent(u.full_name ?? u.email)}`,
  };
}

type BackendAnalytics = {
  leads_scored?: number;
  emails_generated?: number;
  emails_approved?: number;
  active_campaigns?: number;
  pipeline_value?: number;
  churn_at_risk?: number;
  // also accept camelCase in case backend evolves
  leadsScored?: number;
  emailsGenerated?: number;
};

export function backendAnalyticsToFrontend(a: BackendAnalytics): AnalyticsSnapshot {
  return {
    leadsScored: a.leads_scored ?? a.leadsScored ?? 0,
    emailsGenerated: a.emails_generated ?? a.emailsGenerated ?? 0,
    emailsApproved: a.emails_approved ?? 0,
    activeCampaigns: a.active_campaigns ?? 0,
    pipelineValue: a.pipeline_value ?? 0,
    churnAtRisk: a.churn_at_risk ?? 0,
  };
}
