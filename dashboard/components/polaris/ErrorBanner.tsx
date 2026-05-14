// ErrorBanner — red rose-glow banner shown above the hero when either the
// client-side fetch fails OR the SSE pipeline_error event arrives.
import type { State } from "@/lib/state";
import { I } from "./icons";

type Props = { error: State["error"]; pipelineError: State["pipelineError"] };

export function ErrorBanner({ error, pipelineError }: Props) {
  if (!error && !pipelineError) return null;
  return (
    <div className="error-banner">
      <I.Alert />
      <div>
        {error && (
          <div>
            <strong>Client error:</strong> {error}
          </div>
        )}
        {pipelineError && (
          <div>
            <strong>Pipeline failed at {pipelineError.stage}:</strong> {pipelineError.error}
            {pipelineError.test_summary && (
              <div style={{ fontSize: 10.5, color: "oklch(0.85 0.04 18)", marginTop: 4 }}>
                LT test: {pipelineError.test_summary.slice(0, 200)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
