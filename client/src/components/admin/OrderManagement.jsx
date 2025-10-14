import React from 'react';
import { useTranslation } from 'react-i18next';

const OrderManagement = () => {
  const { t } = useTranslation();
  return <div><h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>{t('admin_order_management_title')}</h1><p>{t('admin_coming_soon')}</p></div>;
};

export default OrderManagement;