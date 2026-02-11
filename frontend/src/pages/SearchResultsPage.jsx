import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import CategoryCard from '../components/CategoryCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { search } from '../lib/api';

export default function SearchResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get('q') || '';

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchResults = useCallback(
    (query) => {
      if (!query || query.trim().length < 2) {
        setResults(null);
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      search(query.trim())
        .then((data) => {
          setResults(data);
        })
        .catch((err) => {
          setError(err.message || 'Search failed');
        })
        .finally(() => {
          setLoading(false);
        });
    },
    []
  );

  useEffect(() => {
    fetchResults(q);
  }, [q, fetchResults]);

  function handleSearch(newQuery) {
    setSearchParams({ q: newQuery });
  }

  const categories = results?.categories || [];
  const total = results?.total ?? categories.length;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Search bar at top */}
      <div className="mb-8">
        <SearchBar initialQuery={q} onSearch={handleSearch} />
      </div>

      {/* Short query message */}
      {q.length > 0 && q.trim().length < 2 && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 text-gray-400 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Please enter a longer search term
          </h2>
          <p className="text-gray-500">
            Type at least 2 characters to search for products and categories.
          </p>
        </div>
      )}

      {/* Empty query — prompt to search */}
      {q.length === 0 && (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 text-blue-700 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Search for a product
          </h2>
          <p className="text-gray-500">
            Enter a product name, type, or category to check if it requires a safety seal.
          </p>
        </div>
      )}

      {/* Loading state */}
      {loading && <LoadingSpinner message={`Searching for "${q}"...`} />}

      {/* Error state */}
      {!loading && error && (
        <ErrorState
          title="Search failed"
          message={error}
          onRetry={() => fetchResults(q)}
        />
      )}

      {/* Results */}
      {!loading && !error && results && q.trim().length >= 2 && (
        <>
          <p className="text-sm text-gray-500 mb-6">
            <span className="font-medium text-gray-900">{total}</span>{' '}
            {total === 1 ? 'result' : 'results'} for{' '}
            <span className="font-medium text-gray-900">"{q}"</span>
          </p>

          {categories.length > 0 ? (
            <div className="space-y-3">
              {categories.map((category) => (
                <CategoryCard key={category.id} category={category} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 text-gray-400 mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                No results found
              </h2>
              <p className="text-gray-500 max-w-md mx-auto">
                We couldn't find any products matching "{q}". Try a different
                search term or browse our{' '}
                <Link to="/categories" className="text-blue-700 hover:underline font-medium">
                  categories
                </Link>
                .
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
