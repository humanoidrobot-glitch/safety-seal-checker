export default function ErrorState({ title = 'Something went wrong', message = 'Please try again later.', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-4">
      <div className="text-5xl mb-4" aria-hidden="true">&#9888;&#65039;</div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">{title}</h2>
      <p className="text-gray-600 mb-6 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-5 py-2.5 bg-blue-700 text-white rounded-lg hover:bg-blue-800 transition-colors font-medium"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
