import React from 'react';
import { Line, Bar } from 'react-chartjs-2';
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

  // Datos para el gráfico de ventas
  const salesChartData = {
    labels: salesData?.data.length > 0 ? salesData.data.map(d => new Date(d.fecha).toLocaleDateString('es-AR')) : ['Día 1', 'Día 2', 'Día 3'], // Etiquetas por defecto si no hay datos
    datasets: [{
      label: 'Ventas por Día',
      data: salesData?.data.length > 0 ? salesData.data.map(d => d.total) : [0, 0, 0], // Datos por defecto en 0
      borderColor: 'rgb(75, 192, 192)',
      backgroundColor: 'rgba(75, 192, 192, 0.2)', // Un poco transparente si no hay datos
      pointBackgroundColor: 'rgb(75, 192, 192)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgb(75, 192, 192)',
      tension: 0.3, // Curva suave
      fill: true, // Rellena el área bajo la línea
    }]
  };

  // Opciones para el gráfico de ventas (importante para que muestre los ejes)
  const salesChartOptions = {
    responsive: true,
    maintainAspectRatio: false, // Permite controlar el tamaño del gráfico
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false, // Ya tenemos un h3 con el título
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Fecha',
        },
        grid: {
          display: false, // Opcional: ocultar las líneas de la grilla vertical
        },
      },
      y: {
        title: {
          display: true,
          text: 'Monto ($)',
        },
        beginAtZero: true,
        min: 0,
        // Acá le damos un maximo si no hay datos, para que no se vea chato
        max: salesData?.data.length > 0 ? undefined : 100, 
      },
    },
  };

  // --- GRÁFICO DE VENTAS (MODIFICADO) ---
  const salesChartComponent = (
    <div className="chart-widget" style={{ height: '400px' }}> {/* Le damos una altura fija */}
      <h3>Evolución de Ventas</h3>
      <Line data={salesChartData} options={salesChartOptions} />
    </div>
  );

  // --- Gráfico de Gastos (mejorado un poco también para el caso vacío) ---
  const expensesChartData = {
    labels: expensesData?.data.length > 0 ? expensesData.data.map(d => d.categoria) : ['Categoría 1', 'Categoría 2', 'Categoría 3'],
    datasets: [{
      label: 'Monto Gastado',
      data: expensesData?.data.length > 0 ? expensesData.data.map(d => d.monto) : [0, 0, 0],
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
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
      tooltip: {
        mode: 'index',
        intersect: false,
      },
    },
    scales: {
        x: {
            beginAtZero: true,
            min: 0,
            max: expensesData?.data.length > 0 ? undefined : 100,
            title: {
                display: true,
                text: 'Monto ($)',
            },
        },
        y: {
            title: {
                display: true,
                text: 'Categoría',
            },
        }
    }
  };

  const expensesChartComponent = (
    <div className="chart-widget" style={{ height: '400px' }}> {/* También le damos altura */}
      <h3>Gastos por Categoría</h3>
      <Bar data={expensesChartData} options={expensesChartOptions} />
    </div>
  );

  return (
    <div className="admin-charts-container" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
      {salesChartComponent}
      {expensesChartComponent}
    </div>
  );
};

export default AdminCharts;