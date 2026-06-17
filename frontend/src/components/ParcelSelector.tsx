import React, { useState } from 'react';
import { MapPin, User, Search, Home } from 'lucide-react';

interface ParcelSelectorProps {
  parcels: any[];
  selectedParcelId: string | null;
  onSelectParcel: (id: string) => void;
}

const ParcelSelector: React.FC<ParcelSelectorProps> = ({
  parcels,
  selectedParcelId,
  onSelectParcel,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredParcels = parcels.filter((p) => {
    const term = searchTerm.toLowerCase();
    return (
      p.address.toLowerCase().includes(term) ||
      p.owner.toLowerCase().includes(term) ||
      p.id.toLowerCase().includes(term)
    );
  });

  return (
    <div className="w-80 glass-panel h-[calc(100vh-2rem)] flex flex-col overflow-hidden animate-fade-in">
      {/* Header with Search */}
      <div className="p-6 border-b border-white/5 space-y-4">
        <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold">
          <Home className="w-4 h-4" />
          <span>Parcel Directories</span>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by address or owner..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-white/5 border border-white/5 rounded-lg py-2 pl-9 pr-4 text-xs text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400/50 focus:ring-1 focus:ring-cyan-400/50"
          />
        </div>
      </div>

      {/* List Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredParcels.length === 0 ? (
          <div className="text-center text-xs text-gray-400 py-8">No parcels match your search.</div>
        ) : (
          filteredParcels.map((p) => {
            const isSelected = p.id === selectedParcelId;
            return (
              <div
                key={p.id}
                onClick={() => onSelectParcel(p.id)}
                className={`p-4 rounded-xl border hover-card-interactive cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-500/10 border-cyan-400/50 selected-glow shadow-md shadow-cyan-400/5'
                    : 'bg-white/[0.02] border-white/5 hover:bg-white/5 hover:border-white/10'
                }`}
              >
                <div className="flex justify-between items-start gap-2 mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                    isSelected ? 'bg-cyan-500/20 text-cyan-300' : 'bg-white/5 text-gray-400'
                  }`}>
                    PID: {p.id}
                  </span>
                  <span className="text-xs font-bold text-gray-300">{p.total_acres_rounded} acres</span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-start gap-1.5 text-white font-medium line-clamp-2">
                    <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                    <span>{p.address}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-gray-400">
                    <User className="w-3.5 h-3.5 text-gray-500 shrink-0" />
                    <span className="truncate">{p.owner}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Info Footnote */}
      <div className="p-4 border-t border-white/5 text-[10px] text-gray-500 text-center">
        Select a parcel to visualize spatial constraints.
      </div>
    </div>
  );
};

export default ParcelSelector;
