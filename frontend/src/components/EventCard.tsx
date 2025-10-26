import React, { useState, useEffect } from "react";
import { postJSON, getJSON } from "../api";

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
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const domain = (() => {
    try {
      return ev.url ? new URL(ev.url).hostname.replace(/^www\./, "") : "";
    } catch {
      return "";
    }
  })();

  // Check if event is saved when component mounts
  useEffect(() => {
    if (userId) {
      checkIfSaved();
    }
  }, [userId, ev.id]);

  async function checkIfSaved() {
    try {
      // For now, we'll use a simple approach - check localStorage
      const savedEvents = JSON.parse(localStorage.getItem('saved_events') || '[]');
      console.log(`Checking if event ${ev.id} is saved. Saved events:`, savedEvents);
      const isEventSaved = savedEvents.includes(ev.id);
      console.log(`Event ${ev.id} is saved:`, isEventSaved);
      setIsSaved(isEventSaved);
    } catch (error) {
      console.error("Error checking if event is saved:", error);
    }
  }

  async function toggleSave() {
    if (!userId) return alert("Please onboard first.");
    
    setIsLoading(true);
    try {
      if (isSaved) {
        // Unsave the event - just update localStorage
        const savedEvents = JSON.parse(localStorage.getItem('saved_events') || '[]');
        const updatedEvents = savedEvents.filter(id => id !== ev.id);
        localStorage.setItem('saved_events', JSON.stringify(updatedEvents));
        console.log(`Unsaved event ${ev.id}. Updated saved events:`, updatedEvents);
        setIsSaved(false);
      } else {
        // Save the event - just update localStorage
        const savedEvents = JSON.parse(localStorage.getItem('saved_events') || '[]');
        if (!savedEvents.includes(ev.id)) {
          savedEvents.push(ev.id);
          localStorage.setItem('saved_events', JSON.stringify(savedEvents));
          console.log(`Saved event ${ev.id}. Updated saved events:`, savedEvents);
        }
        setIsSaved(true);
      }
      onSaved?.();
    } catch (error) {
      console.error("Error toggling save:", error);
      alert("Failed to save/unsave event. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  async function signal(kind: "clicked" | "saved") {
    if (!userId) return alert("Please onboard first.");
    
    if (kind === "saved") {
      await toggleSave();
    } else {
      // Call the feedback API for clicked events
      await postJSON("/feedback", {
        user_id: userId,
        event_id: ev.id,
        [kind]: true,
      });
    }
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
        <button 
          className="btn" 
          onClick={() => signal("saved")}
          disabled={isLoading}
          style={{ 
            backgroundColor: isSaved ? "#fff" : "var(--gt-gold)", 
            color: isSaved ? "var(--gt-gold)" : "#111", 
            border: "1px solid var(--gt-gold)",
            opacity: isLoading ? 0.7 : 1
          }}
        >
          {isLoading ? "..." : (isSaved ? "Saved" : "Save")}
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
