import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HostControl } from './routes/HostControl';
import { PublicDisplay } from './routes/PublicDisplay';
import { Landing } from './routes/Landing';
import { NotFound } from './routes/NotFound';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/host/*" element={<HostControl />} />
        <Route path="/display/*" element={<PublicDisplay />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
