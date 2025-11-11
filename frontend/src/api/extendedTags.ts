/**
 * Extended Tags API Client
 * Handles all API calls for extended tags and formulas
 */

import axios from 'axios';
import {
  GatewayTagExtended,
  GatewayTagExtendedCreate,
  GatewayTagExtendedUpdate,
  TagFormula,
  TagFormulaCreate,
  TagFormulaUpdate,
  BulkTagOperation,
  ExtendedTagFilters,
  FormulaFilters
} from '../types/extendedTags';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with auth
const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============================================================================
// Extended Tags
// ============================================================================

export const extendedTagsApi = {
  /**
   * List extended tags with optional filters
   */
  async list(filters?: ExtendedTagFilters): Promise<GatewayTagExtended[]> {
    const response = await client.get<GatewayTagExtended[]>(
      `/api/v1/tags`,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get single extended tag by ID
   */
  async get(tagId: number): Promise<GatewayTagExtended> {
    const response = await client.get<GatewayTagExtended>(
      `/api/v1/tags/${tagId}`
    );
    return response.data;
  },

  /**
   * Create new extended tag
   */
  async create(tagData: GatewayTagExtendedCreate): Promise<GatewayTagExtended> {
    const response = await client.post<GatewayTagExtended>(
      `/api/v1/tags`,
      tagData
    );
    return response.data;
  },

  /**
   * Update existing extended tag
   */
  async update(
    tagId: number,
    tagData: GatewayTagExtendedUpdate
  ): Promise<GatewayTagExtended> {
    const response = await client.put<GatewayTagExtended>(
      `/api/v1/tags/${tagId}`,
      tagData
    );
    return response.data;
  },

  /**
   * Delete extended tag
   */
  async delete(tagId: number): Promise<void> {
    await client.delete(`/api/v1/tags/${tagId}`);
  },

  /**
   * Perform bulk operations on tags
   */
  async bulkOperation(operation: BulkTagOperation): Promise<{ message: string }> {
    const response = await client.post<{ message: string }>(
      `/api/v1/tags/bulk`,
      operation
    );
    return response.data;
  }
};

// ============================================================================
// Tag Formulas
// ============================================================================

export const formulasApi = {
  /**
   * List tag formulas with optional filters
   */
  async list(filters?: FormulaFilters): Promise<TagFormula[]> {
    const response = await client.get<TagFormula[]>(
      `/api/v1/extended-tags/formulas`,
      { params: filters }
    );
    return response.data;
  },

  /**
   * Get single formula by ID
   */
  async get(formulaId: number): Promise<TagFormula> {
    const response = await client.get<TagFormula>(
      `/api/v1/extended-tags/formulas/${formulaId}`
    );
    return response.data;
  },

  /**
   * Create new formula
   */
  async create(formulaData: TagFormulaCreate): Promise<TagFormula> {
    const response = await client.post<TagFormula>(
      `/api/v1/extended-tags/formulas`,
      formulaData
    );
    return response.data;
  },

  /**
   * Update existing formula
   */
  async update(
    formulaId: number,
    formulaData: TagFormulaUpdate
  ): Promise<TagFormula> {
    const response = await client.put<TagFormula>(
      `/api/v1/extended-tags/formulas/${formulaId}`,
      formulaData
    );
    return response.data;
  },

  /**
   * Delete formula
   */
  async delete(formulaId: number): Promise<void> {
    await client.delete(`/api/v1/extended-tags/formulas/${formulaId}`);
  }
};

// Export combined API
export default {
  tags: extendedTagsApi,
  formulas: formulasApi
};
