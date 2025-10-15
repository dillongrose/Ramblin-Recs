import React from "react";
import { postJSON } from "../api";

export type EventT = {
  id: string;
  title: string;
  start_time: string;
  location?: string | null;
  tags?: string[];
  score?: number;
  summary?: string;
  why?: string;
  url?: string;
  description?: string;
  host?: string;
};

export default function EventCard({
  ev,
  onSaved,
}: {
  ev: EventT;
  onSaved?: () => void;
}) {
  const userId = localStorage.getItem("user_id") || "";

  const domain = (() => {
    try {
      return ev.url ? new URL(ev.url).hostname.replace(/^www\./, "") : "";
    } catch {
      return "";
    }
  })();

  async function signal(kind: "clicked" | "saved") {
    if (!userId) return alert("Please onboard first.");
    await postJSON("/feedback", {
      user_id: userId,
      event_id: ev.id,
      [kind]: true,
    });
    onSaved?.();
  }

  return (
    <div className="card" style={{ marginBottom: 14 }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
          alignItems: "baseline",
        }}
      >
        <h3 style={{ margin: 0 }}>{ev.title}</h3>
        {typeof ev.score === "number" && (
          <small className="meta">score {ev.score.toFixed(3)}</small>
        )}
      </div>

      <div className="meta">
        {new Date(ev.start_time).toLocaleString()}
        {ev.location ? ` • ${ev.location}` : ""}
        {ev.host ? ` • ${ev.host}` : ""}
        {domain && (
          <>
            {" "}
            • <span className="chip" style={{ borderColor: "#ccc" }}>{domain}</span>
          </>
        )}
      </div>

      {ev.tags?.length ? (
        <div className="chips">
          {ev.tags.map((t) => (
            <span key={t} className="chip">
              {t}
            </span>
          ))}
        </div>
      ) : null}

      {ev.description && <p style={{ marginTop: 8, fontSize: "0.9em", color: "#666" }}>{ev.description}</p>}
      {ev.summary && <p style={{ marginTop: 8 }}>{ev.summary}</p>}
      {ev.why && (
        <p style={{ marginTop: 4, color: "#0a6" }}>
          <strong>Why:</strong> {ev.why}
        </p>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <button className="btn" onClick={() => signal("clicked")}>
          Like
        </button>
        <button className="btn secondary" onClick={() => signal("saved")}>
          Save
        </button>
        {ev.url && (
          <a 
            className="btn secondary" 
            href={ev.url} 
            target="_blank" 
            rel="noreferrer"
            onClick={() => signal("clicked")}
          >
            View on Georgia Tech
          </a>
        )}
      </div>
    </div>
  );
}
