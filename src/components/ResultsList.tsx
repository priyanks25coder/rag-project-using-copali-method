import type { SearchResult } from "../types";
import ResultCard from "./ResultCard";


interface Props {
    results: SearchResult[];
}


export default function ResultsList({ results }: Props) {
    if (results.length === 0) {
        return (
            <p className="text-center text-gray-500 mt-8">
                No results found.
            </p>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
            {results.map((result, index) => (
                <ResultCard
                    key={result.id}
                    result={result}
                    rank={index + 1}
                />
            ))}
        </div>
    );
}