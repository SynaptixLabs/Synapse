/** Backend access — same-host by design (localhost AND direct-IP access both work). */
export const HOST = location.hostname || 'localhost';
export const API = `http://${HOST}:8000/api/v1`;

/** Honest fetch: non-2xx surfaces the server's `detail`, never a raw TypeError. */
export async function api(path, opts) {
  let res;
  try { res = await fetch(`${API}${path}`, opts); }
  catch { throw new Error(`backend unreachable at ${API} — is ./start.sh running on this host?`); }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `${res.status} ${res.statusText} on ${path} — wrong/old backend build?`);
  return body;
}

export async function health(el) {
  try {
    const d = await (await fetch(`http://${HOST}:8000/health`)).json();
    el.textContent = `${d.status} (build ${d.build_stamp})`; el.dataset.ok = 'true';
    return true;
  } catch { el.textContent = 'down — run ./start.sh'; el.dataset.ok = 'false'; return false; }
}
