/**
 * Ship Loading Page
 *
 * Manual entry form for ship loading operations.
 */

import React, { useState, useEffect } from 'react';

interface ShipLoadingForm {
  ship_name: string;
  ship_imo: string;
  ship_flag: string;
  ship_dwt: string;
  berth_number: string;
  product_type: string;
  target_tonnage: string;
  buyer_company: string;
  destination_port: string;
  destination_country: string;
  contract_number: string;
  notes: string;
}

interface ActiveLoading {
  id: number;
  ship_name: string;
  berth_number: number;
  status: string;
  loaded_tonnage: number;
  target_tonnage: number;
  completion_percent: number;
}

export const ShipLoadingPage: React.FC = () => {
  const [formData, setFormData] = useState<ShipLoadingForm>({
    ship_name: '',
    ship_imo: '',
    ship_flag: '',
    ship_dwt: '',
    berth_number: '1',
    product_type: 'corn',
    target_tonnage: '',
    buyer_company: '',
    destination_port: '',
    destination_country: '',
    contract_number: '',
    notes: '',
  });

  const [activeLoadings, setActiveLoadings] = useState<ActiveLoading[]>([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchActiveLoadings();
  }, []);

  const fetchActiveLoadings = async () => {
    try {
      const siteId = localStorage.getItem('currentSiteId') || '1';
      const response = await fetch(
        `/api/v1/operations/ships?site_id=${siteId}&status=loading&limit=5`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setActiveLoadings(data.loadings || []);
      }
    } catch (err) {
      console.error('Error fetching active loadings:', err);
    }
  };

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
      const siteId = localStorage.getItem('currentSiteId') || '1';

      const requestData = {
        ship_name: formData.ship_name,
        ship_imo: formData.ship_imo || undefined,
        ship_flag: formData.ship_flag || undefined,
        ship_dwt: formData.ship_dwt ? parseFloat(formData.ship_dwt) : undefined,
        berth_number: parseInt(formData.berth_number),
        product_type: formData.product_type,
        target_tonnage: parseFloat(formData.target_tonnage),
        arrival_time: new Date().toISOString(),
        buyer_company: formData.buyer_company || undefined,
        destination_port: formData.destination_port || undefined,
        destination_country: formData.destination_country || undefined,
        contract_number: formData.contract_number || undefined,
        site_id: parseInt(siteId),
        notes: formData.notes || undefined,
      };

      const response = await fetch('/api/v1/operations/ships', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error('Erro ao registrar operação de carregamento');
      }

      setSuccess(true);

      // Reset form
      setFormData({
        ship_name: '',
        ship_imo: '',
        ship_flag: '',
        ship_dwt: '',
        berth_number: '1',
        product_type: 'corn',
        target_tonnage: '',
        buyer_company: '',
        destination_port: '',
        destination_country: '',
        contract_number: '',
        notes: '',
      });

      // Refresh active loadings
      fetchActiveLoadings();

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Carregamento de Navio</h1>
          <p className="text-gray-600 mt-2">Registrar operação de carregamento de grãos</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2">
            {/* Success Alert */}
            {success && (
              <div className="mb-6 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded">
                ✓ Operação de carregamento registrada com sucesso!
              </div>
            )}

            {/* Error Alert */}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
                ✗ {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6 space-y-6">
              {/* Ship Information */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
                  Informações do Navio
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nome do Navio *
                    </label>
                    <input
                      type="text"
                      name="ship_name"
                      value={formData.ship_name}
                      onChange={handleChange}
                      required
                      placeholder="MV Atlantic Star"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Número IMO
                    </label>
                    <input
                      type="text"
                      name="ship_imo"
                      value={formData.ship_imo}
                      onChange={handleChange}
                      placeholder="IMO 9123456"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Bandeira
                    </label>
                    <input
                      type="text"
                      name="ship_flag"
                      value={formData.ship_flag}
                      onChange={handleChange}
                      placeholder="Panamá"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      DWT (toneladas)
                    </label>
                    <input
                      type="number"
                      name="ship_dwt"
                      value={formData.ship_dwt}
                      onChange={handleChange}
                      step="0.01"
                      placeholder="50000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Loading Details */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
                  Detalhes do Carregamento
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Berço *
                    </label>
                    <select
                      name="berth_number"
                      value={formData.berth_number}
                      onChange={handleChange}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="1">Berço 1</option>
                      <option value="2">Berço 2</option>
                      <option value="3">Berço 3</option>
                      <option value="4">Berço 4</option>
                    </select>
                  </div>
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
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tonelagem Alvo *
                    </label>
                    <input
                      type="number"
                      name="target_tonnage"
                      value={formData.target_tonnage}
                      onChange={handleChange}
                      required
                      step="0.01"
                      placeholder="30000"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Commercial Information */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4 border-b pb-2">
                  Informações Comerciais
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Empresa Compradora
                    </label>
                    <input
                      type="text"
                      name="buyer_company"
                      value={formData.buyer_company}
                      onChange={handleChange}
                      placeholder="ABC Trading"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Número do Contrato
                    </label>
                    <input
                      type="text"
                      name="contract_number"
                      value={formData.contract_number}
                      onChange={handleChange}
                      placeholder="CT-2025-001"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Porto de Destino
                    </label>
                    <input
                      type="text"
                      name="destination_port"
                      value={formData.destination_port}
                      onChange={handleChange}
                      placeholder="Rotterdam"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      País de Destino
                    </label>
                    <input
                      type="text"
                      name="destination_country"
                      value={formData.destination_country}
                      onChange={handleChange}
                      placeholder="Holanda"
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
                  placeholder="Observações sobre a operação..."
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
                  {loading ? 'Salvando...' : 'Registrar Operação'}
                </button>
              </div>
            </form>
          </div>

          {/* Active Loadings Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Carregamentos Ativos
              </h2>

              {activeLoadings.length === 0 ? (
                <p className="text-gray-500 text-sm">Nenhum carregamento ativo no momento</p>
              ) : (
                <div className="space-y-4">
                  {activeLoadings.map((loading) => (
                    <div
                      key={loading.id}
                      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold text-gray-900">{loading.ship_name}</p>
                          <p className="text-sm text-gray-600">Berço {loading.berth_number}</p>
                        </div>
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {loading.status}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>{loading.loaded_tonnage.toLocaleString()} t</span>
                          <span>{loading.target_tonnage.toLocaleString()} t</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${Math.min(loading.completion_percent || 0, 100)}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-600 mt-1 text-right">
                          {loading.completion_percent?.toFixed(1) || 0}% concluído
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={fetchActiveLoadings}
                className="mt-4 w-full px-4 py-2 border border-gray-300 rounded-md text-sm text-gray-700 hover:bg-gray-50"
              >
                🔄 Atualizar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
