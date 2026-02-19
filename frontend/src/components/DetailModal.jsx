import { getPropertyImage, formatPrice, capitalize } from "../utils";

export default function DetailModal({ result, index, onClose }) {
    if (!result) return null;
    const meta = result.metadata;

    return (
        <div
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-end justify-center"
            onClick={onClose}
        >
            <div
                className="max-w-lg w-full bg-white rounded-t-2xl shadow-2xl max-h-[85vh] overflow-y-auto animate-fade-in"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Image */}
                <div className="h-48 bg-slate-200 overflow-hidden relative">
                    <img
                        alt={result.title}
                        className="w-full h-full object-cover"
                        src={getPropertyImage(index)}
                    />
                    <button
                        onClick={onClose}
                        className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm p-1.5 rounded-full shadow-md hover:bg-white cursor-pointer"
                    >
                        <span className="material-symbols-outlined text-slate-700 text-xl">
                            close
                        </span>
                    </button>
                    <div className="absolute top-3 right-3 bg-primary text-white text-[11px] font-bold px-3 py-1.5 rounded-full shadow-lg">
                        {result.relevance_score.toFixed(2)} SCORE
                    </div>
                </div>

                {/* Details */}
                <div className="p-6 space-y-4">
                    {/* Title & Price */}
                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-lg font-bold text-slate-900">{result.title}</h3>
                            <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                                <span className="material-symbols-outlined text-sm">location_on</span>
                                {meta.address || meta.neighborhood || ""}
                                {meta.city ? `, ${meta.city}` : ""}
                            </p>
                        </div>
                        <p className="text-xl font-bold text-primary">
                            {formatPrice(meta.price)}
                        </p>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-3 gap-3">
                        <div className="bg-slate-50 rounded-xl p-3 text-center">
                            <span className="material-symbols-outlined text-primary mb-1">bed</span>
                            <p className="text-xs font-bold text-slate-700">
                                {meta.bedrooms} Bed{meta.bedrooms !== 1 ? "s" : ""}
                            </p>
                        </div>
                        <div className="bg-slate-50 rounded-xl p-3 text-center">
                            <span className="material-symbols-outlined text-primary mb-1">bathtub</span>
                            <p className="text-xs font-bold text-slate-700">
                                {meta.bathrooms} Bath{meta.bathrooms !== 1 ? "s" : ""}
                            </p>
                        </div>
                        <div className="bg-slate-50 rounded-xl p-3 text-center">
                            <span className="material-symbols-outlined text-primary mb-1">
                                square_foot
                            </span>
                            <p className="text-xs font-bold text-slate-700">{meta.area_sqft} sqft</p>
                        </div>
                    </div>

                    {/* Amenities */}
                    {meta.amenities?.length > 0 && (
                        <div>
                            <p className="text-xs font-bold text-slate-400 uppercase mb-2 tracking-tight">
                                Amenities
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                                {meta.amenities.map((a, i) => (
                                    <span
                                        key={i}
                                        className="bg-primary/10 text-primary text-[11px] font-semibold px-2.5 py-1 rounded-full"
                                    >
                                        {capitalize(a.replace(/_/g, " "))}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Nearby Places */}
                    {meta.nearby_places?.length > 0 && (
                        <div>
                            <p className="text-xs font-bold text-slate-400 uppercase mb-2 tracking-tight">
                                Nearby Places
                            </p>
                            <div className="space-y-2">
                                {meta.nearby_places.map((p, i) =>
                                    typeof p === "string" ? (
                                        <div
                                            key={i}
                                            className="flex items-center gap-2 text-xs text-slate-600"
                                        >
                                            <span className="material-symbols-outlined text-sm text-primary">
                                                place
                                            </span>
                                            {p}
                                        </div>
                                    ) : null
                                )}
                            </div>
                        </div>
                    )}

                    {/* AI Explanation */}
                    <div className="bg-primary/5 rounded-xl p-4 border border-primary/10">
                        <p className="text-xs font-bold text-primary uppercase mb-1">
                            AI Explanation
                        </p>
                        <p className="text-sm text-slate-700">{result.explanation}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
