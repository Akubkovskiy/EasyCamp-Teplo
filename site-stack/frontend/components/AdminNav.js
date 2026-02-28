export default function AdminNav() {
  const link = { marginRight: 10, color: '#0f172a', textDecoration: 'none', fontWeight: 600 };
  return (
    <p style={{ marginTop: -8, color: '#64748b' }}>
      Разделы:
      {' '}
      <a href="/admin" style={link}>Заявки</a>
      <a href="/admin/bookings" style={link}>Бронирования</a>
      <a href="/admin/houses" style={link}>Домики</a>
      <a href="/admin/audit" style={link}>Аудит</a>
    </p>
  );
}
