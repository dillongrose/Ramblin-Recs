import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { postJSON } from "../api";

const PRESET_INTERESTS = [
  "tech",
  "career",
  "music",
  "sports",
  "wellness",
  "volunteering",
  "arts",
  "social",
];

export default function Onboarding() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [custom, setCustom] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nav = useNavigate();

  function toggle(tag: string) {
    setSelected((s) => (s.includes(tag) ? s.filter((t) => t !== tag) : [...s, tag]));
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
      const res = await postJSON<{ id: string }>("/users/bootstrap", {
        email,
        display_name: name || null,
        interests,
      });
      localStorage.setItem("user_id", res.id);
      nav("/feed", { replace: true });
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 720, margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>Tell us what you like</h2>
      <p className="meta" style={{ marginTop: 4 }}>
        Pick a few interests to personalize your recommendations. You can always change this later.
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

        <div className="meta" style={{ marginBottom: 8 }}>Quick picks</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {PRESET_INTERESTS.map((tag) => {
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
                }}
              >
                {tag}
              </button>
            );
          })}
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
          {saving ? "Saving..." : "Save & Continue"}
        </button>
      </form>
    </div>
  );
}
