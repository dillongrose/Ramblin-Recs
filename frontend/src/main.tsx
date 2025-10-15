import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import Feed from "./pages/Feed";
import Onboarding from "./pages/Onboarding";
import Metrics from "./pages/Metrics";
import Feedback from "./pages/Feedback";
import "./index.css";

function Shell() {
  return (
    <>
      <header className="header">
        <div className="container">
          <div className="brand">
            <img src="/bee.svg" alt="Yellow jacket" />
            <h1>Ramblin Recs</h1>
          </div>
          <nav className="nav">
            <Link to="/feed">Feed</Link>
            <Link to="/onboarding">Onboarding</Link>
            <Link to="/metrics">Metrics</Link>
            <Link to="/feedback">Feedback</Link>
          </nav>
        </div>
      </header>
      <div className="container">
        <div className="banner">Made for Georgia Tech — personalized event recommendations ⚡️</div>
        <Routes>
          <Route path="/" element={<Navigate to="/feed" replace />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="*" element={<div>Not found</div>} />
        </Routes>
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  </React.StrictMode>
);
