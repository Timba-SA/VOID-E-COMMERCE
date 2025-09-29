
import React, { useState, useEffect } from 'react';
import {
    getKpisAPI,
    getSalesOverTimeAPI,
    getExpensesByCategoryAPI
} from '../api/adminApi';
import Spinner from '../components/common/Spinner';
import AdminCharts from '../components/admin/AdminCharts';

const AdminDashboardPage = () => {
  const [kpis, setKpis] = useState(null);
  const [salesData, setSalesData] = useState(null);
  const [expensesData, setExpensesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const [kpisResponse, salesResponse, expensesResponse] = await Promise.all([
          getKpisAPI(),
          getSalesOverTimeAPI(),
          getExpensesByCategoryAPI()
        ]);

        setKpis(kpisResponse);
        setSalesData(salesResponse);
        setExpensesData(expensesResponse);

      } catch (err) {
        setError(err.detail || 'No se pudieron cargar los datos del dashboard.');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <Spinner message="Cargando dashboard..." />;

  return (
    <>
        <h1>Dashboard</h1>
        <p>Desde acá vas a poder controlar toda la magia de VOID.</p>

        {error && <p style={{color: 'red'}}>Error: {error}</p>}

        {kpis && (
          <div className="dashboard-widgets">
            <div className="widget">
              <h3>Ingresos Totales</h3>
              <p className="widget-value">${kpis.total_revenue.toLocaleString('es-AR')}</p>
            </div>
            <div className="widget">
              <h3>Ticket Promedio</h3>
              <p className="widget-value">${kpis.average_ticket.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
            </div>
            <div className="widget">
              <h3>Órdenes Totales</h3>
              <p className="widget-value">{kpis.total_orders}</p>
            </div>

            {/* --- ¡WIDGET NUEVO AGREGADO ACÁ! --- */}
            <div className="widget">
              <h3>Productos Vendidos</h3>
              <p className="widget-value">{kpis.total_products_sold}</p>
            </div>
            {/* --- FIN DEL WIDGET NUEVO --- */}

             <div className="widget">
              <h3>Usuarios Registrados</h3>
              <p className="widget-value">{kpis.total_users}</p>
            </div>
            <div className="widget">
              <h3>Gastos Totales</h3>
              <p className="widget-value">${kpis.total_expenses.toLocaleString('es-AR')}</p>
            </div>
          </div>
        )}
        <div className="dashboard-charts-section">
          <AdminCharts salesData={salesData} expensesData={expensesData} />
        </div>
    </>
  );
};

export default AdminDashboardPage;