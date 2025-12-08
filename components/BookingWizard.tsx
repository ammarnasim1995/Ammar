import React, { useState, useEffect } from 'react';
import { SERVICES, DOCTORS } from '../constants';
import { BookingState, TimeSlot } from '../types';
import { Calendar, Clock, User, CheckCircle, ChevronLeft, ChevronRight, Stethoscope, Baby, Syringe, Activity } from 'lucide-react';

const BookingWizard: React.FC = () => {
  const [state, setState] = useState<BookingState>({
    step: 1,
    selectedService: null,
    selectedDoctor: null,
    selectedDate: null,
    selectedTime: null,
    patientDetails: { name: '', email: '', phone: '', notes: '' }
  });

  const [isSuccess, setIsSuccess] = useState(false);

  // Helper to get icon component
  const getIcon = (name: string) => {
    switch(name) {
      case 'Stethoscope': return <Stethoscope className="w-6 h-6" />;
      case 'Baby': return <Baby className="w-6 h-6" />;
      case 'Syringe': return <Syringe className="w-6 h-6" />;
      case 'Activity': return <Activity className="w-6 h-6" />;
      default: return <Stethoscope className="w-6 h-6" />;
    }
  };

  // Generate fake time slots
  const generateTimeSlots = (): TimeSlot[] => {
    const slots: TimeSlot[] = [];
    for (let i = 9; i < 17; i++) {
      slots.push({ time: `${i}:00`, available: Math.random() > 0.3 });
      slots.push({ time: `${i}:30`, available: Math.random() > 0.3 });
    }
    return slots;
  };

  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);

  useEffect(() => {
    if (state.step === 3) {
      setTimeSlots(generateTimeSlots());
    }
  }, [state.step, state.selectedDate]);

  const handleNext = () => {
    if (state.step === 1 && !state.selectedService) return;
    if (state.step === 2 && !state.selectedDoctor) return;
    if (state.step === 3 && (!state.selectedDate || !state.selectedTime)) return;
    
    setState(prev => ({ ...prev, step: prev.step + 1 }));
  };

  const handleBack = () => {
    setState(prev => ({ ...prev, step: prev.step - 1 }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Simulate API call
    setTimeout(() => {
      setIsSuccess(true);
    }, 1000);
  };

  if (isSuccess) {
    return (
      <div className="bg-brand-card p-8 rounded-2xl shadow-neon border border-brand-primary/20 text-center animate-fade-in">
        <div className="flex justify-center mb-6">
          <div className="rounded-full bg-brand-primary/20 p-4">
            <CheckCircle className="w-16 h-16 text-brand-primary" />
          </div>
        </div>
        <h2 className="text-3xl font-bold text-white mb-2">Booking Confirmed!</h2>
        <p className="text-brand-muted mb-6">
          Thank you, {state.patientDetails.name}. Your appointment for {state.selectedService?.name} with {state.selectedDoctor?.name} is set for {state.selectedDate?.toLocaleDateString()} at {state.selectedTime}.
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="bg-brand-primary text-brand-dark font-bold py-3 px-8 rounded-full hover:bg-brand-glow transition-all duration-300"
        >
          Book Another
        </button>
      </div>
    );
  }

  return (
    <div className="bg-brand-card rounded-2xl shadow-2xl border border-slate-700 overflow-hidden flex flex-col min-h-[500px]">
      {/* Progress Bar */}
      <div className="bg-slate-900 p-4 border-b border-slate-700 flex justify-between items-center">
        {[1, 2, 3, 4].map((s) => (
          <div key={s} className="flex items-center">
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300
              ${state.step >= s ? 'bg-brand-primary text-brand-dark shadow-neon' : 'bg-slate-700 text-slate-400'}
            `}>
              {s}
            </div>
            {s < 4 && <div className={`h-1 w-8 sm:w-16 mx-2 transition-colors duration-300 ${state.step > s ? 'bg-brand-primary' : 'bg-slate-700'}`} />}
          </div>
        ))}
      </div>

      <div className="p-6 md:p-8 flex-grow">
        {/* Step 1: Services */}
        {state.step === 1 && (
          <div className="animate-fade-in">
            <h2 className="text-2xl font-bold text-white mb-6">Select a Service</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {SERVICES.map(service => (
                <button
                  key={service.id}
                  onClick={() => setState(prev => ({ ...prev, selectedService: service }))}
                  className={`
                    p-4 rounded-xl border text-left transition-all duration-200 hover:shadow-lg flex items-start space-x-4
                    ${state.selectedService?.id === service.id 
                      ? 'border-brand-primary bg-brand-primary/10 shadow-[0_0_15px_rgba(45,212,191,0.2)]' 
                      : 'border-slate-700 hover:border-brand-primary/50 bg-slate-800/50'}
                  `}
                >
                  <div className={`p-2 rounded-lg ${state.selectedService?.id === service.id ? 'bg-brand-primary text-brand-dark' : 'bg-slate-700 text-brand-primary'}`}>
                    {getIcon(service.iconName)}
                  </div>
                  <div>
                    <h3 className="font-bold text-white text-lg">{service.name}</h3>
                    <p className="text-brand-muted text-sm mt-1">{service.description}</p>
                    <div className="mt-3 flex items-center space-x-3 text-xs font-medium text-brand-primary">
                      <span className="bg-slate-900/50 px-2 py-1 rounded">Avg. {service.duration} mins</span>
                      <span className="bg-slate-900/50 px-2 py-1 rounded">${service.price}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Doctor */}
        {state.step === 2 && (
          <div className="animate-fade-in">
            <h2 className="text-2xl font-bold text-white mb-6">Choose a Specialist</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {DOCTORS.map(doctor => (
                <button
                  key={doctor.id}
                  onClick={() => setState(prev => ({ ...prev, selectedDoctor: doctor }))}
                  className={`
                    p-4 rounded-xl border flex flex-col items-center text-center transition-all duration-200 hover:scale-[1.02]
                    ${state.selectedDoctor?.id === doctor.id 
                      ? 'border-brand-primary bg-brand-primary/10 shadow-neon' 
                      : 'border-slate-700 bg-slate-800/50 hover:border-brand-primary/50'}
                  `}
                >
                  <img src={doctor.image} alt={doctor.name} className="w-24 h-24 rounded-full mb-4 object-cover border-2 border-slate-600" />
                  <h3 className="font-bold text-white text-lg">{doctor.name}</h3>
                  <p className="text-brand-primary text-sm mb-2">{doctor.specialty}</p>
                  <div className="flex flex-wrap justify-center gap-1 mt-2">
                    {doctor.availability.map(d => (
                      <span key={d} className="text-xs bg-slate-900 text-slate-400 px-1.5 py-0.5 rounded">{d}</span>
                    ))}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Date & Time */}
        {state.step === 3 && (
          <div className="animate-fade-in">
            <h2 className="text-2xl font-bold text-white mb-6">Date & Time</h2>
            <div className="flex flex-col md:flex-row gap-8">
              <div className="flex-1">
                <label className="block text-brand-muted mb-2 text-sm uppercase tracking-wider font-semibold">Select Date</label>
                <input 
                  type="date" 
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setState(prev => ({ ...prev, selectedDate: new Date(e.target.value), selectedTime: null }))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition-colors"
                />
              </div>
              <div className="flex-1">
                <label className="block text-brand-muted mb-2 text-sm uppercase tracking-wider font-semibold">Available Slots</label>
                {!state.selectedDate ? (
                  <div className="text-slate-500 italic p-4 text-center border border-dashed border-slate-700 rounded-lg">Please select a date first</div>
                ) : (
                  <div className="grid grid-cols-3 gap-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                    {timeSlots.map((slot, idx) => (
                      <button
                        key={idx}
                        disabled={!slot.available}
                        onClick={() => setState(prev => ({ ...prev, selectedTime: slot.time }))}
                        className={`
                          py-2 px-1 rounded text-sm font-medium transition-all
                          ${!slot.available 
                            ? 'bg-slate-800 text-slate-600 cursor-not-allowed decoration-slate-500 line-through' 
                            : state.selectedTime === slot.time
                              ? 'bg-brand-primary text-brand-dark shadow-neon'
                              : 'bg-slate-700 text-white hover:bg-slate-600'}
                        `}
                      >
                        {slot.time}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Details */}
        {state.step === 4 && (
          <div className="animate-fade-in">
            <h2 className="text-2xl font-bold text-white mb-6">Patient Details</h2>
            <form id="booking-form" onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-brand-muted mb-1">Full Name</label>
                  <input 
                    required 
                    type="text" 
                    value={state.patientDetails.name}
                    onChange={e => setState(prev => ({...prev, patientDetails: {...prev.patientDetails, name: e.target.value}}))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:border-brand-primary focus:outline-none"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm text-brand-muted mb-1">Email</label>
                  <input 
                    required 
                    type="email" 
                    value={state.patientDetails.email}
                    onChange={e => setState(prev => ({...prev, patientDetails: {...prev.patientDetails, email: e.target.value}}))}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:border-brand-primary focus:outline-none"
                    placeholder="john@example.com"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-brand-muted mb-1">Phone Number</label>
                <input 
                  required 
                  type="tel" 
                  value={state.patientDetails.phone}
                  onChange={e => setState(prev => ({...prev, patientDetails: {...prev.patientDetails, phone: e.target.value}}))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:border-brand-primary focus:outline-none"
                  placeholder="(555) 000-0000"
                />
              </div>
              <div>
                <label className="block text-sm text-brand-muted mb-1">Reason for Visit / Symptoms</label>
                <textarea 
                  rows={3}
                  value={state.patientDetails.notes}
                  onChange={e => setState(prev => ({...prev, patientDetails: {...prev.patientDetails, notes: e.target.value}}))}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:border-brand-primary focus:outline-none"
                  placeholder="Briefly describe your symptoms..."
                />
              </div>

              {/* Summary Card */}
              <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700 mt-6">
                <h3 className="text-white font-semibold mb-2">Booking Summary</h3>
                <div className="text-sm text-slate-300 space-y-1">
                  <div className="flex justify-between"><span>Service:</span> <span className="text-brand-primary">{state.selectedService?.name}</span></div>
                  <div className="flex justify-between"><span>Doctor:</span> <span className="text-brand-primary">{state.selectedDoctor?.name}</span></div>
                  <div className="flex justify-between"><span>Date:</span> <span className="text-brand-primary">{state.selectedDate?.toDateString()} @ {state.selectedTime}</span></div>
                  <div className="flex justify-between border-t border-slate-700 mt-2 pt-2 font-bold text-white"><span>Total:</span> <span>${state.selectedService?.price}</span></div>
                </div>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Footer Controls */}
      <div className="p-6 border-t border-slate-700 flex justify-between bg-slate-900/50">
        <button
          onClick={handleBack}
          disabled={state.step === 1}
          className={`flex items-center px-6 py-3 rounded-lg font-medium transition-colors ${state.step === 1 ? 'opacity-0 cursor-default' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
        >
          <ChevronLeft className="w-5 h-5 mr-1" /> Back
        </button>
        
        {state.step < 4 ? (
          <button
            onClick={handleNext}
            disabled={
              (state.step === 1 && !state.selectedService) ||
              (state.step === 2 && !state.selectedDoctor) ||
              (state.step === 3 && (!state.selectedDate || !state.selectedTime))
            }
            className="bg-brand-primary text-brand-dark font-bold px-8 py-3 rounded-full hover:bg-brand-glow disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-neon flex items-center"
          >
            Next Step <ChevronRight className="w-5 h-5 ml-1" />
          </button>
        ) : (
          <button
            form="booking-form"
            type="submit"
            className="bg-brand-primary text-brand-dark font-bold px-8 py-3 rounded-full hover:bg-brand-glow transition-all shadow-neon flex items-center"
          >
            Confirm Booking <CheckCircle className="w-5 h-5 ml-1" />
          </button>
        )}
      </div>
    </div>
  );
};

export default BookingWizard;