/**
 * Truck Entry Page
 *
 * Manual entry form for weighbridge truck operations.
 */

import React, { useState } from 'react';

interface TruckEntryForm {
  truck_id: string;
  driver_name: string;
  company: string;
  gross_weight: string;
  tare_weight: string;
  product_type: string;
  product_quality: string;
  moisture_percent: string;
  impurity_percent: string;
  origin_farm: string;
  origin_city: string;
  origin_state: string;
  notes: string;
}

export const TruckEntryPage: React.FC = () => {
  const [formData, setFormData] = useState<TruckEntryForm>({
    truck_id: '',
    driver_name: '',
    company: '',
    gross_weight: '',
    tare_weight: '',
    product_type: 'corn',
    product_quality: '',
    moisture_percent: '',
    impurity_percent: '',
    origin_farm: '',
    origin_city: '',
    origin_state: '',
    notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // Get current site_id from localStorage or context
      const siteId = localStorage.getItem('currentSiteId') || '1';

      const requestData = {
        truck_id: formData.truck_id,
        driver_name: formData.driver_name || undefined,
        company: formData.company || undefined,
        gross_weight: parseFloat(formData.gross_weight),
        tare_weight: parseFloat(formData.tare_weight),
        product_type: formData.product_type,
        product_quality: formData.product_quality || undefined,
        moisture_percent: formData.moisture_percent ? parseFloat(formData.moisture_percent) : undefined,
        impurity_percent: formData.impurity_percent ? parseFloat(formData.impurity_percent) : undefined,
        origin_farm: formData.origin_farm || undefined,
        origin_city: formData.origin_city || undefined,
        origin_state: formData.origin_state || undefined,
        entry_time: new Date().toISOString(),
        site_id: parseInt(siteId),
        notes: formData.notes || undefined,
      };

      const response = await fetch('/api/v1/operations/trucks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error('Erro ao registrar entrada de caminhão');
      }

      setSuccess(true);

      // Reset form
      setFormData({
        truck_id: '',
        driver_name: '',
        company: '',
        gross_weight: '',
        tare_weight: '',
        product_type: 'corn',
        product_quality: '',
        moisture_percent: '',
        impurity_percent: '',
        origin_farm: '',
        origin_city: '',
        origin_state: '',
        notes: '',
      });

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  const calculateNetWeight = () => {
    if (formData.gross_weight && formData.tare_weight) {
      const gross = parseFloat(formData.gross_weight);
      const tare = parseFloat(formData.tare_weight);
      if (!isNaN(gross) && !isNaN(tare)) {
        return (gross - tare).toFixed(2);
      }
    }
    return '-';
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Entrada de Caminhão</h1>
          <p className="text-gray-600 mt-2">Registrar pesagem de caminhão na balança</p>
        </div>

        {/* Success Alert */}
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
            ✓ Entrada de caminhão registrada com sucesso!
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            ✗ {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6 space-y-6">
          {/* Truck Identification */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
              Identificação do Caminhão
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Placa do Caminhão *
                </label>
                <input
                  type="text"
                  name="truck_id"
                  value={formData.truck_id}
                  onChange={handleChange}
                  required
                  placeholder="ABC-1234"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome do Motorista
                </label>
                <input
                  type="text"
                  name="driver_name"
                  value={formData.driver_name}
                  onChange={handleChange}
                  placeholder="João Silva"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Empresa Transportadora
                </label>
                <input
                  type="text"
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  placeholder="Transportadora XYZ"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Weight Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
              Pesagem
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Peso Bruto (kg) *
                </label>
                <input
                  type="number"
                  name="gross_weight"
                  value={formData.gross_weight}
                  onChange={handleChange}
                  required
                  step="0.01"
                  placeholder="35000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tara (kg) *
                </label>
                <input
                  type="number"
                  name="tare_weight"
                  value={formData.tare_weight}
                  onChange={handleChange}
                  required
                  step="0.01"
                  placeholder="15000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Peso Líquido (kg)
                </label>
                <div className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-lg font-semibold text-blue-600">
                  {calculateNetWeight()}
                </div>
              </div>
            </div>
          </div>

          {/* Product Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
              Informações do Produto
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Produto *
                </label>
                <select
                  name="product_type"
                  value={formData.product_type}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="corn">Milho</option>
                  <option value="soy">Soja</option>
                  <option value="wheat">Trigo</option>
                  <option value="other">Outro</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Qualidade
                </label>
                <select
                  name="product_quality"
                  value={formData.product_quality}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Selecione...</option>
                  <option value="A">Tipo A</option>
                  <option value="B">Tipo B</option>
                  <option value="C">Tipo C</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Umidade (%)
                </label>
                <input
                  type="number"
                  name="moisture_percent"
                  value={formData.moisture_percent}
                  onChange={handleChange}
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="14.5"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Impureza (%)
                </label>
                <input
                  type="number"
                  name="impurity_percent"
                  value={formData.impurity_percent}
                  onChange={handleChange}
                  step="0.1"
                  min="0"
                  max="100"
                  placeholder="1.2"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Origin Information */}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
              Origem
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fazenda
                </label>
                <input
                  type="text"
                  name="origin_farm"
                  value={formData.origin_farm}
                  onChange={handleChange}
                  placeholder="Fazenda São João"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cidade
                </label>
                <input
                  type="text"
                  name="origin_city"
                  value={formData.origin_city}
                  onChange={handleChange}
                  placeholder="Paranaguá"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estado
                </label>
                <input
                  type="text"
                  name="origin_state"
                  value={formData.origin_state}
                  onChange={handleChange}
                  placeholder="PR"
                  maxLength={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Observações
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={3}
              placeholder="Observações adicionais..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Submit Button */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => window.history.back()}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Salvando...' : 'Registrar Entrada'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
