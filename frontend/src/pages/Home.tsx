import { useEffect, useState } from "react";
import DocumentUpload from "../components/DocumentUpload";
import QueryInput from "../components/QueryInput";
import ResultsList from "../components/ResultsList";
import ClearSession from "../components/ClearSession";
import type { SearchResult, UploadResponse } from "../types";
import { clearSession, getSessionId } from "../api/client";

export default function Home() {
    const [sessionId, setSessionId] = useState<string>("");
    const [uploadSuccess, setUploadSuccess] = useState<UploadResponse | null>(null);
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const initSession = async () => {
            try {
                const id = await getSessionId();
                setSessionId(id);
            } catch (err) {
                console.error("Failed to get session:", err);
            } finally {
                setLoading(false);
            }
        };
        initSession();
    }, []);

    const handleUploadSuccess = (response: UploadResponse) => {
        setUploadSuccess(response);
        setResults([]);
    };

    const handleNewSession = () => {
        setLoading(true);
        clearSession();
        setSessionId("");
        setUploadSuccess(null);
        setResults([]);
        setLoading(false);
        // Get new session ID
        getSessionId().then((newId) => {
            setSessionId(newId);
        });
        
    };

    // Show loading state while fetching initial session
    if (loading) {
        return (
            <main className="min-h-screen bg-gray-50 py-12 px-4">
                <div className="max-w-5xl mx-auto text-center">
                    <p className="text-gray-500">Initializing session...</p>
                </div>
            </main>
        );
    }

    return (
        <main className="min-h-screen bg-gray-50 py-12 px-4">
            <div className="max-w-5xl mx-auto">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex-1" />
                    <h1 className="text-3xl font-bold text-gray-800 text-center">
                        ColPali Document Search
                    </h1>
                    <div className="flex-1 flex justify-end">
                        <ClearSession onClearSession={handleNewSession} />
                    </div>
                </div>

                <p className="text-center text-gray-500 mb-10 text-sm">
                    Upload a PDF and search visually using AI
                </p>

                {sessionId ? (
                    <>
                        <DocumentUpload
                            onUploadSuccess={handleUploadSuccess}
                        />

                        {uploadSuccess && (
                            <div className="mt-6 text-center text-green-600 text-sm">
                                {uploadSuccess.message} ({uploadSuccess.pages} pages ingested)
                            </div>
                        )}

                        <div className="mt-10">
                            <QueryInput
                                onResults={setResults}
                            />
                        </div>

                        <ResultsList results={results} />
                    </>
                ) : (
                    <div className="text-center text-red-500">
                        Failed to create session. Please refresh the page.
                    </div>
                )}
            </div>
        </main>
    );
}