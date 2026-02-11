import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCategory } from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import CategoryCard from '../components/CategoryCard';

export default function CategoryDetailPage() {
  const { slug } = useParams();
  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  function fetchCategory() {
    setLoading(true);
    setError(null);
    setNotFound(false);
    getCategory(slug)
      .then((data) => {
        if (!data) {
          setNotFound(true);
        } else {
          setCategory(data);
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load category');
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchCategory();
    window.scrollTo(0, 0);
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12">
        <LoadingSpinner message="Loading category details..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12">
        <ErrorState
          title="Could not load category"
          message={error}
          onRetry={fetchCategory}
        />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24 text-center">
        <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          Category Not Found
        </h2>
        <p className="text-gray-600 mb-8">
          We couldn't find a product category matching "{slug}". It may have
          been removed or the URL may be incorrect.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/categories"
            className="inline-block px-6 py-3 bg-blue-700 text-white rounded-lg hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors font-medium"
          >
            Browse All Categories
          </Link>
          <Link
            to="/"
            className="inline-block px-6 py-3 bg-white text-blue-700 border border-blue-700 rounded-lg hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors font-medium"
          >
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  const requiresSeal = category.requires_seal;

  // Determine related categories: children if this is a parent, or siblings via parent
  const relatedCategories =
    category.children && category.children.length > 0
      ? category.children
      : [];

  return (
    <>
      {/* Status Banner */}
      {requiresSeal ? (
        <section className="bg-green-50 border-b-2 border-green-200">
          <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-8 w-8 text-green-600"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.535L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <p className="text-lg sm:text-xl font-bold text-green-800">
                  This product requires tamper-evident packaging
                </p>
                <p className="text-green-700 mt-1 text-sm sm:text-base">
                  Federal regulation {category.regulation_code} requires
                  tamper-evident packaging for this product category.
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : (
        <section className="bg-amber-50 border-b-2 border-amber-200">
          <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 mt-0.5">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-8 w-8 text-amber-500"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <p className="text-lg sm:text-xl font-bold text-amber-800">
                  This product may not require tamper-evident packaging
                </p>
                <p className="text-amber-700 mt-1 text-sm sm:text-base">
                  No federal regulation currently mandates tamper-evident
                  packaging for this product category. However, manufacturers
                  may still choose to include one.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Breadcrumb */}
      <nav
        className="max-w-6xl mx-auto px-4 py-4"
        aria-label="Breadcrumb"
      >
        <ol className="flex flex-wrap items-center gap-1.5 text-sm text-gray-500">
          <li>
            <Link to="/" className="hover:text-blue-700 transition-colors">
              Home
            </Link>
          </li>
          <li aria-hidden="true">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </li>
          <li>
            <Link
              to="/categories"
              className="hover:text-blue-700 transition-colors"
            >
              Categories
            </Link>
          </li>
          {category.parent && (
            <>
              <li aria-hidden="true">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </li>
              <li>
                <Link
                  to={`/category/${category.parent.slug}`}
                  className="hover:text-blue-700 transition-colors"
                >
                  {category.parent.name}
                </Link>
              </li>
            </>
          )}
          <li aria-hidden="true">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </li>
          <li className="text-gray-900 font-medium" aria-current="page">
            {category.name}
          </li>
        </ol>
      </nav>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 pb-16">
        <div className="flex flex-col lg:flex-row gap-8 lg:gap-12">
          {/* Left Column - Main Content */}
          <div className="lg:w-2/3">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              {category.name}
            </h1>

            {category.description && (
              <p className="text-lg text-gray-600 leading-relaxed mb-8">
                {category.description}
              </p>
            )}

            {/* Regulation Section */}
            {requiresSeal && category.regulation_code && (
              <section className="mb-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6 text-blue-700"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"
                    />
                  </svg>
                  What Regulation Requires It
                </h2>
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="mb-4">
                    <span className="inline-block text-sm font-semibold text-blue-700 bg-blue-50 rounded-full px-3 py-1">
                      {category.regulation_code}
                    </span>
                  </div>
                  {category.regulation_name && (
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {category.regulation_name}
                    </h3>
                  )}
                  {category.regulation_summary && (
                    <p className="text-gray-600 leading-relaxed mb-4">
                      {category.regulation_summary}
                    </p>
                  )}
                  {category.source_url ? (
                    <a
                      href={category.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-800 transition-colors"
                    >
                      View full regulation
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4 ml-1"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                        />
                      </svg>
                    </a>
                  ) : (
                    <p className="text-sm text-gray-500">
                      Reference: {category.regulation_code}
                    </p>
                  )}
                </div>
              </section>
            )}

            {/* What to Look For Section */}
            {(category.seal_description ||
              (category.seal_types && category.seal_types.length > 0)) && (
              <section className="mb-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6 text-blue-700"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  What to Look For
                </h2>
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  {category.seal_description && (
                    <p className="text-gray-600 leading-relaxed mb-4">
                      {category.seal_description}
                    </p>
                  )}
                  {category.seal_types && category.seal_types.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-3">
                        Common seal types for this category:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {category.seal_types.map((sealType) => (
                          <span
                            key={sealType}
                            className="inline-flex items-center gap-1.5 text-sm font-medium bg-green-50 text-green-700 border border-green-200 rounded-full px-3 py-1.5"
                          >
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-4 w-4"
                              viewBox="0 0 24 24"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M12.516 2.17a.75.75 0 00-1.032 0 11.209 11.209 0 01-7.877 3.08.75.75 0 00-.722.515A12.74 12.74 0 002.25 9.75c0 5.942 4.064 10.933 9.563 12.348a.749.749 0 00.374 0c5.499-1.415 9.563-6.406 9.563-12.348 0-1.39-.223-2.73-.635-3.985a.75.75 0 00-.722-.516 11.209 11.209 0 01-7.877-3.08z"
                                clipRule="evenodd"
                              />
                            </svg>
                            {sealType
                              .split('-')
                              .map(
                                (word) =>
                                  word.charAt(0).toUpperCase() + word.slice(1)
                              )
                              .join(' ')}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* What to Do If Seal Is Missing Section */}
            <section className="mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6 text-amber-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                  />
                </svg>
                What to Do If the Seal Is Missing
              </h2>
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
                {category.what_to_do ? (
                  <p className="text-amber-900 leading-relaxed mb-4">
                    {category.what_to_do}
                  </p>
                ) : (
                  <p className="text-amber-900 leading-relaxed mb-4">
                    If you find a product with a broken or missing safety seal,
                    do not use the product. Return it to the place of purchase
                    or contact the manufacturer. You can also report it to the
                    FDA.
                  </p>
                )}
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 pt-3 border-t border-amber-200">
                  <div className="flex items-center gap-2 text-sm text-amber-800">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5 flex-shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z"
                      />
                    </svg>
                    <span className="font-semibold">FDA MedWatch:</span>{' '}
                    <a
                      href="tel:1-800-332-1088"
                      className="font-semibold hover:underline"
                    >
                      1-800-FDA-1088
                    </a>
                  </div>
                  <Link
                    to="/report"
                    className="inline-flex items-center text-sm font-semibold text-amber-800 hover:text-amber-900 underline transition-colors"
                  >
                    Report online
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4 ml-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
                      />
                    </svg>
                  </Link>
                </div>
              </div>
            </section>
          </div>

          {/* Right Column - Sidebar */}
          <div className="lg:w-1/3 space-y-6">
            {/* Keywords Card */}
            {category.keywords && category.keywords.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 6h.008v.008H6V6z"
                    />
                  </svg>
                  Product Keywords
                </h3>
                <div className="flex flex-wrap gap-2">
                  {category.keywords.map((keyword) => (
                    <Link
                      key={keyword}
                      to={`/search?q=${encodeURIComponent(keyword)}`}
                      className="inline-block text-sm bg-gray-100 text-gray-700 hover:bg-blue-50 hover:text-blue-700 rounded-full px-3 py-1 transition-colors border border-gray-200 hover:border-blue-200"
                    >
                      {keyword}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Related Categories Card */}
            {relatedCategories.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
                    />
                  </svg>
                  {category.children && category.children.length > 0
                    ? 'Subcategories'
                    : 'Related Categories'}
                </h3>
                <div className="space-y-3">
                  {relatedCategories.map((related) => (
                    <CategoryCard key={related.id} category={related} />
                  ))}
                </div>
              </div>
            )}

            {/* Parent Category Link (if this is a child) */}
            {category.parent && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-3">
                  Parent Category
                </h3>
                <Link
                  to={`/category/${category.parent.slug}`}
                  className="flex items-center gap-2 text-blue-700 hover:text-blue-800 font-medium transition-colors"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
                    />
                  </svg>
                  {category.parent.name}
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <section className="bg-blue-50 border-t border-blue-100">
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-3">
            Found a product with a missing seal?
          </h2>
          <p className="text-gray-600 mb-6 max-w-xl mx-auto">
            If you've purchased a product that should have tamper-evident
            packaging but doesn't, let us know so we can help.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/report"
              className="inline-flex items-center px-6 py-3 bg-blue-800 text-white font-semibold rounded-lg hover:bg-blue-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                />
              </svg>
              Report a Product
            </Link>
            <Link
              to="/categories"
              className="inline-flex items-center px-6 py-3 bg-white text-blue-800 font-semibold rounded-lg border-2 border-blue-800 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
            >
              Browse All Categories
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
