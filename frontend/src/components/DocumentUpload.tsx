import { useState } from "react";
import { uploadDocument } from "../api/client";
import type { UploadResponse } from "../types";


interface Props {
    onUploadSuccess: (response: UploadResponse) => void;
}

interface ErrorResponse {
    detail?: string;
}


export default function DocumentUpload({ onUploadSuccess }: Props) {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);


    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0];
        if (selected) {
            if (selected.size > 10 * 1024 * 1024) {
                setError("File too large. Max size is 10 MB.");
                return;
            }
            setFile(selected);
            setError(null);
        }
    };


    const handleUpload = async () => {
        if (!file) return;

        setLoading(true);
        setError(null);

        try {
            const response = await uploadDocument(file);
            onUploadSuccess(response);
            setFile(null);
        } catch (err) {
            const errorResponse = err as { response?: { data?: ErrorResponse } };
            setError(
                errorResponse.response?.data?.detail || "Upload failed. Please try again."
            );
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="w-full max-w-lg mx-auto p-6 border-2 border-dashed border-gray-300 rounded-xl text-center">
            <p className="text-lg font-semibold text-gray-700 mb-4">
                Upload PDF Document
            </p>

            <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 mb-4"
            />

            {file && (
                <p className="text-sm text-gray-600 mb-4">
                    Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
            )}

            {error && (
                <p className="text-sm text-red-500 mb-4">{error}</p>
            )}

            <button
                onClick={handleUpload}
                disabled={!file || loading}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg disabled:opacity-50 hover:bg-blue-700 transition"
            >
                {loading ? "Uploading..." : "Upload"}
            </button>

            <p className="text-xs text-gray-400 mt-3">
                Max file size: 10 MB. Max pages: 20. Documents expire after 24 hours.
            </p>
        </div>
    );
}