import { Link } from 'react-router-dom';

export default function CategoryCard({ category }) {
  return (
    <Link
      to={`/category/${category.slug}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md hover:border-blue-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl mt-0.5" aria-hidden="true">
          {category.requires_seal ? '\u2705' : '\u274C'}
        </span>
        <div className="min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{category.name}</h3>
          {category.description && (
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">{category.description}</p>
          )}
          {category.regulation_code && (
            <span className="inline-block mt-2 text-xs font-medium text-blue-700 bg-blue-50 rounded-full px-2.5 py-0.5">
              {category.regulation_code}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
