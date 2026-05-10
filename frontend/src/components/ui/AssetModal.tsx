import React, { useState } from 'react';
import { Modal } from './Modal';
import { Barcode, Tag, MapPin, Calendar, DollarSign, Activity } from 'lucide-react';
import { useCreateAsset } from '../../hooks/useAssets';
import { useDepartments } from '../../hooks/useDepartments';
import { useWarehouses, useWarehouseDetails } from '../../hooks/useWarehouses';
import { useToast } from '../../context/ToastContext';

interface AssetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AssetModal: React.FC<AssetModalProps> = ({ isOpen, onClose }) => {
  const { addToast } = useToast();
  const createAsset = useCreateAsset();
  const { data: departments } = useDepartments();
  const { data: warehouses } = useWarehouses();
  
  const [formData, setFormData] = useState({
    name: '',
    type: 'Hardware',
    asset_code: '',
    serial_number: '',
    purchase_date: new Date().toISOString().split('T')[0],
    purchase_value: 0,
    useful_life: 5,
    department_id: '',
    warehouse_id: '',
    bin_id: '',
    location: '',
  });

  const { data: bins } = useWarehouseDetails(Number(formData.warehouse_id));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        department_id: Number(formData.department_id),
        warehouse_id: formData.warehouse_id ? Number(formData.warehouse_id) : undefined,
        bin_id: formData.bin_id ? Number(formData.bin_id) : undefined,
      };
      await createAsset.mutateAsync(payload);
      addToast('success', 'Asset Registered', `${formData.name} has been added to the portfolio.`);
      onClose();
      setFormData({
        name: '',
        type: 'Hardware',
        asset_code: '',
        serial_number: '',
        purchase_date: new Date().toISOString().split('T')[0],
        purchase_value: 0,
        useful_life: 5,
        department_id: '',
        warehouse_id: '',
        bin_id: '',
        location: '',
      });
    } catch (err) {
      addToast('error', 'Registration Failed', 'Please verify form data and try again.');
    }
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="Register New Asset" 
      size="xl"
      footer={
        <>
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button 
            onClick={handleSubmit} 
            disabled={createAsset.isPending}
            className="btn-primary"
          >
            {createAsset.isPending ? 'Registering...' : 'Register Asset'}
          </button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Tag className="w-3 h-3" /> Asset Name
            </label>
            <input 
              type="text" 
              required
              className="input-field" 
              placeholder="e.g. MacBook Pro 16 - IT-042"
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-3 h-3" /> Asset Type
            </label>
            <select 
              className="input-field"
              value={formData.type}
              onChange={e => setFormData({...formData, type: e.target.value})}
            >
              <option>Hardware</option>
              <option>Software</option>
              <option>Furniture</option>
              <option>Vehicle</option>
              <option>Infrastructure</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Barcode className="w-3 h-3" /> Asset Code
            </label>
            <input 
              type="text" 
              required
              className="input-field font-mono" 
              placeholder="AST-00000"
              value={formData.asset_code}
              onChange={e => setFormData({...formData, asset_code: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Barcode className="w-3 h-3" /> Serial Number
            </label>
            <input 
              type="text" 
              className="input-field font-mono" 
              placeholder="S/N: XXX-XXX-XXX"
              value={formData.serial_number}
              onChange={e => setFormData({...formData, serial_number: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Calendar className="w-3 h-3" /> Purchase Date
            </label>
            <input 
              type="date" 
              className="input-field" 
              value={formData.purchase_date}
              onChange={e => setFormData({...formData, purchase_date: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <DollarSign className="w-3 h-3" /> Purchase Value (KES)
            </label>
            <input 
              type="number" 
              className="input-field" 
              value={formData.purchase_value}
              onChange={e => setFormData({...formData, purchase_value: Number(e.target.value)})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Calendar className="w-3 h-3" /> Useful Life (Years)
            </label>
            <input 
              type="number" 
              className="input-field" 
              value={formData.useful_life}
              onChange={e => setFormData({...formData, useful_life: Number(e.target.value)})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Tag className="w-3 h-3" /> Assigned Department
            </label>
            <select 
              required
              className="input-field"
              value={formData.department_id}
              onChange={e => setFormData({...formData, department_id: e.target.value})}
            >
              <option value="">Select Department</option>
              {departments?.map((dept: any) => (
                <option key={dept.id} value={dept.id}>{dept.name} ({dept.code})</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-3 h-3" /> Warehouse
            </label>
            <select 
              className="input-field"
              value={formData.warehouse_id}
              onChange={e => setFormData({...formData, warehouse_id: e.target.value, bin_id: ''})}
            >
              <option value="">Select Warehouse</option>
              {warehouses?.map((wh: any) => (
                <option key={wh.id || wh.warehouse_id} value={wh.id || wh.warehouse_id}>{wh.name || wh.warehouse_name}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-3 h-3" /> Specific Bin
            </label>
            <select 
              className="input-field"
              value={formData.bin_id}
              onChange={e => setFormData({...formData, bin_id: e.target.value})}
              disabled={!formData.warehouse_id}
            >
              <option value="">Select Bin (Optional)</option>
              {bins?.map((bin: any) => (
                <option key={bin.id} value={bin.id}>{bin.code} {bin.description ? `- ${bin.description}` : ''}</option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-3 h-3" /> Legacy Location String
            </label>
            <input 
              type="text" 
              className="input-field" 
              placeholder="e.g. Floor 2, Zone B"
              value={formData.location}
              onChange={e => setFormData({...formData, location: e.target.value})}
            />
          </div>
        </div>
      </form>
    </Modal>
  );
};
