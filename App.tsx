import React from 'react';
import BookingWizard from './components/BookingWizard';
import AiAssistant from './components/AiAssistant';
import { HeartPulse, Phone, Clock, MapPin } from 'lucide-react';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-brand-dark font-sans text-brand-text selection:bg-brand-primary selection:text-brand-dark">
      
      {/* Navigation */}
      <nav className="sticky top-0 z-40 bg-brand-dark/80 backdrop-blur-lg border-b border-slate-800">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3 group cursor-pointer">
            <div className="relative">
              <HeartPulse className="w-8 h-8 text-brand-primary drop-shadow-[0_0_8px_rgba(45,212,191,0.8)]" />
              <div className="absolute inset-0 bg-brand-primary blur-xl opacity-20 group-hover:opacity-40 transition-opacity"></div>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-xl tracking-wide leading-none text-white">FAMILY</span>
              <span className="font-light text-sm tracking-[0.2em] text-brand-primary leading-none">MEDICINE</span>
            </div>
          </div>
          <div className="hidden md:flex items-center space-x-6 text-sm font-medium text-slate-300">
            <a href="#" className="hover:text-brand-primary transition-colors">Services</a>
            <a href="#" className="hover:text-brand-primary transition-colors">Our Doctors</a>
            <a href="#" className="hover:text-brand-primary transition-colors">About Us</a>
            <button className="bg-brand-primary/10 text-brand-primary border border-brand-primary/50 px-4 py-2 rounded-full hover:bg-brand-primary hover:text-brand-dark transition-all">
              Patient Portal
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="relative py-12 md:py-20 px-4 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-brand-primary/10 rounded-full blur-[100px] -z-10 pointer-events-none"></div>
        
        <div className="container mx-auto max-w-6xl">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 text-white leading-tight">
              Modern Healthcare for <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-primary to-cyan-200">
                Your Entire Family
              </span>
            </h1>
            <p className="text-slate-400 text-lg md:text-xl mb-8 leading-relaxed">
              Book appointments instantly with our top-rated specialists. 
              We combine compassionate care with advanced technology to keep your family healthy.
            </p>
            
            {/* Quick Info Pills */}
            <div className="flex flex-wrap justify-center gap-4 text-sm font-medium text-slate-300">
              <div className="flex items-center bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700">
                <Clock className="w-4 h-4 mr-2 text-brand-primary" />
                <span>Mon-Sat: 09:30am - 12:30pm & 02:30pm to 07:00pm Sun: 03:00pm to 07:00pm</span>
              </div>
              <div className="flex items-center bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700">
                <MapPin className="w-4 h-4 mr-2 text-brand-primary" />
                <span>A-342/1 Shop 1M, Block 1, Kamran Market, Gulshan-e-Iqbal Karachi</span>
              </div>
              <div className="flex items-center bg-slate-800/50 px-4 py-2 rounded-full border border-slate-700">
                <Phone className="w-4 h-4 mr-2 text-brand-primary" />
                <span>(0336) 127-1458</span>
              </div>
            </div>
          </div>

          {/* Booking Widget Wrapper */}
          <div className="max-w-4xl mx-auto relative z-10">
            <div className="absolute -inset-1 bg-gradient-to-r from-brand-primary via-cyan-500 to-brand-primary rounded-2xl blur opacity-30 animate-pulse"></div>
            <BookingWizard />
          </div>
        </div>
      </header>

      {/* Feature Section (Simple) */}
      <section className="py-20 bg-slate-900 border-t border-slate-800">
        <div className="container mx-auto px-4 max-w-6xl grid md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700 hover:border-brand-primary/50 transition-colors">
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4 text-blue-400">
              <HeartPulse size={24} />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Comprehensive Care</h3>
            <p className="text-slate-400">From pediatrics to geriatrics, we cover all your family's medical needs under one roof.</p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700 hover:border-brand-primary/50 transition-colors">
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4 text-purple-400">
              <Clock size={24} />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Minimal Wait Times</h3>
            <p className="text-slate-400">Our digital booking system ensures your appointment starts on time, every time.</p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700 hover:border-brand-primary/50 transition-colors">
            <div className="w-12 h-12 bg-brand-primary/20 rounded-lg flex items-center justify-center mb-4 text-brand-primary">
              <MapPin size={24} />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Central Location</h3>
            <p className="text-slate-400">Conveniently located in the heart of Wellness City with ample free parking available.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-brand-dark py-8 border-t border-slate-800 text-center text-slate-500 text-sm">
        <div className="container mx-auto">
          <p>&copy; {new Date().getFullYear()} Family Medicine Clinic. All rights reserved.</p>
          <p className="mt-2 text-xs">This is a demo application created with React & Tailwind.</p>
        </div>
      </footer>

      {/* Floating AI Assistant */}
      <AiAssistant />
    </div>
  );
};

export default App;