import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { postJSON } from "../api";

const ALL = ["tech","career","music","sports","wellness","volunteering","arts","social"];

export default function Onboarding() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [sel, setSel] = useState<string[]>([]);
  const [custom, setCustom] = useState("");
  const [saving, setSaving] = useState(false);
  const nav = useNavigate();

  function toggle(tag: string) {
    setSel(s => s.includes(tag) ? s.filter(t => t!==tag) : [...s, tag]);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const interests = [...sel, ...custom.split(",").map(s=>s.trim()).filter(Boolean)];
    setSaving(true);
    try {
      const res = await postJSON<{id:string}>("/users/bootstrap", {
        email, display_name: name, interests
      });
      localStorage.setItem("user_id", res.id);
      nav("/feed", { replace: true });
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>Tell us what you like</h2>
      <label>Email<br/>
        <input required type="email" value={email} onChange={e=>setEmail(e.target.value)} />
      </label>
      <br/><br/>
      <label>Name (optional)<br/>
        <input value={name} onChange={e=>setName(e.target.value)} />
      </label>
      <br/><br/>
      <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
        {ALL.map(tag=>(
          <button
            type="button"
            key={tag}
            onClick={()=>toggle(tag)}
            style={{
              padding:"6px 10px",
              borderRadius:999,
              border:"1px solid #ccc",
              background: sel.includes(tag) ? "#eef" : "white"
            }}
          >{tag}</button>
        ))}
      </div>
      <small>Tip: add custom interests separated by commas</small>
      <br/>
      <input
        placeholder="robotics, hackathons"
        value={custom}
        onChange={e=>setCustom(e.target.value)}
        style={{ width: "100%", marginTop: 8 }}
      />
      <br/><br/>
      <button disabled={saving || !email} type="submit">{saving ? "Saving..." : "Save & Continue"}</button>
    </form>
  );
}
