import React, { useEffect, useState } from "react";
import { useApi } from "../hooks/useAPI";
import { getStoredUser } from "../lib/session";
import type { JobHistoryEntry } from "../types/api";

const formatDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

export const HistoryPanel: React.FC = () => {
  const { get } = useApi();
  const [history, setHistory] = useState<JobHistoryEntry[]>([]);

  const userId = getStoredUser()?.id;

  useEffect(() => {
    if (!userId) return;
    let active = true;
    const fetchHistory = async () => {
      const result = await get<JobHistoryEntry[]>(
        `/api/jobs/history?userId=${userId}&ts=${Date.now()}`
      );
      if (result && active) setHistory(result);
    };
    fetchHistory();
    return () => {
      active = false;
    };
  }, [get, userId]);

  if (!userId) {
    return (
      <div className="text-[#aaa] p-4 text-sm">
        Зареєструйтесь, щоб бачити історію.
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-[#777] p-4 text-sm">
        Історія запусків поки порожня.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 p-4 text-white">
      {history.map((entry) => {
        const steps = entry.pipelineSteps
          .split(",")
          .map((step) => step.trim())
          .filter(Boolean);

        return (
          <div
            key={entry.jobId}
            className="rounded-lg border border-[#555] bg-[#2c2c2c] p-3"
          >
            <div className="flex items-center justify-between text-xs text-[#b6b6b6]">
              <span>{formatDate(entry.createdAt)}</span>
              <span className="uppercase tracking-wide">{entry.status}</span>
            </div>
            <div className="mt-2 text-sm font-semibold">
              {entry.pipelineName || `Pipeline #${entry.jobId}`}
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-[#f28c28]">
              {steps.length > 0 ? (
                steps.map((step, index) => (
                  <span
                    key={`${entry.jobId}-${step}-${index}`}
                    className="rounded bg-[#3b3b3b] px-2 py-1"
                  >
                    {step}
                  </span>
                ))
              ) : (
                <span className="text-[#777]">Без кроків</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
