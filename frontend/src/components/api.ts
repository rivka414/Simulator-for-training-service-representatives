import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const sendMessageToAI = async (
  messages: { role: string; content: string }[],
  isFinished: boolean = false,
) => {
   
    const response = await axios.post(`${API_URL}/chat`, {
        messages,
        is_finished: isFinished
    });
    return response.data.response;
};