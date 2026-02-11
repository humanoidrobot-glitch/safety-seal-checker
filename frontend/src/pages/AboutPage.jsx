import { Link } from 'react-router-dom';

export default function AboutPage() {
  return (
    <>
      {/* Header Section */}
      <section className="bg-gradient-to-br from-blue-800 to-blue-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">About SealCheck</h1>
          <p className="text-lg text-blue-100 max-w-2xl mx-auto">
            Empowering consumers with the knowledge to verify tamper-evident safety seals.
          </p>
        </div>
      </section>

      {/* Content Section */}
      <section className="max-w-3xl mx-auto px-4 py-12 space-y-10">
        {/* Mission */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Our Mission</h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            SealCheck helps consumers quickly determine whether a product they are purchasing
            should have a tamper-evident safety seal, and what that seal should look like.
            In 1982, following a series of product tampering incidents, the FDA mandated
            tamper-evident packaging for many over-the-counter products. These regulations
            save lives, but most consumers are unaware of which products require seals and
            what types of seals to expect.
          </p>
          <p className="text-gray-700 leading-relaxed">
            Our goal is to close that knowledge gap. By making regulatory information
            accessible and easy to understand, SealCheck empowers you to make safer
            purchasing decisions and to report products that may have been tampered with.
          </p>
        </div>

        {/* How It Works */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">How It Works</h2>
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-bold text-sm">
                1
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Search for a product</h3>
                <p className="text-gray-600 text-sm">
                  Enter a product name, brand, or category to find relevant seal requirements.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-bold text-sm">
                2
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Review requirements</h3>
                <p className="text-gray-600 text-sm">
                  See what type of tamper-evident seal is required for that product category, including the specific federal regulations that apply.
                </p>
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-800 flex items-center justify-center font-bold text-sm">
                3
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Check your product</h3>
                <p className="text-gray-600 text-sm">
                  Compare the seal on your product with what is expected. If something looks wrong, you can report it directly through our platform.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Data Sources */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Data Sources</h2>
          <p className="text-gray-700 leading-relaxed mb-3">
            SealCheck draws from authoritative public sources to provide accurate, up-to-date information:
          </p>
          <ul className="space-y-2 text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-blue-700 mt-1 flex-shrink-0">&#8226;</span>
              <span>
                <strong className="font-semibold">FDA / eCFR</strong> &mdash; Federal regulations governing tamper-evident packaging, including 21 CFR 211.132 (OTC drugs) and 21 CFR 700.25 (cosmetics).
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-700 mt-1 flex-shrink-0">&#8226;</span>
              <span>
                <strong className="font-semibold">openFDA</strong> &mdash; Product names, brands, and NDC codes used to match consumer products to their regulatory categories.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-700 mt-1 flex-shrink-0">&#8226;</span>
              <span>
                <strong className="font-semibold">CPSC</strong> &mdash; Consumer Product Safety Commission guidance on packaging safety standards.
              </span>
            </li>
          </ul>
        </div>

        {/* Disclaimer */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Disclaimer
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            This site is for informational purposes only. SealCheck is not affiliated with the
            FDA, CPSC, or any government agency. The information provided here should not be
            considered legal or medical advice. Always follow manufacturer guidelines and consult
            official FDA resources for authoritative guidance on product safety. If you suspect
            a product has been tampered with, do not use it and contact the retailer, the manufacturer,
            or the FDA directly.
          </p>
        </div>

        {/* Contact / Contribute */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Get Involved</h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            SealCheck is an open community resource. If you have feedback, notice inaccurate
            information, or want to contribute, we welcome your input.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link
              to="/report"
              className="inline-flex items-center justify-center px-6 py-3 bg-blue-800 text-white font-semibold rounded-lg hover:bg-blue-900 transition-colors"
            >
              Report a Problem
            </Link>
            <Link
              to="/learn"
              className="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-800 font-semibold rounded-lg border-2 border-blue-800 hover:bg-blue-50 transition-colors"
            >
              Read Our Articles
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
