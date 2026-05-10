import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { useToast } from '../context/ToastContext';

export interface OrganizationSettings {
  id: number;
  name: string;
  code: string;
  description: string;
  logo_url?: string;
  preferences?: Record<string, any>;
  is_active: boolean;
}

export const useOrganizationSettings = () => {
  return useQuery({
    queryKey: ['settings', 'organization'],
    queryFn: async () => {
      const response = await api.get<{ organization: OrganizationSettings }>('/settings/organization');
      return response.data.organization;
    },
  });
};

export const useUpdateOrganizationSettings = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: async (data: Partial<OrganizationSettings>) => {
      const response = await api.put<{ message: string; organization: OrganizationSettings }>('/settings/organization', data);
      return response.data;
    },
    onSuccess: (data) => {
      addToast('success', 'Settings Saved', data.message);
      queryClient.invalidateQueries({ queryKey: ['settings', 'organization'] });
    },
    onError: (error: any) => {
      addToast('error', 'Update Failed', error.response?.data?.message || 'Could not save settings');
    },
  });
};

export const useUploadOrganizationLogo = () => {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('logo', file);
      const response = await api.post<{ message: string; logo_url: string }>('/settings/organization/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: (data) => {
      addToast('success', 'Logo Uploaded', data.message);
      queryClient.invalidateQueries({ queryKey: ['settings', 'organization'] });
    },
    onError: (error: any) => {
      addToast('error', 'Upload Failed', error.response?.data?.message || 'Could not upload logo');
    },
  });
};

export const useExportData = () => {
  const { addToast } = useToast();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/settings/organization/export', {}, { responseType: 'blob' });
      return response.data;
    },
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `system_export_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      addToast('success', 'Export Complete', 'Your data export has been downloaded.');
    },
    onError: (error: any) => {
      addToast('error', 'Export Failed', 'Could not generate data export.');
    },
  });
};

export const usePurgeData = () => {
  const { addToast } = useToast();

  return useMutation({
    mutationFn: async () => {
      const response = await api.delete<{ message: string; records_deleted: number }>('/settings/organization/purge');
      return response.data;
    },
    onSuccess: (data) => {
      addToast('success', 'Data Purged', data.message);
    },
    onError: (error: any) => {
      addToast('error', 'Purge Failed', error.response?.data?.message || 'Could not purge data.');
    },
  });
};
