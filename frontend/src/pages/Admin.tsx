import { useEffect, useMemo, useState } from "react";
import { getToken } from "../auth";
import {
  listVideos,
  createVideo,
  updateVideo,
  deleteVideo,
  archiveVideo,
  restoreVideo,
  listBooks,
  createBook,
  updateBook,
  deleteBook,
  listMusic,
  createMusic,
  updateMusic,
  updateMusicMedia,
  deleteMusic,
  listPlaylists,
  createPlaylist,
  deletePlaylist,
  listGenres,
  createGenre,
  updateGenre,
  deleteGenre,
  listUsers,
  createUser,
  updateUser,
  deleteUser,
} from "../api";
import { Nav } from "../components/Nav";

type Section = "videos" | "books" | "music" | "playlists" | "genres" | "users";

function withArchived(items: any[]) {
  return items.map((item) => ({
    ...item,
    archived: item?.deleted_at ? "ARCHIVED" : "ACTIVE",
  }));
}

export default function Admin() {
  const token = getToken()!;
  const [active, setActive] = useState<Section>("videos");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [videos, setVideos] = useState<any[]>([]);
  const [books, setBooks] = useState<any[]>([]);
  const [music, setMusic] = useState<any[]>([]);
  const [playlists, setPlaylists] = useState<any[]>([]);
  const [genres, setGenres] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<any | null>(null);
  const [selectedBook, setSelectedBook] = useState<any | null>(null);
  const [selectedMusic, setSelectedMusic] = useState<any | null>(null);
  const [selectedGenre, setSelectedGenre] = useState<any | null>(null);
  const [selectedUser, setSelectedUser] = useState<any | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [v, b, m, p, g, u] = await Promise.all([
          listVideos(token),
          listBooks(token),
          listMusic(token),
          listPlaylists(token),
          listGenres(token),
          listUsers(token),
        ]);
        setVideos(v);
        setBooks(b);
        setMusic(m);
        setPlaylists(p);
        setGenres(g);
        setUsers(u);
      } catch (e: any) {
        setError(e.message || "Ошибка загрузки");
      }
    })();
  }, [token]);

  const sections = useMemo<Section[]>(() => ["videos", "books", "music", "playlists", "genres", "users"], []);

  async function run(action: () => Promise<void>, successText: string) {
    try {
      await action();
      setNotice({ type: "success", text: successText });
      return true;
    } catch (e: any) {
      setNotice({ type: "error", text: e.message || "Request failed" });
      return false;
    }
  }

  async function refresh() {
    const [v, b, m, p, g, u] = await Promise.all([
      listVideos(token),
      listBooks(token),
      listMusic(token),
      listPlaylists(token),
      listGenres(token),
      listUsers(token),
    ]);
    setVideos(v);
    setBooks(b);
    setMusic(m);
    setPlaylists(p);
    setGenres(g);
    setUsers(u);
  }

  return (
    <div className="page">
      <Nav role="admin" />
      <h2>Админка</h2>
      {error && <div style={{ color: "red" }}>{error}</div>}
      {notice && (
        <div style={{ color: notice.type === "error" ? "red" : "green", marginTop: 6 }}>{notice.text}</div>
      )}

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        {sections.map((s) => (
          <button
            key={s}
            onClick={() => setActive(s)}
            className="pill"
            data-active={active === s}
          >
            {s}
          </button>
        ))}
      </div>

      {active === "videos" && (
        <SectionCard title="Видео">
          <VideoForm
            onCreate={async (fd) => {
              await run(async () => {
                await createVideo(token, fd);
                await refresh();
              }, "Video created");
            }}
          />
          <ListTable
            items={videos}
            columns={["id", "title", "status"]}
            actions={(item) => (
              <>
                <button onClick={() => setSelectedVideo(item)}>Edit</button>
                <button
                  onClick={async () => {
                    await run(async () => {
                      await archiveVideo(token, item.id);
                      await refresh();
                    }, "Video archived");
                  }}
                >
                  Archive
                </button>
                <button
                  onClick={async () => {
                    await run(async () => {
                      await restoreVideo(token, item.id);
                      await refresh();
                    }, "Video restored");
                  }}
                >
                  Restore
                </button>
                <button
                  onClick={async () => {
                    if (!confirm("Delete video?")) return;
                    const ok = await run(async () => {
                      await deleteVideo(token, item.id);
                      await refresh();
                    }, "Video deleted");
                    if (ok && selectedVideo?.id === item.id) setSelectedVideo(null);
                  }}
                >
                  Delete
                </button>
              </>
            )}
          />
          <VideoUpdate
            initial={selectedVideo}
            onClear={() => setSelectedVideo(null)}
            onUpdate={async (id, fd) => {
              const ok = await run(async () => {
                await updateVideo(token, id, fd);
                await refresh();
              }, "Video updated");
              if (ok) setSelectedVideo(null);
            }}
          />
        </SectionCard>
      )}

      {active === "books" && (
        <SectionCard title="Книги">
          <BookForm
            onCreate={async (fd) => {
              await run(async () => {
                await createBook(token, fd);
                await refresh();
              }, "Book created");
            }}
          />
          <ListTable
            items={withArchived(books)}
            columns={["id", "title", "author", "archived"]}
            actions={(item) => (
              <>
                <button onClick={() => setSelectedBook(item)}>Edit</button>
                <button
                  onClick={async () => {
                    if (!confirm("Delete book?")) return;
                    const ok = await run(async () => {
                      await deleteBook(token, item.id);
                      await refresh();
                    }, "Book deleted");
                    if (ok && selectedBook?.id === item.id) setSelectedBook(null);
                  }}
                >
                  Delete
                </button>
              </>
            )}
          />
          <BookUpdate
            initial={selectedBook}
            onClear={() => setSelectedBook(null)}
            onUpdate={async (id, payload) => {
              const ok = await run(async () => {
                await updateBook(token, id, payload);
                await refresh();
              }, "Book updated");
              if (ok) setSelectedBook(null);
            }}
          />
        </SectionCard>
      )}

      {active === "music" && (
        <SectionCard title="Музыка">
          <MusicForm
            onCreate={async (fd) => {
              await run(async () => {
                await createMusic(token, fd);
                await refresh();
              }, "Music created");
            }}
            playlists={playlists}
          />
          <ListTable
            items={withArchived(music)}
            columns={["id", "title", "description", "archived"]}
            actions={(item) => (
              <>
                <button onClick={() => setSelectedMusic(item)}>Edit</button>
                <button
                  onClick={async () => {
                    if (!confirm("Delete music?")) return;
                    await run(async () => {
                      await deleteMusic(token, item.id);
                      await refresh();
                    }, "Music deleted");
                  }}
                >
                  Delete
                </button>
              </>
            )}
          />
          <MusicUpdate
            initial={selectedMusic}
            onClear={() => setSelectedMusic(null)}
            onUpdate={async (id, payload, files) => {
              const ok = await run(async () => {
                if (files?.preview || files?.music) {
                  const fd = new FormData();
                  if (payload.playlist_id) fd.append("playlist_id", payload.playlist_id);
                  if (payload.title) fd.append("title", payload.title);
                  if (payload.description) fd.append("description", payload.description);
                  if (payload.genre_id) fd.append("genre_id", payload.genre_id);
                  if (files.preview) fd.append("preview_img", files.preview);
                  if (files.music) fd.append("music", files.music);
                  await updateMusicMedia(token, id, fd);
                } else {
                  await updateMusic(token, id, payload);
                }
                await refresh();
              }, "Music updated");
              if (ok) setSelectedMusic(null);
            }}
            playlists={playlists}
          />
        </SectionCard>
      )}

      {active === "playlists" && (
        <SectionCard title="Плейлисты">
          <PlaylistForm
            onCreate={async (fd) => {
              await run(async () => {
                await createPlaylist(token, fd);
                await refresh();
              }, "Playlist created");
            }}
          />
          <ListTable
            items={withArchived(playlists)}
            columns={["id", "title", "description", "archived"]}
            actions={(item) => (
              <button
                onClick={async () => {
                  if (!confirm("Delete playlist?")) return;
                  await run(async () => {
                    await deletePlaylist(token, item.id);
                    await refresh();
                  }, "Playlist deleted");
                }}
              >
                Delete
              </button>
            )}
          />
        </SectionCard>
      )}

      {active === "genres" && (
        <SectionCard title="Жанры">
          <GenreForm
            onCreate={async (payload) => {
              await run(async () => {
                await createGenre(token, payload);
                await refresh();
              }, "Genre created");
            }}
          />
          <ListTable
            items={withArchived(genres)}
            columns={["id", "name", "type", "archived"]}
            actions={(item) => (
              <>
                <button onClick={() => setSelectedGenre(item)}>Edit</button>
                <button
                  onClick={async () => {
                    if (!confirm("Delete genre?")) return;
                    const ok = await run(async () => {
                      await deleteGenre(token, item.id);
                      await refresh();
                    }, "Genre deleted");
                    if (ok && selectedGenre?.id === item.id) setSelectedGenre(null);
                  }}
                >
                  Delete
                </button>
              </>
            )}
          />
          <GenreUpdate
            initial={selectedGenre}
            onClear={() => setSelectedGenre(null)}
            onUpdate={async (id, payload) => {
              const ok = await run(async () => {
                await updateGenre(token, id, payload);
                await refresh();
              }, "Genre updated");
              if (ok) setSelectedGenre(null);
            }}
          />
        </SectionCard>
      )}

      {active === "users" && (
        <SectionCard title="Пользователи">
          <UserForm
            onCreate={async (payload) => {
              await run(async () => {
                await createUser(token, payload);
                await refresh();
              }, "User created");
            }}
          />
          <ListTable
            items={users}
            columns={["id", "fullname", "phone", "role"]}
            actions={(item) => (
              <>
                <button onClick={() => setSelectedUser(item)}>Edit</button>
                <button
                  onClick={async () => {
                    if (!confirm("Delete user?")) return;
                    const ok = await run(async () => {
                      await deleteUser(token, item.id);
                      await refresh();
                    }, "User deleted");
                    if (ok && selectedUser?.id === item.id) setSelectedUser(null);
                  }}
                >
                  Delete
                </button>
              </>
            )}
          />
          <UserUpdate
            initial={selectedUser}
            onClear={() => setSelectedUser(null)}
            onUpdate={async (id, payload) => {
              const ok = await run(async () => {
                await updateUser(token, id, payload);
                await refresh();
              }, "User updated");
              if (ok) setSelectedUser(null);
            }}
          />
        </SectionCard>
      )}
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="panel" style={{ marginBottom: 20 }}>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function ListTable({
  items,
  columns,
  actions,
}: {
  items: any[];
  columns: string[];
  actions?: (item: any) => React.ReactNode;
}) {
  return (
    <table className="table">
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c}>
              {c}
            </th>
          ))}
          {actions && <th>actions</th>}
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id}>
            {columns.map((c) => (
              <td key={c}>
                {String(item[c] ?? "")}
              </td>
            ))}
            {actions && <td className="table-actions">{actions(item)}</td>}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function VideoForm({ onCreate }: { onCreate: (data: FormData) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [genreId, setGenreId] = useState("");
  const [preview, setPreview] = useState<File | null>(null);
  const [file, setFile] = useState<File | null>(null);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!preview || !file) return;
        const fd = new FormData();
        fd.append("title", title);
        fd.append("description", description);
        if (genreId) fd.append("genre_id", genreId);
        fd.append("preview", preview);
        fd.append("file", file);
        await onCreate(fd);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520 }}
    >
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input value={genreId} onChange={(e) => setGenreId(e.target.value)} placeholder="Genre UUID (optional)" />
      <input type="file" accept="image/*" onChange={(e) => setPreview(e.target.files?.[0] ?? null)} />
      <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <button type="submit">Create video</button>
    </form>
  );
}

