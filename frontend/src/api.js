const BASE = "/api";

export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => (t ? localStorage.setItem("token", t) : localStorage.removeItem("token"));

async function req(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`;
  const r = await fetch(BASE + path, { ...opts, headers });
  if (!r.ok) {
    let msg = r.statusText;
    try {
      const j = await r.json();
      msg = typeof j.detail === "string" ? j.detail : "Something went wrong";
    } catch {}
    throw new Error(msg);
  }
  return r.json();
}

const json = (body) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  login: (email, password) => req("/auth/login", json({ email, password })),
  register: (formData) => req("/auth/register", { method: "POST", body: formData }),
  me: () => req("/me"),
  deleteMe: () => req("/me", { method: "DELETE" }),
  events: () => req("/events"),
  createEvent: (body) => req("/events", json(body)),
  indexEvent: (id) => req(`/events/${id}/index`, { method: "POST" }),
  status: (id) => req(`/events/${id}/status`),
  myPhotos: (id) => req(`/events/${id}/my-photos`),
};

export const mediaUrl = (kind, id) => `${BASE}/media/${kind}/${id}?token=${getToken()}`;
export const zipUrl = (eid, cat) =>
  `${BASE}/events/${eid}/download?token=${getToken()}${cat ? `&category=${cat}` : ""}`;
