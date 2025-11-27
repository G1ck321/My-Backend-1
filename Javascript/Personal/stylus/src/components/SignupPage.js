import React from 'react';
import { Link } from "react-router-dom";
export default function SignupPage() {
  const handleSignup = (e) => {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const loader = document.getElementById('btnLoader');
    const successMsg = document.getElementById('successMsg');
    const inputs = document.querySelectorAll('input, textarea');

    // 1. Loading State
    btnText.classList.add('hidden');
    loader.classList.remove('hidden');
    btn.classList.add('opacity-80', 'cursor-not-allowed');

    // Simulate API Call
    setTimeout(() => {
      // Normally send data to backend here
      console.log('Registered:', {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        isCommunity: document.getElementById('joinedCommunity').checked,
        suggestion: document.getElementById('suggestions').value,
      });

      // 3. Success State
      loader.classList.add('hidden');
      btnText.classList.remove('hidden');
      btnText.innerText = 'Joined Successfully!';
      btn.classList.replace('bg-brand-purple', 'bg-green-600');
      successMsg.classList.remove('hidden');

      // Disable form inputs
      inputs.forEach(input => input.disabled = true);
    }, 2000);
  };

  return (
    <div className="royal-bg min-h-screen flex items-center justify-center p-4">
      {/* Back Button */}
      <Link to="/ai-studio">Back to Home</Link>
      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-0 lg:gap-8 items-center">
        {/* Left Visuals */}
        <div className="hidden lg:block p-8">
          <div className="mb-8">
            <div className="w-16 h-16 bg-brand-purple text-brand-gold rounded-full flex items-center justify-center text-3xl font-serif font-bold shadow-lg mb-6">S</div>
            <h1 className="text-5xl font-serif font-bold text-gray-900 mb-6 leading-tight">
              Shape the Future of <br />
              <span className="text-brand-purple">Effortless Style.</span>
            </h1>
            <p className="text-lg text-gray-600 max-w-md leading-relaxed">
              Join the exclusive Stylus community. Get early access to AI-powered recommendations and help us build the features you actually want.
            </p>
          </div>
          {/* Trust Indicators */}
          <div className="flex items-center gap-4 mt-12 opacity-80">
            <div className="flex -space-x-3">
              <img className="w-10 h-10 rounded-full border-2 border-white" src="https://ui-avatars.com/api?name=Alex&background=random" alt="Alex" />
              <img className="w-10 h-10 rounded-full border-2 border-white" src="https://ui-avatars.com/api?name=Sarah&background=random" alt="Sarah" />
              <img className="w-10 h-10 rounded-full border-2 border-white" src="https://ui-avatars.com/api?name=Mike&background=random" alt="Mike" />
            </div>
            <div className="text-sm font-bold text-gray-500">Join 2,000 others waiting</div>
          </div>
        </div>
        {/* Right The Form Card */}
        <div className="glass-panel rounded-3xl p-8 md:p-12 w-full max-w-lg mx-auto">
          {/* Mobile Header */}
          <div className="lg:hidden text-center mb-8">
            <h2 className="text-3xl font-serif font-bold text-brand-purple">Join Stylus</h2>
            <p className="text-gray-500 text-sm mt-2">Create your early access profile</p>
          </div>
          <form id="signupForm" onSubmit={handleSignup} className="space-y-6">
            {/* Full Name */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider" htmlFor="name">Full Name</label>
              <div className="relative">
                <i className="fas fa-user absolute left-4 top-3.5 text-gray-400"></i>
                <input
                  type="text"
                  id="name"
                  required
                  placeholder="Jane Doe"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-brand-purple focus:ring-2 focus:ring-purple-100 outline-none transition-all"
                />
              </div>
            </div>
            {/* Email */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider" htmlFor="email">Email Address</label>
              <div className="relative">
                <i className="fas fa-envelope absolute left-4 top-3.5 text-gray-400"></i>
                <input
                  type="email"
                  id="email"
                  required
                  placeholder="jane@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 bg-white focus:border-brand-purple focus:ring-2 focus:ring-purple-100 outline-none transition-all"
                />
              </div>
            </div>
            {/* Community Checkbox */}
            <div className="bg-purple-50 p-4 rounded-xl border border-purple-100 flex items-start gap-3">
              <div className="relative flex items-center mt-1">
                <input type="checkbox" id="joinedCommunity" className="w-5 h-5 text-brand-purple border-gray-300 rounded focus:ring-brand-purple" />
              </div>
              <div>
                <label htmlFor="joinedCommunity" className="text-sm font-bold text-gray-800 cursor-pointer">I'm part of the Stylus Community</label>
                <p className="text-xs text-gray-500 mt-0.5">Check this if you are already in our group chats.</p>
              </div>
            </div>
            {/* Suggestions */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase tracking-wider" htmlFor="suggestions">Feature Wishlist <span className="text-brand-gold ml-1">Optional</span></label>
              <textarea
                id="suggestions"
                rows="3"
                placeholder="I would love to see..."
                className="w-full p-4 rounded-xl border border-gray-200 bg-white focus:border-brand-purple focus:ring-2 focus:ring-purple-100 outline-none transition-all resize-none"
              />
            </div>
            {/* Submit Button */}
            <button
              type="submit"
              id="submitBtn"
              className="w-full bg-brand-purple text-white py-4 rounded-xl font-bold text-lg hover:bg-purple-900 hover:shadow-lg transition-all transform hover:translate-y-0.5 flex items-center justify-center gap-2"
            >
              <span id="btnText">Secure My Spot</span>
              <div id="btnLoader" className="loader hidden border-white border-t-transparent"></div>
            </button>
            <p id="successMsg" className="hidden text-center text-green-600 font-bold bg-green-50 p-3 rounded-lg border border-green-200">
              You're on the list! We'll be in touch.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
