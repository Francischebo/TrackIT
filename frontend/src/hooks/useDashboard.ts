import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import type { RestockAlert } from '../types';

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const response = await api.get('/analytics/dashboard/summary');
      return response.data as { 
        inventory: { total_items: number; health: Record<string, number> };
        total_valuation: number;
        currency: string;
      };
    },
    refetchInterval: 30000,
  });
};

export const useDashboardMovements = (days: number = 7) => {
  return useQuery({
    queryKey: ['dashboard-movements', days],
    queryFn: async () => {
      const response = await api.get(`/analytics/dashboard/movements?days=${days}`);
      return response.data as Record<string, { IN: number; OUT: number }>;
    },
  });
};

export const useAlerts = () => {
  return useQuery({
    queryKey: ['active-alerts'],
    queryFn: async () => {
      const response = await api.get<RestockAlert[]>('/restock/alerts');
      return response.data;
    },
  });
};
