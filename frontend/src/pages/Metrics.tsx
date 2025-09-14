import React, { useEffect, useState } from "react";
import { getJSON } from "../api";

type M = { window: string; clicks: number; saves: number; rsvps: number; interactions: number };

export default function Metrics() {
  const [m, setM] = useState<M | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try { setM(await getJSON<M>("/admin/metrics")); setErr(null); }
    catch (e: any) { setErr(String(e)); }
  }

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h2>Metrics (last 24h)</h2>
      {err && <p style={{color:"crimson"}}>{err}</p>}
      {!m ? <p>Loading…</p> : (
        <ul>
          <li>Clicks: {m.clicks}</li>
          <li>Saves: {m.saves}</li>
          <li>RSVPs: {m.rsvps}</li>
          <li>Total interactions: {m.interactions}</li>
        </ul>
      )}
      <button onClick={load}>Refresh</button>
    </div>
  );
}
