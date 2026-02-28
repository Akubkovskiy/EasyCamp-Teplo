import { useEffect, useState } from "react";
import AdminNav from "../../components/AdminNav";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

export default function AdminAuditPage() {
  const [rows, setRows] = useState([]);

  async function load() {
    const r = await fetch(`${API}/admin/audit?limit=200`);
    setRows(await r.json());
  }

  useEffect(() => { load(); }, []);

  return (
    <main style={{ fontFamily: "Inter,sans-serif", padding: 24 }}>
      <h1>Admin · Audit Log</h1>
      <AdminNav />
      <p><a href="/admin/audit">Обновить</a></p>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><th>ID</th><th>Entity</th><th>Action</th><th>Payload</th><th>Created</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{r.id}</td>
              <td>{r.entity}:{r.entity_id ?? '-'}</td>
              <td>{r.action}</td>
              <td><code style={{ fontSize: 12 }}>{r.payload}</code></td>
              <td>{r.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
