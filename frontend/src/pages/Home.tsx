import React, { useState } from "react";
import { Header } from '../components/Header';
import { Algorithms } from "../components/Algorithms";
import { SideBar1 } from "../components/SideBar1";
import { SideBar2 } from "../components/SideBar2";
import { Workspace } from "../components/Workspaces";
import { Parameters } from "../components/Parameters";
import { Processes } from "../components/Processes";

const Home: React.FC = () => {
  const [leftPanel, setLeftPanel] = useState<string | null>("processes");
  const [rightPanel, setRightPanel] = useState<string | null>("parameters");

  return (
    <div className="h-screen w-screen flex flex-col bg-[#2c2c2c] overflow-hidden font-sans">
      <Header />
      <div className="flex flex-1 overflow-hidden">


        <div className="bg-[#3a3a3a] border-r-[1px] border-[#555555] w-[50px] flex-shrink-0 z-10">
          <SideBar1 activePanel={leftPanel} setActivePanel={setLeftPanel} />
        </div>


        {leftPanel && (
          <div className="bg-[#3a3a3a] border-r-[1px] border-[#555555] w-[240px] flex-shrink-0 flex flex-col">
            {leftPanel === "algorithms" && <Algorithms />}
            {leftPanel === "processes" && (
              <Processes />

            )}
            {leftPanel === "history" && <div className="text-white p-4 border-t-[1px] border-[#555555]">History panel</div>}
          </div>
        )}


        <div className="flex-1 flex flex-col bg-[#2c2c2c] relative min-w-0">
          <Workspace />
        </div>

        {rightPanel && (
          <div className="bg-[#3a3a3a] border-l-[1px] border-[#555555] w-[260px] flex-shrink-0 flex flex-col">
            {rightPanel === "parameters" && <Parameters />}
            {rightPanel === "algorithms" && <Algorithms />}
            {rightPanel === "history" && <div className="text-white p-4 bg-[#2c2c2c] h-screen  border-[#555555]">History panel</div>}
          </div>
        )}


        <div className="bg-[#3a3a3a] border-l-[1px] border-[#555555] w-[50px] flex-shrink-0 z-10">
          <SideBar2 activePanel={rightPanel} setActivePanel={setRightPanel} />
        </div>

      </div>
    </div>
  );
};

export default Home;