import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="bg-gray-100 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">SealCheck</h3>
            <p className="text-sm text-gray-600">Helping consumers verify tamper-evident safety seals on products they purchase.</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Quick Links</h3>
            <ul className="space-y-2 text-sm">
              <li><Link to="/categories" className="text-gray-600 hover:text-blue-700">Browse Categories</Link></li>
              <li><Link to="/learn" className="text-gray-600 hover:text-blue-700">Learn About Safety Seals</Link></li>
              <li><Link to="/report" className="text-gray-600 hover:text-blue-700">Report a Problem</Link></li>
              <li><Link to="/about" className="text-gray-600 hover:text-blue-700">About SealCheck</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li><a href="https://www.fda.gov/safety/medwatch" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-blue-700">FDA MedWatch</a></li>
              <li><a href="tel:1-800-FDA-1088" className="text-gray-600 hover:text-blue-700">1-800-FDA-1088</a></li>
              <li><a href="https://www.cpsc.gov" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-blue-700">CPSC</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-200 pt-6">
          <p className="text-xs text-gray-500 text-center">
            This site is for informational purposes only. Always follow manufacturer guidelines and consult official FDA resources for authoritative guidance. SealCheck is not affiliated with the FDA, CPSC, or any government agency.
          </p>
        </div>
      </div>
    </footer>
  );
}
