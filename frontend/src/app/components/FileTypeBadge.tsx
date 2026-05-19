'use client';

// ─── Tipos de archivo soportados ───
export type FormatFile =
  | "doc" | "pdf" | "md" | "mdx" | "csv" | "xls" | "xlsx"
  | "txt" | "ppt" | "pptx"
  | "zip" | "rar" | "tar" | "gz"
  | "html" | "js" | "jsx" | "tsx" | "css" | "json"
  | "code" | "img" | "png" | "jpg" | "jpeg"
  | "video" | "audio" | "font" | "epub" | "torrent"
  | "exe" | "dmg" | "app" | "unknown";

// ─── Map extension → FormatFile ───
const EXT_TO_FORMAT: Record<string, FormatFile> = {
  // Documents
  ".doc": "doc", ".docx": "doc",
  ".pdf": "pdf",
  ".md": "md", ".mdx": "mdx",
  ".txt": "txt",
  ".rtf": "doc",
  ".odt": "doc",
  // Spreadsheets
  ".csv": "csv",
  ".xls": "xls", ".xlsx": "xlsx",
  ".ods": "xls",
  // Presentations
  ".ppt": "ppt", ".pptx": "pptx",
  ".odp": "ppt",
  // Archives
  ".zip": "zip", ".rar": "rar", ".tar": "tar", ".gz": "gz",
  ".7z": "zip", ".bz2": "gz", ".xz": "gz",
  ".zst": "gz",
  // Code
  ".html": "html", ".htm": "html",
  ".js": "js", ".jsx": "jsx",
  ".ts": "code", ".tsx": "tsx",
  ".css": "css", ".scss": "css", ".less": "css",
  ".json": "json",
  ".py": "code", ".rb": "code", ".go": "code", ".rs": "code",
  ".java": "code", ".kt": "code", ".swift": "code",
  ".c": "code", ".cpp": "code", ".h": "code", ".hpp": "code",
  ".sh": "code", ".bash": "code", ".zsh": "code",
  ".yaml": "code", ".yml": "code", ".toml": "code",
  ".xml": "code",
  ".sql": "code", ".graphql": "code",
  // Images
  ".png": "png", ".jpg": "jpg", ".jpeg": "jpeg", ".webp": "img",
  ".gif": "img", ".bmp": "img", ".ico": "img",
  ".svg": "img",
  ".psd": "img", ".ai": "img", ".tiff": "img",
  // Video
  ".mp4": "video", ".mov": "video", ".avi": "video", ".mkv": "video",
  ".webm": "video", ".flv": "video", ".wmv": "video",
  ".m4v": "video",
  // Audio
  ".mp3": "audio", ".wav": "audio", ".flac": "audio", ".aac": "audio",
  ".ogg": "audio", ".wma": "audio", ".m4a": "audio",
  // eBooks
  ".epub": "epub", ".mobi": "epub", ".azw3": "epub",
  // Fonts
  ".ttf": "font", ".otf": "font", ".woff": "font", ".woff2": "font",
  // Torrent
  ".torrent": "torrent",
  // Executables
  ".exe": "exe", ".msi": "exe",
  ".dmg": "dmg", ".app": "app",
  ".deb": "exe", ".rpm": "exe", ".apk": "exe",
};

// ─── Map FormatFile → Color ───
const COLOR_MAP: Record<FormatFile, string> = {
  doc: "from-blue-500 to-blue-600",
  pdf: "from-red-500 to-red-600",
  md: "from-gray-500 to-gray-600",
  mdx: "from-gray-500 to-gray-600",
  txt: "from-slate-500 to-slate-600",
  csv: "from-teal-600 to-teal-700",
  xls: "from-emerald-500 to-emerald-600",
  xlsx: "from-emerald-500 to-emerald-600",
  ppt: "from-orange-500 to-orange-600",
  pptx: "from-orange-500 to-orange-600",
  zip: "from-purple-500 to-purple-600",
  rar: "from-purple-600 to-purple-700",
  tar: "from-amber-500 to-amber-600",
  gz: "from-amber-600 to-amber-700",
  html: "from-orange-600 to-orange-700",
  js: "from-yellow-500 to-yellow-600",
  jsx: "from-blue-500 to-blue-600",
  tsx: "from-blue-500 to-blue-600",
  css: "from-blue-500 to-blue-600",
  json: "from-yellow-500 to-yellow-600",
  code: "from-orange-600 to-orange-700",
  img: "from-pink-500 to-pink-600",
  png: "from-emerald-600 to-emerald-700",
  jpg: "from-green-600 to-green-700",
  jpeg: "from-green-600 to-green-700",
  video: "from-violet-500 to-violet-600",
  audio: "from-rose-500 to-rose-600",
  font: "from-cyan-500 to-cyan-600",
  epub: "from-teal-500 to-teal-600",
  torrent: "from-lime-500 to-lime-600",
  exe: "from-stone-500 to-stone-600",
  dmg: "from-sky-500 to-sky-600",
  app: "from-indigo-500 to-indigo-600",
  unknown: "from-slate-500 to-slate-600",
};

