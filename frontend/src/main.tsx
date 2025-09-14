import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import Feed from "./pages/Feed";
import Onboarding from "./pages/Onboarding";
import "./index.css";
import Metrics from "./pages/Metrics";


function Shell() {
  return (
    <div style={{ fontFamily: "system-ui", maxWidth: 900, margin: "24px auto", padding: "0 16px" }}>
      <header style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 24 }}><Link to="/feed">Ramblin Recs</Link></h1>
        <nav style={{ display: "flex", gap: 12 }}>
          <Link to="/feed">Feed</Link>
          <Link to="/onboarding">Onboarding</Link>
          <Link to="/metrics">Metrics</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Navigate to="/feed" replace />} />
        <Route path="/feed" element={<Feed />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="*" element={<div>Not found</div>} />
        <Route path="/metrics" element={<Metrics />} />
      </Routes>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  </React.StrictMode>
);
