export type Role = "admin" | "member" | "viewer";

export type Org = {
  id: string;
  name: string;
  industry: string;
  plan: "seed" | "growth" | "enterprise";
};

export type User = {
  id: string;
  name: string;
  email: string;
  role: Role;
  orgId: string;
  avatarUrl?: string;
};

export type Lead = {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  status: "new" | "enriched" | "scored" | "pending_approval" | "sent";
  icpScore: number;
  emailRisk: number;
  owner: string;
  lastTouchedAt: string;
  city: string;
  notes: string;
  enrichment: {
    source: string;
    employees: number;
    revenue: string;
    technologies: string[];
  };
};

export type Company = {
  id: string;
  name: string;
  domain: string;
  industry: string;
  stage: string;
  healthScore: number;
  owner: string;
  employees: number;
  revenue: string;
  lastSyncAt: string;
};

export type Campaign = {
  id: string;
  name: string;
  goal: string;
  status: "draft" | "active" | "paused";
  tone: string;
  valueProp: string;
  icpMinScore: number;
  sent: number;
  openRate: number;
  replyRate: number;
  createdAt: string;
};

export type ApprovalVariant = {
  id: string;
  subject: string;
  body: string;
  hookType: string;
  confidence: number;
};

export type ApprovalItem = {
  id: string;
  lead: Lead;
  campaign: string;
  status: "pending_approval" | "approved" | "rejected";
  createdAt: string;
  variants: ApprovalVariant[];
  reviewReason?: string;
};

export type AgentStatus = "idle" | "running" | "healthy" | "paused" | "error";

export type AgentSummary = {
  id: string;
  name: string;
  description: string;
  status: AgentStatus;
  lastRunAt: string;
  successRate: number;
  avgLatencyMs: number;
  triggerLabel: string;
};

export type AgentRun = {
  id: string;
  agentName: string;
  status: "started" | "progress" | "completed" | "error";
  message: string;
  progress: number;
  createdAt: string;
};

export type Deal = {
  id: string;
  name: string;
  stage: string;
  amount: number;
  riskScore: number | null;
  orgId: string;
  createdAt: string;
  updatedAt: string;
};

export type AnalyticsSnapshot = {
  leadsScored: number;
  emailsGenerated: number;
  emailsApproved: number;
  activeCampaigns: number;
  pipelineValue: number;
  churnAtRisk: number;
};

export type DashboardActivity = {
  id: string;
  title: string;
  detail: string;
  at: string;
  tone: "success" | "warning" | "neutral";
};
