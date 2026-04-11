interface SideBar1Props {
    activePanel: string | null;
    setActivePanel: (panel: string | null) => void;
}

export const SideBar1 = ({ activePanel, setActivePanel }: SideBar1Props) => {
    const toggle = (label: string) => {
        setActivePanel(activePanel === label ? null : label);
    };

    const btnClass = (label: string) =>
        `flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${activePanel === label
            ? "bg-[#555555] text-white"
            : "text-[#aaaaaa] hover:bg-[#555555] hover:text-white"
        }`;

    return (
        <div className="flex flex-col items-center gap-1 pt-3   border-t-[1px] border-[#555555] ">
            <button onClick={() => toggle("processes")} className={btnClass("processes")} aria-label="processes">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
                </svg>
            </button>

            <button onClick={() => toggle("algorithms")} className={btnClass("algorithms")} aria-label="algorithms">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
                </svg>
            </button>


            <button onClick={() => toggle("history")} className={btnClass("history")} aria-label="history">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
            </button>

        </div>
    );
};