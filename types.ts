export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  image: string;
  availability: string[]; // Days of week
}

export interface Service {
  id: string;
  name: string;
  duration: number; // minutes
  price: number;
  description: string;
  iconName: string;
}

export interface TimeSlot {
  time: string;
  available: boolean;
}

export interface BookingState {
  step: number;
  selectedService: Service | null;
  selectedDoctor: Doctor | null;
  selectedDate: Date | null;
  selectedTime: string | null;
  patientDetails: {
    name: string;
    email: string;
    phone: string;
    notes: string;
  };
}

export enum ChatSender {
  USER = 'user',
  BOT = 'bot'
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: ChatSender;
  timestamp: Date;
}