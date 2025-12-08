import { GoogleGenAI, Chat, GenerateContentResponse } from "@google/genai";
import { CLINIC_INFO } from '../constants';

let chatSession: Chat | null = null;

// Initialize the model
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const initChat = () => {
  try {
    chatSession = ai.chats.create({
      model: 'gemini-2.5-flash',
      config: {
        systemInstruction: CLINIC_INFO.systemInstruction,
        temperature: 0.7,
      },
    });
  } catch (error) {
    console.error("Failed to initialize chat:", error);
  }
};

export const sendMessageToGemini = async (message: string): Promise<string> => {
  if (!chatSession) {
    initChat();
  }
  
  if (!chatSession) {
    return "I'm having trouble connecting to the server right now. Please try again later.";
  }

  try {
    const response: GenerateContentResponse = await chatSession.sendMessage({ 
      message 
    });
    return response.text || "I didn't catch that. Could you rephrase?";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "I apologize, but I'm currently experiencing high traffic. Please try again in a moment.";
  }
};