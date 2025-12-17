import React, { useEffect, useMemo, useState } from "react";
import Hls from "hls.js";
import { getToken, clearToken } from "../auth";
import { listVideos, listBooks, listMusic, listPlaylists, me, videoPlay, musicLinks, bookLinks } from "../api";
import { Nav } from "../components/Nav";

type Profile = { fullname: string; role: "user" | "admin" };

type Category = "videos" | "books" | "music" | "playlists";

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

  const items = useMemo(() => data[active] || [], [data, active]);

  if (error) {
    return (
      <div style={{ padding: 16 }}>
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
    <div style={{ padding: 16 }}>
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
            style={{
              padding: "8px 14px",
              borderRadius: 999,
              border: active === cat ? "1px solid #0f68f5" : "1px solid #e5e7eb",
              background: active === cat ? "#e7f0ff" : "#fff",
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 16 }}>
        {items.map((item) => (
          <Card key={item.id} type={active} item={item} token={token} />
        ))}
      </div>
    </div>
  );
}

function Card({ type, item, token }: { type: Category; item: any; token: string }) {
  const title = item.title || item.name || "Без названия";
  const description = item.description || item.author || "";

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
    return () => {
      ignore = true;
      if (playlistUrl) URL.revokeObjectURL(playlistUrl);
    };
  }, [type, open, playUrl, musicUrl, bookUrl, playlistUrl, previewUrl, token, item.id, preview]);

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
        <div style={{ width: "100%", borderRadius: 8, background: "#f0f2f5", aspectRatio: "16/9" }} />
      )}
      <div style={{ fontWeight: 600 }}>{title}</div>
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
