import { QRCodeSVG } from 'qrcode.react';
import { Download, Printer, Barcode } from 'lucide-react';
import { useRef } from 'react';

interface AssetQRCodeProps {
  entityType: 'asset' | 'inventory';
  entityId: number;
  organisationId: number;
  label?: string;
  code?: string;
}

export const AssetQRCode = ({ entityType, entityId, organisationId, label, code }: AssetQRCodeProps) => {
  const qrRef = useRef<HTMLDivElement>(null);

  const qrData = JSON.stringify({
    type: entityType,
    id: entityId,
    org: organisationId
  });

  const downloadQR = () => {
    const svg = qrRef.current?.querySelector('svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height + 40; // Space for label
      if (ctx) {
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
        
        ctx.fillStyle = 'black';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(code || `ID: ${entityId}`, canvas.width / 2, img.height + 20);
      }
      
      const pngFile = canvas.toDataURL('image/png');
      const downloadLink = document.createElement('a');
      downloadLink.download = `${entityType}-${code || entityId}.png`;
      downloadLink.href = pngFile;
      downloadLink.click();
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  return (
    <div className="flex flex-col items-center gap-4 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
      <div ref={qrRef} className="p-3 bg-white rounded-xl ring-1 ring-slate-100">
        <QRCodeSVG 
          value={qrData} 
          size={160}
          level="H"
          includeMargin={false}
          imageSettings={{
            src: "/logo-mini.png", // If you have a logo
            x: undefined,
            y: undefined,
            height: 24,
            width: 24,
            excavate: true,
          }}
        />
      </div>
      
      <div className="text-center">
        <p className="text-xs font-bold text-slate-900 uppercase tracking-tighter">{label || 'Asset Tag'}</p>
        <p className="text-[10px] font-mono text-slate-400 mt-0.5">{code || `ID-${entityId}`}</p>
      </div>

      <div className="flex gap-2 w-full mt-2">
        <button 
          onClick={downloadQR}
          className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-slate-50 hover:bg-slate-100 text-slate-600 rounded-lg text-[10px] font-bold transition-colors"
        >
          <Download className="w-3.5 h-3.5" /> Download
        </button>
        <button 
          className="flex-1 flex items-center justify-center gap-2 py-2 px-3 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-lg text-[10px] font-bold transition-colors"
          onClick={() => window.print()}
        >
          <Printer className="w-3.5 h-3.5" /> Print
        </button>
      </div>
    </div>
  );
};
