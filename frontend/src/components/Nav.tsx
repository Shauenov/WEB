import { Link } from "react-router-dom";
import { clearToken } from "../auth";

export function Nav({ role }: { role: string }) {
  return (
    <nav className="nav">
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
