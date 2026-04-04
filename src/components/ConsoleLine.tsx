interface ConsoleLineProps {
  text: string;
  type?: "info" | "phase" | "success" | "error" | "warning" | "default";
}

const typeColors: Record<string, string> = {
  info: "text-warning",
  phase: "text-primary",
  success: "text-success",
  error: "text-destructive",
  warning: "text-warning",
  default: "text-console-text",
};

export const ConsoleLine = ({ text, type = "default" }: ConsoleLineProps) => (
  <div className={`font-mono text-xs leading-relaxed ${typeColors[type]} animate-[typing_0.2s_ease-out]`}>
    {text}
  </div>
);

export default ConsoleLine;
