import React from 'react';
import { Line, Bar } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next'; // Importar
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

const AdminCharts = ({ salesData, expensesData }) => {
  const { t } = useTranslation(); // Inicializar

  // Datos para el gráfico de ventas
  const salesChartData = {
    labels: salesData?.data.length > 0 ? salesData.data.map(d => new Date(d.fecha).toLocaleDateString('es-AR')) : ['Día 1', 'Día 2', 'Día 3'],
    datasets: [{
      label: t('admin_chart_sales_per_day'),
      data: salesData?.data.length > 0 ? salesData.data.map(d => d.total) : [0, 0, 0],
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)',
      pointBackgroundColor: 'rgb(75, 192, 192)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgb(75, 192, 192)',
      tension: 0.3,
      fill: true,
    }]
  };

  const salesChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: false },
      tooltip: { mode: 'index', intersect: false },
    },
    scales: {
      x: {
        title: { display: true, text: 'Fecha' },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: 'Monto ($)' },
        beginAtZero: true,
        min: 0,
        max: salesData?.data.length > 0 ? undefined : 100,
      },
    },
  };

  // --- Gráfico de Gastos ---
  const expensesChartData = {
    labels: expensesData?.data.length > 0 ? expensesData.data.map(d => d.categoria) : ['Categoría 1', 'Categoría 2'],
    datasets: [{
      label: t('admin_chart_amount_spent'),
      data: expensesData?.data.length > 0 ? expensesData.data.map(d => d.monto) : [0, 0],
      backgroundColor: 'rgba(255, 99, 132, 0.5)',
      borderColor: 'rgb(255, 99, 132)',
      borderWidth: 1,
    }]
  };

  const expensesChartOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: false },
      tooltip: { mode: 'index', intersect: false },
    },
    scales: {
        x: {
            beginAtZero: true,
            min: 0,
            max: expensesData?.data.length > 0 ? undefined : 100,
            title: { display: true, text: 'Monto ($)' },
        },
        y: {
            title: { display: true, text: 'Categoría' },
        }
    }
  };

  return (
    <div className="admin-charts-container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
      <div className="chart-widget" style={{ height: '400px' }}>
        <h3>{t('admin_chart_sales_evolution')}</h3>
        <Line data={salesChartData} options={salesChartOptions} />
      </div>
      <div className="chart-widget" style={{ height: '400px' }}>
        <h3>{t('admin_chart_expenses_by_category')}</h3>
        <Bar data={expensesChartData} options={expensesChartOptions} />
      </div>
    </div>
  );
};

export default AdminCharts;