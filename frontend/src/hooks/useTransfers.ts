import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';

export interface TransferRequest {
  id: number;
  asset_id: number;
  asset_code: string;
  asset_name: string;
  from_department_name: string;
  to_department_name: string;
  requested_location: string;
  comment: string;
  status: 'pending' | 'approved' | 'rejected';
  requested_by: string;
  requested_at: string;
}

export const useTransferRequests = (status = 'pending', page = 1) => {
  return useQuery({
    queryKey: ['transfer-requests', status, page],
    queryFn: async () => {
      const response = await api.get<{ transfer_requests: TransferRequest[], pagination: any }>('/transfers/requests', {
        params: { status, page }
      });
      return response.data;
    }
  });
};

export const useApproveTransfer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, comments }: { id: number; comments?: string }) => {
      const response = await api.post(`/transfers/requests/${id}/approve`, { comments });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfer-requests'] });
      queryClient.invalidateQueries({ queryKey: ['assets'] });
    }
  });
};

export const useRejectTransfer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, comments }: { id: number; comments: string }) => {
      const response = await api.post(`/transfers/requests/${id}/reject`, { comments });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfer-requests'] });
    }
  });
};

export const useRequestTransfer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { asset_id: number; new_department_id: number; new_location?: string; comment?: string }) => {
      const response = await api.post('/transfers/request', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transfer-requests'] });
    }
  });
};
