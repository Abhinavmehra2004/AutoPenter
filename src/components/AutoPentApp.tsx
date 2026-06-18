import { useState, useRef, useEffect, useCallback } from "react";
import PhaseBadge from "@/components/PhaseBadge";
import ConsoleLine from "@/components/ConsoleLine";
import hackerWatermark from "@/assets/hacker-watermark.png";

type PhaseState = "idle" | "active" | "done" | "error";
type LineType = "info" | "phase" | "success" | "error" | "warning" | "default";

interface ConsoleLine {
  text: string;
  type: LineType;
}

const PHASES = [
  { number: 1, title: "RECON" },
  { number: 2, title: "FUZZING" },
  { number: 3, title: "CHAINING" },
  { number: 4, title: "EXPLOIT" },
  { number: 5, title: "REPORT" },
];

const SIMULATION_LINES: { text: string; type: LineType; phase?: number; phaseState?: PhaseState; delay: number }[] = [
  { text: "[*] Initialising AI Agentic Engine →", type: "info", delay: 500 },
  { text: "[+] PHASE 1 · Zero-API Reconnaissance …", type: "phase", phase: 1, phaseState: "active", delay: 800 },
  { text: "    IP Resolved: 31.3.96.40", type: "default", delay: 600 },
  { text: "    DNS Records: A, AAAA, MX, TXT enumerated", type: "default", delay: 400 },
  { text: "    Whois data collected", type: "default", delay: 300 },
  { text: "    Tech stack: nginx/1.24, PHP/8.2, WordPress/6.4", type: "default", delay: 500 },
  { text: "", type: "default", phase: 1, phaseState: "done", delay: 200 },
  { text: "[+] PHASE 2 · Gemini AI Orchestrator + Fuzzing …", type: "phase", phase: 2, phaseState: "active", delay: 800 },
  { text: "[+] AI Engine formulating aggressive attack strategy...", type: "phase", delay: 600 },
  { text: "[*] Launching Deep Crawler and Intelligent Fuzzer...", type: "info", delay: 700 },
  { text: "    Discovered 247 endpoints", type: "default", delay: 500 },
  { text: "    XSS vectors: 12 potential injection points", type: "default", delay: 400 },
  { text: "    SQLi: 3 parameters vulnerable to blind injection", type: "default", delay: 400 },
  { text: "    7 dynamic vulnerabilities found.", type: "default", phase: 2, phaseState: "done", delay: 300 },
  { text: "", type: "default", delay: 200 },
  { text: "[+] PHASE 3 · AI Vulnerability Chaining …", type: "phase", phase: 3, phaseState: "active", delay: 800 },
  { text: "    Exploit chaining logic mapped.", type: "default", delay: 600 },
  { text: "    Chain: SQLi → Auth Bypass → RCE (confidence: 87%)", type: "default", phase: 3, phaseState: "done", delay: 500 },
  { text: "", type: "default", delay: 200 },
  { text: "[+] PHASE 4 · Metasploit RPC Exploitation …", type: "phase", phase: 4, phaseState: "active", delay: 800 },
  { text: "    Status: Exploitation modules loaded", type: "default", delay: 500 },
  { text: "    Attempting payload delivery...", type: "default", delay: 600 },
  { text: "    Session established (meterpreter)", type: "success", phase: 4, phaseState: "done", delay: 500 },
  { text: "", type: "default", delay: 200 },
  { text: "[+] PHASE 5 · Compiling DevSecOps PDF Report …", type: "phase", phase: 5, phaseState: "active", delay: 800 },
  { text: "    Generating executive summary...", type: "default", delay: 400 },
  { text: "    Adding vulnerability matrices...", type: "default", delay: 400 },
  { text: "", type: "default", delay: 200 },
  { text: "✅  Report saved → /output/security_report.pdf", type: "success", phase: 5, phaseState: "done", delay: 500 },
];

