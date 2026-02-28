import { useEffect, useMemo, useState } from "react";
import AdminNav from "../components/AdminNav";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";
const statuses = ["new", "in_progress", "confirmed", "cancelled"];

export default function AdminPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");

  const stats = useMemo(() => {
    const map = { new: 0, in_progress: 0, confirmed: 0, cancelled: 0 };
    rows.forEach((r) => {
      if (map[r.status] !== undefined) map[r.status] += 1;
    });
    return map;
  }, [rows]);

  async function load() {
    setLoading(true);
    const qs = new URLSearchParams();
    if (statusFilter) qs.set("status", statusFilter);
    if (search) qs.set("q", search);
    const r = await fetch(`${API}/admin/booking-requests${qs.toString() ? `?${qs}` : ""}`);
    const data = await r.json();
    setRows(data || []);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function setStatus(id, status) {
    await fetch(`${API}/admin/booking-requests/${id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status }),
    });
    await load();
  }

  return (
    <main style={{ fontFamily: "Inter,sans-serif", padding: 24, background: "#f7fafc", minHeight: "100vh" }}>
      <h1 style={{ marginTop: 0 }}>Admin V2 · Booking Requests</h1>
      <AdminNav />

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, marginBottom: 14 }}>
        <Stat label="Новые" value={stats.new} />
        <Stat label="В работе" value={stats.in_progress} />
        <Stat label="Подтверждено" value={stats.confirmed} />
        <Stat label="Отменено" value={stats.cancelled} />
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input
          placeholder="Поиск: имя или телефон"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={inputStyle}
        />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} style={inputStyle}>
          <option value="">Все статусы</option>
          {statuses.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button onClick={load} style={btnStyle}>Фильтровать</button>
      </div>

      {loading ? <p>Загрузка...</p> : null}
      <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ background: "#f8fafc" }}>
            <tr>
              <th align="left" style={th}>ID</th>
              <th align="left" style={th}>Имя</th>
              <th align="left" style={th}>Телефон</th>
              <th align="left" style={th}>Даты</th>
              <th align="left" style={th}>Статус</th>
              <th align="left" style={th}>Действия</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} style={{ borderTop: "1px solid #edf2f7" }}>
                <td style={td}>{r.id}</td>
                <td style={td}>{r.guest_name}</td>
                <td style={td}>{r.guest_phone}</td>
                <td style={td}>{r.check_in} → {r.check_out}</td>
                <td style={td}><b>{r.status}</b></td>
                <td style={td}>
                  {statuses.map((s) => (
                    <button key={s} onClick={() => setStatus(r.id, s)} style={{ ...smallBtn, opacity: r.status === s ? 0.6 : 1 }}>
                      {s}
                    </button>
                  ))}
                </td>
              </tr>
            ))}
            {!loading && rows.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: 16, textAlign: "center", color: "#64748b" }}>Нет заявок по фильтру</td></tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 10, padding: 12 }}>
      <div style={{ fontSize: 12, color: "#64748b" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

const inputStyle = {
  border: "1px solid #cbd5e1",
  borderRadius: 10,
  padding: "10px 12px",
  minWidth: 220,
};
const btnStyle = {
  border: "none",
  borderRadius: 10,
  background: "#0f172a",
  color: "#fff",
  padding: "10px 14px",
  cursor: "pointer",
};
const smallBtn = {
  marginRight: 6,
  marginBottom: 6,
  border: "1px solid #cbd5e1",
  borderRadius: 8,
  background: "#fff",
  padding: "4px 8px",
  cursor: "pointer",
  fontSize: 12,
};
const th = { padding: 10, fontSize: 13, color: "#334155" };
const td = { padding: 10, fontSize: 14 };
