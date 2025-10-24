/**
 * App - Main application entry point
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { PortDashboard } from '@/pages/PortDashboard';
import { Toaster } from 'react-hot-toast';

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
          },
          success: {
            iconTheme: {
              primary: '#22c55e',
              secondary: '#f1f5f9',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#f1f5f9',
            },
          },
        }}
      />

      <Routes>
        <Route
          path="/"
          element={
            <MainLayout>
              <PortDashboard />
            </MainLayout>
          }
        />

        {/* Placeholder routes - to be implemented */}
        <Route
          path="/vessels"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Vessels Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/berths"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Berths Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/operations"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Operations Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/equipment"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Equipment Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/analytics"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Analytics Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/alerts"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Alerts Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/reports"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Reports Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        <Route
          path="/settings"
          element={
            <MainLayout>
              <div className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <h2 className="text-2xl font-bold text-dark-100">
                    Settings Page
                  </h2>
                  <p className="mt-2 text-dark-400">Coming soon...</p>
                </div>
              </div>
            </MainLayout>
          }
        />

        {/* 404 - Not Found */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
