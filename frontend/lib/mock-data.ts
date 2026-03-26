import {
  type AgentRun,
  type AgentSummary,
  type AnalyticsSnapshot,
  type ApprovalItem,
  type Campaign,
  type Company,
  type DashboardActivity,
  type Lead,
  type User
} from "@/lib/types";

export const mockOrg = {
  id: "org_artifex",
  name: "Artifex",
  industry: "B2B SaaS",
  plan: "growth" as const
};

export const mockUser: User = {
  id: "user_sam",
  name: "Samir Rao",
  email: "samir@artifex.ai",
  role: "admin",
  orgId: mockOrg.id,
  avatarUrl: "https://api.dicebear.com/8.x/initials/svg?seed=SR"
};

export const mockLeads: Lead[] = [
  {
    id: "lead_1",
    name: "Ava Martinez",
    title: "VP of Revenue",
    company: "Northstar Analytics",
    email: "ava@northstar.ai",
    status: "pending_approval",
    icpScore: 0.86,
    emailRisk: 0.12,
    owner: "Samir Rao",
    lastTouchedAt: "2026-03-26T09:20:00Z",
    city: "Austin, TX",
    notes: "Strong fit. Looking at outbound automation and pipeline efficiency.",
    enrichment: {
      source: "Apollo + Hunter",
      employees: 214,
      revenue: "$22M ARR",
      technologies: ["HubSpot", "Salesforce", "Segment"]
    }
  },
  {
    id: "lead_2",
    name: "Jordan Lee",
    title: "Head of Growth",
    company: "Vector Forge",
    email: "jordan@vectorforge.com",
    status: "scored",
    icpScore: 0.67,
    emailRisk: 0.31,
    owner: "Maya Patel",
    lastTouchedAt: "2026-03-25T15:10:00Z",
    city: "San Francisco, CA",
    notes: "Interested in campaign personalization and reporting automation.",
    enrichment: {
      source: "Apollo",
      employees: 88,
      revenue: "$8M ARR",
      technologies: ["HubSpot", "Clearbit"]
    }
  },
  {
    id: "lead_3",
    name: "Priya Shah",
    title: "Director of Sales Ops",
    company: "Atlas Systems",
    email: "priya@atlas.sys",
    status: "enriched",
    icpScore: 0.42,
    emailRisk: 0.46,
    owner: "Owen Reed",
    lastTouchedAt: "2026-03-25T13:05:00Z",
    city: "New York, NY",
    notes: "Potential fit once implementation tooling matures.",
    enrichment: {
      source: "Hunter",
      employees: 420,
      revenue: "$56M ARR",
      technologies: ["Salesforce", "Outreach"]
    }
  }
];

export const mockCompanies: Company[] = [
  {
    id: "company_1",
    name: "Northstar Analytics",
    domain: "northstar.ai",
    industry: "Data infrastructure",
    stage: "Pipeline",
    healthScore: 0.92,
    owner: "Samir Rao",
    employees: 214,
    revenue: "$22M ARR",
    lastSyncAt: "2026-03-26T09:00:00Z"
  },
  {
    id: "company_2",
    name: "Vector Forge",
    domain: "vectorforge.com",
    industry: "Marketing tech",
    stage: "Discovery",
    healthScore: 0.71,
    owner: "Maya Patel",
    employees: 88,
    revenue: "$8M ARR",
    lastSyncAt: "2026-03-25T18:00:00Z"
  }
];

export const mockCampaigns: Campaign[] = [
  {
    id: "campaign_1",
    name: "Pipeline Recovery",
    goal: "Increase reply rate from reactivated accounts",
    status: "active",
    tone: "Clear, direct, consultative",
    valueProp: "Turn dormant interest into qualified meetings",
    icpMinScore: 0.6,
    sent: 184,
    openRate: 0.41,
    replyRate: 0.16,
    createdAt: "2026-03-22T08:00:00Z"
  },
  {
    id: "campaign_2",
    name: "Enterprise Expansion",
    goal: "Land multi-threaded enterprise opportunities",
    status: "draft",
    tone: "Executive, evidence-led",
    valueProp: "Reduce GTM waste and accelerate signal-driven outreach",
    icpMinScore: 0.72,
    sent: 0,
    openRate: 0,
    replyRate: 0,
    createdAt: "2026-03-24T11:30:00Z"
  }
];

