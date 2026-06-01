/* =============================================
   MinisterPortrait Component - 人物头像组件
   支持专属立绘 / 池头像 / 占位符三级fallback
   ============================================= */

import React, { useState } from 'react';

interface MinisterPortraitProps {
  primary?: string;
  fallback?: string;
  name: string;
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export function MinisterPortrait({
  primary,
  fallback,
  name,
  size = 'medium',
  className = ''
}: MinisterPortraitProps) {
  const [stage, setStage] = useState<"primary" | "fallback" | "placeholder">(
    primary ? "primary" : (fallback ? "fallback" : "placeholder")
  );

  const sizeClasses = {
    small: 'portrait-small',
    medium: 'portrait-medium',
    large: 'portrait-large'
  };

  const src = stage === "primary" ? primary : stage === "fallback" ? fallback : "";

  if (stage === "placeholder") {
    return (
      <div className={`minister-portrait-placeholder ${sizeClasses[size]} ${className}`}>
        <span className="portrait-initial">{name.charAt(0)}</span>
      </div>
    );
  }

  return (
    <img
      className={`minister-portrait ${sizeClasses[size]} ${className}`}
      src={src}
      alt={name}
      onError={() => {
        if (stage === "primary" && fallback) {
          setStage("fallback");
        } else {
          setStage("placeholder");
        }
      }}
    />
  );
}

/* CharacterPortrait 已迁移到独立文件 CharacterPortrait.tsx
   v2.0.0 P0-B5: 避免同名 export 冲突
*/

/* =============================================
   PortraitUploadButton - 头像上传按钮
   ============================================= */

interface PortraitUploadButtonProps {
  ministerName: string;
  onUpload: (ministerName: string, file: File) => Promise<void>;
  disabled?: boolean;
}

export function PortraitUploadButton({
  ministerName,
  onUpload,
  disabled = false
}: PortraitUploadButtonProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setBusy(true);
    try {
      await onUpload(ministerName, file);
    } catch (err) {
      window.alert(`上传失败：${(err as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className="portrait-upload-btn"
        title="上传立绘"
        disabled={disabled || busy}
        onClick={(e) => {
          e.stopPropagation();
          inputRef.current?.click();
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17,8 12,3 7,8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        style={{ display: "none" }}
        onClick={(e) => e.stopPropagation()}
        onChange={handleUpload}
      />
    </>
  );
}

/* =============================================
   Portrait Gallery - 头像选择画廊
   ============================================= */

interface PortraitGalleryProps {
  portraits: Array<{
    id: string;
    name: string;
    url: string;
    faction?: string;
  }>;
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function PortraitGallery({ portraits, selectedId, onSelect }: PortraitGalleryProps) {
  return (
    <div className="portrait-gallery">
      {portraits.map((portrait) => (
        <button
          key={portrait.id}
          className={`portrait-gallery-item ${selectedId === portrait.id ? 'selected' : ''}`}
          onClick={() => onSelect(portrait.id)}
        >
          <img src={portrait.url} alt={portrait.name} />
          <span>{portrait.name}</span>
        </button>
      ))}
    </div>
  );
}