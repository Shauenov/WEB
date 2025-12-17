import { Link } from "react-router-dom";
import { clearToken } from "../auth";

export function Nav({ role }: { role: string }) {
  return (
    <nav style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center" }}>
      <Link to="/">Главная</Link>
      {role === "admin" && <Link to="/admin">Админка</Link>}
      <button
        onClick={() => {
          clearToken();
          location.href = "/login";
        }}
      >
        Выйти
      </button>
    </nav>
  );
}
