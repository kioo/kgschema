import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import UserList from './pages/UserList';
import ProtectedRoute from './router/ProtectedRoute';
import MainLayout from './layouts/MainLayout';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Navigate to="/entities" replace />} />
          <Route path="/users" element={<UserList />} />
          <Route path="/entities" element={<div>实体管理 (TODO)</div>} />
          <Route path="/relations" element={<div>关系管理 (TODO)</div>} />
          <Route path="/audit" element={<div>审计日志 (TODO)</div>} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
