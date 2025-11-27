import React, { useState } from 'react';

export default function AiStudioPage() {
  // const [featureType, setFeatureType] = useState('beta');
  const [toastVisible, setToastVisible] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    suggestions: '',
    joinedCommunity: false,
  });

  // Data for feature grid and phone animation omitted, can be added similarly

  const handleInputChange = (e) => {
    const { id, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [id]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleJoin = (e) => {
    e.preventDefault();
    const btnText = document.getElementById('btnText');
    const loader = document.getElementById('btnLoader');
    const btn = document.getElementById('submitBtn');

    btnText.classList.add('hidden');
    loader.classList.remove('hidden');
    btn.disabled = true;
    btn.classList.add('opacity-80', 'cursor-not-allowed');

    setTimeout(() => {
      console.log('Form Submitted:', formData);

      loader.classList.add('hidden');
      btnText.classList.remove('hidden');
      btnText.innerText = `Welcome ${formData.name.split(' ')[0] || ''}!`;
      btn.classList.replace('bg-brand-purple', 'bg-green-600');

      // Show toast notification
      setToastVisible(true);

      // Reset form
      setFormData({ name: '', email: '', suggestions: '', joinedCommunity: false });

      setTimeout(() => {
        btnText.innerText = 'Get Early Access';
        btn.disabled = false;
        btn.classList.replace('bg-green-600', 'bg-brand-purple');
        btn.classList.remove('opacity-80', 'cursor-not-allowed');
        setToastVisible(false);
      }, 3000);
    }, 1500);
  };

  return (
    <div className="font-sans text-gray-800 bg-gray-50">
      {/* Toast Notification */}
      <div
        id="toast"
        className={`fixed top-24 right-5 z-50 transform transition-transform duration-500 ease-in-out bg-white border-l-4 border-brand-gold shadow-2xl rounded-r-lg p-4 flex items-center pr-8 ${
          toastVisible ? '' : 'translate-x-full'
        }`}
      >
        <div className="text-green-500 rounded-full bg-green-100 p-2 mr-3">
          <i className="fas fa-check"></i>
        </div>
        <div>
          <p className="font-bold text-gray-800">You're on the list!</p>
          <p className="text-sm text-gray-600">Thanks for your suggestion.</p>
        </div>
      </div>

      {/* Navigation (simplified) */}
      <nav className="fixed w-full z-40 py-4 bg-white backdrop-blur-md shadow-lg">
        <div className="max-w-7xl mx-auto px-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-purple rounded-full flex items-center justify-center text-brand-gold border-2 border-brand-gold shadow-md">
              <span className="font-serif font-bold text-xl">S</span>
            </div>
            <span className="text-2xl font-serif font-bold text-brand-purple tracking-wide">Stylus</span>
          </div>
          <div className="hidden md:flex space-x-8 items-center">
            <a href="#features" className="text-gray-600 hover:text-brand-purple font-medium transition-colors">Features</a>
            <a href="#vision" className="text-gray-600 hover:text-brand-purple font-medium transition-colors">Vision</a>
          </div>
          <button onClick={() => document.getElementById('waitlistForm').scrollIntoView({ behavior: 'smooth', block: 'center' })} className="bg-brand-purple text-white px-6 py-2 rounded-full font-bold hover:bg-purple-900 transition-all shadow-md transform hover:scale-105 active:scale-95 text-sm">
            Get Early Access
          </button>
        </div>
      </nav>

      {/* Hero Section and other parts omitted */}
      {/* Form */}
      <section className="max-w-md mx-auto bg-white60 backdrop-blur-md border border-white50 p-6 rounded-2xl shadow-xl mt-32">
        <form id="waitlistForm" onSubmit={handleJoin} className="space-y-4">
          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Name</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              placeholder="Your Name"
              className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-white80 focus:border-brand-purple focus:ring-1 focus:ring-brand-purple outline-none transition-all text-sm"
            />
          </div>
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Email</label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              placeholder="name@email.com"
              className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-white80 focus:border-brand-purple focus:ring-1 focus:ring-brand-purple outline-none transition-all text-sm"
            />
          </div>
          {/* Checkbox */}
          <div className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              id="joinedCommunity"
              checked={formData.joinedCommunity}
              onChange={handleInputChange}
              className="w-5 h-5 border-2 border-gray-300 rounded transition-all focus:ring-2 focus:ring-brand-purple"
            />
            <label htmlFor="joinedCommunity" className="text-sm text-gray-600 hover:text-brand-purple transition-colors cursor-pointer">
              I've already joined the Stylus Community
            </label>
          </div>
          {/* Suggestions */}
          <div>
            <label htmlFor="suggestions" className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">What feature would you love?</label>
            <textarea
              id="suggestions"
              value={formData.suggestions}
              onChange={handleInputChange}
              rows="2"
              placeholder="Tell us your ideas for the app..."
              className="w-full px-4 py-2 rounded-lg border border-gray-200 bg-white80 focus:border-brand-purple focus:ring-1 focus:ring-brand-purple outline-none transition-all text-sm resize-none"
            />
          </div>
          {/* Submit Button */}
          <button
            type="submit"
            id="submitBtn"
            className="w-full bg-brand-purple text-white py-3 rounded-xl font-bold hover:bg-purple-900 transition-all shadow-lg flex items-center justify-center gap-2"
          >
            <span id="btnText">Get Early Access</span>
            <div id="btnLoader" className="loader hidden border-white border-t-transparent"></div>
          </button>
        </form>
      </section>
    </div>
  );
}
