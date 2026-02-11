import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorState from '../components/ErrorState';
import { getArticle } from '../lib/api';

/**
 * Basic markdown-to-HTML renderer.
 * Handles headings, bold, links, bullet lists, numbered lists,
 * horizontal rules, and paragraphs.
 */
function renderMarkdown(md) {
  if (!md) return '';

  const lines = md.split('\n');
  const htmlParts = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Blank line — skip
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Horizontal rule
    if (/^---+\s*$/.test(line.trim())) {
      htmlParts.push('<hr class="my-6 border-gray-200" />');
      i++;
      continue;
    }

    // Headings
    if (line.startsWith('### ')) {
      htmlParts.push(`<h3 class="text-lg font-semibold text-gray-900 mt-6 mb-3">${inlineFormat(line.slice(4))}</h3>`);
      i++;
      continue;
    }
    if (line.startsWith('## ')) {
      htmlParts.push(`<h2 class="text-xl font-bold text-gray-900 mt-8 mb-3">${inlineFormat(line.slice(3))}</h2>`);
      i++;
      continue;
    }

    // Unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ''));
        i++;
      }
      htmlParts.push(
        `<ul class="list-disc list-inside space-y-1.5 my-4 text-gray-700">${items.map((item) => `<li>${inlineFormat(item)}</li>`).join('')}</ul>`
      );
      continue;
    }

    // Ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ''));
        i++;
      }
      htmlParts.push(
        `<ol class="list-decimal list-inside space-y-1.5 my-4 text-gray-700">${items.map((item) => `<li>${inlineFormat(item)}</li>`).join('')}</ol>`
      );
      continue;
    }

    // Paragraph — collect consecutive non-special lines
    const paraLines = [];
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].startsWith('## ') &&
      !lines[i].startsWith('### ') &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !/^---+\s*$/.test(lines[i].trim())
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      htmlParts.push(`<p class="text-gray-700 leading-relaxed my-4">${inlineFormat(paraLines.join(' '))}</p>`);
    }
  }

  return htmlParts.join('\n');
}

/**
 * Handle inline formatting: bold, links.
 */
function inlineFormat(text) {
  // Escape basic HTML
  let result = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Bold: **text**
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');

  // Links: [text](url)
  result = result.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" class="text-blue-700 underline hover:text-blue-900" target="_blank" rel="noopener noreferrer">$1</a>'
  );

  return result;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export default function ArticlePage() {
  const { slug } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(null);

  function fetchArticle() {
    setLoading(true);
    setError(null);
    setNotFound(false);
    getArticle(slug)
      .then((data) => {
        if (data === null) {
          setNotFound(true);
        } else {
          setArticle(data);
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load article');
      })
      .finally(() => {
        setLoading(false);
      });
  }

  useEffect(() => {
    fetchArticle();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <LoadingSpinner message="Loading article..." />
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Article Not Found</h2>
        <p className="text-gray-600 mb-8">
          The article you are looking for does not exist or may have been removed.
        </p>
        <Link
          to="/learn"
          className="inline-block px-6 py-3 bg-blue-700 text-white rounded-lg hover:bg-blue-800 transition-colors font-medium"
        >
          Back to Learn
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <ErrorState
          title="Could not load article"
          message={error}
          onRetry={fetchArticle}
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      {/* Back Link */}
      <Link
        to="/learn"
        className="inline-flex items-center text-sm font-medium text-blue-700 hover:text-blue-900 transition-colors mb-8"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Learn
      </Link>

      {/* Article Header */}
      <article>
        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4 leading-tight">
          {article.title}
        </h1>
        {article.meta_description && (
          <p className="text-lg text-gray-600 mb-8 leading-relaxed border-l-4 border-blue-200 pl-4">
            {article.meta_description}
          </p>
        )}

        {/* Article Content */}
        <div
          className="article-content"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(article.content) }}
        />

        {/* Published Date */}
        <div className="mt-10 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Published {formatDate(article.created_at)}
            {article.updated_at && article.updated_at !== article.created_at && (
              <span> &middot; Updated {formatDate(article.updated_at)}</span>
            )}
          </p>
        </div>
      </article>
    </div>
  );
}
