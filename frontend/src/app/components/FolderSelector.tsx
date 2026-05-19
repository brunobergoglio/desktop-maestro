'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

// ─── Types ───
interface FolderSuggestion {
  name: string;
  path: string;
  has_children: boolean;
}

interface FolderSelectorProps {
  value: string;
  onChange: (path: string) => void;
  onBrowse: (path: string) => void;
  loading?: boolean;
  lang?: 'en' | 'es';
}

// ─── Quick-access bookmarks (macOS paths) ───
const BOOKMARKS: { path: string; label: Record<'en' | 'es', string>; icon: string }[] = [
  { path: '~/Desktop',     label: { en: 'Desktop',     es: 'Escritorio' },  icon: '🖥️' },
  { path: '~/Documents',   label: { en: 'Documents',   es: 'Documentos' },  icon: '📄' },
  { path: '~/Downloads',   label: { en: 'Downloads',   es: 'Descargas' },   icon: '⬇️' },
  { path: '~',             label: { en: 'Home',         es: 'Inicio' },     icon: '🏠' },
  { path: '/tmp',          label: { en: 'Temp',         es: 'Temp' },       icon: '📁' },
];

// ─── FOLDER PICKER via File System Access API (Chrome 86+) ───
async function pickFolderNative(): Promise<string | null> {
  try {
    // @ts-ignore — showDirectoryPicker is not in all TS libs
    if (!window.showDirectoryPicker) return null;
    const handle = await (window as any).showDirectoryPicker();
    // The File System Access API doesn't reveal full path,
    // but we can get the folder name and use it as a hint
    return handle.name;
  } catch {
    // User cancelled or API not available
    return null;
  }
}

// ─── GENERATE FOLDER ICON ───
function getFolderEmoji(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes('desktop') || lower.includes('escritorio')) return '🖥️';
  if (lower.includes('document')) return '📄';
  if (lower.includes('download')) return '⬇️';
  if (lower.includes('music') || lower.includes('música') || lower.includes('audio')) return '🎵';
  if (lower.includes('picture') || lower.includes('image') || lower.includes('foto') || lower.includes('imágen')) return '🖼️';
  if (lower.includes('video') || lower.includes('movie') || lower.includes('película')) return '🎬';
  if (lower.includes('app')) return '📱';
  if (lower.includes('developer') || lower.includes('dev') || lower.includes('code') || lower.includes('código')) return '💻';
  if (lower.includes('tmp') || lower.includes('temp')) return '🗑️';
  if (lower.includes('library') || lower.includes('librer')) return '📚';
  if (lower.includes('system') || lower.includes('sistema')) return '⚙️';
  return '📁';
}