function VideoUpdate({
  initial,
  onUpdate,
  onClear,
}: {
  initial: any | null;
  onUpdate: (id: string, data: FormData) => Promise<void>;
  onClear: () => void;
}) {
  const [id, setId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("");
  const [genreId, setGenreId] = useState("");

  useEffect(() => {
    if (!initial) {
      setId("");
      setTitle("");
      setDescription("");
      setStatus("");
      setGenreId("");
      return;
    }
    setId(initial.id ?? "");
    setTitle(initial.title ?? "");
    setDescription(initial.description ?? "");
    setStatus(initial.status ?? "");
    setGenreId(initial.genre_id ?? "");
  }, [initial]);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!id) return;
        const fd = new FormData();
        if (title) fd.append("title", title);
        if (description) fd.append("description", description);
        if (status) fd.append("status", status);
        if (genreId) fd.append("genre_id", genreId);
        await onUpdate(id, fd);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520, marginTop: 12 }}
    >
      <h4>Update video</h4>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="Video ID" />
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input value={status} onChange={(e) => setStatus(e.target.value)} placeholder="Status (ACTIVE/ARCHIVED)" />
      <input value={genreId} onChange={(e) => setGenreId(e.target.value)} placeholder="Genre UUID" />
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit">Update</button>
        <button type="button" onClick={onClear}>Clear</button>
      </div>
    </form>
  );
}

