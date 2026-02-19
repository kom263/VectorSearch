import { useState } from "react";

export default function SearchBar({ onSearch, isLoading }) {
    const [query, setQuery] = useState("");
    const [topK, setTopK] = useState(10);

    const handleSubmit = () => {
        if (query.trim() && !isLoading) {
            onSearch(query.trim(), topK);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <section className="p-6 space-y-4">
            <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-700 ml-1">
                    Natural Language Query
                </label>
                <div className="relative group">
                    <textarea
                        className="w-full rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all min-h-[100px] resize-none text-slate-800 outline-none"
                        placeholder="Looking for 2 bedroom under 40k near Pine Street with nearby school"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                    <div className="absolute bottom-3 right-3 flex items-center gap-1 text-slate-400">
                        <span className="material-symbols-outlined text-sm">
                            auto_awesome
                        </span>
                        <span className="text-[10px] font-bold uppercase tracking-tighter">
                            AI Ready
                        </span>
                    </div>
                </div>
            </div>

            <div className="flex gap-3 items-end">
                <div className="flex-1 space-y-2">
                    <label className="text-sm font-semibold text-slate-700 ml-1">
                        Top-K Results
                    </label>
                    <div className="relative">
                        <select
                            className="w-full rounded-xl border border-slate-200 bg-slate-50 text-sm py-2.5 pl-4 pr-10 appearance-none focus:ring-2 focus:ring-primary/20 outline-none"
                            value={topK}
                            onChange={(e) => setTopK(parseInt(e.target.value))}
                        >
                            <option value={5}>Top 5 Matches</option>
                            <option value={10}>Top 10 Matches</option>
                            <option value={25}>Top 25 Matches</option>
                            <option value={50}>Top 50 Matches</option>
                        </select>
                        <span className="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                            expand_more
                        </span>
                    </div>
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={isLoading || !query.trim()}
                    className="bg-primary hover:bg-primary/90 disabled:opacity-50 text-white rounded-xl h-[42px] px-6 flex items-center justify-center gap-2 transition-all font-semibold shadow-lg shadow-primary/20 active:scale-95 cursor-pointer disabled:cursor-not-allowed"
                >
                    <span
                        className={`material-symbols-outlined text-lg ${isLoading ? "animate-spin" : ""
                            }`}
                    >
                        {isLoading ? "progress_activity" : "search"}
                    </span>
                    <span>{isLoading ? "Searching..." : "Search"}</span>
                </button>
            </div>
        </section>
    );
}
