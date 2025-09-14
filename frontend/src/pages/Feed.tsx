import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getJSON } from "../api";
import EventCard, { EventT } from "../components/EventCard";
import SearchBar from "../components/SearchBar";

export default function Feed() {
  const [events, setEvents] = useState<EventT[]>([]);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => { loadFeed(); }, [userId]);

  return (
    <div>
      <h2>{userId ? "Your feed" : "Feed (not personalized yet — go to Onboarding)"}</h2>
      <SearchBar onSearch={doSearch} />
      {loading ? <p>Loading…</p> :
        events.length ? events.map(ev=>(
          <EventCard key={ev.id} ev={ev} onSaved={loadFeed}/>
        )) : <p>No events yet.</p>}
      {!userId && <p><button onClick={()=>nav("/onboarding")}>Go to Onboarding</button></p>}
    </div>
  );
}
