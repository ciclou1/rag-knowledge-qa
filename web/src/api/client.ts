/**
 * API 请求封装。
 */
import axios, { AxiosRequestConfig } from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Admin Key（从 sessionStorage 读取）
function getAdminKey(): string | null {
  return sessionStorage.getItem('admin_key');
}

export function setAdminKey(key: string) {
  sessionStorage.setItem('admin_key', key);
}

export function clearAdminKey() {
  sessionStorage.removeItem('admin_key');
}

export function isAdminAuthenticated(): boolean {
  return !!getAdminKey();
}

// ── 管理后台请求 ──

export async function adminGet<T>(path: string, params?: any): Promise<T> {
  const key = getAdminKey();
  if (!key) throw new Error('Not authenticated');
  const res = await client.get(`/admin${path}`, {
    headers: { Authorization: `Bearer ${key}` },
    params,
  });
  return res.data;
}

export async function adminPost<T>(path: string, body?: any): Promise<T> {
  const key = getAdminKey();
  if (!key) throw new Error('Not authenticated');
  const res = await client.post(`/admin${path}`, body, {
    headers: { Authorization: `Bearer ${key}` },
  });
  return res.data;
}

export async function adminPut<T>(path: string, body?: any): Promise<T> {
  const key = getAdminKey();
  if (!key) throw new Error('Not authenticated');
  const res = await client.put(`/admin${path}`, body, {
    headers: { Authorization: `Bearer ${key}` },
  });
  return res.data;
}

export async function adminDelete(path: string): Promise<void> {
  const key = getAdminKey();
  if (!key) throw new Error('Not authenticated');
  await client.delete(`/admin${path}`, {
    headers: { Authorization: `Bearer ${key}` },
  });
}

export async function adminUpload(
  path: string,
  file: File,
  folder?: string,
  tags?: string,
): Promise<any> {
  const key = getAdminKey();
  if (!key) throw new Error('Not authenticated');
  const form = new FormData();
  form.append('file', file);
  if (folder) form.append('folder', folder);
  if (tags) form.append('tags', tags);
  const res = await client.post(`/admin${path}`, form, {
    headers: {
      Authorization: `Bearer ${key}`,
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

// ── 问答请求（公开）──

export async function qaGet<T>(path: string, params?: any): Promise<T> {
  const res = await client.get(`/qa${path}`, { params });
  return res.data;
}

export async function qaPost<T>(path: string, body?: any): Promise<T> {
  const res = await client.post(`/qa${path}`, body);
  return res.data;
}

// ── 健康检查 ──

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await client.get('/health');
    return res.data.status === 'ok';
  } catch {
    return false;
  }
}
