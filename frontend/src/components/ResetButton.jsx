// src/components/ResetButton.jsx
import React, { useState } from 'react';
import { resetAllData } from '../services/apiService';

const ResetButton = ({ onResetComplete }) => {
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await resetAllData();
      setShowConfirm(false);
      if (onResetComplete) {
        onResetComplete();
      }
    } catch (error) {
      console.error('Reset failed:', error);
      alert('Reset failed: ' + error.message);
    } finally {
      setIsResetting(false);
    }
  };

  if (showConfirm) {
    return (
      <div className="text-center">
        <p className="mb-2 text-sm">Are you sure? This will delete all data.</p>
        <div className="space-x-2">
          <button
            onClick={handleReset}
            disabled={isResetting}
            className="px-4 py-2 text-white bg-red-600 rounded hover:bg-red-700 disabled:bg-gray-400"
          >
            {isResetting ? 'Resetting...' : 'Yes, Reset'}
          </button>
          <button
            onClick={() => setShowConfirm(false)}
            className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      onClick={() => setShowConfirm(true)}
      className="w-full px-4 py-2 text-white font-semibold rounded bg-red-600 hover:bg-red-700"
    >
      Reset All Data
    </button>
  );
};

export default ResetButton;