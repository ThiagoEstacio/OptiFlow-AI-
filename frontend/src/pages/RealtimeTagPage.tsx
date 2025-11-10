import React from 'react';
import { RealtimeTagViewer } from '@/components/RealtimeTagViewer';

const RealtimeTagPage: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Real-Time Tag Monitor</h1>
        <p className="text-gray-600 mt-2">
          Monitor simulator tags in real-time with automatic updates
        </p>
      </div>

      <RealtimeTagViewer tagName="TEST_COUNTER_PV" pollInterval={1000} />
    </div>
  );
};

export default RealtimeTagPage;
