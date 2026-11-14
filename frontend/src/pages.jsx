import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Webcam from "react-webcam";
import { api, mediaUrl, zipUrl } from "./api.js";
import { Scene, Brand } from "./scene.jsx";

/* ---------------- Auth shell: violet panel + form ---------------- */
function AuthShell({ headline, sub, children }) {
  return (
    <div className="auth">
      <aside className="panel">
        <Brand light />
        <div>
          <h1>{headline}</h1>
          <p>{sub}</p>
        </div>
        <Scene />
      </aside>
      <section className="formside">
        <div className="formbox">{children}</div>
      </section>
    </div>
  );
}

export function Login({ onAuth }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      onAuth(await api.login(email, password));
    } catch (e) {
      setErr(e.message);
    }
    setBusy(false);
  };

  return (
    <AuthShell
      headline="Find every photo you're in."
      sub="Log in and the event album sorts itself: just you, you with friends, and group shots."
    >
      <h2>Log in</h2>
      <form onSubmit={submit} className="stack">
        <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
        {err && <p className="error" role="alert">{err}</p>}
        <button className="primary" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
      </form>
      <p>New here? <Link to="/register">Create an account</Link></p>
    </AuthShell>
  );
}

/* ---------------- Register ---------------- */
function SelfiePicker({ shots, setShots }) {
  const cam = useRef(null);
  const [camOn, setCamOn] = useState(false);

  const snap = async () => {
    const src = cam.current?.getScreenshot();
    if (!src) return;
    const blob = await (await fetch(src)).blob();
    setShots((s) => [...s, { blob, url: src }].slice(0, 3));
  };
  const upload = (e) => {
    const add = [...e.target.files].map((f) => ({ blob: f, url: URL.createObjectURL(f) }));
    setShots((s) => [...s, ...add].slice(0, 3));
    e.target.value = "";
  };

  return (
    <div className="stack tight">
      <span className="label">
        Selfies <span className="hint">{shots.length} of 3. Add one straight-on and one at a slight angle.</span>
      </span>
      <div className="slots">
        {[0, 1, 2].map((i) =>
          shots[i] ? (
            <div key={i} className="slot filled">
              <img src={shots[i].url} alt={`Selfie ${i + 1}`} />
              <button type="button" className="x" aria-label={`Remove selfie ${i + 1}`} onClick={() => setShots(shots.filter((_, j) => j !== i))}>×</button>
            </div>
          ) : (
            <div key={i} className="slot" aria-hidden="true">+</div>
          )
        )}
      </div>
      {camOn && (
        <>
          <div className="camview">
            <Webcam ref={cam} audio={false} mirrored screenshotFormat="image/jpeg" videoConstraints={{ facingMode: "user" }} />
            <div className="guide" />
          </div>
          <button type="button" className="primary" onClick={snap} disabled={shots.length >= 3}>Take photo</button>
        </>
      )}
      <div className="row">
        <button type="button" onClick={() => setCamOn((v) => !v)}>{camOn ? "Close camera" : "Use camera"}</button>
        <label className="btn">Upload photos<input type="file" accept="image/*" multiple hidden onChange={upload} /></label>
      </div>
    </div>
  );
}

export function Register({ onAuth }) {
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const [shots, setShots] = useState([]);
  const [consent, setConsent] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!shots.length) return setErr("Add at least one selfie.");
    setBusy(true);
    setErr("");
    const fd = new FormData();
    Object.entries(f).forEach(([k, v]) => fd.append(k, v));
    fd.append("consent", consent);
    shots.forEach((s, i) => fd.append("selfies", s.blob, `selfie${i}.jpg`));
    try {
      onAuth(await api.register(fd));
    } catch (e) {
      setErr(e.message);
    }
    setBusy(false);
  };

  return (
    <AuthShell
      headline="Add a selfie. We'll find you."
      sub="Your face becomes a numeric signature that is only used to match you in event photos. You can delete it any time."
    >
      <h2>Create your account</h2>
      <form onSubmit={submit} className="stack">
        <label>Name<input value={f.name} onChange={set("name")} required /></label>
        <label>Email<input type="email" value={f.email} onChange={set("email")} required /></label>
        <label>Password<input type="password" minLength={6} value={f.password} onChange={set("password")} required /></label>
        <SelfiePicker shots={shots} setShots={setShots} />
        <label className="check">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          <span>I agree to my face being analysed to find me in event photos.</span>
        </label>
        {err && <p className="error" role="alert">{err}</p>}
        <button className="primary" disabled={busy || !consent}>{busy ? "Checking your selfies…" : "Create account"}</button>
      </form>
      <p>Already registered? <Link to="/login">Log in</Link></p>
    </AuthShell>
  );
}