function BookForm({ onCreate }: { onCreate: (data: FormData) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState("");
  const [year, setYear] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [cover, setCover] = useState<File | null>(null);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!file) return;
        const fd = new FormData();
        fd.append("title", title);
        fd.append("author", author);
        fd.append("description", description);
        if (genre) fd.append("genre", genre);
        if (year) fd.append("published_year", year);
        fd.append("file", file);
        if (cover) fd.append("cover", cover);
        await onCreate(fd);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520 }}
    >
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Author" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input value={genre} onChange={(e) => setGenre(e.target.value)} placeholder="Genre (optional)" />
      <input value={year} onChange={(e) => setYear(e.target.value)} placeholder="Published year (optional)" />
      <input type="file" accept=".pdf,.epub" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <input type="file" accept="image/*" onChange={(e) => setCover(e.target.files?.[0] ?? null)} />
      <button type="submit">Create book</button>
    </form>
  );
}

function BookUpdate({
  initial,
  onUpdate,
  onClear,
}: {
  initial: any | null;
  onUpdate: (id: string, data: any) => Promise<void>;
  onClear: () => void;
}) {
  const [id, setId] = useState("");
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState("");
  const [year, setYear] = useState("");

  useEffect(() => {
    if (!initial) {
      setId("");
      setTitle("");
      setAuthor("");
      setDescription("");
      setGenre("");
      setYear("");
      return;
    }
    setId(initial.id ?? "");
    setTitle(initial.title ?? "");
    setAuthor(initial.author ?? "");
    setDescription(initial.description ?? "");
    setGenre(initial.genre ?? "");
    setYear(initial.published_year ? String(initial.published_year) : "");
  }, [initial]);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!id) return;
        await onUpdate(id, {
          ...(title ? { title } : {}),
          ...(author ? { author } : {}),
          ...(description ? { description } : {}),
          ...(genre ? { genre } : {}),
          ...(year ? { published_year: Number(year) } : {}),
        });
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520, marginTop: 12 }}
    >
      <h4>Update book</h4>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="Book ID" />
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Author" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input value={genre} onChange={(e) => setGenre(e.target.value)} placeholder="Genre" />
      <input value={year} onChange={(e) => setYear(e.target.value)} placeholder="Published year" />
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit">Update</button>
        <button type="button" onClick={onClear}>Clear</button>
      </div>
    </form>
  );
}

