import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Loader from './Loader';

/**
 * Route guard that restricts access to authenticated users.
 * Shows a loader while auth state is being determined.
 *
 * @returns {JSX.Element}
 */
export default function ProtectedRoute() {
  const { isAuth, loading } = useAuth();

  if (loading) return <Loader text="Checking authentication..." />;
  if (!isAuth) return <Navigate to="/login" replace />;

  return <Outlet />;
}
