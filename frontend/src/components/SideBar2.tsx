

interface SideBar2Props {
    activePanel: string | null;
    setActivePanel: (panel: string | null) => void;
}

export const SideBar2 = ({ activePanel, setActivePanel }: SideBar2Props) => {

    const toggle = (label: string) => {
        setActivePanel(activePanel === label ? null : label);
    };

    const btnClass = (label: string) =>
        `flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${activePanel === label
            ? "bg-[#555555] text-white"
            : "text-[#aaaaaa] hover:bg-[#555555] hover:text-white"
        }`;

    return (
        <div className="flex flex-col items-center gap-1 pt-3 bg-[#2c2c2c] h-screen border-t border-[#555]">


            <button
                onClick={() => toggle("parameters")}
                className={btnClass("parameters")}
                aria-label="parameters"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                    strokeWidth={1.5} stroke="currentColor" className="size-5">
                    <path strokeLinecap="round" strokeLinejoin="round"
                        d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 0 1-.657.643 48.39 48.39 0 0 1-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 0 1-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 0 0-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 0 1-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 0 0 .657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 0 1-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.401.604-.401.959v0c0 .333.277.599.61.58a48.1 48.1 0 0 0 5.427-.63 48.05 48.05 0 0 0 .582-4.717.532.532 0 0 0-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.959.401v0c.333 0 .599-.277.58-.61a48.153 48.153 0 0 0-.630-5.427 48.159 48.159 0 0 0-4.716-.582.532.532 0 0 0-.57.533Z"
                    />
                </svg>
            </button>

            <button
                onClick={() => toggle("algorithms")}
                className={btnClass("algorithms")}
                aria-label="algorithms"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                    strokeWidth={1.5} stroke="currentColor" className="size-5">
                    <path strokeLinecap="round" strokeLinejoin="round"
                        d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5"
                    />
                </svg>
            </button>


            <button
                onClick={() => toggle("history")}
                className={btnClass("history")}
                aria-label="history"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                    strokeWidth={1.5} stroke="currentColor" className="size-5">
                    <path strokeLinecap="round" strokeLinejoin="round"
                        d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                    />
                </svg>
            </button>

        </div>
    );
};