// ─── FOLDER SELECTOR COMPONENT ───
export default function FolderSelector({
  value,
  onChange,
  onBrowse,
  loading = false,
  lang = 'en',
}: FolderSelectorProps) {
  const [inputValue, setInputValue] = useState(value);
  const [suggestions, setSuggestions] = useState<FolderSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isFocused, setIsFocused] = useState(false);
  const [recentPaths, setRecentPaths] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ─── Load recent paths from localStorage ───
  useEffect(() => {
    try {
      const stored = localStorage.getItem('dmaestro_recent_paths');
      if (stored) setRecentPaths(JSON.parse(stored));
    } catch { /* ignore */ }
  }, []);

  // ─── Save recent path ───
  const addRecentPath = useCallback((path: string) => {
    setRecentPaths(prev => {
      const updated = [path, ...prev.filter(p => p !== path)].slice(0, 8);
      try { localStorage.setItem('dmaestro_recent_paths', JSON.stringify(updated)); } catch { /* ignore */ }
      return updated;
    });
  }, []);

  // ─── Sync input with external value ───
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // ─── Fetch autocomplete suggestions ───
  const fetchSuggestions = useCallback(async (query: string) => {
    if (!query || query.length < 1) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const res = await fetch(`/api/desktopmaestro/folders?path=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      
      if (data.folders && Array.isArray(data.folders)) {
        const items: FolderSuggestion[] = data.folders.map((f: string) => ({
          name: f,
          path: data.path.endsWith('/') ? `${data.path}${f}` : `${data.path}/${f}`,
          has_children: true,
        }));
        setSuggestions(items);
        setShowSuggestions(items.length > 0);
        setSelectedIndex(-1);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, []);

  // ─── Debounced input handler ───
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInputValue(val);
    onChange(val);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchSuggestions(val), 150);
  };

  // ─── Keyboard navigation ───
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        onBrowse(inputValue);
        addRecentPath(inputValue);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          const selected = suggestions[selectedIndex];
          setInputValue(selected.path);
          onChange(selected.path);
          setShowSuggestions(false);
          onBrowse(selected.path);
          addRecentPath(selected.path);
        } else {
          onBrowse(inputValue);
          addRecentPath(inputValue);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        break;
      case 'Tab':
        setShowSuggestions(false);
        break;
    }
  };

  // ─── Select a suggestion ───
  const selectSuggestion = (suggestion: FolderSuggestion) => {
    setInputValue(suggestion.path);
    onChange(suggestion.path);
    setShowSuggestions(false);
    onBrowse(suggestion.path);
    addRecentPath(suggestion.path);
    inputRef.current?.focus();
  };

  // ─── Click bookmark ───
  const handleBookmark = (path: string) => {
    setInputValue(path);
    onChange(path);
    onBrowse(path);
    addRecentPath(path);
  };

  // ─── Native folder picker (Chrome) ───
  const handleNativePicker = async () => {
    const folderName = await pickFolderNative();
    if (folderName) {
      // We can only get the name, so let's try to use it
      // The user can then navigate via the file explorer
      // For now, just trigger the webkitdirectory input as fallback
    }
    // Also trigger the webkitdirectory input
    fileInputRef.current?.click();
  };

  // ─── Handle webkitdirectory file input ───
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    
    // Try to extract path from the first file's webkitRelativePath
    const firstFile = files[0];
    // webkitRelativePath gives us "folder/subfolder/file", we want everything before the first /
    const sepIndex = firstFile.webkitRelativePath.indexOf('/');
    if (sepIndex > 0) {
      const folderName = firstFile.webkitRelativePath.substring(0, sepIndex);
      // We can't get the full path, but we can use the name
      // The best we can do is navigate to a known base path
      // Actually, we should try to get the full path
      // Let's just use it as a hint and let the user navigate
    }
    
    // Reset so the same folder can be picked again
    e.target.value = '';
  };

  // ─── Close suggestions on outside click ───
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionRef.current && 
        !suggestionRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="space-y-3">
      {/* ─── Label with native picker hint ─── */}
      <div className="flex items-center justify-between">
        <label className="block text-xs text-slate-400 font-medium tracking-wide uppercase">
          {lang === 'en' ? '📂 Target Folder' : '📂 Carpeta Destino'}
        </label>
        <span className="text-[10px] text-slate-600 hidden sm:block">
          {lang === 'en' ? '⌘K to search · ↑↓ to navigate' : '⌘K buscar · ↑↓ navegar'}
        </span>
      </div>

      {/* ─── Input with integrated actions ─── */}
      <div className="relative" ref={suggestionRef}>
        <div className={`
          flex items-center gap-2 bg-slate-800/80 border rounded-2xl 
          transition-all duration-200
          ${isFocused 
            ? 'border-maestro-500/50 ring-2 ring-maestro-500/10 shadow-lg shadow-maestro-500/5' 
            : 'border-slate-700/50 hover:border-slate-600/50'
          }
          ${loading ? 'opacity-60 pointer-events-none' : ''}
        `}>
          {/* Icon */}
          <span className="pl-4 text-lg flex-shrink-0">
            {loading ? '⏳' : '📁'}
          </span>

          {/* Input */}
          <input
            ref={inputRef}
            data-folder-input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              setIsFocused(true);
              if (suggestions.length > 0) setShowSuggestions(true);
            }}
            onBlur={() => {
              // Delay to allow suggestion click
              setTimeout(() => setIsFocused(false), 200);
            }}
            placeholder={lang === 'en' ? '~/Desktop or /path/to/folder' : '~/Escritorio o /ruta/carpeta'}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 py-3 focus:outline-none font-mono"
            spellCheck={false}
            autoComplete="off"
          />

          {/* Action buttons */}
          <div className="flex items-center gap-1 pr-2">
            {/* Clear */}
            {inputValue && (
              <button
                onClick={() => { setInputValue(''); onChange(''); setShowSuggestions(false); }}
                className="p-1.5 text-slate-500 hover:text-slate-300 hover:bg-slate-700/50 rounded-lg transition-all text-xs"
                title={lang === 'en' ? 'Clear' : 'Limpiar'}
              >
                ✕
              </button>
            )}

            {/* Native Folder Picker (Chrome/Edge) */}
            <button
              onClick={handleNativePicker}
              className="p-1.5 text-slate-500 hover:text-maestro-400 hover:bg-slate-700/50 rounded-lg transition-all text-sm"
              title={lang === 'en' ? 'Browse folders...' : 'Examinar carpetas...'}
            >
              🔍
            </button>

            {/* Go button */}
            <button
              onClick={() => {
                onBrowse(inputValue);
                addRecentPath(inputValue);
              }}
              disabled={loading || !inputValue}
              className="p-1.5 text-slate-500 hover:text-white hover:bg-maestro-600/50 rounded-lg transition-all text-sm disabled:opacity-30"
              title={lang === 'en' ? 'Go to folder' : 'Ir a carpeta'}
            >
              ⏎
            </button>
          </div>
        </div>

        {/* ─── Hidden file input for webkitdirectory fallback ─── */}
        <input
          ref={fileInputRef}
          type="file"
          /* @ts-ignore */
          webkitdirectory=""
          directory=""
          className="hidden"
          onChange={handleFileInput}
        />

        {/* ─── Autocomplete Dropdown ─── */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-50 mt-1 w-full bg-slate-800 border border-slate-700/80 rounded-2xl overflow-hidden shadow-2xl shadow-black/40 backdrop-blur-xl">
            <div className="max-h-60 overflow-y-auto py-1 scrollbar-thin">
              {suggestions.map((suggestion, index) => (
                <button
                  key={suggestion.path}
                  onClick={() => selectSuggestion(suggestion)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`
                    w-full flex items-center gap-3 px-4 py-2.5 text-left transition-all duration-100
                    ${index === selectedIndex 
                      ? 'bg-maestro-600/20 text-white border-l-2 border-maestro-500' 
                      : 'text-slate-300 hover:bg-slate-700/50 border-l-2 border-transparent'
                    }
                  `}
                >
                  <span className="text-lg flex-shrink-0">
                    {getFolderEmoji(suggestion.name)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      {suggestion.name}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono truncate">
                      {suggestion.path}
                    </div>
                  </div>
                  {suggestion.has_children && (
                    <span className="text-xs text-slate-600 flex-shrink-0">📂</span>
                  )}
                </button>
              ))}
            </div>
            <div className="px-4 py-1.5 border-t border-slate-700/50 text-[10px] text-slate-600 flex items-center gap-3 bg-slate-800/80">
              <span>↑↓ {lang === 'en' ? 'Navigate' : 'Navegar'}</span>
              <span>↵ {lang === 'en' ? 'Select' : 'Seleccionar'}</span>
              <span>Esc {lang === 'en' ? 'Close' : 'Cerrar'}</span>
            </div>
          </div>
        )}
      </div>

      {/* ─── Quick Access Bookmarks ─── */}
      <div className="flex flex-wrap gap-1.5">
        {BOOKMARKS.map(bookmark => (
          <button
            key={bookmark.path}
            onClick={() => handleBookmark(bookmark.path)}
            className={`
              flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium 
              transition-all duration-200 border
              ${value === bookmark.path
                ? 'bg-maestro-600/20 border-maestro-500/30 text-maestro-300 shadow-sm shadow-maestro-500/10'
                : 'bg-slate-800/50 border-slate-700/30 text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 hover:border-slate-600/50'
              }
            `}
          >
            <span>{bookmark.icon}</span>
            <span>{bookmark.label[lang]}</span>
          </button>
        ))}
      </div>

      {/* ─── Recent Paths ─── */}
      {recentPaths.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          <span className="text-[10px] text-slate-600 self-center mr-1">
            {lang === 'en' ? 'Recent:' : 'Recientes:'}
          </span>
          {recentPaths.slice(0, 4).map(path => (
            <button
              key={path}
              onClick={() => handleBookmark(path)}
              className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-mono 
                         text-slate-500 bg-slate-800/30 border border-slate-700/20 
                         hover:bg-slate-700/40 hover:text-slate-300 transition-all"
            >
              <span>↻</span>
              <span className="truncate max-w-[150px]">{path}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