function MusicForm({ onCreate, playlists }: { onCreate: (data: FormData) => Promise<void>; playlists: any[] }) {
  const [playlistId, setPlaylistId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [genreId, setGenreId] = useState("");
  const [preview, setPreview] = useState<File | null>(null);
  const [music, setMusic] = useState<File | null>(null);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!preview || !music) return;
        const fd = new FormData();
        fd.append("playlist_id", playlistId);
        fd.append("title", title);
        fd.append("description", description);
        if (genreId) fd.append("genre_id", genreId);
        fd.append("preview_img", preview);
        fd.append("music", music);
        await onCreate(fd);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520 }}
    >
      <select value={playlistId} onChange={(e) => setPlaylistId(e.target.value)}>
        <option value="">Select playlist</option>
        {playlists.map((pl) => (
          <option key={pl.id} value={pl.id}>
            {pl.title}
          </option>
        ))}
      </select>
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input value={genreId} onChange={(e) => setGenreId(e.target.value)} placeholder="Genre UUID (optional)" />
      <input type="file" accept="image/*" onChange={(e) => setPreview(e.target.files?.[0] ?? null)} />
      <input type="file" accept="audio/*,video/webm" onChange={(e) => setMusic(e.target.files?.[0] ?? null)} />
      <button type="submit">Create music</button>
    </form>
  );
}

