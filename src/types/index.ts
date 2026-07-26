export type SearchResult = {
    id: string;
    score: number;
    metadata: {
        doc_id: string;
        source: string;
        page: number;
        total_pages: number;
        image_name: string;
        file_type: string;
        user_id: string;
        expires_at: number;
    };
}

export type SearchResponse = {
    query: string;
    results: SearchResult[];
}

export type UploadResponse = {
    message: string;
    doc_id: string;
    pages: number;
    expires_in: string;
}