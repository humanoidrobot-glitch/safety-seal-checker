import { useState, useEffect, useMemo } from 'react';
import SearchBar from '../components/SearchBar';
import CategoryCard from '../components/CategoryCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { getCategories } from '../lib/api';

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sealFilter, setSealFilter] = useState('all');
  const [parentFilter, setParentFilter] = useState('all');

  function fetchCategories() {
    setLoading(true);
    setError(null);
    getCategories()
      .then((data) => {
        setCategories(data || []);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load categories');
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchCategories();
  }, []);

  // Build parent category list for the filter dropdown
  const parentCategories = useMemo(() => {
    const parents = categories.filter(
      (cat) =>
        cat.parent_category_id === null ||
        cat.parent_category_id === undefined
    );
    return parents;
  }, [categories]);

  // Determine which categories are children of which parent
  const parentMap = useMemo(() => {
    const map = {};
    for (const cat of categories) {
      if (
        cat.parent_category_id === null ||
        cat.parent_category_id === undefined
      ) {
        if (!map[cat.id]) {
          map[cat.id] = { parent: cat, children: [] };
        } else {
          map[cat.id].parent = cat;
        }
      }
    }
    for (const cat of categories) {
      if (cat.parent_category_id) {
        if (!map[cat.parent_category_id]) {
          map[cat.parent_category_id] = { parent: null, children: [] };
        }
        map[cat.parent_category_id].children.push(cat);
      }
    }
    return map;
  }, [categories]);

  // Apply filters
  const filteredGroups = useMemo(() => {
    let groupIds = Object.keys(parentMap);

    // Filter by parent category
    if (parentFilter !== 'all') {
      groupIds = groupIds.filter((id) => id === parentFilter);
    }

    return groupIds
      .map((id) => {
        const group = parentMap[id];
        if (!group || !group.parent) return null;

        // Collect all categories in this group (parent + children)
        let groupCategories = [group.parent, ...group.children];

        // Apply seal filter
        if (sealFilter === 'requires') {
          groupCategories = groupCategories.filter(
            (cat) => cat.requires_seal === true
          );
        } else if (sealFilter === 'not-required') {
          groupCategories = groupCategories.filter(
            (cat) => cat.requires_seal === false
          );
        }

        if (groupCategories.length === 0) return null;

        return {
          parent: group.parent,
          categories: groupCategories,
        };
      })
      .filter(Boolean);
  }, [parentMap, parentFilter, sealFilter]);

  // Flat filtered list for when a specific parent or seal filter is active
  const isGrouped = parentFilter === 'all' && sealFilter === 'all';

  const flatFilteredCategories = useMemo(() => {
    if (isGrouped) return [];
    return filteredGroups.flatMap((group) => group.categories);
  }, [filteredGroups, isGrouped]);

  const totalCount = isGrouped
    ? categories.length
    : flatFilteredCategories.length;

  return (
    <>
      {/* Page Header */}
      <section className="bg-gradient-to-br from-blue-800 to-blue-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-14 sm:py-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">
            Browse Product Categories
          </h1>
          <p className="text-lg text-blue-100 mb-8 max-w-2xl mx-auto">
            Explore all product categories to learn which ones require
            tamper-evident packaging under federal regulations.
          </p>
          <SearchBar />
        </div>
      </section>

      {/* Filters & Content */}
      <section className="max-w-6xl mx-auto px-4 py-10">
        {loading && <LoadingSpinner message="Loading categories..." />}

        {error && (
          <ErrorState
            title="Could not load categories"
            message={error}
            onRetry={fetchCategories}
          />
        )}

        {!loading && !error && (
          <>
            {/* Filter Controls */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8">
              {/* Parent Category Filter */}
              <div className="flex items-center gap-2">
                <label
                  htmlFor="parent-filter"
                  className="text-sm font-medium text-gray-700 whitespace-nowrap"
                >
                  Category:
                </label>
                <select
                  id="parent-filter"
                  value={parentFilter}
                  onChange={(e) => setParentFilter(e.target.value)}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All Categories</option>
                  {parentCategories.map((parent) => (
                    <option key={parent.id} value={parent.id}>
                      {parent.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Seal Requirement Filter */}
              <div className="flex items-center gap-2">
                <label
                  htmlFor="seal-filter"
                  className="text-sm font-medium text-gray-700 whitespace-nowrap"
                >
                  Seal requirement:
                </label>
                <select
                  id="seal-filter"
                  value={sealFilter}
                  onChange={(e) => setSealFilter(e.target.value)}
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">All</option>
                  <option value="requires">Requires Seal</option>
                  <option value="not-required">May Not Require</option>
                </select>
              </div>

              {/* Result Count */}
              <span className="text-sm text-gray-500 sm:ml-auto">
                {totalCount} {totalCount === 1 ? 'category' : 'categories'}
              </span>
            </div>

            {/* Grouped View */}
            {isGrouped ? (
              <div className="space-y-10">
                {filteredGroups.map((group) => (
                  <div key={group.parent.id}>
                    <div className="flex items-center gap-3 mb-4">
                      <h2 className="text-xl font-bold text-gray-900">
                        {group.parent.name}
                      </h2>
                      {group.parent.regulation_code && (
                        <span className="text-xs font-medium text-blue-700 bg-blue-50 rounded-full px-2.5 py-0.5">
                          {group.parent.regulation_code}
                        </span>
                      )}
                    </div>
                    {group.parent.description && (
                      <p className="text-sm text-gray-600 mb-4 max-w-3xl">
                        {group.parent.description}
                      </p>
                    )}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {group.categories.map((cat) => (
                        <CategoryCard key={cat.id} category={cat} />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              /* Flat Filtered View */
              <>
                {flatFilteredCategories.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {flatFilteredCategories.map((cat) => (
                      <CategoryCard key={cat.id} category={cat} />
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-12 w-12 text-gray-300 mx-auto mb-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={1.5}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                      />
                    </svg>
                    <p className="text-gray-500 text-lg font-medium mb-2">
                      No categories match your filters
                    </p>
                    <p className="text-gray-400 text-sm mb-6">
                      Try changing the category or seal requirement filter.
                    </p>
                    <button
                      onClick={() => {
                        setParentFilter('all');
                        setSealFilter('all');
                      }}
                      className="text-sm font-medium text-blue-700 hover:text-blue-800 transition-colors"
                    >
                      Clear all filters
                    </button>
                  </div>
                )}
              </>
            )}

            {!loading && !error && categories.length === 0 && (
              <p className="text-center text-gray-500 py-8">
                No categories available at this time.
              </p>
            )}
          </>
        )}
      </section>
    </>
  );
}
