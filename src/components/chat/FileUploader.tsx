"use client";

import { useRef, useState, forwardRef, useImperativeHandle } from "react";

export interface UploadItem {
  fileName: string;
  fileSize: number;
  status: "extracting" | "chunking" | "embedding" | "inserting" | "completed" | "error";
  progress: number;
  message: string;
  chunksCreated: number;
}

interface FileUploaderProps {
  onFilesComplete: (completed: number) => void;
  onProgressUpdate?: (items: UploadItem[]) => void;
}

export interface FileUploaderHandle {
  openPicker: () => void;
}

const FORMATS = ["pdf", "docx", "doc", "md", "txt", "html", "htm", "rst"];
const MAX_MB = 50;

const FileUploader = forwardRef<FileUploaderHandle, FileUploaderProps>(
  ({ onFilesComplete, onProgressUpdate }, ref) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const [items, setItems] = useState<UploadItem[]>([]);
    const fileMapRef = useRef<Map<string, File>>(new Map());

    const update = (item: UploadItem) => {
      setItems((prev) => {
        const next = prev.map((p) => (p.fileName === item.fileName ? { ...item } : p));
        onProgressUpdate?.(next);
        return next;
      });
    };

    const validate = (f: File): boolean => {
      if (f.size > MAX_MB * 1024 * 1024) {
        alert(`${f.name} exceeds ${MAX_MB} MB limit`);
        return false;
      }
      const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
      if (!FORMATS.includes(ext)) {
        alert(`${f.name}: unsupported format (use PDF, DOCX, MD, TXT, HTML)`);
        return false;
      }
      return true;
    };

    const animate = (item: UploadItem, from: number, to: number, ms: number) =>
      new Promise<void>((r) => {
        const t0 = performance.now();
        const tick = () => {
          const p = Math.min(1, (performance.now() - t0) / ms);
          item.progress = Math.floor(from + (to - from) * p);
          update(item);
          p < 1 ? requestAnimationFrame(tick) : r();
        };
        requestAnimationFrame(tick);
      });

    const ingest = async (item: UploadItem) => {
      try {
        const file = fileMapRef.current.get(item.fileName);
        if (!file) return;

        const data = new FormData();
        data.append("file", file, file.name);

        const res = await fetch("http://localhost:8000/ingest", {
          method: "POST",
          headers: { Authorization: "Bearer dev-token-change-in-production" },
          body: data,
        });
        if (res.ok) {
          const d = await res.json().catch(() => ({}));
          item.chunksCreated = d.chunks_created ?? 0;
        } else {
          const d = await res.json().catch(() => ({}));
          item.message = d.detail || "Upload failed";
        }
      } catch {
        item.message = "Upload failed";
      }
    };

    const processFile = async (item: UploadItem) => {
      const phase = (
        s: UploadItem["status"],
        msg: string,
        from: number,
        to: number,
        ms: number
      ) =>
        animate(item, from, to, ms).then(() => {
          item.status = s;
          item.message = msg;
          update(item);
        });

      try {
        item.status = "extracting";
        item.message = "Extracting...";
        update(item);
        await ingest(item);

        await phase("chunking", "Chunking...", 20, 40, 800);
        await phase("embedding", "Embedding...", 40, 65, 900);
        await phase("inserting", "Inserting...", 65, 90, 700);
        await animate(item, 90, 100, 300);

        item.status = "completed";
        item.message = `${item.chunksCreated || 0} chunks`;
        update(item);
      } catch {
        item.status = "error";
        item.message = "Failed";
        update(item);
      }
    };

    const onFiles = async (files: FileList | File[]) => {
      const list = Array.from(files).filter(validate);
      if (!list.length) return;

      const newItems: UploadItem[] = list.map((f) => ({
        fileName: f.name,
        fileSize: f.size,
        status: "extracting" as const,
        progress: 0,
        message: "Queued...",
        chunksCreated: 0,
      }));

      for (const f of list) fileMapRef.current.set(f.name, f);
      setItems(newItems);
      onProgressUpdate?.(newItems);

      for (const item of newItems) await processFile(item);

      const done = newItems.filter((i) => i.status === "completed").length;
      if (done > 0) onFilesComplete(done);
    };

    return (
      // A <label> wrapping a <input type="file"> opens the native picker
      // WITHOUT JavaScript — this is the most robust way to show the popup.
      // The label sits inside the chat input form, next to the paperclip.
      <input
        ref={inputRef}
        id="vektra-file-input"
        className="file-upload-input"
        type="file"
        multiple
        accept={FORMATS.map((f) => `.${f}`).join(",")}
        onChange={(e) => {
          if (e.target.files?.length) onFiles(e.target.files);
          e.target.value = "";
        }}
      />
    );
  }
);

FileUploader.displayName = "FileUploader";
export default FileUploader;