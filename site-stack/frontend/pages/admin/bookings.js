import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";
const statuses = ["new", "in_progress", "confirmed", "cancelled"];

export default function AdminBookingsPage() {
  const [rows, setRows] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");

  async function load() {
    const qs = new URLSearchParams();
    if (statusFilter) qs.set("status", statusFilter);
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
      <div style={{ marginBottom: 12 }}>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Все статусы</option>
          {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
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
