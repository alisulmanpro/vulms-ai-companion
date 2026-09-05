export const LANDING_NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#ecosystem", label: "Ecosystem" },
  { href: "#about", label: "About" },
] as const;

export const FEATURES = [
  {
    title: "Assignment Tracking",
    description:
      "Monitors active assignments across your VULMS courses and surfaces upcoming deadlines.",
    accent: "violet",
  },
  {
    title: "Quiz & GDB Alerts",
    description:
      "Tracks open quizzes and graded discussion boards so you know when windows close.",
    accent: "magenta",
  },
  {
    title: "WhatsApp Notifications",
    description:
      "Queues alerts through the backend dispatcher so updates reach your phone.",
    accent: "indigo",
  },
  {
    title: "Browser Extension",
    description:
      "A WXT extension watches vu.edu.pk pages and detects LMS changes locally.",
    accent: "blue",
  },
  {
    title: "Background Watcher",
    description:
      "Server-side scheduler polls linked accounts and syncs academic data automatically.",
    accent: "violet",
  },
  {
    title: "Encrypted Credentials",
    description:
      "VULMS passwords are stored with AES-256-GCM encryption on the server backend.",
    accent: "magenta",
  },
] as const;

export const STEPS = [
  {
    step: "01",
    title: "Sign in with Google",
    description: "Authenticate securely through Auth.js — no separate password system.",
  },
  {
    step: "02",
    title: "Link your VULMS account",
    description: "Connect your student credentials once through the companion dashboard.",
  },
  {
    step: "03",
    title: "Install the extension",
    description: "Add the browser extension to monitor LMS pages while you study.",
  },
  {
    step: "04",
    title: "Receive smart alerts",
    description: "Get WhatsApp notifications for assignments, quizzes, GDBs, and fees.",
  },
] as const;

export const CAPABILITIES = [
  { label: "Assignments", detail: "Active deadline monitoring" },
  { label: "Quizzes", detail: "Open window detection" },
  { label: "GDBs", detail: "Discussion board tracking" },
  { label: "Challans", detail: "Unpaid fee alerts" },
  { label: "Extension", detail: "On-page LMS observer" },
  { label: "WhatsApp", detail: "Queued notification delivery" },
] as const;

export const ECOSYSTEM_POINTS = [
  "Extension scrapes LMS data directly from your authenticated browser session.",
  "Server watcher runs scheduled cycles for linked VULMS accounts.",
  "Web dashboard provides your authenticated control center.",
  "Notifications flow through a dedicated backend dispatcher.",
] as const;

export const AI_WORKFLOW_POINTS = [
  {
    title: "Observe",
    description: "Detect changes in assignments, quizzes, GDBs, and account summaries.",
  },
  {
    title: "Analyze",
    description: "Compare snapshots and identify new deadlines or status updates.",
  },
  {
    title: "Alert",
    description: "Queue WhatsApp messages when actionable items need your attention.",
  },
] as const;
