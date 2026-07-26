interface ClearSessionProps {
    onClearSession: () => void;
}

export default function ClearSession({ onClearSession }: ClearSessionProps) {
    return (
        <button onClick={onClearSession} className="bg-red-600 text-white px-5 py-2 rounded-lg hover:bg-red-700 transition text-sm">
            Start New Session
        </button>
    );
}
 