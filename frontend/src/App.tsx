import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Result from './pages/CandidateDetail';
import Pipeline from './pages/Pipeline';
import Health from './pages/Health';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/result" element={<Result />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/health" element={<Health />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
