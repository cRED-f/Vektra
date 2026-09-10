"use client";

import { create } from "zustand";

export interface FileUploadStatus {
  fileName: string;
  status:
    | "extracting"
    | "chunking"
    | "embedding"
    | "inserting"
    | "completed"
    | "error";
  progress: number;
  chunksCreated: number;
  timestamp: number;
}

export interface ChatStore {
  // Messages
  messages: Array<{ id: string; role: "user" | "assistant"; content: string }>;
  addMessage: (message: { role: "user" | "assistant"; content: string }) => void;
  clearMessages: () => void;

  // Uploads
  recentUploads: FileUploadStatus[];
  addUploadStatus: (upload: FileUploadStatus) => void;
  clearUploads: () => void;
  uploadQueue: number;
  setUploadQueue: (count: number) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        { ...message, id: crypto.randomUUID() },
      ] as ChatStore["messages"],
    })),
  clearMessages: () => set({ messages: [] }),

  recentUploads: [],
  addUploadStatus: (upload) =>
    set((state) => ({
      recentUploads: [upload, ...state.recentUploads].slice(0, 50), // Keep last 50
    })),
  clearUploads: () => set({ recentUploads: [] }),

  uploadQueue: 0,
  setUploadQueue: (count) => set({ uploadQueue: count }),
}));