import type { SearchResult } from "../types";
import { API_BASE_URL } from "../api/client";

interface Props {
    result: SearchResult;
    rank: number;
}


export default function ResultCard({ result, rank }: Props) {
    const { metadata, score } = result;


    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition">
            <div className="bg-gray-50 px-4 py-2 flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">
                    Result {rank} - Page {metadata.page} of {metadata.total_pages}
                </span>
                <span className="text-xs text-blue-600 font-semibold">
                    Score: {score.toFixed(4)}
                </span>
            </div>

            <div className="p-4">
                <img
                    src={`${API_BASE_URL}/api/v1/images/${metadata.image_name}`}
                    alt={`Page ${metadata.page}`}
                    className="w-full rounded-lg border border-gray-100"
                    loading="lazy"
                />
            </div>

            <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-500">
                Source: {metadata.source}
            </div>
        </div>
    );
}