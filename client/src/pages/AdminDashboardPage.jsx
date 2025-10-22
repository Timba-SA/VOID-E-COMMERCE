import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
    getKpisAPI,
    getSalesOverTimeAPI,
    getExpensesByCategoryAPI,
    getSalesByCategoryAPI,
    getTopProductsAPI,
    getUserActivityAPI
} from '../api/adminApi';
import Spinner from '../components/common/Spinner';
import AdminCharts from '../components/admin/AdminCharts';

const AdminDashboardPage = () => {
  const { t } = useTranslation();
  const [kpis, setKpis] = useState(null);
  const [salesData, setSalesData] = useState(null);
  const [expensesData, setExpensesData] = useState(null);
  const [salesByCategoryData, setSalesByCategoryData] = useState(null);
  const [topProductsData, setTopProductsData] = useState(null);
  const [userActivityData, setUserActivityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const [
          kpisResponse, 
          salesResponse, 
          expensesResponse,
          salesByCategoryResponse,
          topProductsResponse,
          userActivityResponse
        ] = await Promise.all([
          getKpisAPI(),
          getSalesOverTimeAPI(),
          getExpensesByCategoryAPI(),
          getSalesByCategoryAPI(),
          getTopProductsAPI(5),
          getUserActivityAPI()
        ]);
        
        setKpis(kpisResponse);
        setSalesData(salesResponse);
        setExpensesData(expensesResponse);
        setSalesByCategoryData(salesByCategoryResponse);
        setTopProductsData(topProductsResponse);
        setUserActivityData(userActivityResponse);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError(err.detail || t('admin_dashboard_error', 'Could not load dashboard data.'));
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [t]);

  if (loading) return <Spinner message={t('admin_dashboard_loading')} />;

  return (
    <>
        <h1>{t('admin_dashboard_title')}</h1>
        <p>{t('admin_dashboard_subtitle')}</p>

        {error && <p style={{color: 'red'}}>Error: {error}</p>}

        {kpis && (
          <div className="dashboard-widgets">
            <div className="widget">
              <h3>{t('admin_kpi_total_revenue')}</h3>
              <p className="widget-value">${kpis.total_revenue.toLocaleString('es-AR')}</p>
            </div>
            <div className="widget">
              <h3>{t('admin_kpi_avg_ticket')}</h3>
              <p className="widget-value">${kpis.average_ticket.toLocaleString('es-AR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
            </div>
            <div className="widget">
              <h3>{t('admin_kpi_total_orders')}</h3>
              <p className="widget-value">{kpis.total_orders}</p>
            </div>
            <div className="widget">
              <h3>{t('admin_kpi_products_sold')}</h3>
              <p className="widget-value">{kpis.total_products_sold}</p>
            </div>
             <div className="widget">
              <h3>{t('admin_kpi_total_users')}</h3>
              <p className="widget-value">{kpis.total_users}</p>
            </div>
            <div className="widget">
              <h3>{t('admin_kpi_total_expenses')}</h3>
              <p className="widget-value">${kpis.total_expenses.toLocaleString('es-AR')}</p>
            </div>
          </div>
        )}
        <div className="dashboard-charts-section">
          <AdminCharts 
            salesData={salesData} 
            expensesData={expensesData}
            salesByCategoryData={salesByCategoryData}
            topProductsData={topProductsData}
            userActivityData={userActivityData}
          />
        </div>
    </>
  );
};

export default AdminDashboardPage;