const AutoPentApp = () => {
  const [targetUrl, setTargetUrl] = useState("");
  const [phaseStates, setPhaseStates] = useState<PhaseState[]>(Array(5).fill("idle"));
  const [consoleLines, setConsoleLines] = useState<ConsoleLine[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [status, setStatus] = useState<{ text: string; color: string }>({ text: "● IDLE", color: "muted-foreground" });
  const consoleRef = useRef<HTMLDivElement>(null);
  const timeoutsRef = useRef<NodeJS.Timeout[]>([]);

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleLines]);

  const clearConsole = () => {
    setConsoleLines([]);
    setPhaseStates(Array(5).fill("idle"));
    setStatus({ text: "● IDLE", color: "muted-foreground" });
  };

  const startScan = useCallback(() => {
    if (!targetUrl.trim()) {
      setConsoleLines((prev) => [...prev, { text: "[!] Please enter a target URL.", type: "warning" }]);
      return;
    }

    setIsScanning(true);
    setConsoleLines([]);
    setPhaseStates(Array(5).fill("idle"));
    setStatus({ text: "● SCANNING", color: "destructive" });

    // Use EventSource to connect to the backend
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const eventSource = new EventSource(`${apiUrl}/api/scan?url=${encodeURIComponent(targetUrl)}`);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.text) {
        setConsoleLines((prev) => [...prev, { text: data.text, type: data.type || "default" }]);
      }
      
      if (data.phase && data.phaseState) {
        setPhaseStates((prev) => {
          const next = [...prev];
          next[data.phase - 1] = data.phaseState;
          return next;
        });
        
        if (data.phase === 5 && data.phaseState === "done") {
          setIsScanning(false);
          setStatus({ text: "● COMPLETE", color: "success" });
          eventSource.close();
        }
      }
    };

    eventSource.onerror = (err) => {
      // If the scan was already marked as complete or is not scanning, ignore the close event
      if (eventSource.readyState === EventSource.CLOSED) {
        return;
      }
      console.error("EventSource failed:", err);
      setConsoleLines((prev) => [...prev, { text: "[!] Connection to backend lost.", type: "error" }]);
      setIsScanning(false);
      setStatus({ text: "● ERROR", color: "destructive" });
      eventSource.close();
    };
  }, [targetUrl]);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-[72px] border-b border-primary/30 flex-shrink-0 relative">
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
        <div>
          <h1 className="font-mono text-xl font-black tracking-[6px] text-primary">AUTOPENT</h1>
          <p className="font-mono text-[9px] tracking-[4px] text-muted-foreground">AI · AGENTIC · PENTEST FRAMEWORK</p>
        </div>
        <div className={`font-mono text-[11px] px-3.5 py-1 rounded-xl border ${
          status.color === "destructive" 
            ? "text-destructive border-destructive bg-destructive/10" 
            : status.color === "success" 
            ? "text-success border-success bg-success/10" 
            : "text-muted-foreground border-border bg-card"
        }`}>
          {status.text}
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 gap-4 p-5 overflow-hidden">
        {/* Left Panel */}
        <div className="w-[320px] flex-shrink-0 bg-panel border border-border rounded-lg p-5 flex flex-col gap-3.5 overflow-y-auto">
          {/* Target */}
          <label className="font-mono text-[10px] tracking-[3px] text-muted-foreground">TARGET</label>
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="http://target-app:5000"
            className="bg-card text-primary font-mono text-sm border border-border rounded-md px-3 py-2.5 focus:border-primary focus:bg-card/80 outline-none transition-colors"
          />

          <div className="h-px bg-border my-1" />

          {/* Phases */}
          <label className="font-mono text-[10px] tracking-[3px] text-muted-foreground">PIPELINE PHASES</label>
          <div className="flex flex-col gap-2">
            {PHASES.map((phase, i) => (
              <PhaseBadge key={phase.number} number={phase.number} title={phase.title} state={phaseStates[i]} />
            ))}
          </div>

          <div className="h-px bg-border my-1" />
          <div className="flex-1" />

          {/* Deploy Button */}
          <div className="flex items-center gap-2">
            {isScanning && (
              <div className="w-8 h-8 rounded-full border-2 border-primary border-t-destructive animate-spin flex-shrink-0" />
            )}
            <button
              onClick={startScan}
              disabled={isScanning}
              className="flex-1 bg-gradient-to-r from-primary to-primary/70 text-primary-foreground font-mono text-sm font-bold tracking-[2px] uppercase py-3 px-7 rounded-md shadow-[0_0_20px_hsl(var(--primary)/0.3)] hover:shadow-[0_0_30px_hsl(var(--primary)/0.5)] disabled:bg-card disabled:text-muted-foreground disabled:border disabled:border-border disabled:shadow-none transition-all"
            >
              ▶ DEPLOY AGENT
            </button>
          </div>

          {/* Export */}
          <button
            disabled={isScanning || phaseStates[4] !== "done"}
            className="border border-success text-success font-mono text-xs font-bold tracking-wider py-2.5 px-5 rounded-md hover:bg-success/10 disabled:text-muted-foreground disabled:border-border transition-all"
          >
            ⬇ EXPORT REPORT
          </button>

          {/* Clear */}
          <button
            onClick={clearConsole}
            className="border border-muted-foreground text-muted-foreground font-mono text-xs font-bold tracking-wider py-2.5 px-5 rounded-md hover:bg-muted-foreground/10 transition-all"
          >
            ✕ CLEAR CONSOLE
          </button>
        </div>

        {/* Right Panel - Console */}
        <div className="flex-1 bg-panel border border-border rounded-lg flex flex-col overflow-hidden">
          {/* Console Header */}
          <div className="flex items-center gap-4 px-4 h-10 bg-card border-b border-border rounded-t-lg flex-shrink-0">
            <div className="flex gap-1.5">
              <span className="text-destructive text-[10px]">●</span>
              <span className="text-warning text-[10px]">●</span>
              <span className="text-success text-[10px]">●</span>
            </div>
            <span className="font-mono text-[10px] tracking-[3px] text-muted-foreground">LIVE CONSOLE OUTPUT</span>
            <div className="flex-1" />
            <span className="font-mono text-[10px] text-muted-foreground/50">{consoleLines.length} lines</span>
          </div>

          {/* Console Body */}
          <div ref={consoleRef} className="flex-1 overflow-y-auto p-4 bg-console-bg relative">
            {/* Hacker watermark */}
            <img
              src={hackerWatermark}
              alt=""
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 object-contain opacity-50 pointer-events-none select-none"
              aria-hidden="true"
            />
            <div className="relative z-10">
              {consoleLines.map((line, i) => (
                <div key={i} className={`font-mono text-xs leading-relaxed animate-[typing_0.2s_ease-out] ${
                  line.type === "info" ? "text-warning" :
                  line.type === "phase" ? "text-primary" :
                  line.type === "success" ? "text-success" :
                  line.type === "error" ? "text-destructive" :
                  line.type === "warning" ? "text-warning" :
                  "text-console-text"
                }`}>
                  {line.text}
                </div>
              ))}
              {isScanning && (
                <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-0.5" />
              )}
            </div>
          </div>

          {/* Progress bar */}
          {isScanning && (
            <div className="h-[3px] bg-card rounded-b-lg overflow-hidden">
              <div className="h-full bg-gradient-to-r from-primary to-destructive rounded-sm animate-[shimmer_1.5s_ease-in-out_infinite] bg-[length:200%_100%]" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AutoPentApp;
