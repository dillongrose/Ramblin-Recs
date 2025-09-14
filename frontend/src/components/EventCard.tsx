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
};

export default function EventCard({ ev, onSaved }: { ev: EventT; onSaved?: () => void }) {
  const userId = localStorage.getItem("user_id") || "";

  async function click(kind: "clicked" | "saved") {
    if (!userId) return alert("Please onboard first.");
    await postJSON("/feedback", {
      user_id: userId,
      event_id: ev.id,
      [kind]: true,
    });
    onSaved?.();
  }

  return (
    <div style={{ border: "1px solid #e5e5e5", borderRadius: 12, padding: 12, marginBottom: 12 }}>
      <div style={{ display:"flex", justifyContent:"space-between", gap:12, alignItems:"baseline" }}>
        <h3 style={{ margin: 0 }}>{ev.title}</h3>
        {typeof ev.score === "number" && <small>score {ev.score.toFixed(3)}</small>}
      </div>
      <div style={{ color:"#555" }}>
        {new Date(ev.start_time).toLocaleString()}
        {ev.location ? ` • ${ev.location}` : ""}
      </div>
      {ev.tags?.length ? (
        <div style={{ marginTop:8, display:"flex", flexWrap:"wrap", gap:6 }}>
          {ev.tags.map(t=>(
            <span key={t} style={{ padding:"2px 8px", border:"1px solid #ddd", borderRadius:999, fontSize:12 }}>{t}</span>
          ))}
        </div>
      ) : null}
      {ev.summary && <p style={{ marginTop:8 }}>{ev.summary}</p>}
      {ev.why && <p style={{ marginTop:4, color:"#0a6" }}>Why: {ev.why}</p>}
      <div style={{ display:"flex", gap:8, marginTop:8 }}>
        <button onClick={()=>click("clicked")}>Like</button>
        <button onClick={()=>click("saved")}>Save</button>
      </div>
    </div>
  );
}
