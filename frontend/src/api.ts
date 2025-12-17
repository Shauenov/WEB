const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API = `${API_BASE.replace(/\/+$/, "")}/api/v1`;

const headers = (token?: string) => ({
  "Content-Type": "application/json",
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
});
const authHeaders = (token: string) => ({
  Authorization: `Bearer ${token}`,
});

export async function signIn(phone: string, password: string) {
  const res = await fetch(`${API}/auth/sign-in`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ phone, password }),
  });
  if (!res.ok) throw new Error("Auth failed");
  return res.json(); // {access_token, refresh_token}
}

export async function me(token: string) {
  const res = await fetch(`${API}/auth/me`, { headers: headers(token) });
  if (!res.ok) throw new Error("Unauthorized");
  return res.json();
}

export async function listVideos(token: string) {
  const res = await fetch(`${API}/videos?limit=50&offset=0`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load videos");
  return res.json();
}
export async function videoPlay(token: string, id: string) {
  const res = await fetch(`${API}/videos/${id}/play`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load video link");
  return res.json();
}
export async function createVideo(token: string, data: FormData) {
  const res = await fetch(`${API}/videos`, { method: "POST", headers: authHeaders(token), body: data });
  if (!res.ok) throw new Error("Failed to create video");
  return res.json();
}
export async function updateVideo(token: string, id: string, data: FormData) {
  const res = await fetch(`${API}/videos/${id}`, { method: "PATCH", headers: authHeaders(token), body: data });
  if (!res.ok) throw new Error("Failed to update video");
  return res.json();
}
export async function deleteVideo(token: string, id: string) {
  const res = await fetch(`${API}/videos/${id}`, { method: "DELETE", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to delete video");
  return res.json();
}
export async function archiveVideo(token: string, id: string) {
  const res = await fetch(`${API}/videos/${id}/archive`, { method: "POST", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to archive video");
  return res.json();
}
export async function restoreVideo(token: string, id: string) {
  const res = await fetch(`${API}/videos/${id}/restore`, { method: "POST", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to restore video");
  return res.json();
}
export async function listBooks(token: string) {
  const res = await fetch(`${API}/books/books`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load books");
  return res.json();
}
export async function bookLinks(token: string, id: string) {
  const res = await fetch(`${API}/books/books/${id}/links`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load book link");
  return res.json();
}
export async function createBook(token: string, data: FormData) {
  const res = await fetch(`${API}/books/books`, { method: "POST", headers: authHeaders(token), body: data });
  if (!res.ok) throw new Error("Failed to create book");
  return res.json();
}
export async function updateBook(token: string, id: string, data: any) {
  const res = await fetch(`${API}/books/books/${id}`, { method: "PATCH", headers: headers(token), body: JSON.stringify(data) });
  if (!res.ok) throw new Error("Failed to update book");
  return res.json();
}
export async function deleteBook(token: string, id: string) {
  const res = await fetch(`${API}/books/books/${id}`, { method: "DELETE", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to delete book");
  return res.json();
}
export async function listMusic(token: string) {
  const res = await fetch(`${API}/music/musics/`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load music");
  return res.json();
}
export async function musicLinks(token: string, id: string) {
  const res = await fetch(`${API}/music/musics/${id}/links`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load music link");
  return res.json();
}
export async function createMusic(token: string, data: FormData) {
  const res = await fetch(`${API}/music/musics/`, { method: "POST", headers: authHeaders(token), body: data });
  if (!res.ok) throw new Error("Failed to create music");
  return res.json();
}
export async function deleteMusic(token: string, id: string) {
  const res = await fetch(`${API}/music/musics/${id}`, { method: "DELETE", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to delete music");
  return res.json();
}
export async function listPlaylists(token: string) {
  const res = await fetch(`${API}/playlists/playlists/`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load playlists");
  return res.json();
}
export async function createPlaylist(token: string, data: FormData) {
  const res = await fetch(`${API}/playlists/playlists/`, { method: "POST", headers: authHeaders(token), body: data });
  if (!res.ok) throw new Error("Failed to create playlist");
  return res.json();
}
export async function deletePlaylist(token: string, id: string) {
  const res = await fetch(`${API}/playlists/playlists/${id}`, { method: "DELETE", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to delete playlist");
  return res.json();
}

// admin example
export async function createGenre(token: string, data: { name: string; type: string }) {
  const res = await fetch(`${API}/genres/genres/`, {
    method: "POST",
    headers: headers(token),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create genre");
  return res.json();
}
export async function listGenres(token: string) {
  const res = await fetch(`${API}/genres/genres/`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load genres");
  return res.json();
}
export async function updateGenre(token: string, id: string, data: any) {
  const res = await fetch(`${API}/genres/genres/${id}`, { method: "PUT", headers: headers(token), body: JSON.stringify(data) });
  if (!res.ok) throw new Error("Failed to update genre");
  return res.json();
}
export async function deleteGenre(token: string, id: string) {
  const res = await fetch(`${API}/genres/genres/${id}`, { method: "DELETE", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to delete genre");
  return res.json();
}
export async function listUsers(token: string) {
  const res = await fetch(`${API}/users/users/`, { headers: headers(token) });
  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}
export async function createUser(token: string, data: any) {
  const res = await fetch(`${API}/users/users/`, { method: "POST", headers: headers(token), body: JSON.stringify(data) });
  if (!res.ok) throw new Error("Failed to create user");
  return res.json();
}
export async function updateUser(token: string, id: string, data: any) {
  const res = await fetch(`${API}/users/users/${id}`, { method: "PATCH", headers: headers(token), body: JSON.stringify(data) });
  if (!res.ok) throw new Error("Failed to update user");
  return res.json();
}
export async function deleteUser(token: string, id: string) {
  const res = await fetch(`${API}/users/users/${id}`, { method: "DELETE", headers: headers(token) });
  if (!res.ok) throw new Error("Failed to delete user");
  return res.json();
}
