export type User = { id: string; fullname: string; phone: string; role: "user" | "admin" };

const TOKEN_KEY = "access_token";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}
