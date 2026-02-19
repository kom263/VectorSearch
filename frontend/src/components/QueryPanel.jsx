import { useState } from "react";
import { capitalize, formatPrice } from "../utils";

const PREF_ICONS = {
    school: "school",
    hospital: "local_hospital",
    metro: "train",
    park: "park",
    calm: "spa",
    transit: "directions_bus",
};

function getPreferenceIcon(pref) {
    for (const [key, icon] of Object.entries(PREF_ICONS)) {
        if (pref.toLowerCase().includes(key)) return icon;
    }
    return "favorite";
}

export default function QueryPanel({ parsedQuery }) {
    const [showJson, setShowJson] = useState(false);

    if (!parsedQuery) return null;

    const pq = parsedQuery;
    const fields = [];

    if (pq.locations?.length > 0) {
        fields.push({
            label: "Location",
            value: pq.locations.map((l) => capitalize(l)).join(", "),
            icon: "location_on",
        });
    }
    if (pq.budget_max) {
        fields.push({
            label: "Max Price",
            value: formatPrice(pq.budget_max),
            icon: "payments",
        });
    }
    if (pq.budget_min) {
        fields.push({
            label: "Min Price",
            value: formatPrice(pq.budget_min),
            icon: "payments",
        });
    }
    if (pq.bedrooms) {
        fields.push({
            label: "Bedrooms",
            value: `${pq.bedrooms} Unit${pq.bedrooms > 1 ? "s" : ""}`,
            icon: "bed",
        });
    }
    if (pq.property_type) {
        fields.push({
            label: "Property Type",
            value: capitalize(pq.property_type),
            icon: "home",
        });
    }
    if (pq.amenities?.length > 0) {
        fields.push({
            label: "Amenities",
            value: pq.amenities.map((a) => capitalize(a.replace(/_/g, " "))).join(", "),
            icon: "check_circle",
        });
    }
    if (pq.preferences?.length > 0) {
        fields.push({
            label: "Preferences",
            value: pq.preferences.map((p) => capitalize(p)).join(", "),
            icon: getPreferenceIcon(pq.preferences[0]),
        });
    }
    if (fields.length === 0) {
        fields.push({ label: "Mode", value: "Pure Semantic Search", icon: "auto_awesome" });
    }

    return (
        <>
            <section className="px-6 py-4 bg-primary/5 border-y border-primary/10 animate-fade-in">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary text-sm">
                            psychology
                        </span>
                        <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wide">
                            Query Understanding Output
                        </h2>
                    </div>
                    <button
                        onClick={() => setShowJson(true)}
                        className="text-[10px] font-bold text-primary bg-white border border-primary/20 px-2 py-1 rounded-md flex items-center gap-1 hover:bg-primary hover:text-white transition-colors cursor-pointer"
                    >
                        <span className="material-symbols-outlined text-xs">code</span>
                        JSON PREVIEW
                    </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                    {fields.map((f, i) => (
                        <div
                            key={i}
                            className="bg-white p-3 rounded-lg border border-slate-100 shadow-sm"
                        >
                            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1 tracking-tight">
                                {f.label}
                            </p>
                            <p className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                                <span className="material-symbols-outlined text-xs text-primary">
                                    {f.icon}
                                </span>
                                {f.value}
                            </p>
                        </div>
                    ))}
                </div>
            </section>

            {/* JSON Modal */}
            {showJson && (
                <div
                    className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-end justify-center"
                    onClick={() => setShowJson(false)}
                >
                    <div
                        className="max-w-lg w-full bg-white rounded-t-2xl shadow-2xl p-6 animate-fade-in max-h-[70vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
                                <span className="material-symbols-outlined text-primary text-sm">
                                    code
                                </span>
                                Parsed Query JSON
                            </h3>
                            <button
                                onClick={() => setShowJson(false)}
                                className="text-slate-400 hover:text-slate-600 cursor-pointer"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>
                        <div className="bg-slate-900 text-green-400 rounded-xl p-4 font-mono">
                            <pre className="text-[11px] leading-relaxed whitespace-pre-wrap break-all">
                                {JSON.stringify(pq, null, 2)}
                            </pre>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
