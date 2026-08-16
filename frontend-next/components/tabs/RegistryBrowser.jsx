"use client";
import { useState, useEffect } from "react";
import { Database, Search } from "lucide-react";

export default function RegistryBrowser({ isActive }) {
  const [query, setQuery] = useState("");
  const [titles, setTitles] = useState([]);
  const [loading, setLoading] = useState(false);

  async function searchRegistry(q) {
    setLoading(true);
    try {
      const res = await fetch(`/api/titles/search?query=${encodeURIComponent(q)}&limit=30`);
      const data = await res.json();
      setTitles(data.titles || []);
    } catch (e) {
      console.error("Registry search error:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (isActive) searchRegistry("");
  }, [isActive]);

  return (
    <section id="db-tab" className="tab-content active">
      <div className="card glass-card">
        <div className="card-header">
          <div className="card-title"><Database size={18} /> Registered Titles Master Registry (160k+ Dataset)</div>
          <span className="pill-info">Sub-Second Search</span>
        </div>

        <div className="db-search-bar">
          <div className="input-wrapper flex-1">
            <Search className="input-icon" size={18} />
            <input
              type="text"
              id="db-search-input"
              placeholder="Search by title, anchor word, registration number, or state..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && searchRegistry(query.trim())}
            />
          </div>
          <button id="db-search-btn" className="btn btn-primary" onClick={() => searchRegistry(query.trim())}>
            <Search size={15} /> Search Registry
          </button>
        </div>

        <div className="table-wrapper">
          <table className="custom-table" id="registry-table">
            <thead>
              <tr>
                <th># ID</th>
                <th>Registered Title</th>
                <th>Distinct Anchor</th>
                <th>Registration No.</th>
                <th>Language</th>
                <th>State / UT</th>
                <th>Periodicity</th>
              </tr>
            </thead>
            <tbody id="registry-tbody">
              {loading ? (
                <tr><td colSpan={7} className="text-center text-muted">Loading registry dataset...</td></tr>
              ) : titles.length === 0 ? (
                <tr><td colSpan={7} className="text-center text-muted">No matching titles found in registry.</td></tr>
              ) : titles.map((t, i) => (
                <tr key={i}>
                  <td><code>#{t.id + 1}</code></td>
                  <td><strong>{t.title}</strong></td>
                  <td><span className="text-muted">{t.anchor_words || "N/A"}</span></td>
                  <td><code>{t.registration_no}</code></td>
                  <td>{t.language}</td>
                  <td>{t.state}</td>
                  <td>{t.periodicity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
