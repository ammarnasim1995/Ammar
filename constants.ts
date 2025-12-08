import { Doctor, Service } from './types';

export const SERVICES: Service[] = [
  {
    id: 's1',
    name: 'General Consultation',
    duration: 30,
    price: 80,
    description: 'Routine check-up, illness diagnosis, and general health advice.',
    iconName: 'Stethoscope'
  },
  {
    id: 's2',
    name: 'Pediatric Checkup',
    duration: 45,
    price: 100,
    description: 'Specialized care for infants, children, and adolescents.',
    iconName: 'Baby'
  },
  {
    id: 's3',
    name: 'Vaccination',
    duration: 15,
    price: 40,
    description: 'Flu shots, travel vaccines, and routine immunizations.',
    iconName: 'Syringe'
  },
  {
    id: 's4',
    name: 'Blood Work / Lab',
    duration: 20,
    price: 60,
    description: 'Blood sample collection and basic laboratory testing.',
    iconName: 'Activity'
  }
];

export const DOCTORS: Doctor[] = [
  {
    id: 'd1',
    name: 'Dr. Syeda Maha Shafi',
    specialty: 'Family Medicine',
    image: 'https://picsum.photos/200/200?random=1',
    availability: ['Mon', 'Tue', 'Wed', 'Thu' 'Fri', 'Sat']
  },
  {
    id: 'd2',
    name: 'Dr. James Chen',
    specialty: 'Pediatrics',
    image: 'https://picsum.photos/200/200?random=2',
    availability: ['Tue', 'Thu', 'Sat']
  },
  {
    id: 'd3',
    name: 'Dr. Emily Ross',
    specialty: 'Internal Medicine',
    image: 'https://picsum.photos/200/200?random=3',
    availability: ['Mon', 'Wed', 'Thu', 'Fri']
  }
];

export const CLINIC_INFO = {
  name: 'Family Medicine Clinic',
  address: '123 Health Avenue, Wellness City',
  phone: '(0336) 127-1458',
  hours: 'Mon-Sat: 09:30am - 12:30pm & 02:30pm to 07:00pm, Sun: 03:00pm - 07:00pm',
  systemInstruction: `You are the AI Receptionist for the Family Medicine Clinic. 
  
  Key Information:
  - We offer General Consultations (800), Pediatric Checkups (1000), Vaccinations (500), and Blood Work ($60).
  - Our doctors are Dr. Syeda Maha Shafi (Family Med), Dr.  (Pediatrics), and Dr.  (Internal Med).
  - Open Mon-Sat: 09:30am - 12:30pm & 02:30pm to 07:00pm, Sun: 03:00pm - 07:00pm.
  - Located at 123 Health Avenue.
  
  Your Role:
  - Answer questions about services, prices, and hours.
  - Help users decide which service they might need based on simple symptoms (always add a disclaimer to seek emergency help for serious conditions).
  - Be friendly, professional, and concise.
  - If they want to book, encourage them to use the "Book Appointment" form on the left.
  `
};