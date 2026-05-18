'use client';

import { useEffect, useState, useCallback } from 'react';
import { api, DesktopStats, CategoryInfo, SnapshotInfo, ConfigData, ScanResult } from '@/lib/api';

// ─── Types ───
type Tab = 'dashboard' | 'categories' | 'config' | 'undo';
type Lang = 'en' | 'es';

// ─── Icons ───
const ICONS: Record<string, string> = {
  dashboard: '📊',
  organize: '🧹',
  categories: '📂',
  config: '⚙️',
  undo: '↩️',
  stats: '📈',
  folder: '📁',
  file: '📄',
  check: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
  clean: '✨',
  settings: '🔧',
  language: '🌐',
  schedule: '⏰',
  trash: '🗑️',
};

// ─── Component ───
export default function Home() {
  // ─── State ───
  const [tab, setTab] = useState<Tab>('dashboard');
  const [lang, setLang] = useState<Lang>('en');
  const [stats, setStats] = useState<DesktopStats | null>(null);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [snapshots, setSnapshots] = useState<SnapshotInfo[]>([]);
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [loading, setLoading] = useState(false);
  const [orgResult, setOrgResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [orgPath, setOrgPath] = useState('~/Desktop');
  const [scanData, setScanData] = useState<ScanResult | null>(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  const [configSaving, setConfigSaving] = useState(false);

  // ─── Fetch helpers ───
  const checkHealth = useCallback(async () => {
    try {
      const h = await api.health();
      setConnected(true);
      setStatusMsg(`v${h.version} · ${h.status}`);
    } catch {
      setConnected(false);
      setStatusMsg('Disconnected');
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const s = await api.stats(lang);
      setStats(s);
    } catch { /* ignore */ }
  }, [lang]);

  const fetchCategories = useCallback(async () => {
    try {
      const c = await api.categories(lang);
      setCategories(c);
    } catch { /* ignore */ }
  }, [lang]);

  const fetchSnapshots = useCallback(async () => {
    try {
      const s = await api.snapshots();
      setSnapshots(s);
    } catch { /* ignore */ }
  }, []);

  const fetchConfig = useCallback(async () => {
    try {
      const c = await api.config();
      setConfig(c);
    } catch { /* ignore */ }
  }, []);

  const fetchScan = useCallback(async (path?: string) => {
    setScanLoading(true);
    try {
      const target = path || orgPath;
      const result = await api.scan(target);
      setScanData(result);
      setOrgPath(result.path);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanLoading(false);
    }
  }, [orgPath]);

  const navigateToFolder = useCallback(async (folderName: string) => {
    const base = scanData?.path || orgPath;
    const newPath = base.endsWith('/') ? `${base}${folderName}` : `${base}/${folderName}`;
    setOrgPath(newPath);
    await fetchScan(newPath);
  }, [scanData, orgPath, fetchScan]);

  const navigateUp = useCallback(async () => {
    if (scanData?.parent) {
      setOrgPath(scanData.parent);
      await fetchScan(scanData.parent);
    }
  }, [scanData, fetchScan]);

  const navigateToPath = useCallback(async (path: string) => {
    setOrgPath(path);
    await fetchScan(path);
  }, [fetchScan]);

  // ─── Init ───
  useEffect(() => { checkHealth(); }, [checkHealth]);
  useEffect(() => {
    if (connected) {
      fetchStats();
      fetchCategories();
      fetchScan('~/Desktop');
    }
  }, [connected, fetchStats, fetchCategories, fetchScan]);

  // ─── Organize ───
  const handleOrganize = async (dryRun: boolean) => {
    setLoading(true);
    setError(null);
    setOrgResult(null);
    try {
      const res = await api.organize(dryRun, lang, orgPath || undefined);
      const mode = dryRun ? '🔍 Dry Run' : '✅ Organized';
      setOrgResult(`${mode}: ${res.success_count} files moved, ${res.skipped_count} skipped, ${res.error_count} errors in ${res.duration}`);
      if (!dryRun) { fetchSnapshots(); fetchStats(); }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ─── Undo ───
  const handleUndo = async (snapshot?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.undo(snapshot);
      setOrgResult(`↩️ Restored: ${res.restored} files (${res.errors} errors)`);
      fetchSnapshots();
      fetchStats();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ─── Config ───
  const handleSaveConfig = async () => {
    if (!config) return;
    setConfigSaving(true);
    try {
      await api.updateConfig(config);
      setOrgResult('✅ Configuration saved');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setConfigSaving(false);
    }
  };

  // ─── Language ───
  const toggleLang = () => {
    const next = lang === 'en' ? 'es' : 'en';
    setLang(next);
    setOrgResult(next === 'es' ? '🌐 Cambiado a Español' : '🌐 Switched to English');
  };

  // ─── Tabs ───
  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'dashboard', label: lang === 'en' ? 'Dashboard' : 'Panel', icon: ICONS.dashboard },
    { id: 'categories', label: lang === 'en' ? 'Categories' : 'Categorías', icon: ICONS.categories },
    { id: 'config', label: lang === 'en' ? 'Settings' : 'Configuración', icon: ICONS.config },
    { id: 'undo', label: lang === 'en' ? 'Undo' : 'Deshacer', icon: ICONS.undo },
  ];

  // ─── Render ───
  return (
    <div className="min-h-screen bg-slate-900">
      {/* ─── Header ─── */}
      <header className="glass border-b border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🧹</span>
            <span className="font-bold text-lg">DesktopMaestro</span>
            <span className="text-xs text-slate-500 hidden sm:inline">
              {statusMsg}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`} />
            <button onClick={toggleLang} className="btn-secondary text-xs py-1.5 px-3">
              {ICONS.language} {lang === 'en' ? 'ES' : 'EN'}
            </button>
          </div>
        </div>
      </header>

      {/* ─── Tabs ─── */}
      <nav className="max-w-6xl mx-auto px-4 py-4 flex gap-2 overflow-x-auto">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); if (t.id === 'undo') fetchSnapshots(); if (t.id === 'config') fetchConfig(); }}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all whitespace-nowrap
              ${tab === t.id
                ? 'bg-maestro-600 text-white shadow-lg shadow-maestro-600/20'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
              }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </nav>

      {/* ─── Content ─── */}
      <main className="max-w-6xl mx-auto px-4 pb-12">
        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-900/30 border border-red-800 rounded-xl text-red-300 text-sm flex items-center gap-2">
            {ICONS.error} {error}
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-200">&times;</button>
          </div>
        )}
        {orgResult && (
          <div className="mb-4 p-4 bg-slate-800/50 border border-slate-700 rounded-xl text-slate-300 text-sm flex items-center gap-2">
            {ICONS.info} {orgResult}
            <button onClick={() => setOrgResult(null)} className="ml-auto text-slate-500 hover:text-slate-300">&times;</button>
          </div>
        )}

        {/* Tab: Dashboard */}
        {tab === 'dashboard' && (
          <div className="space-y-6">
            {/* Stats Grid — from scan data (what's in the browsed folder) */}
            {scanData ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="card text-center">
                  <div className="text-3xl mb-2">📄</div>
                  <div className="stat-value">{scanData.total_files}</div>
                  <div className="stat-label">{lang === 'en' ? 'Files' : 'Archivos'}</div>
                </div>
                <div className="card text-center">
                  <div className="text-3xl mb-2">📁</div>
                  <div className="stat-value">{scanData.total_folders}</div>
                  <div className="stat-label">{lang === 'en' ? 'Folders' : 'Carpetas'}</div>
                </div>
                <div className="card text-center">
                  <div className="text-3xl mb-2">💾</div>
                  <div className="stat-value">{scanData.total_size_human}</div>
                  <div className="stat-label">{lang === 'en' ? 'Total Size' : 'Tamaño Total'}</div>
                </div>
                <div className="card text-center">
                  <div className="text-3xl mb-2">📂</div>
                  <div className="stat-value">{Object.keys(scanData.by_category || {}).length}</div>
                  <div className="stat-label">{lang === 'en' ? 'Categories' : 'Categorías'}</div>
                </div>
              </div>
            ) : (
              <div className="card text-center py-12">
                <div className="text-4xl mb-4">📂</div>
                <p className="text-slate-400">
                  {lang === 'en'
                    ? 'Browse a folder below or type a path to get started.'
                    : 'Navegá una carpeta abajo o escribí una ruta para empezar.'}
                </p>
              </div>
            )}

            {/* ── File Explorer ── */}
            <div className="card">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                📂 {lang === 'en' ? 'File Explorer' : 'Explorador de Archivos'}
              </h2>
              <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
                {/* Path bar with breadcrumbs */}
                <div className="px-4 py-2.5 border-b border-slate-700/50 flex items-center gap-1 bg-slate-800/80">
                  <span className="text-lg flex-shrink-0">📁</span>
                  <div className="flex-1 flex items-center gap-1 overflow-x-auto text-sm font-mono scrollbar-thin">
                    {(scanData?.path || orgPath || '~/Desktop').split('/').filter(Boolean).map((part, i, parts) => {
                      const isLast = i === parts.length - 1;
                      const pathSoFar = '/' + parts.slice(0, i + 1).join('/');
                      return (
                        <span key={i} className="flex items-center gap-1 whitespace-nowrap">
                          <span className="text-slate-600">/</span>
                          {isLast ? (
                            <span className="text-slate-200">{part}</span>
                          ) : (
                            <button
                              onClick={() => navigateToPath(pathSoFar)}
                              className="text-slate-400 hover:text-maestro-400 transition-colors"
                            >
                              {part}
                            </button>
                          )}
                        </span>
                      );
                    })}
                  </div>
                  <button
                    onClick={navigateUp}
                    disabled={!scanData?.parent}
                    className="text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed text-sm px-2 py-1 rounded-lg hover:bg-slate-700 transition-colors flex-shrink-0"
                    title={lang === 'en' ? 'Go up' : 'Subir'}
                  >
                    ⬆
                  </button>
                  <button
                    onClick={() => fetchScan()}
                    className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded-lg hover:bg-slate-700 transition-colors flex-shrink-0"
                    title={lang === 'en' ? 'Refresh' : 'Actualizar'}
                  >
                    ↻
                  </button>
                </div>

                {/* Items */}
                {scanLoading ? (
                  <div className="py-12 text-center text-slate-500">
                    <span className="text-2xl">⏳</span>
                    <p className="mt-2 text-sm">
                      {lang === 'en' ? 'Scanning folder...' : 'Escaneando carpeta...'}
                    </p>
                  </div>
                ) : scanData && scanData.items.length > 0 ? (
                  <div className="divide-y divide-slate-700/30 max-h-96 overflow-y-auto">
                    {scanData.items.map(item => (
                      <div
                        key={item.name}
                        className="flex items-center gap-3 px-4 py-2.5 hover:bg-slate-700/30 transition-colors text-sm"
                      >
                        {/* Icon */}
                        <span className="text-lg w-8 text-center flex-shrink-0">
                          {item.is_dir ? '📁' : (item.category?.icon || '📄')}
                        </span>

                        {/* Name */}
                        {item.is_dir ? (
                          <button
                            onClick={() => navigateToFolder(item.name)}
                            className="font-medium text-slate-200 hover:text-maestro-400 transition-colors truncate flex-1 text-left"
                          >
                            {item.name}
                          </button>
                        ) : (
                          <span className="text-slate-300 truncate flex-1 font-mono text-xs">
                            {item.name}
                          </span>
                        )}

                        {/* Size */}
                        <span className="text-slate-500 text-xs w-20 text-right flex-shrink-0 hidden sm:block">
                          {item.size_human || '-'}
                        </span>

                        {/* Modified */}
                        <span className="text-slate-500 text-xs w-24 text-right flex-shrink-0 hidden md:block">
                          {item.modified ? item.modified.split(' ')[0] : ''}
                        </span>

                        {/* Category */}
                        {!item.is_dir && item.category && (
                          <span className="text-xs text-slate-400 w-28 text-right flex-shrink-0 hidden lg:block">
                            {item.category.icon} {item.category.localized_name}
                          </span>
                        )}

                        {/* Folder click hint */}
                        {item.is_dir && (
                          <span className="text-xs text-slate-600 flex-shrink-0 hidden sm:block">
                            →
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                ) : scanData ? (
                  <div className="py-8 text-center text-slate-500 text-sm">
                    {lang === 'en' ? 'Empty folder' : 'Carpeta vacía'}
                  </div>
                ) : (
                  <div className="py-8 text-center text-slate-500 text-sm">
                    {lang === 'en' ? 'Enter a path and press ↵' : 'Ingresá una ruta y presioná ↵'}
                  </div>
                )}

                {/* Footer stats */}
                {scanData && (
                  <div className="px-4 py-2 border-t border-slate-700/50 bg-slate-800/80 flex items-center gap-4 text-xs text-slate-500">
                    <span>📊 <strong className="text-slate-400">{scanData.total_files}</strong> {lang === 'en' ? 'files' : 'archivos'}</span>
                    <span>💾 <strong className="text-slate-400">{scanData.total_size_human}</strong></span>
                    <span>📂 <strong className="text-slate-400">{Object.keys(scanData.by_category || {}).length}</strong> {lang === 'en' ? 'categories' : 'categorías'}</span>
                  </div>
                )}
              </div>
            </div>

            {/* ── Actions ── */}
            <div className="card">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                {ICONS.organize} {lang === 'en' ? 'Actions' : 'Acciones'}
              </h2>
              <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
                <div className="flex-1 w-full sm:w-auto min-w-[200px]">
                  <label className="block text-xs text-slate-400 mb-1">
                    {lang === 'en' ? 'Target folder' : 'Carpeta destino'}
                  </label>
                  <input
                    value={orgPath}
                    onChange={e => setOrgPath(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') fetchScan(orgPath); }}
                    placeholder={lang === 'en' ? '~/Desktop' : '~/Escritorio'}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-maestro-500 transition-colors"
                  />
                </div>
                <button onClick={() => handleOrganize(false)} disabled={loading || scanLoading}
                  className="btn-primary whitespace-nowrap">
                  {loading ? '⏳...' : '🧹'} {lang === 'en' ? 'Organize Now' : 'Organizar Ahora'}
                </button>
                <button onClick={() => handleOrganize(true)} disabled={loading || scanLoading}
                  className="btn-secondary whitespace-nowrap">
                  🔍 {lang === 'en' ? 'Simulate' : 'Simular'}
                </button>
                <button onClick={() => { fetchStats(); fetchScan(); fetchCategories(); }}
                  className="btn-secondary whitespace-nowrap">
                  🔄 {lang === 'en' ? 'Refresh' : 'Actualizar'}
                </button>
              </div>
            </div>

            {/* Extensions bar chart (from scan data) */}
            {scanData && scanData.by_extension && Object.keys(scanData.by_extension).length > 0 && (
              <div className="card">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  {ICONS.stats} {lang === 'en' ? 'File Types' : 'Tipos de Archivo'}
                </h2>
                <div className="space-y-2">
                  {Object.entries(scanData.by_extension)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 8)
                    .map(([ext, count]) => (
                      <div key={ext} className="flex items-center gap-3">
                        <span className="text-sm font-mono text-slate-400 w-20">{ext}</span>
                        <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div className="h-full bg-maestro-500 rounded-full"
                            style={{ width: `${(count / Math.max(...Object.values(scanData.by_extension))) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-slate-400 w-12 text-right">{count}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Category breakdown (from scan data) */}
            {scanData && scanData.by_category && Object.keys(scanData.by_category).length > 0 && (
              <div className="card">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  📊 {lang === 'en' ? 'Category Preview' : 'Vista por Categorías'}
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {Object.entries(scanData.by_category)
                    .sort(([,a], [,b]) => b - a)
                    .map(([catName, count]) => {
                      const catInfo = categories.find(c => c.name === catName);
                      return (
                        <div key={catName} className="bg-slate-800 rounded-xl px-4 py-3 flex items-center gap-3">
                          <span className="text-xl">{catInfo?.icon || '📦'}</span>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">
                              {catInfo?.folder_name || catName}
                            </div>
                            <div className="text-xs text-slate-500">
                              {count} {count === 1
                                ? (lang === 'en' ? 'file' : 'archivo')
                                : (lang === 'en' ? 'files' : 'archivos')}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab: Categories */}
        {tab === 'categories' && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">
              {ICONS.categories} {lang === 'en' ? 'Categories' : 'Categorías'}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {categories.filter(c => c.name !== 'macOS System').map(cat => (
                <div key={cat.name} className="bg-slate-800 rounded-xl p-4 flex items-center gap-3">
                  <span className="text-2xl">{cat.icon}</span>
                  <div>
                    <div className="font-medium">{cat.folder_name}</div>
                    <div className="text-xs text-slate-500">{cat.extensions.length} extensions</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab: Config */}
        {tab === 'config' && config && (
          <div className="card space-y-6">
            <h2 className="text-lg font-semibold mb-4">
              {ICONS.settings} {lang === 'en' ? 'Settings' : 'Configuración'}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">
                  {lang === 'en' ? 'Language' : 'Idioma'}
                </label>
                <select value={config.language} onChange={e => setConfig({...config, language: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white">
                  <option value="en">English</option>
                  <option value="es">Español</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">
                  {lang === 'en' ? 'Desktop Path' : 'Ruta del Escritorio'}
                </label>
                <input value={config.desktop_path} onChange={e => setConfig({...config, desktop_path: e.target.value})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white" />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center gap-3 bg-slate-800 rounded-xl px-4 py-3 cursor-pointer">
                <input type="checkbox" checked={config.dry_run} onChange={e => setConfig({...config, dry_run: e.target.checked})}
                  className="w-4 h-4 accent-maestro-500" />
                <span className="text-sm">{lang === 'en' ? 'Dry Run (simulate)' : 'Simular solo'}</span>
              </label>
              <label className="flex items-center gap-3 bg-slate-800 rounded-xl px-4 py-3 cursor-pointer">
                <input type="checkbox" checked={config.verbose} onChange={e => setConfig({...config, verbose: e.target.checked})}
                  className="w-4 h-4 accent-maestro-500" />
                <span className="text-sm">Verbose</span>
              </label>
              <label className="flex items-center gap-3 bg-slate-800 rounded-xl px-4 py-3 cursor-pointer">
                <input type="checkbox" checked={config.show_notifications} onChange={e => setConfig({...config, show_notifications: e.target.checked})}
                  className="w-4 h-4 accent-maestro-500" />
                <span className="text-sm">{lang === 'en' ? 'Notifications' : 'Notificaciones'}</span>
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">
                  {lang === 'en' ? 'Schedule (hours)' : 'Programar (horas)'}
                </label>
                <input type="number" value={config.schedule_interval_hours} onChange={e => setConfig({...config, schedule_interval_hours: parseInt(e.target.value) || 6})}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white" />
              </div>
            </div>

            <button onClick={handleSaveConfig} disabled={configSaving}
              className="btn-primary">
              {configSaving ? '⏳...' : '💾'} {lang === 'en' ? 'Save Settings' : 'Guardar'}
            </button>
          </div>
        )}

        {/* Tab: Undo */}
        {tab === 'undo' && (
          <div className="space-y-4">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">
                {ICONS.undo} {lang === 'en' ? 'Undo History' : 'Historial de Deshacer'}
              </h2>

              {snapshots.length === 0 && (
                <p className="text-slate-500 text-sm">
                  {lang === 'en'
                    ? 'No undo snapshots available. Run an organization first.'
                    : 'No hay snapshots disponibles. Ejecutá una organización primero.'}
                </p>
              )}

              <div className="space-y-3">
                {snapshots.map(snap => (
                  <div key={snap.file} className="bg-slate-800 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm">{snap.description || 'Organization'}</div>
                      <div className="text-xs text-slate-500">
                        {snap.created_at} · {snap.entries_count} files
                      </div>
                    </div>
                    <button onClick={() => handleUndo(snap.file)} disabled={loading}
                      className="btn-danger text-xs py-1.5 px-3">
                      {ICONS.undo} {lang === 'en' ? 'Restore' : 'Restaurar'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <button onClick={() => fetchSnapshots()} className="btn-secondary">
              🔄 {lang === 'en' ? 'Refresh' : 'Actualizar'}
            </button>
          </div>
        )}
      </main>

      {/* ─── Footer ─── */}
      <footer className="text-center text-slate-600 text-xs py-8">
        DesktopMaestro · MIT License
      </footer>
    </div>
  );
}
