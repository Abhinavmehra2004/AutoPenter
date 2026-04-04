import { useState } from "react";

type PhaseState = "idle" | "active" | "done" | "error";

interface PhaseBadgeProps {
  number: number;
  title: string;
  state: PhaseState;
}

const stateStyles: Record<PhaseState, string> = {
  idle: "border-border text-muted-foreground bg-card",
  active: "border-primary text-primary bg-primary/10",
  done: "border-success text-success bg-success/10",
  error: "border-destructive text-destructive bg-destructive/10",
};

const stateIcons: Record<PhaseState, string> = {
  idle: "○",
  active: "◉",
  done: "✓",
  error: "✕",
};

export const PhaseBadge = ({ number, title, state }: PhaseBadgeProps) => (
  <div
    className={`flex items-center gap-3 px-4 py-2.5 rounded-md border font-mono text-xs font-bold tracking-widest transition-all duration-300 ${stateStyles[state]}`}
  >
    <span>{stateIcons[state]}</span>
    <span>PHASE {number}</span>
    <span className="text-muted-foreground">·</span>
    <span>{title}</span>
  </div>
);

export default PhaseBadge;
