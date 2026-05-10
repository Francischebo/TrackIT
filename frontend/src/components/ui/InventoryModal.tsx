import React, { useState } from 'react';
import { Modal } from './Modal';
import { Package, Hash, Layers, AlertTriangle, DollarSign, Settings } from 'lucide-react';
import { useCreateInventoryItem } from '../../hooks/useInventory';
import { useToast } from '../../context/ToastContext';

interface InventoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const InventoryModal: React.FC<InventoryModalProps> = ({ isOpen, onClose }) => {
  const { addToast } = useToast();
  const createItem = useCreateInventoryItem();
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    description: '',
    reorder_level: 10,
    unit_price: 0,
    unit: 'pcs',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createItem.mutateAsync(formData);
      addToast('success', 'SKU Created', `${formData.name} has been added to inventory.`);
      onClose();
      setFormData({
        name: '',
        sku: '',
        description: '',
        reorder_level: 10,
        unit_price: 0,
        unit: 'pcs',
      });
    } catch (err) {
      addToast('error', 'Creation Failed', 'Please verify form data and try again.');
    }
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="Create New Inventory SKU" 
      size="lg"
      footer={
        <>
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button 
            onClick={handleSubmit} 
            disabled={createItem.isPending}
            className="btn-primary"
          >
            {createItem.isPending ? 'Creating...' : 'Create SKU'}
          </button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Package className="w-3 h-3" /> Item Name
            </label>
            <input 
              type="text" 
              required
              className="input-field" 
              placeholder="e.g. Ethernet Cable Cat6"
              value={formData.name}
              onChange={e => setFormData({...formData, name: e.target.value})}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                <Hash className="w-3 h-3" /> SKU / Model
              </label>
              <input 
                type="text" 
                required
                className="input-field font-mono" 
                placeholder="SKU-XXXXXX"
                value={formData.sku}
                onChange={e => setFormData({...formData, sku: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                <Settings className="w-3 h-3" /> Unit Type
              </label>
              <select 
                className="input-field"
                value={formData.unit}
                onChange={e => setFormData({...formData, unit: e.target.value})}
              >
                <option value="pcs">Pieces (pcs)</option>
                <option value="box">Boxes (box)</option>
                <option value="kg">Kilograms (kg)</option>
                <option value="m">Meters (m)</option>
                <option value="ltr">Liters (ltr)</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                <DollarSign className="w-3 h-3" /> Unit Price (KES)
              </label>
              <input 
                type="number" 
                className="input-field" 
                value={formData.unit_price}
                onChange={e => setFormData({...formData, unit_price: Number(e.target.value)})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-3 h-3" /> Reorder Level
              </label>
              <input 
                type="number" 
                className="input-field" 
                value={formData.reorder_level}
                onChange={e => setFormData({...formData, reorder_level: Number(e.target.value)})}
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-3 h-3" /> Description
            </label>
            <textarea 
              className="input-field h-24 resize-none" 
              placeholder="Operational details and specifications..."
              value={formData.description}
              onChange={e => setFormData({...formData, description: e.target.value})}
            />
          </div>
        </div>
      </form>
    </Modal>
  );
};
