"use client";

import { useState } from "react";
import { MessageSquare, ChevronLeft, ChevronRight, Terminal } from "lucide-react";
import { useChatStore } from "@/stores/chat-store";

interface ChunkingStatusPanelProps {
  totalProcessed: number;
  totalChunks: number;
  onToggle?: () => void;
  isOpen?: boolean;
}

export default function ChunkingStatusPanel({
  totalProcessed,
  totalChunks,
  onToggle,
  isOpen = true,
}: ChunkingStatusPanelProps) {
  const [showDetails, setShowDetails] = useState(false);

  const recentUploads = useChatStore((state) => state.recentUploads).slice(0, 5);

  return (
    <div
      className={`chunking-panel ${isOpen ? "open" : "closed"}`}
      style={{
        width: isOpen ? "280px" : "0px",
        minWidth: isOpen ? "280px" : "0px",
        opacity: isOpen ? 1 : 0,
        overflow: "hidden",
        position: "relative",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
      }}
    >
      {/* Panel Header */}
      <div className="status-panel-header">
        <div className="status-header-left">
          <Terminal size={18} className="status-icon" />
          <span className="status-title">Processing</span>
        </div>
        <button
          onClick={onToggle}
          className="status-toggle-btn"
          title={isOpen ? "Hide processing panel" : "Show processing panel"}
        >
          {isOpen ? (
            <ChevronLeft size={20} />
          ) : (
            <ChevronRight size={20} />
          )}
        </button>
      </div>

      {/* Progress Overview */}
      <div className="status-progress-section">
        <div className="progress-header">
          <span className="progress-label">Files Processed</span>
          <span className="progress-count">
            {totalProcessed}/{recentUploads.length || 5}
          </span>
        </div>
        <div className="progress-bar-container">
          <div
            className="progress-bar-fill"
            style={{
              width: recentUploads.length > 0
                ? `${(totalProcessed / recentUploads.length) * 100}%`
                : "0%",
            }}
          />
        </div>
        <div className="progress-stats">
          <span className="stat-item">
            <span className="stat-icon">📊</span>
            <span className="stat-text">{recentUploads.length} files</span>
          </span>
        </div>
      </div>

      {/* Recent Activity */}
      {recentUploads.length > 0 && (
        <div className="status-recent-section">
          <div className="recent-header">
            <MessageSquare size={14} />
            <span className="recent-title">Recent Uploads</span>
            {showDetails && (
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="recent-toggle"
              >
                {showDetails ? "Hide" : "Show"}
              </button>
            )}
          </div>

          {showDetails && (
            <div className="recent-list">
              {recentUploads.map((upload, index) => (
                <div key={index} className="recent-item">
                  <div className="file-icon">
                    <div className={`status-dot ${upload.status}`} />
                  </div>
                  <div className="file-info">
                    <p className="file-name">{upload.fileName}</p>
                    <p className="file-status">
                      {upload.status.replace(/_/g, " ").toUpperCase()}
                    </p>
                    {upload.progress > 0 && upload.progress < 100 && (
                      <div className="file-progress">
                        <div
                          className={`progress-fill ${getStatusColor(
                            upload.status as string
                          )}`}
                          style={{ width: `${upload.progress}%` }}
                        />
                      </div>
                    )}
                    {upload.chunksCreated > 0 && (
                      <p className="file-chunks">
                        {upload.chunksCreated} chunks created
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!showDetails && recentUploads.length > 3 && (
            <p className="recent-hint">
              {recentUploads.length - 3} more uploads...
              <button onClick={() => setShowDetails(true)} className="hint-toggle">
                Show all
              </button>
            </p>
          )}
        </div>
      )}

      {/* Empty State */}
      {recentUploads.length === 0 && isOpen && (
        <div className="status-empty">
          <MessageSquare size={32} className="status-empty-icon" />
          <p className="status-empty-text">No files processed yet</p>
          <p className="status-empty-hint">
            Upload files to see them here
          </p>
        </div>
      )}

      {/* Action Buttons */}
      {isOpen && totalProcessed > 0 && (
        <div className="status-actions">
          <button className="action-btn clear-btn">
            <span>✕</span>
            <span>Clear History</span>
          </button>
          <button className="action-btn action-btn-refresh">
            <span>🔄</span>
            <span>Refresh</span>
          </button>
        </div>
      )}

      {/* Details Footer */}
      {isOpen && (
        <div className="status-footer">
          <p className="footer-hint">
            💡 Files appear here as they're processed and will be used for chat
          </p>
        </div>
      )}
    </div>
  );
}

function getStatusColor(status: string): string {
  const colors = {
    extracting: "bg-orange-500",
    chunking: "bg-blue-500",
    embedding: "bg-purple-500",
    inserting: "bg-green-500",
    completed: "bg-green-500",
    error: "bg-red-500",
  };
  return colors[status as keyof typeof colors] || "bg-gray-500";
}