import React, { useState, useEffect } from 'react';
import { Upload } from 'lucide-react';
import { uploadFile } from '../services/s3Service';
import { getPlayers } from '../services/apiService';
import ChatInterface from '../components/chat/ChatInterface';
import ResetButton from '../components/ResetButton';

const Dashboard = () => {
  const [players, setPlayers] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetchPlayers();
  }, []);

  const fetchPlayers = async () => {
    try {
      const data = await getPlayers();
      setPlayers(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch player data');
      console.error('Error:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    console.log('*** Dashboard: File selected:', file);
    
    console.log('File selected:', {
      name: file.name,
      type: file.type,
      size: file.size
    });
    
    setIsUploading(true);
    try {
      console.log('Starting upload process...');
      await uploadFile(file);
      console.log('Upload completed successfully');
      await fetchPlayers();
    } catch (error) {
      console.error('Upload error:', error);
      setError('Failed to upload file: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  // Add this handler for the reset button
  const handleResetComplete = async () => {
    try {
      setIsLoading(true);
      await fetchPlayers(); // Refresh the player data after reset
    } catch (error) {
      console.error('Error refreshing data after reset:', error);
      setError('Failed to refresh data after reset');
    } finally {
      setIsLoading(false);
    }
  };

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <div className="text-red-600 text-center">
          <p className="text-xl font-semibold">{error}</p>
          <button 
            onClick={fetchPlayers}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Left Panel - Upload */}
      <div className="w-1/4 p-4 bg-white shadow-md overflow-auto">
        <h2 className="text-xl font-semibold mb-4">File Upload</h2>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-4">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
            id="file-upload"
            disabled={isUploading}
          />
          <label
            htmlFor="file-upload"
            className={`flex flex-col items-center ${
              isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
            }`}
          >
            <Upload className="w-12 h-12 text-gray-400 mb-2" />
            <span className="text-gray-600">
              {isUploading ? 'Uploading...' : 'Drop CSV file here or click to upload'}
            </span>
          </label>
        </div>

        <div className="mb-4 text-center">
          <ResetButton onResetComplete={handleResetComplete} />
        </div>
        
        {/* Chat Interface */}
        <div className="mt-4">
          <ChatInterface />
        </div>
      </div>
      
      {/* Right Panel - Player Data */}
      <div className="flex-1 p-4 overflow-auto">
        <h2 className="text-xl font-semibold mb-4">Player Analytics</h2>
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          {isLoading ? (
            <div className="p-4 text-center text-gray-600">Loading player data...</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mobile
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    E-Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Segment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Gear
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {players.map((player) => (
                  <tr key={player.mobile}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {`${player.last_name}, ${player.other_names}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">{player.mobile}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{player.e_score}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{player.segment}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{player.gear}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;