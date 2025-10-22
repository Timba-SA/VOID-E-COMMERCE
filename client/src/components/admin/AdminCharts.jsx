import React from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement, 
  ArcElement,
  Title, 
  Tooltip, 
  Legend
);

const AdminCharts = ({ 
  salesData, 
  expensesData, 
  salesByCategoryData, 
  topProductsData, 
  userActivityData 
}) => {
  const { t } = useTranslation();

  // =================== 1. GRÁFICO DE VENTAS EN EL TIEMPO (LÍNEAS) ===================
  const salesChartData = {
    labels: salesData?.data?.length > 0 
      ? salesData.data.map(d => new Date(d.fecha).toLocaleDateString('es-AR'))
      : ['Sin datos'],
    datasets: [{
      label: t('admin_chart_sales_per_day', 'Ventas por día ($)'),
      data: salesData?.data?.length > 0 
        ? salesData.data.map(d => d.total) 
        : [0],
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
      tooltip: { 
        mode: 'index', 
        intersect: false,
        callbacks: {
          label: (context) => `${context.dataset.label}: $${context.parsed.y.toLocaleString('es-AR')}`
        }
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Fecha' },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: 'Monto ($)' },
        beginAtZero: true,
        ticks: {
          callback: (value) => `$${value.toLocaleString('es-AR')}`
        }
      },
    },
  };

  // =================== 2. GRÁFICO DE GASTOS POR CATEGORÍA (BARRAS HORIZONTALES) ===================
  const expensesChartData = {
    labels: expensesData?.data?.length > 0 
      ? expensesData.data.map(d => d.categoria) 
      : ['Sin datos'],
    datasets: [{
      label: t('admin_chart_amount_spent', 'Monto gastado ($)'),
      data: expensesData?.data?.length > 0 
        ? expensesData.data.map(d => d.monto) 
        : [0],
      backgroundColor: 'rgba(255, 99, 132, 0.6)',
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
      tooltip: {
        callbacks: {
          label: (context) => `${context.dataset.label}: $${context.parsed.x.toLocaleString('es-AR')}`
        }
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        title: { display: true, text: 'Monto ($)' },
        ticks: {
          callback: (value) => `$${value.toLocaleString('es-AR')}`
        }
      },
      y: {
        title: { display: true, text: 'Categoría' },
      }
    }
  };

  // =================== 3. GRÁFICO DE VENTAS POR CATEGORÍA (TORTA) ===================
  const pieColors = [
    'rgba(255, 99, 132, 0.8)',
    'rgba(54, 162, 235, 0.8)',
    'rgba(255, 206, 86, 0.8)',
    'rgba(75, 192, 192, 0.8)',
    'rgba(153, 102, 255, 0.8)',
    'rgba(255, 159, 64, 0.8)',
  ];

  const salesByCategoryChartData = {
    labels: salesByCategoryData?.data?.length > 0
      ? salesByCategoryData.data.map(d => d.categoria)
      : ['Sin datos'],
    datasets: [{
      label: t('admin_chart_sales_amount', 'Ventas'),
      data: salesByCategoryData?.data?.length > 0
        ? salesByCategoryData.data.map(d => d.total_vendido)
        : [0],
      backgroundColor: pieColors,
      borderColor: '#fff',
      borderWidth: 2,
    }]
  };

  const salesByCategoryChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { 
        position: 'right',
        labels: {
          padding: 15,
          font: { size: 12 }
        }
      },
      title: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => {
            const dataPoint = salesByCategoryData?.data?.[context.dataIndex];
            if (dataPoint) {
              return `${context.label}: $${dataPoint.total_vendido.toLocaleString('es-AR')} (${dataPoint.porcentaje}%)`;
            }
            return '';
          }
        }
      },
    },
  };

  // =================== 4. GRÁFICO DE TOP PRODUCTOS (BARRAS) ===================
  const topProductsChartData = {
    labels: topProductsData?.data?.length > 0
      ? topProductsData.data.map(d => d.nombre_producto)
      : ['Sin datos'],
    datasets: [{
      label: t('admin_chart_units_sold', 'Unidades vendidas'),
      data: topProductsData?.data?.length > 0
        ? topProductsData.data.map(d => d.cantidad_vendida)
        : [0],
      backgroundColor: 'rgba(54, 162, 235, 0.6)',
      borderColor: 'rgb(54, 162, 235)',
      borderWidth: 1,
    }]
  };

  const topProductsChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => {
            const dataPoint = topProductsData?.data?.[context.dataIndex];
            if (dataPoint) {
              return [
                `Unidades: ${dataPoint.cantidad_vendida}`,
                `Ingresos: $${dataPoint.ingresos_totales.toLocaleString('es-AR')}`
              ];
            }
            return '';
          }
        }
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Producto' },
      },
      y: {
        title: { display: true, text: 'Cantidad vendida' },
        beginAtZero: true,
      }
    }
  };

  // =================== 5. GRÁFICO DE ACTIVIDAD DE USUARIOS (LÍNEAS) ===================
  const userActivityChartData = {
    labels: userActivityData?.data?.length > 0
      ? userActivityData.data.map(d => new Date(d.fecha).toLocaleDateString('es-AR'))
      : ['Sin datos'],
    datasets: [{
      label: t('admin_chart_new_users', 'Nuevos usuarios'),
      data: userActivityData?.data?.length > 0
        ? userActivityData.data.map(d => d.nuevos_usuarios)
        : [0],
      borderColor: 'rgb(153, 102, 255)',
      backgroundColor: 'rgba(153, 102, 255, 0.2)',
      pointBackgroundColor: 'rgb(153, 102, 255)',
      pointBorderColor: '#fff',
      tension: 0.3,
      fill: true,
    }]
  };

  const userActivityChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: false },
      tooltip: { 
        mode: 'index', 
        intersect: false 
      },
    },
    scales: {
      x: {
        title: { display: true, text: 'Fecha' },
        grid: { display: false },
      },
      y: {
        title: { display: true, text: 'Cantidad de usuarios' },
        beginAtZero: true,
        ticks: {
          stepSize: 1,
        }
      },
    },
  };

  return (
    <div className="admin-charts-container">
      {/* Fila 1: Ventas en el tiempo (ancho completo) */}
      {salesData?.data?.length > 0 && (
        <div className="chart-widget chart-full-width">
          <h3>{t('admin_chart_sales_evolution', 'Evolución de Ventas (últimos 30 días)')}</h3>
          <div className="chart-wrapper">
            <Line data={salesChartData} options={salesChartOptions} />
          </div>
        </div>
      )}

      {/* Fila 2: Ventas por categoría (torta) + Top productos (barras) */}
      {salesByCategoryData?.data?.length > 0 && (
        <div className="chart-widget chart-half-width">
          <h3>{t('admin_chart_sales_by_category', 'Distribución de Ventas por Categoría')}</h3>
          <div className="chart-wrapper">
            <Pie data={salesByCategoryChartData} options={salesByCategoryChartOptions} />
          </div>
        </div>
      )}

      {topProductsData?.data?.length > 0 && (
        <div className="chart-widget chart-half-width">
          <h3>{t('admin_chart_top_products', 'Top 5 Productos Más Vendidos')}</h3>
          <div className="chart-wrapper">
            <Bar data={topProductsChartData} options={topProductsChartOptions} />
          </div>
        </div>
      )}

      {/* Fila 3: Gastos por categoría (SIEMPRE SE MUESTRA) + Actividad de usuarios */}
      <div className="chart-widget chart-half-width">
        <h3>{t('admin_chart_expenses_by_category', 'Gastos por Categoría')}</h3>
        <div className="chart-wrapper">
          {expensesData?.data?.length > 0 ? (
            <Bar data={expensesChartData} options={expensesChartOptions} />
          ) : (
            <div className="chart-empty-state">
              <p>{t('no_expenses_chart', 'No hay gastos registrados.')}</p>
              <a href="/admin/expenses" className="btn btn-primary">
                {t('manage_expenses', 'Gestionar Gastos')}
              </a>
            </div>
          )}
        </div>
      </div>

      {userActivityData?.data?.length > 0 && (
        <div className="chart-widget chart-half-width">
          <h3>{t('admin_chart_user_activity', 'Actividad de Usuarios (últimos 30 días)')}</h3>
          <div className="chart-wrapper">
            <Line data={userActivityChartData} options={userActivityChartOptions} />
          </div>
        </div>
      )}

      {/* Mensaje si no hay datos en ningún gráfico */}
      {!salesData?.data?.length && 
       !salesByCategoryData?.data?.length && 
       !topProductsData?.data?.length && 
       !expensesData?.data?.length && 
       !userActivityData?.data?.length && (
        <div className="no-data-message">
          <p>{t('admin_charts_no_data', 'No hay datos suficientes para mostrar gráficos. Asegúrate de tener órdenes aprobadas, productos vendidos y usuarios registrados.')}</p>
        </div>
      )}
    </div>
  );
};

export default AdminCharts;