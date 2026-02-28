import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

export default function Home() {
  const [houses, setHouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState("");
  const [form, setForm] = useState({
    house_id: "",
    guest_name: "",
    guest_phone: "",
    guest_comment: "",
    check_in: "",
    check_out: "",
    guests_count: 2,
  });

  useEffect(() => {
    fetch(`${API}/houses`)
      .then((r) => r.json())
      .then((data) => {
        setHouses(data || []);
        if (data?.[0]?.id) setForm((f) => ({ ...f, house_id: String(data[0].id) }));
      })
      .finally(() => setLoading(false));
  }, []);

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    setResult("");
    try {
      const payload = {
        ...form,
        house_id: form.house_id ? Number(form.house_id) : null,
        guests_count: Number(form.guests_count),
      };
      const r = await fetch(`${API}/booking-requests`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || "Ошибка отправки");
      setResult(`✅ Заявка отправлена! Номер: #${data.id}`);
    } catch (err) {
      setResult(`❌ ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main style={{ fontFamily: "Inter, sans-serif", color: "#F5F7FA", background: "linear-gradient(180deg,#0b1220 0%,#0f172a 60%,#111827 100%)", minHeight: "100vh" }}>
      <section style={{ padding: "64px 24px", maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: 44, margin: 0, lineHeight: 1.1 }}>База отдыха «Тепло» · Архыз</h1>
          <p style={{ opacity: 0.9, fontSize: 18, maxWidth: 760 }}>
            Домики в лесу с видом на горы, тишина, мангальная зона и быстрый Wi‑Fi.
            Оставьте заявку — подберём лучший вариант по вашим датам.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24 }}>
          <div style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 16, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>🏔 Домики и цены</h2>
            {loading ? (
              <p>Загрузка...</p>
            ) : (
              <div style={{ display: "grid", gap: 12 }}>
                {houses.map((h) => (
                  <div key={h.id} style={{ padding: 14, borderRadius: 12, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                      <b>{h.name}</b>
                      <span>{h.base_price} ₽/сутки</span>
                    </div>
                    <div style={{ opacity: 0.85 }}>До {h.capacity} гостей</div>
                    <div style={{ opacity: 0.85 }}>{h.short_description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <form onSubmit={submit} style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.14)", borderRadius: 16, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>📝 Заявка на бронирование</h2>
            <label>Домик</label>
            <select value={form.house_id} onChange={(e) => setForm({ ...form, house_id: e.target.value })} style={inputStyle}>
              {houses.map((h) => <option key={h.id} value={h.id}>{h.name} · {h.base_price} ₽</option>)}
            </select>

            <label>Имя</label>
            <input required value={form.guest_name} onChange={(e) => setForm({ ...form, guest_name: e.target.value })} style={inputStyle} />
            <label>Телефон</label>
            <input required value={form.guest_phone} onChange={(e) => setForm({ ...form, guest_phone: e.target.value })} placeholder="+7..." style={inputStyle} />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label>Заезд</label>
                <input type="date" required value={form.check_in} onChange={(e) => setForm({ ...form, check_in: e.target.value })} style={inputStyle} />
              </div>
              <div>
                <label>Выезд</label>
                <input type="date" required value={form.check_out} onChange={(e) => setForm({ ...form, check_out: e.target.value })} style={inputStyle} />
              </div>
            </div>

            <label>Гостей</label>
            <input type="number" min={1} max={20} value={form.guests_count} onChange={(e) => setForm({ ...form, guests_count: e.target.value })} style={inputStyle} />

            <label>Комментарий</label>
            <textarea value={form.guest_comment} onChange={(e) => setForm({ ...form, guest_comment: e.target.value })} rows={3} style={inputStyle} />

            <button disabled={submitting} style={btnStyle}>{submitting ? "Отправка..." : "Отправить заявку"}</button>
            {result ? <p style={{ marginTop: 10 }}>{result}</p> : null}
          </form>
        </div>
      </section>
    </main>
  );
}

const inputStyle = {
  width: "100%",
  marginTop: 4,
  marginBottom: 10,
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.2)",
  background: "rgba(255,255,255,0.08)",
  color: "#fff",
};

const btnStyle = {
  marginTop: 8,
  width: "100%",
  padding: "12px 14px",
  borderRadius: 12,
  border: "none",
  background: "linear-gradient(90deg,#22c55e,#16a34a)",
  color: "white",
  fontWeight: 700,
  cursor: "pointer",
};