function MusicUpdate({
  initial,
  onUpdate,
  onClear,
  playlists,
}: {
  initial: any | null;
  onUpdate: (id: string, data: any, files?: { preview?: File | null; music?: File | null }) => Promise<void>;
  onClear: () => void;
  playlists: any[];
}) {
  const [id, setId] = useState("");
  const [playlistId, setPlaylistId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [genreId, setGenreId] = useState("");
  const [preview, setPreview] = useState<File | null>(null);
  const [music, setMusic] = useState<File | null>(null);

  useEffect(() => {
    if (!initial) {
      setId("");
      setPlaylistId("");
      setTitle("");
      setDescription("");
      setGenreId("");
      setPreview(null);
      setMusic(null);
      return;
    }
    setId(initial.id ?? "");
    setPlaylistId(initial.playlist_id ?? "");
    setTitle(initial.title ?? "");
    setDescription(initial.description ?? "");
    setGenreId(initial.genre_id ?? "");
    setPreview(null);
    setMusic(null);
  }, [initial]);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!id) return;
        const payload: any = {};
        if (playlistId) payload.playlist_id = playlistId;
        if (title) payload.title = title;
        if (description) payload.description = description;
        if (genreId) payload.genre_id = genreId;
        await onUpdate(id, payload, { preview, music });
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520, marginTop: 12 }}
    >
      <h4>Update music</h4>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="Music ID" />
      <select value={playlistId} onChange={(e) => setPlaylistId(e.target.value)}>
        <option value="">Select playlist</option>
        {playlists.map((pl) => (
          <option key={pl.id} value={pl.id}>
            {pl.title}
          </option>
        ))}
      </select>
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input value={genreId} onChange={(e) => setGenreId(e.target.value)} placeholder="Genre UUID" />
      <input type="file" accept="image/*" onChange={(e) => setPreview(e.target.files?.[0] ?? null)} />
      <input type="file" accept="audio/*,video/webm" onChange={(e) => setMusic(e.target.files?.[0] ?? null)} />
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit">Update</button>
        <button type="button" onClick={onClear}>Clear</button>
      </div>
    </form>
  );
}

function PlaylistForm({ onCreate }: { onCreate: (data: FormData) => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [preview, setPreview] = useState<File | null>(null);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!preview) return;
        const fd = new FormData();
        fd.append("title", title);
        fd.append("description", description);
        fd.append("preview_img", preview);
        await onCreate(fd);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 520 }}
    >
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <input type="file" accept="image/*" onChange={(e) => setPreview(e.target.files?.[0] ?? null)} />
      <button type="submit">Create playlist</button>
    </form>
  );
}

