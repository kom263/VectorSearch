export default function Header() {
    return (
        <header className="p-6 pb-4 border-b border-slate-100">
            <div className="flex items-center gap-3 mb-2">
                <div className="bg-primary/10 p-2 rounded-lg">
                    <span className="material-symbols-outlined text-primary text-2xl">
                        neurology
                    </span>
                </div>
                <div>
                    <h1 className="text-xl font-bold tracking-tight text-slate-900">
                        AI Semantic Property Search
                    </h1>
                    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                        Vector Search + Intelligent Ranking
                    </p>
                </div>
            </div>
        </header>
    );
}
