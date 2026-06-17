import { useState, useEffect, useCallback } from 'react';
import Map from './components/Map';
import Sidebar from './components/Sidebar';
import ParcelSelector from './components/ParcelSelector';
import { Compass, RefreshCw } from 'lucide-react';

const API_BASE_URL = import.meta.env.DEV ? 'http://localhost:8000' : '';

function App() {
  const [parcels, setParcels] = useState<any[]>([]);
  const [selectedParcelId, setSelectedParcelId] = useState<string | null>(null);
  
  // Buffers and Drawing state
  const [wetlandBuffer, setWetlandBuffer] = useState<number>(100);
  const [buildingBuffer, setBuildingBuffer] = useState<number>(50);
  const [userExclusions, setUserExclusions] = useState<any[]>([]);
  const [userRestores, setUserRestores] = useState<any[]>([]);
  const [drawMode, setDrawMode] = useState<'exclude' | 'restore'>('exclude');
  
  // API Results
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch available parcels on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/parcels`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to retrieve parcel list');
        return res.json();
      })
      .then((data) => {
        setParcels(data);
        if (data.length > 0) {
          setSelectedParcelId(data[0].id);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError('Connection to GIS Backend failed. Please ensure the FastAPI server is running.');
        setLoading(false);
      });
  }, []);

  // 2. Perform Buildable Land Analysis
  const performAnalysis = useCallback(() => {
    if (!selectedParcelId) return;

    // Build analyze request payload
    const payload = {
      parcel_id: selectedParcelId,
      wetland_buffer_feet: wetlandBuffer,
      building_buffer_feet: buildingBuffer,
      user_exclusions: {
        type: 'FeatureCollection',
        features: userExclusions,
      },
      user_restores: {
        type: 'FeatureCollection',
        features: userRestores,
      },
    };

    fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Analysis request failed');
        return res.json();
      })
      .then((data) => {
        setAnalysisResult(data);
      })
      .catch((err) => {
        console.error('Analysis error:', err);
      });
  }, [selectedParcelId, wetlandBuffer, buildingBuffer, userExclusions, userRestores]);

  // Trigger analysis when relevant parameters change
  useEffect(() => {
    performAnalysis();
  }, [performAnalysis]);

  // Callback to add drawn exclusion shapes
  const handleAddExclusion = useCallback((geojson: any) => {
    setUserExclusions((prev) => [...prev, geojson]);
  }, []);

  // Callback to add drawn restore shapes
  const handleAddRestore = useCallback((geojson: any) => {
    setUserRestores((prev) => [...prev, geojson]);
  }, []);

  // Callback to remove specific exclusion
  const handleRemoveExclusion = useCallback((index: number) => {
    setUserExclusions((prev) => prev.filter((_, idx) => idx !== index));
  }, []);

  // Callback to remove specific restore
  const handleRemoveRestore = useCallback((index: number) => {
    setUserRestores((prev) => prev.filter((_, idx) => idx !== index));
  }, []);

  // Clear all custom drawn layers
  const handleClearDrawing = useCallback(() => {
    setUserExclusions([]);
    setUserRestores([]);
  }, []);

  // Handle switching selected parcel
  const handleSelectParcel = useCallback((id: string) => {
    setSelectedParcelId(id);
    // Clear user drawings when switching parcels
    setUserExclusions([]);
    setUserRestores([]);
  }, []);

  // Find selected parcel details
  const selectedParcel = parcels.find((p) => p.id === selectedParcelId);

  // Loading Screen
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center w-screen h-screen bg-[#090a0f] text-white space-y-4">
        <Compass className="w-12 h-12 text-cyan-400 animate-spin" />
        <h2 className="text-lg font-semibold tracking-wide">Initializing LandBuilder ...</h2>
        <p className="text-xs text-gray-500">Loading spatial layers and parcel models</p>
      </div>
    );
  }

  // Error Screen
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center w-screen h-screen bg-[#090a0f] text-white p-6 text-center space-y-6">
        <div className="bg-rose-500/10 border border-rose-500/30 p-8 rounded-2xl max-w-md">
          <h2 className="text-xl font-bold text-rose-400 mb-2">Backend Connection Error</h2>
          <p className="text-sm text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-2 mx-auto bg-cyan-500 hover:bg-cyan-600 text-black font-semibold py-2 px-6 rounded-lg transition-colors cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Connection</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-screen h-screen overflow-hidden p-4 gap-4 bg-[#090a0f]">
      {/* 1. Directory Sidebar */}
      <ParcelSelector
        parcels={parcels}
        selectedParcelId={selectedParcelId}
        onSelectParcel={handleSelectParcel}
      />

      {/* 2. Interactive Map Canvas */}
      <div className="flex-1 glass-panel overflow-hidden relative">
        <Map
          parcel={selectedParcel?.geometry}
          buildableGeom={analysisResult?.geometries?.buildable}
          wetlandsGeom={analysisResult?.geometries?.wetlands_clipped}
          buildingsGeom={analysisResult?.geometries?.buildings_clipped}
          userExclusions={userExclusions}
          userRestores={userRestores}
          drawMode={drawMode}
          onAddExclusion={handleAddExclusion}
          onAddRestore={handleAddRestore}
        />
      </div>

      {/* 3. Metrics & Setback Controller */}
      <Sidebar
        wetlandBuffer={wetlandBuffer}
        setWetlandBuffer={setWetlandBuffer}
        buildingBuffer={buildingBuffer}
        setBuildingBuffer={setBuildingBuffer}
        drawMode={drawMode}
        setDrawMode={setDrawMode}
        metrics={analysisResult?.metrics || null}
        userExclusions={userExclusions}
        onRemoveExclusion={handleRemoveExclusion}
        userRestores={userRestores}
        onRemoveRestore={handleRemoveRestore}
        onClearDrawing={handleClearDrawing}
      />
    </div>
  );
}

export default App;
