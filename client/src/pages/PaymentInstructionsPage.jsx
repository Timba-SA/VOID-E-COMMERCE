import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const PaymentInstructionsPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [countdown, setCountdown] = useState(5);
  const paymentUrl = searchParams.get('url');
  const orderId = searchParams.get('order_id');

  useEffect(() => {
    if (!paymentUrl) {
      navigate('/');
      return;
    }

    // Countdown antes de redirigir
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          window.location.href = paymentUrl; // Redirigir a Mercado Pago
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [paymentUrl, navigate]);

  const handleContinue = () => {
    window.location.href = paymentUrl;
  };

  const successUrl = orderId 
    ? `${window.location.origin}/payment/success?order_id=${orderId}`
    : `${window.location.origin}/payment/success`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-8 md:p-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-6">
            <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {t('payment.redirecting', 'Redirigiendo a Mercado Pago...')}
          </h1>
          <p className="text-gray-600">
            {t('payment.redirectingIn', 'Serás redirigido en')} <span className="font-bold text-blue-600 text-2xl">{countdown}</span>s
          </p>
        </div>

        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 mb-6">
          <div className="flex items-start">
            <svg className="w-6 h-6 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                {t('payment.important', '⚠️ Instrucciones Importantes')}
              </h3>
              <ol className="list-decimal list-inside space-y-2 text-sm text-yellow-700">
                <li>Completa el pago en la página de Mercado Pago que se abrirá</li>
                <li>Después del pago, <strong>haz clic en el botón "Volver al sitio"</strong></li>
                <li>Si no ves el botón, copia esta URL y pégala en tu navegador:</li>
              </ol>
              <div className="mt-3 bg-white border border-yellow-300 rounded-lg p-3">
                <code className="text-xs text-gray-800 break-all select-all">
                  {successUrl}
                </code>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={handleContinue}
            className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-indoo-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
          >
            {t('payment.continueNow', 'Continuar Ahora →')}
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-4 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-all duration-200"
          >
            {t('common.cancel', 'Cancelar')}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            🔒 {t('payment.secure', 'Pago seguro procesado por Mercado Pago')}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentInstructionsPage;
