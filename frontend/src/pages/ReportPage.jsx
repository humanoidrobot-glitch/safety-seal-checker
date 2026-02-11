import { useState } from 'react';
import { submitReport } from '../lib/api';

export default function ReportPage() {
  const [formData, setFormData] = useState({
    product_name: '',
    brand: '',
    upc: '',
    store_name: '',
    store_location: '',
    description: '',
    photo_url: '',
    email: '',
  });

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [success, setSuccess] = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field error on change
    if (errors[name]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  }

  function validate() {
    const newErrors = {};

    if (!formData.product_name.trim()) {
      newErrors.product_name = 'Product name is required.';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required.';
    } else if (formData.description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters.';
    }

    if (formData.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = 'Please enter a valid email address.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError(null);

    if (!validate()) return;

    setSubmitting(true);
    try {
      const result = await submitReport({
        product_name: formData.product_name.trim(),
        brand: formData.brand.trim() || undefined,
        upc: formData.upc.trim() || undefined,
        store_name: formData.store_name.trim() || undefined,
        store_location: formData.store_location.trim() || undefined,
        description: formData.description.trim(),
        photo_url: formData.photo_url.trim() || undefined,
        email: formData.email.trim() || undefined,
      });
      setSuccess(result);
    } catch (err) {
      setSubmitError(err.message || 'Failed to submit report. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16">
        <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 text-green-600 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Thank you for your report</h2>
          <p className="text-gray-600 mb-4">
            Your report has been submitted successfully. Your report ID is:
          </p>
          <p className="text-lg font-mono font-semibold text-green-700 bg-green-100 inline-block px-4 py-2 rounded-lg mb-6">
            #{success.id}
          </p>
          <p className="text-sm text-gray-500 mb-6">
            {success.product_name} {success.brand ? `by ${success.brand}` : ''} — Status: {success.status}
          </p>
          <button
            onClick={() => {
              setSuccess(null);
              setFormData({
                product_name: '',
                brand: '',
                upc: '',
                store_name: '',
                store_location: '',
                description: '',
                photo_url: '',
                email: '',
              });
            }}
            className="px-6 py-3 bg-blue-800 text-white font-semibold rounded-lg hover:bg-blue-900 transition-colors"
          >
            Submit Another Report
          </button>
        </div>
      </div>
    );
  }

  const inputClass = (field) =>
    `w-full px-4 py-2.5 border rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
      errors[field] ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'
    }`;

  return (
    <>
      {/* Header Section */}
      <section className="bg-gradient-to-br from-blue-800 to-blue-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-12 text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">Report a Problem</h1>
          <p className="text-blue-100 text-lg max-w-2xl mx-auto">
            Help protect other consumers by reporting products with missing or broken safety seals.
          </p>
        </div>
      </section>

      {/* Form Section */}
      <section className="max-w-2xl mx-auto px-4 py-10">
        <form onSubmit={handleSubmit} noValidate>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="p-6 sm:p-8 space-y-6">

              {submitError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
                  {submitError}
                </div>
              )}

              {/* Product Name */}
              <div>
                <label htmlFor="product_name" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Product Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="product_name"
                  name="product_name"
                  value={formData.product_name}
                  onChange={handleChange}
                  className={inputClass('product_name')}
                  placeholder="e.g., Tylenol Extra Strength Caplets"
                />
                {errors.product_name && (
                  <p className="mt-1.5 text-sm text-red-600">{errors.product_name}</p>
                )}
              </div>

              {/* Brand */}
              <div>
                <label htmlFor="brand" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Brand
                </label>
                <input
                  type="text"
                  id="brand"
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  className={inputClass('brand')}
                  placeholder="e.g., Johnson & Johnson"
                />
              </div>

              {/* UPC/Barcode */}
              <div>
                <label htmlFor="upc" className="block text-sm font-medium text-gray-700 mb-1.5">
                  UPC/Barcode
                </label>
                <input
                  type="text"
                  id="upc"
                  name="upc"
                  value={formData.upc}
                  onChange={handleChange}
                  className={inputClass('upc')}
                  placeholder="e.g., 012345678901"
                />
                <p className="mt-1.5 text-xs text-gray-500">Found on the product packaging</p>
              </div>

              {/* Store Name and Location - side by side on desktop */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="store_name" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Store Name
                  </label>
                  <input
                    type="text"
                    id="store_name"
                    name="store_name"
                    value={formData.store_name}
                    onChange={handleChange}
                    className={inputClass('store_name')}
                    placeholder="e.g., Walgreens"
                  />
                </div>
                <div>
                  <label htmlFor="store_location" className="block text-sm font-medium text-gray-700 mb-1.5">
                    Store Location
                  </label>
                  <input
                    type="text"
                    id="store_location"
                    name="store_location"
                    value={formData.store_location}
                    onChange={handleChange}
                    className={inputClass('store_location')}
                    placeholder="City, State"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Description of the Issue <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={4}
                  className={inputClass('description')}
                  placeholder="Describe what you noticed about the seal (e.g., missing shrink wrap, broken foil seal, loose cap ring)..."
                />
                {errors.description && (
                  <p className="mt-1.5 text-sm text-red-600">{errors.description}</p>
                )}
              </div>

              {/* Photo URL */}
              <div>
                <label htmlFor="photo_url" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Photo URL
                </label>
                <input
                  type="text"
                  id="photo_url"
                  name="photo_url"
                  value={formData.photo_url}
                  onChange={handleChange}
                  className={inputClass('photo_url')}
                  placeholder="Paste a link to a photo"
                />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className={inputClass('email')}
                  placeholder="your@email.com"
                />
                {errors.email && (
                  <p className="mt-1.5 text-sm text-red-600">{errors.email}</p>
                )}
                <p className="mt-1.5 text-xs text-gray-500">Optional. Used only for follow-up contact about this report.</p>
              </div>

            </div>

            {/* Submit Button */}
            <div className="px-6 sm:px-8 py-5 bg-gray-50 border-t border-gray-200">
              <button
                type="submit"
                disabled={submitting}
                className="w-full sm:w-auto px-8 py-3 bg-blue-800 text-white font-semibold rounded-lg hover:bg-blue-900 transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Report'
                )}
              </button>
            </div>
          </div>
        </form>
      </section>
    </>
  );
}
