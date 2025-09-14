import React, { useState } from "react";

export default function SearchBar({ onSearch }: { onSearch: (q: string)=>void }) {
  const [q, setQ] = useState("");
  return (
    <form onSubmit={e=>{e.preventDefault(); onSearch(q);}} style={{display:"flex", gap:8, margin:"8px 0 16px"}}>
      <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search events (workshop, career, music…)" style={{flex:1}} />
      <button type="submit">Search</button>
    </form>
  );
}
