import { useState } from "react";
import { searchDocuments } from "../api/client";
import type { SearchResult } from "../types";


interface Props {
    onResults: (results: SearchResult[]) => void;
}

interface ErrorResponse {
    detail?: string;
}


export default function QueryInput({ onResults }: Props) {
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);


    const handleSearch = async () => {
        if (!query.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await searchDocuments(query);
            onResults(response.results);
        } catch (err) {
            const errorResponse = err as { response?: { data?: ErrorResponse } };
            setError(
                errorResponse.response?.data?.detail || "Search failed. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };


    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") {
            handleSearch();
        }
    };


    return (
        <div className="w-full max-w-2xl mx-auto">
            <div className="flex gap-2">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask a question about your document..."
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                    onClick={handleSearch}
                    disabled={!query.trim() || loading}
                    className="bg-blue-600 text-white px-5 py-2 rounded-lg disabled:opacity-50 hover:bg-blue-700 transition text-sm"
                >
                    {loading ? "Searching..." : "Search"}
                </button>
            </div>

            {error && (
                <p className="text-sm text-red-500 mt-2">{error}</p>
            )}
        </div>
    );
}