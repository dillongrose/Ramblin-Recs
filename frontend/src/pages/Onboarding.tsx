import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { postJSON, getJSON } from "../api";

const PRESET_INTERESTS = [
  // Row 1: Academic & Core Interests
  "academic", "technology", "student", "arts", "social",
  "volunteer", "free", "food", "sports", "wellness",
  
  // Row 2: Culture & Community
  "religious", "culture", "career", "graduate-student", "first-year",
  "music", "dance", "theater", "film", "photography",
  
  // Row 3: Activities & Hobbies
  "gaming", "anime", "manga", "books", "writing",
  "drawing", "painting", "crafts", "cooking", "baking",
  
  // Row 4: Specialized Interests
  "robotics", "ai", "machine-learning", "data-science", "cybersecurity",
  "web-development", "mobile-apps", "startups", "entrepreneurship", "networking"
];

export default function Onboarding() {
  const [email, setEmail] = useState(localStorage.getItem("user_email") || "");
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [custom, setCustom] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const nav = useNavigate();

  function toggle(tag: string) {
    setSelected((s) => (s.includes(tag) ? s.filter((t) => t !== tag) : [...s, tag]));
  }

  async function loadExistingInterests() {
    const userId = localStorage.getItem("user_id");
    if (!userId || !email) return;
    
    try {
      const userData = await getJSON<{interests: string[], display_name: string}>(`/users/${userId}`);
      setSelected(userData.interests || []);
      setName(userData.display_name || "");
      setIsEditing(true);
    } catch (error) {
      console.error("Error loading existing interests:", error);
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const customs = custom
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const interests = Array.from(new Set([...selected, ...customs]));

    if (!email) {
      setError("Please enter an email.");
      return;
    }

    setSaving(true);
    try {
      console.log("Submitting onboarding with:", { email, name, interests });
      const res = await postJSON<{ id: string }>("/users/bootstrap", {
        email,
        display_name: name || null,
        interests,
      });
      console.log("Bootstrap response:", res);
      localStorage.setItem("user_id", res.id);
      localStorage.setItem("user_email", email);
      console.log("Saved user_id to localStorage:", res.id);
      nav("/feed", { replace: true });
    } catch (err: any) {
      console.error("Bootstrap error:", err);
      setError(String(err?.message || err));
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    if (email) {
      loadExistingInterests();
    }
  }, [email]);

  return (
    <div className="card" style={{ maxWidth: 720, margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>
        {isEditing ? "Update Your Interests" : "Tell us what you like"}
      </h2>
      <p className="meta" style={{ marginTop: 4 }}>
        {isEditing 
          ? "Add or remove interests to update your recommendations. Your email is saved."
          : "Pick a few interests to personalize your recommendations. You can always change this later."
        }
      </p>

      <form onSubmit={submit} style={{ marginTop: 12 }}>
        <label>
          Email<br />
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@gatech.edu"
            style={{ width: "100%", padding: 10, borderRadius: 10, border: "1px solid #ddd" }}
          />
        </label>

        <div style={{ height: 12 }} />

        <label>
          Name (optional)<br />
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Buzz"
            style={{ width: "100%", padding: 10, borderRadius: 10, border: "1px solid #ddd" }}
          />
        </label>

        <div style={{ height: 16 }} />

        <div className="meta" style={{ marginBottom: 8 }}>Quick picks (40 most popular interests)</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {Array.from({ length: 4 }, (_, rowIndex) => (
            <div key={rowIndex} style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {PRESET_INTERESTS.slice(rowIndex * 10, (rowIndex + 1) * 10).map((tag) => {
                const active = selected.includes(tag);
                return (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => toggle(tag)}
                    className="chip"
                    style={{
                      background: active ? "var(--gt-gold)" : "#fff",
                      borderColor: active ? "var(--gt-gold)" : "#ddd",
                      color: active ? "#111" : "inherit",
                      cursor: "pointer",
                      fontSize: "0.9em",
                      padding: "6px 12px",
                    }}
                  >
                    {tag}
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        <div style={{ height: 16 }} />

        <label>
          Custom interests
          <div className="meta" style={{ margin: "4px 0 6px" }}>
            Add your own, separated by commas (e.g., <em>robotics, hackathons</em>)
          </div>
          <input
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            placeholder="robotics, hackathons"
            style={{ width: "100%", padding: 10, borderRadius: 10, border: "1px solid #ddd" }}
          />
        </label>

        {error && (
          <p style={{ color: "crimson", marginTop: 12 }}>
            {error}
          </p>
        )}

        <div style={{ height: 16 }} />

        <button className="btn" disabled={saving || !email} type="submit">
          {saving ? "Saving..." : (isEditing ? "Update Interests" : "Save & Continue")}
        </button>
      </form>
    </div>
  );
}
