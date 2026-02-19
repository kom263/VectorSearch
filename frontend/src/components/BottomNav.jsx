export default function BottomNav() {
    return (
        <nav className="sticky bottom-0 bg-white/90 backdrop-blur-md border-t border-slate-100 px-6 py-3 pb-6">
            <div className="flex justify-between items-center">
                <a className="flex flex-col items-center gap-1 text-primary" href="#">
                    <span className="material-symbols-outlined">search</span>
                    <span className="text-[10px] font-bold uppercase tracking-widest">
                        Search
                    </span>
                </a>
                <a
                    className="flex flex-col items-center gap-1 text-slate-400 hover:text-primary transition-colors"
                    href="#"
                >
                    <span className="material-symbols-outlined">favorite</span>
                    <span className="text-[10px] font-bold uppercase tracking-widest">
                        Saved
                    </span>
                </a>
                <a
                    className="flex flex-col items-center gap-1 text-slate-400 hover:text-primary transition-colors"
                    href="#"
                >
                    <span className="material-symbols-outlined">history</span>
                    <span className="text-[10px] font-bold uppercase tracking-widest">
                        History
                    </span>
                </a>
                <a
                    className="flex flex-col items-center gap-1 text-slate-400 hover:text-primary transition-colors"
                    href="#"
                >
                    <span className="material-symbols-outlined">person</span>
                    <span className="text-[10px] font-bold uppercase tracking-widest">
                        Profile
                    </span>
                </a>
            </div>
        </nav>
    );
}
