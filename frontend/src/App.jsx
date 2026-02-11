import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import LoadingSpinner from './components/LoadingSpinner';

const HomePage = lazy(() => import('./pages/HomePage'));
const SearchResultsPage = lazy(() => import('./pages/SearchResultsPage'));
const CategoryDetailPage = lazy(() => import('./pages/CategoryDetailPage'));
const CategoriesPage = lazy(() => import('./pages/CategoriesPage'));
const ReportPage = lazy(() => import('./pages/ReportPage'));
const LearnPage = lazy(() => import('./pages/LearnPage'));
const ArticlePage = lazy(() => import('./pages/ArticlePage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Suspense fallback={<LoadingSpinner />}><HomePage /></Suspense>} />
            <Route path="/search" element={<Suspense fallback={<LoadingSpinner />}><SearchResultsPage /></Suspense>} />
            <Route path="/category/:slug" element={<Suspense fallback={<LoadingSpinner />}><CategoryDetailPage /></Suspense>} />
            <Route path="/categories" element={<Suspense fallback={<LoadingSpinner />}><CategoriesPage /></Suspense>} />
            <Route path="/report" element={<Suspense fallback={<LoadingSpinner />}><ReportPage /></Suspense>} />
            <Route path="/learn" element={<Suspense fallback={<LoadingSpinner />}><LearnPage /></Suspense>} />
            <Route path="/learn/:slug" element={<Suspense fallback={<LoadingSpinner />}><ArticlePage /></Suspense>} />
            <Route path="/about" element={<Suspense fallback={<LoadingSpinner />}><AboutPage /></Suspense>} />
            <Route path="*" element={<Suspense fallback={<LoadingSpinner />}><NotFoundPage /></Suspense>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
