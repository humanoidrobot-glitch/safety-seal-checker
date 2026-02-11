import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SearchBar({ initialQuery = '', large = false, onSearch }) {
  const [query, setQuery] = useState(initialQuery);
  const navigate = useNavigate();

  function handleSubmit(e) {
    e.preventDefault();
    const q = query.trim();
    if (q.length < 2) return;
    if (onSearch) {
      onSearch(q);
    } else {
      navigate(`/search?q=${encodeURIComponent(q)}`);
    }
  }

  return (
    <form onSubmit={handleSubmit} role="search" aria-label="Product search" className="w-full max-w-2xl mx-auto">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for a product (e.g., Tylenol, eye drops, baby formula)..."
          className={`w-full rounded-xl border border-gray-300 bg-white text-gray-900 placeholder-gray-400 shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:border-blue-500 ${large ? 'px-6 py-4 text-lg' : 'px-4 py-3 text-base'} pr-14`}
          aria-label="Search for a product"
        />
        <button
          type="submit"
          className={`absolute right-2 bg-blue-700 hover:bg-blue-800 text-white rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors ${large ? 'top-2 p-3' : 'top-1.5 p-2.5'}`}
          aria-label="Search"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={large ? 'h-6 w-6' : 'h-5 w-5'} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </div>
    </form>
  );
}
