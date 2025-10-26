import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import Feed from "./pages/Feed";
import Onboarding from "./pages/Onboarding";
import Feedback from "./pages/Feedback";
import SavedEvents from "./pages/SavedEvents";
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
            <Link to="/saved">Saved Events</Link>
            <Link to="/onboarding">Onboarding</Link>
            <Link to="/feedback">Feedback</Link>
          </nav>
        </div>
      </header>
      <div className="container">
        <div className="banner">Made for Georgia Tech — personalized event recommendations ⚡️</div>
        <Routes>
          <Route path="/" element={<Navigate to="/feed" replace />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/saved" element={<SavedEvents />} />
          <Route path="/onboarding" element={<Onboarding />} />
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