function GenreForm({ onCreate }: { onCreate: (data: { name: string; type: string }) => Promise<void> }) {
  const [name, setName] = useState("");
  const [type, setType] = useState("music");

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        await onCreate({ name, type });
      }}
      style={{ display: "grid", gap: 8, maxWidth: 320 }}
    >
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" />
      <select value={type} onChange={(e) => setType(e.target.value)}>
        <option value="music">music</option>
        <option value="movie">movie</option>
        <option value="book">book</option>
      </select>
      <button type="submit">Create genre</button>
    </form>
  );
}

function GenreUpdate({
  initial,
  onUpdate,
  onClear,
}: {
  initial: any | null;
  onUpdate: (id: string, data: any) => Promise<void>;
  onClear: () => void;
}) {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("music");

  useEffect(() => {
    if (!initial) {
      setId("");
      setName("");
      setDescription("");
      setType("music");
      return;
    }
    setId(initial.id ?? "");
    setName(initial.name ?? "");
    setDescription(initial.description ?? "");
    setType(initial.type ?? "music");
  }, [initial]);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!id) return;
        const payload: any = {};
        if (name) payload.name = name;
        if (description) payload.description = description;
        if (type) payload.type = type;
        await onUpdate(id, payload);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 320, marginTop: 12 }}
    >
      <h4>Update genre</h4>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="Genre ID" />
      <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" />
      <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
      <select value={type} onChange={(e) => setType(e.target.value)}>
        <option value="music">music</option>
        <option value="movie">movie</option>
        <option value="book">book</option>
      </select>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit">Update</button>
        <button type="button" onClick={onClear}>Clear</button>
      </div>
    </form>
  );
}

function UserForm({ onCreate }: { onCreate: (data: any) => Promise<void> }) {
  const [fullname, setFullname] = useState("");
  const [phone, setPhone] = useState("+7");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("user");

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        await onCreate({ fullname, phone, password, role });
      }}
      style={{ display: "grid", gap: 8, maxWidth: 320 }}
    >
      <input value={fullname} onChange={(e) => setFullname(e.target.value)} placeholder="Full name" />
      <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+70000000000" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" />
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="user">user</option>
        <option value="admin">admin</option>
      </select>
      <button type="submit">Create user</button>
    </form>
  );
}

function UserUpdate({
  initial,
  onUpdate,
  onClear,
}: {
  initial: any | null;
  onUpdate: (id: string, data: any) => Promise<void>;
  onClear: () => void;
}) {
  const [id, setId] = useState("");
  const [fullname, setFullname] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("user");

  useEffect(() => {
    if (!initial) {
      setId("");
      setFullname("");
      setPhone("");
      setRole("user");
      setPassword("");
      return;
    }
    setId(initial.id ?? "");
    setFullname(initial.fullname ?? "");
    setPhone(initial.phone ?? "");
    setRole(initial.role ?? "user");
    setPassword("");
  }, [initial]);

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (!id) return;
        const payload: any = {};
        if (fullname) payload.fullname = fullname;
        if (phone) payload.phone = phone;
        if (password) payload.password = password;
        if (role) payload.role = role;
        await onUpdate(id, payload);
      }}
      style={{ display: "grid", gap: 8, maxWidth: 320, marginTop: 12 }}
    >
      <h4>Update user</h4>
      <input value={id} onChange={(e) => setId(e.target.value)} placeholder="User ID" />
      <input value={fullname} onChange={(e) => setFullname(e.target.value)} placeholder="Full name" />
      <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+70000000000" />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password (optional)" />
      <select value={role} onChange={(e) => setRole(e.target.value)}>
        <option value="user">user</option>
        <option value="admin">admin</option>
      </select>
      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit">Update</button>
        <button type="button" onClick={onClear}>Clear</button>
      </div>
    </form>
  );
}