// ─── Map FormatFile → Emoji (fallback) ───
const EMOJI_MAP: Record<FormatFile, string> = {
  doc: "📝", pdf: "📕", md: "📄", mdx: "📄", txt: "📃",
  csv: "📊", xls: "📊", xlsx: "📊",
  ppt: "📽️", pptx: "📽️",
  zip: "🗜️", rar: "🗜️", tar: "🗜️", gz: "🗜️",
  html: "🌐", js: "🟨", jsx: "⚛️", tsx: "⚛️",
  css: "🎨", json: "📋",
  code: "💻",
  img: "🖼️", png: "🖼️", jpg: "🖼️", jpeg: "🖼️",
  video: "🎬", audio: "🎵",
  font: "🔤", epub: "📖", torrent: "🧲",
  exe: "⚙️", dmg: "💿", app: "📱",
  unknown: "📄",
};

// ─── Get FormatFile from filename/extension ───
export function getFormat(extension: string, filename?: string): FormatFile {
  const ext = extension.toLowerCase().startsWith(".")
    ? extension.toLowerCase()
    : `.${extension.toLowerCase()}`;

  // Check extension map
  if (EXT_TO_FORMAT[ext]) return EXT_TO_FORMAT[ext];

  // Check common names
  if (filename) {
    const lower = filename.toLowerCase();
    if (lower === "makefile" || lower === "dockerfile" || lower === "gemfile") return "code";
    if (lower.startsWith(".env") || lower.startsWith(".git")) return "code";
    if (lower === "package.json" || lower === "tsconfig.json") return "json";
  }

  return "unknown";
}

// ─── FileTypeBadge Component ───
interface FileTypeBadgeProps {
  extension: string;
  filename?: string;
  size?: "sm" | "md" | "lg";
}

export default function FileTypeBadge({
  extension,
  filename,
  size = "md",
}: FileTypeBadgeProps) {
  const format = getFormat(extension, filename);
  const colorClass = COLOR_MAP[format];
  const emoji = EMOJI_MAP[format];
  const label = format === "unknown" ? (extension.replace(".", "").toUpperCase() || "?") : format.toUpperCase();

  const sizeClasses = {
    sm: "text-[8px] px-1.5 py-0.5 min-w-[32px]",
    md: "text-[10px] px-2 py-0.5 min-w-[38px]",
    lg: "text-xs px-2.5 py-1 min-w-[44px]",
  };

  return (
    <div className="relative flex items-center gap-2">
      {/* Emoji icon */}
      <span className="text-base flex-shrink-0 leading-none w-6 text-center">
        {emoji}
      </span>

      {/* Format badge */}
      <span
        className={`
          inline-flex items-center justify-center font-semibold tracking-wide
          rounded-md text-white shadow-sm
          bg-gradient-to-br ${colorClass}
          ${sizeClasses[size]}
        `}
      >
        {label}
      </span>
    </div>
  );
}

// ─── FilePreview Mini Card (for grid view) ───
interface FilePreviewCardProps {
  extension: string;
  filename?: string;
  size?: "sm" | "md";
}

export function FilePreviewCard({
  extension,
  filename,
  size = "md",
}: FilePreviewCardProps) {
  const format = getFormat(extension, filename);
  const colorClass = COLOR_MAP[format];
  const emoji = EMOJI_MAP[format];
  const label = format === "unknown"
    ? (extension.replace(".", "").toUpperCase().slice(0, 4) || "?")
    : format.toUpperCase();

  const cardSizes = {
    sm: "w-16 h-20",
    md: "w-20 h-24",
  };

  return (
    <div className="relative inline-flex flex-col items-center gap-1">
      {/* Mini card */}
      <div
        className={`
          ${cardSizes[size]}
          relative rounded-xl border border-slate-700/60
          bg-gradient-to-b from-slate-800 to-slate-850
          flex items-center justify-center
          shadow-lg overflow-hidden
          group-hover:border-maestro-500/30 group-hover:shadow-maestro-500/5
          transition-all duration-200
        `}
      >
        {/* Emoji large */}
        <span className="text-3xl opacity-80">{emoji}</span>

        {/* Corner badge */}
        <div
          className={`
            absolute -bottom-0.5 -right-0.5
            px-1.5 py-0.5 rounded-tl-lg rounded-br-lg
            text-[7px] font-bold tracking-wider text-white
            bg-gradient-to-tr ${colorClass}
          `}
        >
          {label}
        </div>
      </div>
    </div>
  );
}
