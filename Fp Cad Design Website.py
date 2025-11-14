
// "Homepage Updated" — Launch-ready Next.js React component
// Uses: Tailwind CSS, Framer Motion, Google reCAPTCHA v3 (invisible), Formspree, optional Slack and Sheets integrations.

import Head from 'next/head';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

// Small inline Logo component (kept local for single-file deploy)
function Logo({ className = 'w-10 h-10' }) {
  return (
    <svg className={className} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <rect x="2" y="2" width="96" height="96" rx="12" fill="#0F4C81" />
      <g transform="translate(18,22)" fill="#fff">
        <path d="M6 50 L18 10 L30 50 Z" />
        <rect x="36" y="10" width="8" height="40" rx="2" />
        <rect x="54" y="10" width="8" height="40" rx="2" />
      </g>
    </svg>
  );
}

export default function HomePage() {
  const [submitted, setSubmitted] = useState(false);
  const [recaptchaLoaded, setRecaptchaLoaded] = useState(false);
  const [recaptchaKey, setRecaptchaKey] = useState(null);
  const [selectedLogo, setSelectedLogo] = useState('default');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Resolve public env vars safely on client (support window.__FP_ENV shim)
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const keyClient = window.__FP_ENV?.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || window.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;
    const key = keyClient || (typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_RECAPTCHA_SITE_KEY : null) || null;
    setRecaptchaKey(key);

    // Load reCAPTCHA v3 script if a key exists and not already loaded
    if (key) {
      // if grecaptcha already exists and is ready
      if (window.grecaptcha && typeof window.grecaptcha.execute === 'function') {
        setRecaptchaLoaded(true);
        return;
      }

      // Prevent injecting duplicate script
      const exists = Array.from(document.getElementsByTagName('script')).some((s) => s.src.includes('recaptcha'));
      if (!exists) {
        const script = document.createElement('script');
        script.src = `https://www.google.com/recaptcha/api.js?render=${key}`;
        script.async = true;
        script.defer = true;
        script.onload = () => {
          // grecaptcha may not be immediately ready, but calling ready is safe
          if (window.grecaptcha && typeof window.grecaptcha.ready === 'function') {
            window.grecaptcha.ready(() => setRecaptchaLoaded(true));
          } else {
            setRecaptchaLoaded(true);
          }
        };
        script.onerror = () => {
          console.error('Failed to load reCAPTCHA script');
          setRecaptchaLoaded(false);
        };
        document.body.appendChild(script);
      } else {
        // script already present, attempt to mark loaded
        if (window.grecaptcha && typeof window.grecaptcha.ready === 'function') {
          window.grecaptcha.ready(() => setRecaptchaLoaded(true));
        } else {
          // fallback — assume it's loaded
          setRecaptchaLoaded(true);
        }
      }
    }
  }, []);

  // Optional integration helpers — both safe to call on client
  async function sendToSlack(formData) {
    try {
      const slackWebhook = typeof window !== 'undefined'
        ? (window.__FP_ENV?.NEXT_PUBLIC_SLACK_WEBHOOK || window.NEXT_PUBLIC_SLACK_WEBHOOK)
        : null;
      if (!slackWebhook) return;
      const text = `New quote request from ${formData.get('name')} — ${formData.get('company') || 'no company'} — ${formData.get('email')}`;
      await fetch(slackWebhook, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
    } catch (e) {
      console.error('Slack send error', e);
    }
  }

  async function sendToSheets(payload) {
    try {
      // It's recommended to implement server-side /api/sheets that uses service credentials.
      // This client-side helper simply calls that API route if it exists.
      await fetch('/api/sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      console.error('Sheets send error', e);
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);

    if (typeof window === 'undefined') return;
    const form = e.target;
    const formData = new FormData(form);

    // disable multiple submissions
    setSubmitting(true);

    try {
      // If recaptchaKey is present, get a v3 token
      if (recaptchaKey) {
        if (!window.grecaptcha || typeof window.grecaptcha.execute !== 'function') {
          throw new Error('reCAPTCHA not ready. Please try again.');
        }
        // execute with action 'submit' — adjust action name as needed for analytics
        const token = await window.grecaptcha.execute(recaptchaKey, { action: 'submit' });
        // Append token to form data under the conventional name expected by many backends
        formData.append('g-recaptcha-response', token);
      }

      // Post to Formspree (keep Accept header for JSON response)
      const res = await fetch('https://formspree.io/f/mgvejzdo', {
        method: 'POST',
        body: formData,
        headers: { Accept: 'application/json' },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        console.error('Formspree error:', data);
        throw new Error((data?.error && Array.isArray(data.error) ? data.error.join(', ') : data?.message) || 'Submission failed');
      }

      // On success: optional integrations
      const payload = Object.fromEntries(formData.entries());
      await Promise.all([sendToSlack(formData), sendToSheets(payload)]);

      setSubmitted(true);
      form.reset();
      setSubmitting(false);

      // reCAPTCHA v3 tokens auto-expire — nothing to reset client-side
    } catch (err) {
      console.error(err);
      setErrorMessage(err?.message || 'Something went wrong. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen font-sans text-gray-800 bg-white">
      <Head>
        <title>FP CAD Design Services — Precision CAD Drafting for Telecom</title>
        <meta name="description" content="FP CAD Design Services specializes in underground telecommunication CAD drafting — fiber, conduit, and micro-duct systems. Request a quote today." />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <meta property="og:title" content="FP CAD Design Services" />
      </Head>

      <header className="sticky top-0 bg-white/90 backdrop-blur z-40 shadow-sm">
        <nav className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo />
            <div>
              <div className="text-lg font-bold">FP CAD Design Services</div>
              <div className="text-xs text-gray-500">Waterloo Region, Ontario</div>
            </div>
          </div>
          <ul className="hidden md:flex items-center gap-6 text-sm">
            <li><a href="#about" className="hover:underline">About</a></li>
            <li><a href="#services" className="hover:underline">Services</a></li>
            <li><a href="#quote" className="hover:underline">Request a Quote</a></li>
            <li><a href="#contact" className="hover:underline">Contact</a></li>
          </ul>
          <a href="#quote" className="hidden md:inline-block bg-blue-900 text-white px-4 py-2 rounded-lg text-sm">Request a Quote</a>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="bg-gradient-to-b from-blue-900 to-blue-800 text-white py-20">
          <div className="max-w-6xl mx-auto px-6 grid md:grid-cols-2 gap-8 items-center">
            <div>
              <motion.h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-4"
                initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                Precision CAD Drafting for Underground Telecom
              </motion.h1>
              <p className="text-lg text-blue-100 mb-6">FP CAD Design Services specializes in underground telecommunication design — fiber, conduit, and micro-duct systems — delivering permit-ready drawings for telecoms, engineering firms, and contractors.</p>
              <a href="#quote" className="inline-block bg-white text-blue-900 font-semibold px-5 py-3 rounded-lg shadow">Get a Quote</a>
            </div>
            <div className="hidden md:block">
              <div className="bg-white/10 p-8 rounded-xl">
                <svg viewBox="0 0 400 300" className="w-full h-64" aria-hidden>
                  <rect width="100%" height="100%" rx="12" fill="#08345a" />
                  <g transform="translate(40,30)" fill="#9fd0ff">
                    <rect x="0" y="0" width="240" height="20" rx="4" />
                    <rect x="0" y="40" width="200" height="14" rx="4" />
                    <rect x="0" y="70" width="260" height="14" rx="4" />
                    <rect x="0" y="100" width="160" height="14" rx="4" />
                  </g>
                </svg>
              </div>
            </div>
          </div>
        </section>

        {/* About */}
        <section id="about" className="py-16">
          <div className="max-w-5xl mx-auto px-6 text-center">
            <h2 className="text-3xl font-semibold text-blue-900 mb-4">About FP CAD Design Services</h2>
            <p className="text-lg text-gray-700">FP CAD Design Services is a professional CAD drafting business based in the Waterloo Region, Ontario. The company specializes in underground telecommunication design, including fiber, conduit, and micro-duct systems. Founded by Fritz Point-Du-Jour, who brings over nine years of experience as a CAD Technician, the business provides precise, permit-ready drawings for telecom companies, engineering firms, and local contractors.</p>

            {/* Logo selector + download brochure */}
            <div className="mt-8 flex flex-col md:flex-row items-center justify-center gap-6">
              <div className="text-center">
                <div className="mb-2 font-medium">Logo options</div>
                <div className="flex gap-3 items-center">
                  <button onClick={() => setSelectedLogo('default')} className={`p-2 border rounded ${selectedLogo==='default' ? 'ring-2 ring-blue-500' : ''}`} aria-label="Default logo"><Logo className="w-12 h-12" /></button>
                  <button onClick={() => setSelectedLogo('monogram')} className={`p-2 border rounded ${selectedLogo==='monogram' ? 'ring-2 ring-blue-500' : ''}`} aria-label="Monogram logo">
                    <svg className="w-12 h-12" viewBox="0 0 100 100" aria-hidden><circle cx="50" cy="50" r="44" fill="#0F4C81"/><text x="50%" y="58%" fill="#fff" fontSize="34" textAnchor="middle" fontFamily="sans-serif">FP</text></svg>
                  </button>
                  <button onClick={() => setSelectedLogo('geo')} className={`p-2 border rounded ${selectedLogo==='geo' ? 'ring-2 ring-blue-500' : ''}`} aria-label="Geometric logo">
                    <svg className="w-12 h-12" viewBox="0 0 100 100" aria-hidden><rect x="10" y="10" width="80" height="80" rx="14" fill="#0F4C81"/><polygon points="30,70 50,20 70,70" fill="#fff"/></svg>
                  </button>
                </div>
                <div className="mt-3 text-xs text-gray-500">Selected: {selectedLogo}</div>
              </div>

              <div className="text-center">
                <div className="mb-2 font-medium">Brochure</div>
                <a href="/assets/FP-CAD-Brochure.pdf" download className="inline-block bg-blue-900 text-white px-4 py-2 rounded">Download PDF</a>
                <div className="text-xs text-gray-500 mt-2">Placeholder brochure (replace /assets/FP-CAD-Brochure.pdf with your brochure)</div>
              </div>
            </div>
          </div>
        </section>

        {/* Services */}
        <section id="services" className="py-16 bg-gray-50">
          <div className="max-w-6xl mx-auto px-6">
            <h2 className="text-3xl font-semibold text-center text-blue-900 mb-8">Our Services</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="font-semibold text-lg mb-2">Underground Fiber Network Design</h3>
                <p className="text-sm text-gray-600">Detailed CAD layouts for underground fiber optic installations — conduits, micro-ducts and jointing.</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="font-semibold text-lg mb-2">Permit & Construction Drawings</h3>
                <p className="text-sm text-gray-600">Permit-ready drawings that meet municipal and utility standards for seamless permitting and construction.</p>
              </div>
              <div className="bg-white p-6 rounded-xl shadow">
                <h3 className="font-semibold text-lg mb-2">As-Built & Redline Updates</h3>
                <p className="text-sm text-gray-600">Accurate as-built documentation and redline updates after construction or field changes.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Quote Form */}
        <section id="quote" className="py-16">
          <div className="max-w-3xl mx-auto px-6">
            <h2 className="text-2xl font-semibold text-center text-blue-900 mb-4">Request a Quote</h2>
            <p className="text-center text-gray-600 mb-6">Tell us about your project and we’ll reply with a tailored quote.</p>

            <div className="bg-white p-6 rounded-xl shadow">
              {submitted ? (
                <div className="text-green-600 text-center font-medium" role="status" aria-live="polite">Thank you! Your request has been received — we’ll be in touch shortly.</div>
              ) : (
                <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4" aria-describedby="form-help">
                  <input name="name" required placeholder="Full Name" className="border rounded-md p-3" />
                  <input name="email" type="email" required placeholder="Email Address" className="border rounded-md p-3" />
                  <input name="company" placeholder="Company (optional)" className="border rounded-md p-3" />
                  <textarea name="message" required placeholder="Project details (scope, locations, deliverables)" className="border rounded-md p-3 h-32"></textarea>

                  {/* Formspree auto-response and hidden fields */}
                  <input type="hidden" name="_autoresponse" value="Thank you for contacting FP CAD Design Services. We’ve received your message and will get back to you soon." />
                  <input type="hidden" name="_subject" value="New project quote request" />

                  {/* Provide feedback while token or submit in progress */}
                  {errorMessage && <div className="text-red-600 text-sm" role="alert">{errorMessage}</div>}

                  <div className="flex justify-between items-center">
                    <a href="/assets/FP-CAD-Brochure.pdf" download className="text-sm text-gray-600 underline">Download brochure</a>
                    <div>
                      <button type="submit" disabled={submitting} className={`bg-blue-900 text-white px-5 py-2 rounded-md ${submitting ? 'opacity-70 cursor-wait' : ''}`}>
                        {submitting ? 'Submitting…' : 'Submit Request'}
                      </button>
                    </div>
                  </div>
                </form>
              )}
            </div>

            <p className="text-xs text-gray-500 mt-3" id="form-help">Integrations available: Slack webhook and Google Sheets (requires serverless /api/sheets). See deployment notes in the project README.</p>
          </div>
        </section>

        {/* Contact */}
        <section id="contact" className="py-12 bg-blue-900 text-white">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h3 className="text-xl font-semibold mb-2">Contact</h3>
            <p className="text-sm">Email: <a href="mailto:fpcaddesign@gmail.com" className="underline">fpcaddesign@gmail.com</a></p>
            <p className="text-sm">Phone: <a href="tel:+16475732397" className="underline">(647) 573-2397</a></p>
            <p className="text-sm">Location: Waterloo Region, Ontario</p>
          </div>
        </section>
      </main>

      <footer className="py-6 text-center text-sm text-gray-600">
        © {new Date().getFullYear()} FP CAD Design Services — All rights reserved.
      </footer>
    </div>
  );
}
