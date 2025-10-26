import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getJSON, postJSON } from "../api";
import EventCard, { EventT } from "../components/EventCard";
import SearchBar from "../components/SearchBar";

interface PaginationInfo {
  current_page: number;
  total_pages: number;
  total_events: number;
  events_per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

interface FeedResponse {
  events: EventT[];
  pagination: PaginationInfo;
}

export default function Feed() {
  const [events, setEvents] = useState<EventT[]>([]);
  const [pagination, setPagination] = useState<PaginationInfo | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [userInterests, setUserInterests] = useState<string[]>([]);
  const nav = useNavigate();
  const userId = localStorage.getItem("user_id") || "";
  console.log("Feed page - Current user_id:", userId);

  async function loadUserInterests() {
    if (!userId) return;
    try {
      const userData = await getJSON<{interests: string[]}>(`/users/${userId}`);
      console.log("User interests loaded:", userData.interests);
      setUserInterests(userData.interests || []);
    } catch (error) {
      console.error("Error loading user interests:", error);
      setUserInterests([]);
    }
  }

  async function loadFeed(page: number = 1) {
    setLoading(true);
    try {
      const path = userId 
        ? `/events/feed?user_id=${userId}&limit=20&page=${page}` 
        : `/events/feed?limit=20&page=${page}`;
      const data = await getJSON<FeedResponse>(path);
      setEvents(data.events);
      setPagination(data.pagination);
      setCurrentPage(page);
    } finally { setLoading(false); }
  }

  async function doSearch(q: string) {
    if (!q.trim()) return loadFeed(1);
    setLoading(true);
    try {
      const data = await getJSON<EventT[]>(`/events/search?q=${encodeURIComponent(q)}&limit=20&user_id=${userId}`);
      setEvents(data);
      setPagination(null); // Clear pagination for search results
    } finally { setLoading(false); }
  }

  async function ingestGatechEvents() {
    setIngesting(true);
    try {
      const result = await postJSON("/ingestion/gatech-events", {});
      alert(`Successfully ingested ${result.results?.total_events || 0} Georgia Tech events!`);
      // Reload the feed to show new events
      await loadFeed(1);
    } catch (error) {
      alert("Failed to ingest events. Check console for details.");
      console.error("Ingestion error:", error);
    } finally {
      setIngesting(false);
    }
  }

  function goToPage(page: number) {
    if (page >= 1 && pagination && page <= pagination.total_pages) {
      loadFeed(page);
    }
  }

  useEffect(() => { 
    loadFeed(1);
    loadUserInterests();
  }, [userId]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2>{userId ? "Your feed" : "Feed (not personalized yet — go to Onboarding)"}</h2>
          {userId && userInterests.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <span className="meta">Your interests: </span>
              <div style={{ display: "inline-flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                {userInterests.map(interest => (
                  <span key={interest} className="chip" style={{ fontSize: "0.8em", padding: "2px 6px" }}>
                    {interest}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        <button 
          className="btn secondary" 
          onClick={ingestGatechEvents}
          disabled={ingesting}
          style={{ fontSize: "0.9em" }}
        >
          {ingesting ? "Loading Georgia Tech Events..." : "Load Georgia Tech Events"}
        </button>
      </div>
      
      {pagination && (
        <div style={{ marginBottom: 16, padding: "8px 12px", backgroundColor: "#f8f9fa", borderRadius: "4px", fontSize: "0.9em" }}>
          Showing {events.length} of {pagination.total_events} events (Page {pagination.current_page} of {pagination.total_pages})
        </div>
      )}
      
      <SearchBar onSearch={doSearch} />
      
      {loading ? <p>Loading…</p> :
        events.length ? (
          <>
            {events.map(ev=>(
              <EventCard key={ev.id} ev={ev} onSaved={() => loadFeed(currentPage)}/>
            ))}
            
            {/* Pagination Controls */}
            {pagination && pagination.total_pages > 1 && (
              <div style={{ 
                display: "flex", 
                justifyContent: "center", 
                alignItems: "center", 
                gap: "8px", 
                marginTop: "24px",
                padding: "16px",
                backgroundColor: "#f8f9fa",
                borderRadius: "8px"
              }}>
                {/* First Page Button */}
                <button 
                  className="btn secondary"
                  onClick={() => goToPage(1)}
                  disabled={currentPage === 1}
                  style={{ padding: "8px 12px" }}
                >
                  1
                </button>
                
                <button 
                  className="btn secondary"
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={!pagination.has_previous}
                  style={{ padding: "8px 12px" }}
                >
                  ← Previous
                </button>
                
                <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
                  {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                    let pageNum;
                    if (pagination.total_pages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= pagination.total_pages - 2) {
                      pageNum = pagination.total_pages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        className={pageNum === currentPage ? "btn" : "btn secondary"}
                        onClick={() => goToPage(pageNum)}
                        style={{ 
                          padding: "8px 12px", 
                          minWidth: "40px",
                          backgroundColor: pageNum === currentPage ? "#007bff" : "transparent",
                          color: pageNum === currentPage ? "white" : "#007bff"
                        }}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <button 
                  className="btn secondary"
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={!pagination.has_next}
                  style={{ padding: "8px 12px" }}
                >
                  Next →
                </button>
                
                {/* Last Page Button */}
                <button 
                  className="btn secondary"
                  onClick={() => goToPage(pagination.total_pages)}
                  disabled={currentPage === pagination.total_pages}
                  style={{ padding: "8px 12px" }}
                >
                  {pagination.total_pages}
                </button>
              </div>
            )}
          </>
        ) : <p>No events yet. Click "Load Georgia Tech Events" to get started!</p>}
      
      {!userId && <p><button onClick={()=>nav("/onboarding")}>Go to Onboarding</button></p>}
    </div>
  );
}
