import { useState, useEffect, useCallback } from "react";
import Header from "./components/Header";
import SearchBar from "./components/SearchBar";
import QueryPanel from "./components/QueryPanel";
import PropertyCard from "./components/PropertyCard";
import DetailModal from "./components/DetailModal";
import BottomNav from "./components/BottomNav";
import { searchProperties } from "./api";

export default function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [searchData, setSearchData] = useState(null);
  const [error, setError] = useState(null);
  const [detailResult, setDetailResult] = useState(null);
  const [detailIndex, setDetailIndex] = useState(0);

  const handleSearch = useCallback(async (query, topK) => {
    setIsLoading(true);
    setError(null);
    setSearchData(null);
    try {
      const data = await searchProperties(query, topK);
      setSearchData(data);
    } catch (err) {
      setError("Could not connect to API. Make sure the backend is running on port 8000.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const openDetail = useCallback((result, index) => {
    setDetailResult(result);
    setDetailIndex(index);
  }, []);

  const closeDetail = useCallback(() => {
    setDetailResult(null);
  }, []);

  // Close modals on Escape
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") closeDetail();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [closeDetail]);

  const results = searchData?.results || [];
  const hasResults = results.length > 0;
  const searched = searchData !== null || error !== null;

  return (
    <div className="w-full bg-white min-h-screen flex flex-col">
      <Header />
      <SearchBar onSearch={handleSearch} isLoading={isLoading} />

      {/* Query Understanding Panel */}
      {searchData?.parsed_query && (
        <QueryPanel parsedQuery={searchData.parsed_query} />
      )}

      {/* Results Area */}
      <section className="p-6 flex-1 space-y-6">
        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="flex gap-2">
              <div className="w-3 h-3 bg-primary rounded-full loading-dot" />
              <div className="w-3 h-3 bg-primary rounded-full loading-dot" />
              <div className="w-3 h-3 bg-primary rounded-full loading-dot" />
            </div>
            <p className="text-sm text-slate-500 font-medium">
              Searching with AI...
            </p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !searched && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
            <span className="material-symbols-outlined text-5xl">search</span>
            <p className="text-sm font-medium">Enter a query to start searching</p>
          </div>
        )}

        {/* Error */}
        {!isLoading && error && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-red-400">
            <span className="material-symbols-outlined text-5xl">error</span>
            <p className="text-sm font-medium text-center">{error}</p>
          </div>
        )}

        {/* Results */}
        {!isLoading && hasResults && (
          <>
            <div className="flex items-center justify-between animate-fade-in">
              <h3 className="font-bold text-slate-800">Ranked Results</h3>
              <span className="text-xs text-slate-500 font-medium">
                {searchData.total_results} result
                {searchData.total_results !== 1 ? "s" : ""} found
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.map((result, i) => (
                <PropertyCard
                  key={result.property_id || i}
                  result={result}
                  index={i}
                  onViewDetails={openDetail}
                />
              ))}
            </div>
          </>
        )}

        {/* No results */}
        {!isLoading && searched && !error && !hasResults && (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
            <span className="material-symbols-outlined text-5xl">search_off</span>
            <p className="text-sm font-medium">No properties match your criteria</p>
            <p className="text-xs">Try broadening your search</p>
          </div>
        )}
      </section>

      <BottomNav />

      {/* Detail Modal */}
      {detailResult && (
        <DetailModal
          result={detailResult}
          index={detailIndex}
          onClose={closeDetail}
        />
      )}
    </div>
  );
}
