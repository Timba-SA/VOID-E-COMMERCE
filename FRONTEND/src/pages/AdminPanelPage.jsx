import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios'; // Usaremos axios directamente para simplificar

// Función para buscar los datos de telemetría (KPIs)
// NOTA: Para que esto funcione, axios debe tener el token. 
// Una buena práctica sería crear un 'axiosClient' con interceptores.
const fetchKpis = async () => {
  const token = localStorage.getItem('authToken');
  const { data } = await axios.get('http://localhost:8000/api/admin/metrics/kpis', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  return data;
};

const AdminPanelPage = () => {
  // Usamos React Query para obtener y cachear los datos
  const { data: kpis, isLoading, error } = useQuery({
    queryKey: ['admin-kpis'],
    queryFn: fetchKpis,
    // Opciones para evitar reintentos en caso de error 401/403
    retry: (failureCount, error) => {
      if (error.response?.status === 401 || error.response?.status === 403) {
        return false;
      }
      return failureCount < 3;
    },
  });

  return (
    <div style={{ display: 'flex', fontFamily: "'Montserrat', sans-serif" }}>
      <aside style={{ width: '250px', background: '#f8f9fa', padding: '1rem', minHeight: 'calc(100vh - 160px)', borderRight: '1px solid #dee2e6' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: '700' }}>VOID Race Control</h2>
        <nav>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li style={{ marginBottom: '0.5rem' }}><a href="/admin">Dashboard (Telemetría)</a></li>
            {/* Aquí irían los links a otras secciones del panel */}
            {/* <li><a href="/admin/products">Gestión de Productos</a></li> */}
            {/* <li><a href="/admin/users">Gestión de Usuarios</a></li> */}
          </ul>
        </nav>
      </aside>
      
      <main style={{ flex: 1, padding: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '2rem' }}>Dashboard de Telemetría</h1>
        
        {isLoading && <p>Cargando datos del auto...</p>}
        {error && <p style={{ color: 'red' }}>¡Alerta! Se perdió la telemetría: {error.response?.data?.detail || error.message}</p>}

        {kpis && (
          <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
            <div className="kpi-card" style={{ border: '1px solid #ddd', padding: '1.5rem', borderRadius: '8px', background: '#fff' }}>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#6c757d' }}>Ingresos Totales</h3>
              <p style={{ margin: 0, fontSize: '1.75rem', fontWeight: '700' }}>${kpis.total_revenue.toFixed(2)}</p>
            </div>
            <div className="kpi-card" style={{ border: '1px solid #ddd', padding: '1.5rem', borderRadius: '8px', background: '#fff' }}>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#6c757d' }}>Usuarios Totales</h3>
              <p style={{ margin: 0, fontSize: '1.75rem', fontWeight: '700' }}>{kpis.total_users}</p>
            </div>
            <div className="kpi-card" style={{ border: '1px solid #ddd', padding: '1.5rem', borderRadius: '8px', background: '#fff' }}>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#6c757d' }}>Órdenes Totales</h3>
              <p style={{ margin: 0, fontSize: '1.75rem', fontWeight: '700' }}>{kpis.total_orders}</p>
            </div>
            <div className="kpi-card" style={{ border: '1px solid #ddd', padding: '1.5rem', borderRadius: '8px', background: '#fff' }}>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#6c757d' }}>Ticket Promedio</h3>
              <p style={{ margin: 0, fontSize: '1.75rem', fontWeight: '700' }}>${kpis.average_ticket.toFixed(2)}</p>
            </div>
            <div className="kpi-card" style={{ border: '1px solid #ddd', padding: '1.5rem', borderRadius: '8px', background: '#fff' }}>
              <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: '#6c757d' }}>Gastos Totales</h3>
              <p style={{ margin: 0, fontSize: '1.75rem', fontWeight: '700' }}>${kpis.total_expenses.toFixed(2)}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminPanelPage;