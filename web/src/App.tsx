import { Routes, Route, Navigate } from 'react-router-dom';
import QAPage from './pages/QAPage';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import AdminKBDetail from './pages/AdminKBDetail';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<QAPage />} />
      <Route path="/admin" element={<Navigate to="/admin/login" replace />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/dashboard" element={<AdminDashboard />} />
      <Route path="/admin/kb/:id" element={<AdminKBDetail />} />
      <Route path="*" element={
        <div style={{ padding: 80, textAlign: 'center' }}>
          <h1>404</h1>
          <p>页面未找到</p>
          <a href="/">返回首页</a>
        </div>
      } />
    </Routes>
  );
}
