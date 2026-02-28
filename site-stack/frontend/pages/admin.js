import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";
const statuses = ["new", "in_progress", "confirmed", "cancelled"];

export default function AdminPage() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    const r = await fetch(`${API}/admin/booking-requests`);
    const data = await r.json();
    setRows(data || []);
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function setStatus(id, status) {
    await fetch(`${API}/admin/booking-requests/${id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status }),
    });
    await load();
  }

  return (
    <main style={{ fontFamily: "Inter,sans-serif", padding: 24 }}>
      <h1>Admin · Booking Requests</h1>
      {loading ? <p>Загрузка...</p> : null}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">ID</th><th align="left">Имя</th><th align="left">Телефон</th><th align="left">Даты</th><th align="left">Статус</th><th align="left">Действия</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{r.id}</td>
              <td>{r.guest_name}</td>
              <td>{r.guest_phone}</td>
              <td>{r.check_in} → {r.check_out}</td>
              <td><b>{r.status}</b></td>
              <td>
                {statuses.map((s) => (
                  <button key={s} onClick={() => setStatus(r.id, s)} style={{ marginRight: 6 }}>{s}</button>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
