import React from "react";

export const Parameters: React.FC = () => {
    return (
        <div className="flex flex-col h-full text-white bg-[#2c2c2c]">
            <div className="flex items-center justify-between px-4 h-[40px] border-t border-[#555] ">
                <div className="flex items-center gap-2 ">
                    Parameters
                </div>


            </div>

            <div className="flex-1 flex items-center justify-center text-[#777] text-sm">
                Select a node to edit parameters
            </div>
        </div>
    );
};