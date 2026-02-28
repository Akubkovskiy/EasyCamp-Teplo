import { useEffect, useMemo, useState } from "react";
import AdminNav from "../../components/AdminNav";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";
const statuses = ["new", "in_progress", "confirmed", "cancelled"];

export default function AdminBookingsPage() {
  const [rows, setRows] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const stats = useMemo(() => {
    const map = { new: 0, in_progress: 0, confirmed: 0, cancelled: 0 };
    rows.forEach((r) => {
      if (map[r.status] !== undefined) map[r.status] += 1;
    });
    return map;
  }, [rows]);

  async function load() {
    const qs = new URLSearchParams();
    if (statusFilter) qs.set("status", statusFilter);
    if (dateFrom) qs.set("date_from", dateFrom);
    if (dateTo) qs.set("date_to", dateTo);
    const r = await fetch(`${API}/admin/bookings${qs.toString() ? `?${qs}` : ""}`);
    setRows(await r.json());
  }

  useEffect(() => { load(); }, []);

  async function setStatus(id, status) {
    await fetch(`${API}/admin/bookings/${id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status }),
    });
    await load();
  }

  return (
    <main style={{ fontFamily: "Inter,sans-serif", padding: 24 }}>
      <h1>Admin · Bookings</h1>
      <AdminNav />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, marginBottom: 12 }}>
        <Stat label="Новые" value={stats.new} />
        <Stat label="В работе" value={stats.in_progress} />
        <Stat label="Подтверждено" value={stats.confirmed} />
        <Stat label="Отменено" value={stats.cancelled} />
      </div>
      <div style={{ marginBottom: 12 }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Все статусы</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={{ marginLeft: 8 }} />
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={{ marginLeft: 8 }} />
        <button onClick={load} style={{ marginLeft: 8 }}>Фильтровать</button>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><th>ID</th><th>Гость</th><th>Телефон</th><th>Даты</th><th>Статус</th><th>Действия</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{r.id}</td>
              <td>{r.guest_name}</td>
              <td>{r.guest_phone}</td>
              <td>{r.check_in} → {r.check_out}</td>
              <td>{r.status}</td>
              <td>{statuses.map((s) => <button key={s} onClick={() => setStatus(r.id, s)} style={{ marginRight: 6 }}>{s}</button>)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 10, padding: 12 }}>
      <div style={{ fontSize: 12, color: "#64748b" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
    </div>
  );
}
