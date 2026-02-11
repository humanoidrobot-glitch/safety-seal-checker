import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { getArticles } from '../lib/api';

export default function LearnPage() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function fetchArticles() {
    setLoading(true);
    setError(null);
    getArticles()
      .then((data) => {
        setArticles(data || []);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load articles');
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchArticles();
  }, []);

  return (
    <>
      {/* Header Section */}
      <section className="bg-gradient-to-br from-blue-800 to-blue-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">Learn About Safety Seals</h1>
          <p className="text-lg text-blue-100 max-w-2xl mx-auto">
            Understanding tamper-evident packaging helps you protect yourself and your family.
          </p>
        </div>
      </section>

      {/* Articles Grid */}
      <section className="max-w-5xl mx-auto px-4 py-12">
        {loading && <LoadingSpinner message="Loading articles..." />}

        {error && (
          <ErrorState
            title="Could not load articles"
            message={error}
            onRetry={fetchArticles}
          />
        )}

        {!loading && !error && articles.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-500 text-lg">No articles available yet. Check back soon.</p>
          </div>
        )}

        {!loading && !error && articles.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {articles.map((article) => (
              <Link
                key={article.id}
                to={`/learn/${article.slug}`}
                className="group block bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-blue-200 transition-all"
              >
                <h2 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-800 transition-colors">
                  {article.title}
                </h2>
                {article.meta_description && (
                  <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                    {article.meta_description}
                  </p>
                )}
                <span className="text-sm font-medium text-blue-700 group-hover:text-blue-900 transition-colors">
                  Read more &rarr;
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
