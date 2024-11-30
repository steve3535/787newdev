import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL;

export const getPlayers = async () => {
  try {
    const response = await axios.get(`${API_URL}/players`);
    return response.data;
  } catch (error) {
    console.error('Error fetching players:', error);
    throw error;
  }
};

export const resetAllData = async () => {
  try {
    const response = await fetch(`${process.env.REACT_APP_API_URL}/reset-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Reset failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Reset error:', error);
    throw error;
  }
};