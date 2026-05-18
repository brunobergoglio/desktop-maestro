const API_BASE = '/api/desktopmaestro';

export interface DesktopStats {
  total_files: number;
  total_folders: number;
  total_size_human: string;
  by_extension: Record<string, number>;
  by_size_category: Record<string, number>;
  oldest_file?: { name: string; age_days: number };
  newest_file?: { name: string; age_days: number };
}

export interface CategoryInfo {
  name: string;
  icon: string;
  folder_name: string;
  extensions: string[];
  priority: number;
}

export interface OrganizeResult {
  success_count: number;
  skipped_count: number;
  error_count: number;
  categories_created: string[];
  dry_run: boolean;
  duration: string;
}

export interface SnapshotInfo {
  file: string;
  created_at: string;
  entries_count: number;
  description: string;
}

export interface ConfigData {
  language: string;
  desktop_path: string;
  dry_run: boolean;
  verbose: boolean;
  show_notifications: boolean;
  schedule_enabled: boolean;
  schedule_interval_hours: number;
  [key: string]: any;
}

export interface SystemInfo {
  [key: string]: string;
}

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `API error: ${res.status}`);
  }
  return res.json();
}

export interface ScanCategory {
  name: string;
  localized_name: string;
  icon: string;
  folder_name: string;
}

export interface ScanItem {
  name: string;
  is_dir: boolean;
  size: number;
  size_human: string;
  extension: string;
  modified: string;
  category: ScanCategory | null;
}

export interface ScanResult {
  path: string;
  name: string;
  parent: string | null;
  items: ScanItem[];
  total_files: number;
  total_folders: number;
  total_size: number;
  total_size_human: string;
  by_extension: Record<string, number>;
  by_category: Record<string, number>;
}

export const api = {
  health: () => apiFetch<{ status: string; version: string }>('/health'),
  stats: (lang?: string) => apiFetch<DesktopStats>(`/stats${lang ? `?lang=${lang}` : ''}`),
  categories: (lang?: string) => apiFetch<CategoryInfo[]>(`/categories${lang ? `?lang=${lang}` : ''}`),
  organize: (dryRun?: boolean, lang?: string, path?: string) =>
    apiFetch<OrganizeResult>('/organize', {
      method: 'POST',
      body: JSON.stringify({ dry_run: dryRun, language: lang, path }),
    }),
  snapshots: () => apiFetch<SnapshotInfo[]>('/undo/snapshots'),
  undo: (snapshot?: string) =>
    apiFetch<{ restored: number; errors: number }>('/undo', {
      method: 'POST',
      body: JSON.stringify({ snapshot }),
    }),
  config: () => apiFetch<ConfigData>('/config'),
  updateConfig: (data: Partial<ConfigData>) =>
    apiFetch<ConfigData>('/config', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  system: () => apiFetch<SystemInfo>('/system'),
  folders: (path?: string) =>
    apiFetch<{ path: string; folders: string[]; parent: string | null }>(
      `/folders${path ? `?path=${encodeURIComponent(path)}` : ''}`
    ),
  scan: (path?: string) =>
    apiFetch<ScanResult>(`/scan${path ? `?path=${encodeURIComponent(path)}` : ''}`),
};
