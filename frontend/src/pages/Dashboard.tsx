import React, { useEffect, useMemo, useState } from "react";
import Hls from "hls.js";
import { getToken, clearToken } from "../auth";
import { listVideos, listBooks, listMusic, listPlaylists, me, videoPlay, musicLinks, bookLinks } from "../api";
import { Nav } from "../components/Nav";

type Profile = { fullname: string; role: "user" | "admin" };

type Category = "videos" | "books" | "music" | "playlists";

function isArchived(item: any) {
  if (item?.status && String(item.status).toUpperCase() === "ARCHIVED") return true;
  return Boolean(item?.deleted_at);
}

export default function Dashboard() {
  const token = getToken()!;
  const [profile, setProfile] = useState<Profile | null>(null);
  const [data, setData] = useState<Record<Category, any[]>>({
    videos: [],
    books: [],
    music: [],
    playlists: [],
  });
  const [active, setActive] = useState<Category>("videos");
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const u = await me(token);
        setProfile({ fullname: u.fullname ?? u.phone, role: u.role });

        const results = await Promise.allSettled([
          listVideos(token),
          listBooks(token),
          listMusic(token),
          listPlaylists(token),
        ]);

        const [videosRes, booksRes, musicRes, playlistsRes] = results;
        setData({
          videos: videosRes.status === "fulfilled" ? videosRes.value : [],
          books: booksRes.status === "fulfilled" ? booksRes.value : [],
          music: musicRes.status === "fulfilled" ? musicRes.value : [],
          playlists: playlistsRes.status === "fulfilled" ? playlistsRes.value : [],
        });

        if (results.some((r) => r.status === "rejected")) {
          const msgs = results
            .map((r, i) => (r.status === "rejected" ? ["videos", "books", "music", "playlists"][i] : null))
            .filter(Boolean)
            .join(", ");
          setError(`Не удалось загрузить: ${msgs}`);
        } else {
          setError("");
        }
      } catch (e: any) {
        setError("Ошибка загрузки: " + e.message);
      }
    })();
  }, [token]);

  const items = useMemo(() => {
    const list = data[active] || [];
    if (profile?.role === "user") {
      return list.filter((item) => !isArchived(item));
    }
    return list;
  }, [data, active, profile?.role]);

  if (error) {
    return (
      <div className="page">
        {error}{" "}
        <button
          onClick={() => {
            clearToken();
            location.href = "/login";
          }}
        >
          Войти заново
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      <Nav role={profile?.role ?? "user"} />
      <header style={{ marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>Hello, {profile?.role ?? "user"}</h2>
        <div style={{ color: "#555" }}>{profile?.fullname}</div>
      </header>

      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        {(["videos", "books", "music", "playlists"] as Category[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setActive(cat)}
            className="pill"
            data-active={active === cat}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
        {items.map((item) => (
          <Card key={item.id} type={active} item={item} token={token} role={profile?.role ?? "user"} />
        ))}
      </div>
    </div>
  );
}

function Card({
  type,
  item,
  token,
  role,
}: {
  type: Category;
  item: any;
  token: string;
  role: "user" | "admin";
}) {
  const title = item.title || item.name || "Без названия";
  const description = item.description || item.author || "";
  const archived = isArchived(item);

  const preview =
    (type === "videos" && item.preview_img) ||
    (type === "books" && item.cover_url) ||
    (type === "music" && item.preview_img) ||
    (type === "playlists" && item.preview_img) ||
    null;

  const [playUrl, setPlayUrl] = useState<string | null>(null);
  const [musicUrl, setMusicUrl] = useState<string | null>(null);
  const [bookUrl, setBookUrl] = useState<string | null>(null);
  const [playlistUrl, setPlaylistUrl] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [playlistItems, setPlaylistItems] = useState<any[] | null>(null);
  const [playlistError, setPlaylistError] = useState("");

  useEffect(() => {
    let ignore = false;
    if (!previewUrl) {
      if (preview && preview.startsWith("http")) {
        setPreviewUrl(preview);
      } else if (type === "videos") {
        videoPlay(token, item.id)
          .then((res) => {
            if (!ignore && res.preview_url) setPreviewUrl(res.preview_url);
          })
          .catch(() => {});
      }
      if (type === "music") {
        musicLinks(token, item.id)
          .then((res) => {
            if (!ignore && res.preview_img) setPreviewUrl(res.preview_img);
          })
          .catch(() => {});
      }
      if (type === "books") {
        bookLinks(token, item.id)
          .then((res) => {
            if (!ignore && res.cover_url) setPreviewUrl(res.cover_url);
          })
          .catch(() => {});
      }
      if (type === "playlists" && preview) {
        setPreviewUrl(preview);
      }
    }
    if (type === "videos" && open && !playUrl) {
      videoPlay(token, item.id)
        .then((res) => {
          if (ignore) return;
          if (res.playlist) {
            const blob = new Blob([res.playlist], { type: "application/vnd.apple.mpegurl" });
            const url = URL.createObjectURL(blob);
            setPlaylistUrl(url);
            setPlayUrl(url);
          } else {
            setPlayUrl(res.video_url);
          }
        })
        .catch(() => {});
    }
    if (type === "music" && open && !musicUrl) {
      musicLinks(token, item.id)
        .then((res) => {
          if (ignore) return;
          if (res.playlist) {
            const blob = new Blob([res.playlist], { type: "application/vnd.apple.mpegurl" });
            const url = URL.createObjectURL(blob);
            setPlaylistUrl(url);
            setMusicUrl(url);
          } else {
            setMusicUrl(res.music_url);
          }
        })
        .catch(() => {});
    }
    if (type === "books" && open && !bookUrl) {
      bookLinks(token, item.id)
        .then((res) => {
          if (!ignore) setBookUrl(res.file_url);
        })
        .catch(() => {});
    }
    if (type === "playlists" && open && playlistItems === null) {
      listMusic(token, item.id)
        .then((res) => {
          if (ignore) return;
          const filtered = role === "user" ? res.filter((m: any) => !isArchived(m)) : res;
          setPlaylistItems(filtered);
          setPlaylistError("");
        })
        .catch((e: any) => {
          if (ignore) return;
          setPlaylistItems([]);
          setPlaylistError(e.message || "Failed to load playlist");
        });
    }
    return () => {
      ignore = true;
      if (playlistUrl) URL.revokeObjectURL(playlistUrl);
    };
  }, [type, open, playUrl, musicUrl, bookUrl, playlistUrl, previewUrl, token, item.id, preview, playlistItems, role]);

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {type === "videos" && open && playUrl ? (
        <VideoPlayer url={playUrl} />
      ) : type === "music" && open && musicUrl ? (
        <AudioPlayer url={musicUrl} />
      ) : type === "books" && open && bookUrl ? (
        <a href={bookUrl} target="_blank" rel="noreferrer">
          Читать
        </a>
      ) : previewUrl ? (
        <img src={previewUrl} alt={title} style={{ width: "100%", borderRadius: 8, objectFit: "cover", aspectRatio: "16/9" }} />
      ) : (
        <div style={{ width: "100%", borderRadius: 8, background: "var(--surface-muted)", aspectRatio: "16/9" }} />
      )}
      <div style={{ fontWeight: 600 }}>
        {title} {role === "admin" && archived && <span style={{ color: "#dc2626" }}>(ARCHIVED)</span>}
      </div>
      <div style={{ color: "#555", fontSize: 14, minHeight: 40 }}>{description}</div>
      {type === "videos" && (
        <button onClick={() => setOpen((v) => !v)}>
          {open ? "Скрыть" : "Смотреть"}
        </button>
      )}
      {type === "music" && (
        <button onClick={() => setOpen((v) => !v)}>
          {open ? "Скрыть" : "Слушать"}
        </button>
      )}
      {type === "books" && (
        <button onClick={() => setOpen((v) => !v)}>
          {open ? "Скрыть" : "Читать"}
        </button>
      )}
      {type === "playlists" && (
        <button onClick={() => setOpen((v) => !v)}>
          {open ? "Скрыть" : "Открыть плейлист"}
        </button>
      )}
      {type === "playlists" && open && (
        <div style={{ display: "grid", gap: 12, marginTop: 8 }}>
          {playlistError && <div style={{ color: "#b91c1c" }}>{playlistError}</div>}
          {!playlistError && playlistItems?.length === 0 && <div style={{ color: "#666" }}>Плейлист пуст</div>}
          {playlistItems?.map((track) => (
            <PlaylistTrack key={track.id} item={track} token={token} role={role} />
          ))}
        </div>
      )}
    </div>
  );
}

function PlaylistTrack({ item, token, role }: { item: any; token: string; role: "user" | "admin" }) {
  const title = item.title || "Без названия";
  const description = item.description || "";
  const archived = isArchived(item);
  const [open, setOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [musicUrl, setMusicUrl] = useState<string | null>(null);
  const [playlistUrl, setPlaylistUrl] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    if (!previewUrl) {
      if (item.preview_img && item.preview_img.startsWith("http")) {
        setPreviewUrl(item.preview_img);
      } else {
        musicLinks(token, item.id)
          .then((res) => {
            if (!ignore && res.preview_img) setPreviewUrl(res.preview_img);
          })
          .catch(() => {});
      }
    }
    if (open && !musicUrl) {
      musicLinks(token, item.id)
        .then((res) => {
          if (ignore) return;
          if (res.playlist) {
            const blob = new Blob([res.playlist], { type: "application/vnd.apple.mpegurl" });
            const url = URL.createObjectURL(blob);
            setPlaylistUrl(url);
            setMusicUrl(url);
          } else {
            setMusicUrl(res.music_url);
          }
        })
        .catch(() => {});
    }
    return () => {
      ignore = true;
      if (playlistUrl) URL.revokeObjectURL(playlistUrl);
    };
  }, [open, musicUrl, playlistUrl, previewUrl, token, item.id, item.preview_img]);

  return (
    <div style={{ border: "1px solid #eef2f7", borderRadius: 8, padding: 10, display: "grid", gap: 8 }}>
      {open && musicUrl ? (
        <AudioPlayer url={musicUrl} />
      ) : previewUrl ? (
        <img src={previewUrl} alt={title} style={{ width: "100%", borderRadius: 6, objectFit: "cover", aspectRatio: "16/9" }} />
      ) : (
        <div style={{ width: "100%", borderRadius: 6, background: "var(--surface-muted)", aspectRatio: "16/9" }} />
      )}
      <div style={{ fontWeight: 600 }}>
        {title} {role === "admin" && archived && <span style={{ color: "#dc2626" }}>(ARCHIVED)</span>}
      </div>
      <div style={{ color: "#555", fontSize: 14 }}>{description}</div>
      <button onClick={() => setOpen((v) => !v)}>{open ? "Скрыть" : "Слушать"}</button>
    </div>
  );
}

function VideoPlayer({ url }: { url: string }) {
  const ref = React.useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(ref.current);
      return () => hls.destroy();
    }
    ref.current.src = url;
  }, [url]);

  return (
    <video ref={ref} controls style={{ width: "100%", borderRadius: 8, aspectRatio: "16/9", background: "#000" }} />
  );
}

function AudioPlayer({ url }: { url: string }) {
  const ref = React.useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(url);
      hls.attachMedia(ref.current);
      return () => hls.destroy();
    }
    ref.current.src = url;
  }, [url]);

  return <audio ref={ref} controls style={{ width: "100%" }} />;
}