export const mockApprovals: ApprovalItem[] = [
  {
    id: "approval_1",
    lead: mockLeads[0],
    campaign: "Pipeline Recovery",
    status: "pending_approval",
    createdAt: "2026-03-26T10:15:00Z",
    variants: [
      {
        id: "variant_a",
        subject: "Northstar's pipeline isn't the problem",
        body:
          "Ava, I noticed your team is already doing the hard part: building real pipeline. The opportunity is usually the handoff between intent and follow-up. We help revenue teams turn that gap into a repeatable motion without adding more tooling to the stack.",
        hookType: "Pain-point reframing",
        confidence: 0.91
      },
      {
        id: "variant_b",
        subject: "A faster way to qualify signal",
        body:
          "Ava, teams like Northstar usually hit a ceiling when their signal volume outpaces manual follow-up. We built Artifex to score, personalize, and route the right accounts before the opportunity gets cold.",
        hookType: "Efficiency",
        confidence: 0.84
      },
      {
        id: "variant_c",
        subject: "Where your reps spend the most time",
        body:
          "Ava, if your team is still stitching together scoring, enrichment, and outbound in separate tools, there is probably a hidden tax on speed. Artifex replaces that handoff with a single approval flow.",
        hookType: "Process simplification",
        confidence: 0.79
      }
    ]
  }
];

export const mockAgents: AgentSummary[] = [
  {
    id: "icp_agent",
    name: "ICP Agent",
    description: "Scores fit and finds lookalike patterns across your pipeline.",
    status: "running",
    lastRunAt: "2026-03-26T09:15:00Z",
    successRate: 0.97,
    avgLatencyMs: 1420,
    triggerLabel: "Score lead"
  },
  {
    id: "outbound_agent",
    name: "Outbound Agent",
    description: "Generates three review-ready email variations with hooks.",
    status: "healthy",
    lastRunAt: "2026-03-26T09:00:00Z",
    successRate: 0.94,
    avgLatencyMs: 1860,
    triggerLabel: "Generate outbound"
  },
  {
    id: "deal_intel_agent",
    name: "Deal Intel Agent",
    description: "Reads transcripts and flags risk before deals slip.",
    status: "paused",
    lastRunAt: "2026-03-24T18:20:00Z",
    successRate: 0.88,
    avgLatencyMs: 2200,
    triggerLabel: "Analyze deal"
  },
  {
    id: "retention_agent",
    name: "Retention Agent",
    description: "Detects churn risk and suggests playbooks.",
    status: "idle",
    lastRunAt: "2026-03-23T16:30:00Z",
    successRate: 0.91,
    avgLatencyMs: 1640,
    triggerLabel: "Assess account"
  }
];

export const mockAgentRuns: AgentRun[] = [
  {
    id: "run_1",
    agentName: "ICP Agent",
    status: "completed",
    message: "Scored 18 leads. 6 crossed the outbound threshold.",
    progress: 100,
    createdAt: "2026-03-26T09:16:00Z"
  },
  {
    id: "run_2",
    agentName: "Outbound Agent",
    status: "progress",
    message: "Drafting three variants for Northstar Analytics.",
    progress: 64,
    createdAt: "2026-03-26T10:18:00Z"
  }
];

export const mockAnalytics: AnalyticsSnapshot = {
  leadsScored: 1842,
  emailsGenerated: 316,
  emailsApproved: 82,
  activeCampaigns: 7,
  pipelineValue: 1240000,
  churnAtRisk: 14
};

export const mockActivity: DashboardActivity[] = [
  {
    id: "act_1",
    title: "New outbound draft queued",
    detail: "Ava Martinez at Northstar Analytics needs approval.",
    at: "2026-03-26T10:16:00Z",
    tone: "success"
  },
  {
    id: "act_2",
    title: "ICP retrained",
    detail: "5 customer examples refreshed the lookalike set.",
    at: "2026-03-26T09:40:00Z",
    tone: "neutral"
  },
  {
    id: "act_3",
    title: "Risk alert acknowledged",
    detail: "Vector Forge moved from warning to monitored.",
    at: "2026-03-25T21:00:00Z",
    tone: "warning"
  }
];
