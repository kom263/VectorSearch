import { getPropertyImage, extractSchoolDistance, formatPrice, capitalize } from "../utils";

export default function PropertyCard({ result, index, onViewDetails }) {
    const isTop = index === 0;
    const scorePercent = Math.round(result.vector_score * 100);
    const meta = result.metadata;
    const schoolDist = extractSchoolDistance(meta.nearby_places);

    // Parse boost text from explanation
    const explanation = result.explanation || "";
    const boostMatch = explanation.match(/;\s*(.+)$/);
    const boostText = boostMatch ? boostMatch[1].replace(/;/g, " · ") : "";

    return (
        <div
            className="relative bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all overflow-hidden animate-fade-in"
            style={{ animationDelay: `${index * 0.1}s` }}
        >
            {/* Image */}
            <div className={`h-40 bg-slate-200 overflow-hidden relative ${!isTop ? "grayscale-[10%] opacity-95" : ""}`}>
                <img
                    alt={result.title}
                    className="w-full h-full object-cover"
                    src={getPropertyImage(index)}
                    onError={(e) => (e.target.style.display = "none")}
                />
                <div
                    className={`absolute top-3 right-3 ${isTop ? "bg-primary" : "bg-slate-800"
                        } text-white text-[11px] font-bold px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1`}
                >
                    <span className="material-symbols-outlined text-xs">
                        {isTop ? "star" : "trending_up"}
                    </span>
                    {result.relevance_score.toFixed(2)} SCORE
                </div>
            </div>

            {/* Content */}
            <div className="p-4">
                {/* Title & Price */}
                <div className="flex justify-between items-start mb-2">
                    <div>
                        <h4 className="font-bold text-slate-900">{result.title}</h4>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                            <span className="material-symbols-outlined text-xs">location_on</span>
                            {meta.address || meta.neighborhood || ""}
                        </p>
                    </div>
                    <p className="text-lg font-bold text-primary whitespace-nowrap ml-2">
                        {meta.price ? formatPrice(meta.price) : ""}
                    </p>
                </div>

                {/* Quick stats */}
                <div className="flex gap-4 mb-4">
                    <div className="flex items-center gap-1 text-slate-600 text-xs">
                        <span className="material-symbols-outlined text-sm">bed</span>
                        {meta.bedrooms} Bed{meta.bedrooms !== 1 ? "s" : ""}
                    </div>
                    {schoolDist && (
                        <div className="flex items-center gap-1 text-slate-600 text-xs">
                            <span className="material-symbols-outlined text-sm">school</span>
                            {schoolDist} to School
                        </div>
                    )}
                    {meta.area_sqft && (
                        <div className="flex items-center gap-1 text-slate-600 text-xs">
                            <span className="material-symbols-outlined text-sm">square_foot</span>
                            {meta.area_sqft} sqft
                        </div>
                    )}
                </div>

                {/* Ranking Explanation */}
                <div
                    className={`${isTop
                            ? "bg-primary/5 border-primary/10"
                            : "bg-slate-50 border-slate-100"
                        } rounded-lg p-3 mb-4 border`}
                >
                    <div
                        className={`flex justify-between text-[10px] font-bold ${isTop ? "text-primary" : "text-slate-500"
                            } uppercase mb-1`}
                    >
                        <span>Vector Similarity</span>
                        <span>{result.vector_score.toFixed(2)}</span>
                    </div>
                    <div className="w-full bg-slate-200 h-1 rounded-full overflow-hidden mb-2">
                        <div
                            className={`${isTop ? "bg-primary" : "bg-slate-400"} h-full transition-all duration-700`}
                            style={{ width: `${scorePercent}%` }}
                        />
                    </div>
                    <p className="text-[11px] text-slate-600 italic">
                        {boostText ? (
                            <span className={`font-bold ${isTop ? "text-primary" : ""}`}>
                                {boostText}
                            </span>
                        ) : (
                            <span className="text-slate-400">Matched via semantic similarity</span>
                        )}
                    </p>
                </div>

                {/* View Details Button */}
                <button
                    onClick={() => onViewDetails(result, index)}
                    className="w-full bg-slate-100 hover:bg-primary hover:text-white text-slate-700 font-bold py-2.5 rounded-xl transition-all text-sm cursor-pointer active:scale-95"
                >
                    View Details
                </button>
            </div>
        </div>
    );
}
