import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getJSON, postJSON } from "../api";
import EventCard, { EventT } from "../components/EventCard";
import SearchBar from "../components/SearchBar";

export default function Feed() {
  const [events, setEvents] = useState<EventT[]>([]);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const nav = useNavigate();
  const userId = localStorage.getItem("user_id") || "";

  async function loadFeed() {
    setLoading(true);
    try {
      const path = userId ? `/events/feed?user_id=${userId}&limit=12` : `/events/feed?limit=12`;
      const data = await getJSON<EventT[]>(path);
      setEvents(data);
    } finally { setLoading(false); }
  }

  async function doSearch(q: string) {
    if (!q.trim()) return loadFeed();
    setLoading(true);
    try {
      const data = await getJSON<EventT[]>(`/events/search?q=${encodeURIComponent(q)}&limit=12&user_id=${userId}`);
      setEvents(data);
    } finally { setLoading(false); }
  }

  async function ingestGatechEvents() {
    setIngesting(true);
    try {
      const result = await postJSON("/ingestion/gatech-events", {});
      alert(`Successfully ingested ${result.results?.total_events || 0} Georgia Tech events!`);
      // Reload the feed to show new events
      await loadFeed();
    } catch (error) {
      alert("Failed to ingest events. Check console for details.");
      console.error("Ingestion error:", error);
    } finally {
      setIngesting(false);
    }
  }

  useEffect(() => { loadFeed(); }, [userId]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h2>{userId ? "Your feed" : "Feed (not personalized yet — go to Onboarding)"}</h2>
        <button 
          className="btn secondary" 
          onClick={ingestGatechEvents}
          disabled={ingesting}
          style={{ fontSize: "0.9em" }}
        >
          {ingesting ? "Loading Georgia Tech Events..." : "Load Georgia Tech Events"}
        </button>
      </div>
      <SearchBar onSearch={doSearch} />
      {loading ? <p>Loading…</p> :
        events.length ? events.map(ev=>(
          <EventCard key={ev.id} ev={ev} onSaved={loadFeed}/>
        )) : <p>No events yet. Click "Load Georgia Tech Events" to get started!</p>}
      {!userId && <p><button onClick={()=>nav("/onboarding")}>Go to Onboarding</button></p>}
    </div>
  );
}
