import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { HostControl } from './routes/HostControl';
import { PublicDisplay } from './routes/PublicDisplay';
import { NotFound } from './routes/NotFound';

/**
 * Root application component.
 *
 * URL routing determines mode:
 *  /host/*    → Host-control mode (operator interface)
 *  /display/* → Public display mode (room-facing leaderboard)
 *  /          → Redirect to /display (default for room-facing setup)
 */
export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/display" replace />} />
        <Route path="/host/*" element={<HostControl />} />
        <Route path="/display/*" element={<PublicDisplay />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
