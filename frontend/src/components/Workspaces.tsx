import React from "react";

export const Workspace: React.FC = () => {
    return (
        <div className="flex flex-col h-full w-full relative">


            <div className="flex bg-[#2c2c2c] h-[40px]">
                <div className="flex items-center px-4 text-[#777] text-sm">
                    No tabs open
                </div>
            </div>


            <div className="flex-1 relative overflow-hidden flex items-center justify-center">
                <span className="text-[#666] text-sm">
                    Canvas is empty
                </span>
                <button className="absolute bottom-6 right-6 bg-[#f97316] hover:bg-[#ea580c] text-white px-6 py-2 rounded-md font-semibold transition-colors">
                    Run
                </button>
            </div>


            <div className="h-[200px] border-t border-[#555] bg-[#2c2c2c] flex flex-col">
                <div className="px-4 py-2 border-b border-[#333] text-sm text-[#aaa]">
                    Result
                </div>
                <div className="flex-1 p-4 text-[#666] text-sm font-mono">
                    No output yet
                </div>

            </div>
        </div>
    );
};