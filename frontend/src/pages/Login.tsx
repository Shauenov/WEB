import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signIn, me } from "../api";
import { saveToken } from "../auth";

export default function Login() {
  const [phone, setPhone] = useState("+7");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const nav = useNavigate();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const { access_token } = await signIn(phone, password);
      saveToken(access_token);
      await me(access_token);
      nav("/");
    } catch (err: any) {
      setError(err.message || "Ошибка входа");
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: "80px auto", background: "#fff", padding: 24, borderRadius: 8 }}>
      <h2>Вход</h2>
      <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+70000000000" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Пароль" />
        <button type="submit">Войти</button>
        {error && <div style={{ color: "red" }}>{error}</div>}
      </form>
    </div>
  );
}
