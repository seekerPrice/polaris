// Dropzone — drag/click target for the SOC 2 PDF + Load-demo CTA. All
// behavior is delegated via props so the page owns the upload pipeline.
"use client";
import type { ChangeEvent, DragEvent, MouseEvent } from "react";
import { I } from "./icons";

type Props = {
  isDragging: boolean;
  jobId: string | null;
  replaying: boolean;
  onDrop: (e: DragEvent<HTMLDivElement>) => void;
  onDragOver: (e: DragEvent<HTMLDivElement>) => void;
  onDragLeave: (e: DragEvent<HTMLDivElement>) => void;
  onPickFile: (e: ChangeEvent<HTMLInputElement>) => void;
  onLoadDemo: () => void;
};

export function Dropzone({
  isDragging, jobId, replaying, onDrop, onDragOver, onDragLeave, onPickFile, onLoadDemo,
}: Props) {
  const handleLoadDemoClick = (e: MouseEvent) => {
    e.stopPropagation();
    onLoadDemo();
  };
  return (
    <div
      className={"dropzone" + (isDragging ? " dropzone--armed" : "")}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      onClick={() => document.getElementById("file-pick")?.click()}
      role="button"
      tabIndex={0}
    >
      <div className="dropzone__icon"><I.Upload /></div>
      <div className="dropzone__title">
        {isDragging ? "Release to ingest" : "Drop a SOC 2 / OWASP / EU AI Act PDF"}
      </div>
      <div className="dropzone__sub">.pdf · .md · .txt — single file</div>
      <div className="dropzone__demo">
        <button
          className={"btn " + (jobId ? "btn--primary" : "btn--cta")}
          onClick={handleLoadDemoClick}
          disabled={replaying}
        >
          <I.Play /> Load demo SOC 2 PDF
        </button>
      </div>
      <input
        id="file-pick"
        type="file"
        className="hidden-input"
        accept=".pdf,.md,.txt"
        onChange={onPickFile}
        data-testid="upload-input"
      />
    </div>
  );
}
