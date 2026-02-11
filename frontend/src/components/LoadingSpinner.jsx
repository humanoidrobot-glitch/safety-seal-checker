export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="h-10 w-10 border-4 border-blue-200 border-t-blue-700 rounded-full animate-spin" />
      <p className="mt-4 text-gray-500 text-sm">{message}</p>
    </div>
  );
}
