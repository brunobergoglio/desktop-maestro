'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

// ─── Types ───
interface TreeNode {
  name: string;
  path: string;
  is_dir: boolean;
  icon: string;
  children: TreeNode[];
  loaded: boolean;
  loading: boolean;
}

interface DirectoryTreeProps {
  currentPath: string;
  onNavigate: (path: string) => void;
  onSelect: (path: string) => void;
  lang?: 'en' | 'es';
}

// ─── Quick macOS roots ───
const ROOTS = [
  { path: '~/Desktop',     icon: '🖥️', label_en: 'Desktop',     label_es: 'Escritorio' },
  { path: '~/Documents',   icon: '📄', label_en: 'Documents',   label_es: 'Documentos' },
  { path: '~/Downloads',   icon: '⬇️', label_en: 'Downloads',   label_es: 'Descargas' },
  { path: '~',             icon: '🏠', label_en: 'Home',         label_es: 'Inicio' },
  { path: '/',             icon: '💻', label_en: 'Root',         label_es: 'Raíz' },
];

// ─── Icon helpers ───
function getFolderIcon(name: string): string {
  const lower = name.toLowerCase();
  if (lower.includes('desktop') || lower.includes('escritorio')) return '🖥️';
  if (lower.includes('document')) return '📄';
  if (lower.includes('download')) return '⬇️';
  if (lower.includes('music') || lower.includes('música') || lower.includes('audio')) return '🎵';
  if (lower.includes('picture') || lower.includes('image') || lower.includes('foto') || lower.includes('imagen') || lower.includes('photo')) return '🖼️';
  if (lower.includes('video') || lower.includes('movie') || lower.includes('película')) return '🎬';
  if (lower.includes('app') || lower.includes('application')) return '📱';
  if (lower.includes('developer') || lower.includes('dev') || lower.includes('code') || lower.includes('código')) return '💻';
  if (lower.includes('tmp') || lower.includes('temp')) return '🗑️';
  if (lower.includes('library') || lower.includes('librer')) return '📚';
  if (lower.includes('system') || lower.includes('sistema')) return '⚙️';
  if (lower.includes('.config') || lower.includes('.cache')) return '⚙️';
  if (lower.includes('node_modules')) return '📦';
  if (lower.includes('github')) return '🐙';
  return '📁';
}

// ─── Build initial tree from roots ───
function buildInitialTree(): TreeNode[] {
  return ROOTS.map(root => ({
    name: root.label_en,
    path: root.path,
    is_dir: true,
    icon: root.icon,
    children: [],
    loaded: false,
    loading: false,
  }));
}

