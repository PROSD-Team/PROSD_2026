import React, { useEffect, useState } from "react";
import { useApi } from "../hooks/useAPI";
import { getStoredUser } from "../lib/session";
import { Store, type PipelineStep } from "../store/Store";
import type { PipelineSummary } from "../types/api";

const parseSteps = (definitionJson: string): PipelineStep[] => {
  try {
    const parsed = JSON.parse(definitionJson) as { steps?: PipelineStep[] };
    if (Array.isArray(parsed)) return parsed as PipelineStep[];
    if (Array.isArray(parsed.steps)) return parsed.steps;
  } catch {
    return [];
  }
  return [];
};

export const Processes: React.FC = () => {
  const { get, post } = useApi();
  const { setPipeline, activePipelineId } = Store();
  const [pipelines, setPipelines] = useState<PipelineSummary[]>([]);

  const userId = getStoredUser()?.id;

  useEffect(() => {
    if (!userId) return;
    const fetchPipelines = async () => {
      const result = await get<PipelineSummary[]>(
        `/api/pipelines?userId=${userId}&ts=${Date.now()}`
      );
      if (result) setPipelines(result);
    };
    fetchPipelines();
  }, [get, activePipelineId, userId]);

  const handleLoad = (pipeline: PipelineSummary) => {
    const steps = parseSteps(pipeline.definitionJson);
    setPipeline(steps, pipeline.name, pipeline.id);
  };

  const handleBranch = async (pipeline: PipelineSummary) => {
    if (!userId) return;
    const name = window.prompt("Назва нового відгалуження", `${pipeline.name} (branch)`);
    if (!name) return;
    const result = await post<PipelineSummary>(
      `/api/pipelines/${pipeline.id}/branch`,
      { userId, name }
    );
    if (result) {
      setPipeline(parseSteps(result.definitionJson), result.name, result.id);
      if (userId) {
        const updated = await get<PipelineSummary[]>(
          `/api/pipelines?userId=${userId}&ts=${Date.now()}`
        );
        if (updated) setPipelines(updated);
      }
    }
  };

  if (!userId) {
    return (
      <div className="text-[#aaa] p-4 text-sm">
        Зареєструйтесь, щоб зберігати пайплайни.
      </div>
    );
  }

  return (
    <div className="text-white border-t border-[#555] h-screen overflow-y-auto">
      <div className="flex items-center justify-between px-4 py-3 text-sm">
        <span>Saved pipelines</span>
        <button
          type="button"
          onClick={() => {
            if (!userId) return;
            get<PipelineSummary[]>(
              `/api/pipelines?userId=${userId}&ts=${Date.now()}`
            ).then((result) => {
              if (result) setPipelines(result);
            });
          }}
          className="text-xs text-[#f28c28] hover:text-[#f6a052]"
        >
          Refresh
        </button>
      </div>
      <div className="flex flex-col gap-3 px-3 pb-4">
        {pipelines.length === 0 && (
          <div className="text-[#777] text-sm">Немає збережених пайплайнів.</div>
        )}
        {pipelines.map((pipeline) => (
          <div
            key={pipeline.id}
            className="rounded-lg border border-[#555] bg-[#2c2c2c] p-3"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold">{pipeline.name}</div>
                {pipeline.parentPipelineId && (
                  <div className="text-xs text-[#888]">
                    Branch from #{pipeline.parentPipelineId}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleLoad(pipeline)}
                  className="rounded bg-[#3b3b3b] px-2 py-1 text-xs"
                >
                  Load
                </button>
                <button
                  type="button"
                  onClick={() => handleBranch(pipeline)}
                  className="rounded bg-[#f28c28] px-2 py-1 text-xs text-white"
                >
                  Branch
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
