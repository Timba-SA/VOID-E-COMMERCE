import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { getExpensesAPI, createExpenseAPI, deleteExpenseAPI } from '../../api/adminApi';
import Spinner from '../common/Spinner';

const ExpenseManagement = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Estados del formulario
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    descripcion: '',
    monto: '',
    categoria: '',
    fecha: new Date().toISOString().split('T')[0] // Fecha actual por defecto
  });

  // Función para formatear fecha correctamente (sin problema de zona horaria)
  const formatDate = (dateString) => {
    if (!dateString) return '';
    
    // Agregar 'T00:00:00' para evitar problema de zona horaria
    const date = new Date(dateString + 'T00:00:00');
    
    return date.toLocaleDateString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  // Query para obtener gastos
  const { data: expenses, isLoading, error } = useQuery({
    queryKey: ['expenses'],
    queryFn: getExpensesAPI
  });

  // Mutation para crear gasto
  const createMutation = useMutation({
    mutationFn: createExpenseAPI,
    onSuccess: () => {
      // Invalidar todas las queries relacionadas
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      queryClient.invalidateQueries({ queryKey: ['expensesByCategory'] });
      
      // Resetear formulario
      setShowForm(false);
      setFormData({
        descripcion: '',
        monto: '',
        categoria: '',
        fecha: new Date().toISOString().split('T')[0]
      });
      
      alert(t('expense_created_success', 'Gasto creado exitosamente'));
    },
    onError: (error) => {
      alert(t('expense_created_error', 'Error al crear gasto: ') + (error.detail || error.message));
    }
  });

  // Mutation para eliminar gasto
  const deleteMutation = useMutation({
    mutationFn: deleteExpenseAPI,
    onSuccess: () => {
      // Invalidar todas las queries relacionadas
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
      queryClient.invalidateQueries({ queryKey: ['expensesByCategory'] });
      
      alert(t('expense_deleted_success', 'Gasto eliminado exitosamente'));
    },
    onError: (error) => {
      alert(t('expense_deleted_error', 'Error al eliminar gasto: ') + (error.detail || error.message));
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validaciones
    if (!formData.descripcion.trim()) {
      alert(t('expense_error_description', 'La descripción es obligatoria'));
      return;
    }
    if (!formData.monto || parseFloat(formData.monto) <= 0) {
      alert(t('expense_error_amount', 'El monto debe ser mayor a 0'));
      return;
    }
    if (!formData.categoria.trim()) {
      alert(t('expense_error_category', 'La categoría es obligatoria'));
      return;
    }
    if (!formData.fecha) {
      alert(t('expense_error_date', 'La fecha es obligatoria'));
      return;
    }

    createMutation.mutate({
      descripcion: formData.descripcion,
      monto: parseFloat(formData.monto),
      categoria: formData.categoria,
      fecha: formData.fecha
    });
  };

  const handleDelete = (expenseId) => {
    if (window.confirm(t('expense_delete_confirm', '¿Estás seguro de eliminar este gasto?'))) {
      deleteMutation.mutate(expenseId);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (isLoading) return <Spinner message={t('loading_expenses', 'Cargando gastos...')} />;

  return (
    <div className="expense-management">
      <div className="admin-header">
        <h1>{t('expense_management_title', 'Gestión de Gastos')}</h1>
        <button 
          className="btn btn-primary" 
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? t('cancel', 'Cancelar') : t('add_expense', 'Agregar Gasto')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {t('error_loading_expenses', 'Error al cargar gastos: ')} {error.detail || error.message}
        </div>
      )}

      {/* Formulario para crear gasto */}
      {showForm && (
        <div className="expense-form-container">
          <h2>{t('new_expense_title', 'Nuevo Gasto')}</h2>
          <form onSubmit={handleSubmit} className="expense-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="descripcion">
                  {t('expense_description', 'Descripción')} <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="descripcion"
                  name="descripcion"
                  value={formData.descripcion}
                  onChange={handleChange}
                  placeholder={t('expense_description_placeholder', 'Ej: Hosting mensual AWS')}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="monto">
                  {t('expense_amount', 'Monto ($)')} <span className="required">*</span>
                </label>
                <input
                  type="number"
                  id="monto"
                  name="monto"
                  value={formData.monto}
                  onChange={handleChange}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="categoria">
                  {t('expense_category', 'Categoría')} <span className="required">*</span>
                </label>
                <select
                  id="categoria"
                  name="categoria"
                  value={formData.categoria}
                  onChange={handleChange}
                  required
                >
                  <option value="">-- {t('select', 'Seleccione')} --</option>
                  <option value="Tecnología">Tecnología</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Logística">Logística</option>
                  <option value="Finanzas">Finanzas</option>
                  <option value="Operaciones">Operaciones</option>
                  <option value="RRHH">Recursos Humanos</option>
                  <option value="Otros">Otros</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="fecha">
                  {t('expense_date', 'Fecha')} <span className="required">*</span>
                </label>
                <input
                  type="date"
                  id="fecha"
                  name="fecha"
                  value={formData.fecha}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending 
                  ? t('saving', 'Guardando...') 
                  : t('save_expense', 'Guardar Gasto')
                }
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tabla de gastos */}
      <div className="expenses-table-container">
        <h2>{t('expenses_list', 'Lista de Gastos')}</h2>
        
        {expenses && expenses.length === 0 ? (
          <p className="no-data-message">
            {t('no_expenses', 'No hay gastos registrados. Agrega el primero para verlo reflejado en el gráfico.')}
          </p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('expense_date', 'Fecha')}</th>
                <th>{t('expense_description', 'Descripción')}</th>
                <th>{t('expense_category', 'Categoría')}</th>
                <th>{t('expense_amount', 'Monto')}</th>
                <th>{t('actions', 'Acciones')}</th>
              </tr>
            </thead>
            <tbody>
              {expenses?.map((expense) => (
                <tr key={expense.id}>
                  <td>{expense.id}</td>
                  <td>{formatDate(expense.fecha)}</td>
                  <td>{expense.descripcion}</td>
                  <td>
                    <span className={`category-badge category-${expense.categoria?.toLowerCase().replace(/\s/g, '-')}`}>
                      {expense.categoria}
                    </span>
                  </td>
                  <td className="text-right">
                    ${expense.monto.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td>
                    <button
                      onClick={() => handleDelete(expense.id)}
                      className="action-btn delete"
                      disabled={deleteMutation.isPending}
                    >
                      {t('delete', 'Eliminar')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            {expenses && expenses.length > 0 && (
              <tfoot>
                <tr>
                  <td colSpan="4" className="text-right"><strong>{t('total', 'Total')}:</strong></td>
                  <td className="text-right">
                    <strong>
                      ${expenses.reduce((sum, exp) => sum + exp.monto, 0).toLocaleString('es-AR', { 
                        minimumFractionDigits: 2, 
                        maximumFractionDigits: 2 
                      })}
                    </strong>
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            )}
          </table>
        )}
      </div>
    </div>
  );
};

export default ExpenseManagement;