// ─── Directory Tree Component ───
export default function DirectoryTree({
  currentPath,
  onNavigate,
  onSelect,
  lang = 'en',
}: DirectoryTreeProps) {
  const [treeData, setTreeData] = useState<TreeNode[]>(buildInitialTree);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
  const treeRef = useRef<HTMLDivElement>(null);

  // ─── Fetch children for a node ───
  const loadChildren = useCallback(async (node: TreeNode): Promise<TreeNode[]> => {
    try {
      const res = await fetch(
        `/api/desktopmaestro/scan?path=${encodeURIComponent(node.path)}`
      );
      if (!res.ok) throw new Error('Failed to scan');
      const data = await res.json();

      if (data.items && Array.isArray(data.items)) {
        return data.items
          .filter((item: any) => item.is_dir && !item.name.startsWith('.'))
          .map((item: any) => ({
            name: item.name,
            path: node.path.endsWith('/')
              ? `${node.path}${item.name}`
              : `${node.path}/${item.name}`,
            is_dir: true,
            icon: getFolderIcon(item.name),
            children: [],
            loaded: false,
            loading: false,
          }));
      }
      return [];
    } catch {
      return [];
    }
  }, []);

  // ─── Toggle expand/collapse ───
  const toggleExpand = useCallback(async (path: string) => {
    setExpandedPaths(prev => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });

    setTreeData(prev => {
      const updateNode = (nodes: TreeNode[]): TreeNode[] =>
        nodes.map(node => {
          if (node.path === path && !node.loaded && !node.loading) {
            setLoadingMessage(`Loading ${node.name}...`);
            loadChildren(node).then(children => {
              setTreeData(prev2 => {
                const updateChildren = (nodes2: TreeNode[]): TreeNode[] =>
                  nodes2.map(n => {
                    if (n.path === path) {
                      return { ...n, children, loaded: true, loading: false };
                    }
                    return { ...n, children: updateChildren(n.children) };
                  });
                return updateChildren(prev2);
              });
              setLoadingMessage(null);
            });
            return { ...node, loading: true };
          }
          return { ...node, children: updateNode(node.children) };
        });
      return updateNode(prev);
    });
  }, [loadChildren]);

  // ─── Render a tree node ───
  const renderNode = (node: TreeNode, depth: number = 0): React.ReactNode => {
    if (!node.is_dir) return null;

    const isExpanded = expandedPaths.has(node.path);
    const isCurrent = node.path === currentPath;
    const indent = depth * 16;

    return (
      <div key={node.path}>
        <div
          className={`
            group flex items-center gap-1.5 px-2 py-1.5 rounded-lg cursor-pointer
            transition-all duration-100 text-sm
            ${isCurrent
              ? 'bg-maestro-600/20 text-maestro-300 border border-maestro-500/20'
              : 'text-slate-300 hover:bg-slate-700/40 hover:text-slate-100 border border-transparent'
            }
          `}
          style={{ paddingLeft: `${12 + indent}px` }}
          onClick={() => {
            onNavigate(node.path);
            onSelect(node.path);
          }}
        >
          <button
            onClick={(e) => {
              e.stopPropagation();
              toggleExpand(node.path);
            }}
            className={`
              w-4 h-4 flex items-center justify-center flex-shrink-0
              transition-transform duration-150
              ${isExpanded ? 'rotate-90' : 'rotate-0'}
            `}
          >
            <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
              <path d="M3 1l5 4-5 4V1z" />
            </svg>
          </button>
          <span className="text-base flex-shrink-0 leading-none">
            {node.loading ? '⏳' : node.icon}
          </span>
          <span className="truncate flex-1 text-sm leading-tight">{node.name}</span>
          {isCurrent && (
            <span className="text-[10px] text-maestro-500 flex-shrink-0">●</span>
          )}
        </div>

        {isExpanded && (
          <div className="overflow-hidden animate-fade-in">
            {node.loading ? (
              <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-slate-500"
                style={{ paddingLeft: `${28 + indent}px` }}>
                <span className="animate-pulse">⏳</span>
                <span>{lang === 'en' ? 'Loading...' : 'Cargando...'}</span>
              </div>
            ) : node.children.length > 0 ? (
              node.children.map(child => renderNode(child, depth + 1))
            ) : (
              <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-slate-600 italic"
                style={{ paddingLeft: `${28 + indent}px` }}>
                {lang === 'en' ? '(empty)' : '(vacía)'}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // ─── Filter ───
  const [filter, setFilter] = useState('');
  const filteredRoots = treeData.filter(root =>
    root.name.toLowerCase().includes(filter.toLowerCase()) ||
    root.path.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="card !p-0 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/30 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          📂 {lang === 'en' ? 'Browse Folders' : 'Explorar Carpetas'}
        </h3>
        <span className="text-[10px] text-slate-600">
          {lang === 'en' ? 'click to navigate' : 'clic para navegar'}
        </span>
      </div>

      {/* Inline filter */}
      <div className="px-3 py-2 border-b border-slate-700/20">
        <input
          type="text"
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder={lang === 'en' ? '🔍 Filter folders...' : '🔍 Filtrar carpetas...'}
          className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-maestro-500/50 transition-colors"
        />
      </div>

      {/* Tree */}
      <div ref={treeRef} className="overflow-y-auto max-h-[400px] py-2 scrollbar-thin">
        {filteredRoots.length === 0 ? (
          <div className="px-4 py-6 text-center text-slate-500 text-sm">
            {lang === 'en' ? 'No folders match your filter' : 'Ninguna carpeta coincide'}
          </div>
        ) : (
          filteredRoots.map(root => renderNode(root, 0))
        )}
        {loadingMessage && (
          <div className="px-4 py-2 text-xs text-slate-500 flex items-center gap-2">
            <span className="animate-pulse">⏳</span>
            {loadingMessage}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-slate-700/30 bg-slate-800/40 flex items-center justify-between text-[10px] text-slate-600">
        <span>{lang === 'en' ? '▶ click to expand' : '▶ clic para expandir'}</span>
        <span>{lang === 'en' ? '● current folder' : '● carpeta actual'}</span>
      </div>
    </div>
  );
}