/* ---------------- Events ---------------- */
export function Events() {
  const [events, setEvents] = useState(null);
  useEffect(() => { api.events().then(setEvents); }, []);
  if (!events) return <div className="scanning" role="status"><div className="scanbar" /><span>Loading events…</span></div>;

  return (
    <section>
      <div className="pagehead">
        <h1>Events</h1>
        <p className="lede">Pick an event to see the photos you're in.</p>
      </div>
      {!events.length && <p className="lede">No events yet. An admin needs to add one first.</p>}
      <ul className="reels">
        {events.map((e) => {
          const ready = e.status === "ready";
          const inner = (
            <>
              <span className="rname">{e.name}</span>
              <span className="rmeta">
                {ready ? <><b>{e.total}</b>photos</> : e.status === "indexing" ? `Processing ${e.processed} of ${e.total}` : "Not ready yet"}
              </span>
            </>
          );
          return (
            <li key={e.id}>
              {ready ? <Link to={`/events/${e.id}`} className="reel">{inner}</Link> : <div className="reel off">{inner}</div>}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/* ---------------- Gallery ---------------- */
const TABS = [
  ["only_you", "Only you"],
  ["with_one_person", "With one person"],
  ["small_group", "Small group"],
  ["group_photo", "Group photos"],
];

// little head-count icons: dots stand for faces in the frame
const GLYPH = {
  only_you: { r: 3, pts: [[14, 8]] },
  with_one_person: { r: 3, pts: [[9, 8], [19, 8]] },
  small_group: { r: 3, pts: [[7, 5], [14, 5], [21, 5], [10.5, 11.5], [17.5, 11.5]] },
  group_photo: {
    r: 2.3,
    pts: [[4, 3.5], [10, 3.5], [16, 3.5], [22, 3.5], [7, 8], [13, 8], [19, 8], [25, 8], [4, 12.5], [10, 12.5], [16, 12.5], [22, 12.5]],
  },
};

function Heads({ kind }) {
  const { r, pts } = GLYPH[kind];
  return (
    <svg viewBox="0 0 28 16" width="28" height="16" aria-hidden="true">
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={r} fill="currentColor" />)}
    </svg>
  );
}

function Lightbox({ items, index, setIndex, onClose }) {
  const p = items[index];
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") setIndex((i) => Math.min(i + 1, items.length - 1));
      if (e.key === "ArrowLeft") setIndex((i) => Math.max(i - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items.length, onClose, setIndex]);

  return (
    <div className="lightbox" role="dialog" aria-modal="true" aria-label="Photo viewer" onClick={onClose}>
      <img src={mediaUrl("full", p.id)} alt="" onClick={(e) => e.stopPropagation()} />
      <div className="lb-bar" onClick={(e) => e.stopPropagation()}>
        <button onClick={() => setIndex(index - 1)} disabled={index === 0}>Previous</button>
        <span className="lb-count">{index + 1} of {items.length}</span>
        <button onClick={() => setIndex(index + 1)} disabled={index === items.length - 1}>Next</button>
        <span className="lb-match">match {p.score.toFixed(2)}</span>
        <a className="btn" href={mediaUrl("full", p.id)} download>Download</a>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

export function Gallery() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [tab, setTab] = useState("only_you");
  const [openIdx, setOpenIdx] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.myPhotos(id).then((d) => {
      setData(d);
      const first = TABS.find(([k]) => d[k].length);
      if (first) setTab(first[0]);
    }).catch((e) => setErr(e.message));
  }, [id]);

  if (err) return <p className="error">{err}</p>;
  if (!data) {
    return (
      <div className="scanning" role="status">
        <div className="scanbar" />
        <span>Looking for you in the photos…</span>
      </div>
    );
  }

  const total = TABS.reduce((n, [k]) => n + data[k].length, 0);
  const list = data[tab];
  const pick = (k) => { setTab(k); setOpenIdx(null); };

  return (
    <section>
      <Link to="/" className="back">All events</Link>
      <div className="ghead">
        <div>
          <h1>{total ? `${total} photo${total === 1 ? "" : "s"} of you` : "No photos of you found"}</h1>
          {!total && <p className="lede">Try a clearer selfie, or ask the organiser to process the event again.</p>}
        </div>
        {total > 0 && <a className="btn" href={zipUrl(id)}>Download all as ZIP</a>}
      </div>

      <div className="tabs" role="tablist">
        {TABS.map(([k, label]) => (
          <button
            key={k}
            role="tab"
            aria-selected={tab === k}
            className={`chip${tab === k ? " on" : ""}${data[k].length ? "" : " empty"}`}
            onClick={() => pick(k)}
          >
            <Heads kind={k} />
            <span>{label}</span>
            <span className="n">{data[k].length}</span>
          </button>
        ))}
      </div>

      {list.length > 0 ? (
        <>
          <a className="link-dl" href={zipUrl(id, tab)}>Download this group as ZIP</a>
          <div className="wall">
            {list.map((p, i) => (
              <button key={p.id} className="tile" onClick={() => setOpenIdx(i)} aria-label="Open photo">
                <img loading="lazy" src={mediaUrl("thumb", p.id)} alt="" />
                <span className="score">{p.score.toFixed(2)} match</span>
              </button>
            ))}
          </div>
        </>
      ) : (
        total > 0 && <p className="lede">Nothing in this group.</p>
      )}

      {openIdx !== null && list[openIdx] && (
        <Lightbox items={list} index={openIdx} setIndex={setOpenIdx} onClose={() => setOpenIdx(null)} />
      )}
    </section>
  );
}

/* ---------------- Admin ---------------- */
export function Admin() {
  const [events, setEvents] = useState([]);
  const [f, setF] = useState({ name: "", source: "drive", folder: "" });
  const [err, setErr] = useState("");
  const load = () => api.events().then(setEvents);

  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (!events.some((e) => e.status === "indexing")) return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [events]);

  const create = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      await api.createEvent(f);
      setF({ name: "", source: f.source, folder: "" });
      load();
    } catch (e) {
      setErr(e.message);
    }
  };
  const start = async (id) => {
    try { await api.indexEvent(id); load(); } catch (e) { setErr(e.message); }
  };

  return (
    <section>
      <div className="pagehead">
        <h1>Manage events</h1>
        <p className="lede">Add a photo folder, then process it so people can find themselves.</p>
      </div>

      <form onSubmit={create} className="stack formcard">
        <label>Event name<input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required /></label>
        <label>Photo source
          <select value={f.source} onChange={(e) => setF({ ...f, source: e.target.value })}>
            <option value="drive">Google Drive folder</option>
            <option value="local">Folder on this server</option>
          </select>
        </label>
        <label>{f.source === "drive" ? "Drive folder ID (the part after /folders/ in the URL)" : "Folder path"}
          <input value={f.folder} onChange={(e) => setF({ ...f, folder: e.target.value })} required />
        </label>
        {err && <p className="error" role="alert">{err}</p>}
        <button className="primary">Add event</button>
      </form>

      <ul className="reels">
        {events.map((e) => (
          <li key={e.id}>
            <div className="reel admin">
              <span className="rname">{e.name}</span>
              <span className="rmeta">
                {e.status === "indexing" ? `Processing ${e.processed} of ${e.total}` : `${e.status}, ${e.total} photos`}
              </span>
              {e.status === "indexing" && <progress value={e.processed} max={e.total || 1} />}
              <span className="acts">
                {e.status === "ready" && <Link className="btn" to={`/events/${e.id}`}>View my photos</Link>}
                <button onClick={() => start(e.id)} disabled={e.status === "indexing"}>
                  {e.status === "ready" ? "Re-scan for new photos" : "Process photos"}
                </button>
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
