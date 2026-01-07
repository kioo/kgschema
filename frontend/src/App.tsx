import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import UserList from './pages/UserList';
import EntityList from './pages/EntityList';
import EntityDetail from './pages/EntityDetail';
import RelationList from './pages/RelationList';
import RelationDetail from './pages/RelationDetail';
import VersionList from './pages/VersionList';
import PromptList from './pages/PromptList';
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
          <Route path="/entities" element={<EntityList />} />
          <Route path="/entities/:id" element={<EntityDetail />} />
          <Route path="/relations" element={<RelationList />} />
          <Route path="/relations/:id" element={<RelationDetail />} />
          <Route path="/prompts" element={<PromptList />} />
          <Route path="/versions" element={<VersionList />} />
          <Route path="/audit" element={<div>审计日志 (TODO)</div>} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;



