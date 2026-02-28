import { useEffect, useState } from "react";
import AdminNav from "../../components/AdminNav";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

export default function AdminHousesPage() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ name: "", slug: "", capacity: 4, base_price: 0, short_description: "" });

  async function load() {
    const r = await fetch(`${API}/admin/houses`);
    setRows(await r.json());
  }

  useEffect(() => { load(); }, []);

  async function createHouse(e) {
    e.preventDefault();
    await fetch(`${API}/admin/houses`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...form, capacity: Number(form.capacity), base_price: Number(form.base_price) }),
    });
    setForm({ name: "", slug: "", capacity: 4, base_price: 0, short_description: "" });
    await load();
  }

  return (
    <main style={{ fontFamily: "Inter,sans-serif", padding: 24 }}>
      <h1>Admin · Houses</h1>
      <AdminNav />

      <form onSubmit={createHouse} style={{ display: "grid", gap: 8, maxWidth: 520, marginBottom: 20 }}>
        <input required placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input required placeholder="Slug" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
        <input type="number" min={1} placeholder="Вместимость" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} />
        <input type="number" min={0} placeholder="Цена" value={form.base_price} onChange={(e) => setForm({ ...form, base_price: e.target.value })} />
        <textarea placeholder="Короткое описание" value={form.short_description} onChange={(e) => setForm({ ...form, short_description: e.target.value })} />
        <button type="submit">Добавить домик</button>
      </form>

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr><th align="left">ID</th><th align="left">Название</th><th align="left">Slug</th><th align="left">Вмест.</th><th align="left">Цена</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} style={{ borderTop: "1px solid #ddd" }}>
              <td>{r.id}</td><td>{r.name}</td><td>{r.slug}</td><td>{r.capacity}</td><td>{r.base_price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
