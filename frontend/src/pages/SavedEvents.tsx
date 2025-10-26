import React, { useEffect, useState } from "react";
import { getJSON } from "../api";
import EventCard, { EventT } from "../components/EventCard";

export default function SavedEvents() {
  const [savedEvents, setSavedEvents] = useState<EventT[]>([]);
  const [loading, setLoading] = useState(true);
  const userId = localStorage.getItem("user_id") || "";

  async function loadSavedEvents() {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    try {
      // Get saved event IDs from localStorage
      const savedEventIds = JSON.parse(localStorage.getItem('saved_events') || '[]');
      console.log("Saved event IDs from localStorage:", savedEventIds);
      
      if (savedEventIds.length === 0) {
        console.log("No saved events found in localStorage");
        setSavedEvents([]);
        setLoading(false);
        return;
      }
      
      // Get all events from the feed
      console.log("Fetching events from feed...");
      const feedResponse = await getJSON("/events/feed");
      console.log("Feed response:", feedResponse);
      
      const allEvents = feedResponse.events || [];
      console.log("All events count:", allEvents.length);
      
      // Filter events to only include saved ones
      const savedEventsList = allEvents.filter(event => {
        const isSaved = savedEventIds.includes(event.id);
        console.log(`Event ${event.id} (${event.title}): ${isSaved ? 'SAVED' : 'not saved'}`);
        return isSaved;
      });
      
      console.log("Filtered saved events count:", savedEventsList.length);
      
      // Sort events by start_time in chronological order (earliest first)
      const sortedEvents = savedEventsList.sort((a, b) => 
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
      );
      
      console.log("Final sorted events:", sortedEvents.length);
      setSavedEvents(sortedEvents);
    } catch (error) {
      console.error("Error loading saved events:", error);
      setSavedEvents([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Test localStorage immediately
    console.log("=== SAVED EVENTS DEBUG ===");
    console.log("localStorage available:", typeof localStorage !== 'undefined');
    console.log("Raw localStorage 'saved_events':", localStorage.getItem('saved_events'));
    
    try {
      const parsed = JSON.parse(localStorage.getItem('saved_events') || '[]');
      console.log("Parsed saved events:", parsed);
      console.log("Type:", typeof parsed, "Length:", parsed.length);
    } catch (e) {
      console.error("Error parsing saved events:", e);
    }
    
    loadSavedEvents();
  }, [userId]);

  if (!userId) {
    return (
      <div>
        <h2>Saved Events</h2>
        <p>Please complete onboarding to save events.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h2>Saved Events</h2>
        <p style={{ color: "#666", fontSize: "0.9em", marginBottom: 16 }}>
          Events are sorted in chronological order (earliest first)
        </p>
      </div>
      
      {loading ? (
        <p>Loading saved events...</p>
      ) : savedEvents.length > 0 ? (
        <>
          <div style={{ 
            marginBottom: 16, 
            padding: "8px 12px", 
            backgroundColor: "#f8f9fa", 
            borderRadius: "4px", 
            fontSize: "0.9em" 
          }}>
            You have {savedEvents.length} saved event{savedEvents.length !== 1 ? 's' : ''}
          </div>
          
          {savedEvents.map(ev => (
            <EventCard 
              key={ev.id} 
              ev={ev} 
              onSaved={loadSavedEvents}
            />
          ))}
        </>
      ) : (
        <div style={{ 
          textAlign: "center", 
          padding: "40px 20px", 
          color: "#666" 
        }}>
          <h3>No saved events yet</h3>
          <p>Start exploring events in the Feed and save the ones you're interested in!</p>
        </div>
      )}
    </div>
  );
}
