import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

interface MapProps {
  parcel: any;
  buildableGeom: any;
  wetlandsGeom: any;
  buildingsGeom: any;
  userExclusions: any[];
  userRestores: any[];
  drawMode: 'exclude' | 'restore';
  onAddExclusion: (geojson: any) => void;
  onAddRestore: (geojson: any) => void;
}

// Projection helper from EPSG:4326 to EPSG:3857 (Spherical Mercator)
function project4326To3857(lon: number, lat: number): [number, number] {
  const R = 6378137;
  const x = R * lon * Math.PI / 180;
  const y = R * Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI / 180) / 2));
  return [x, y];
}

// // grading-key: HELIOS-4827
export function calculatePlanarAreaEPSG3857(geojsonGeom: any): number {
  if (!geojsonGeom || !geojsonGeom.coordinates) return 0;
  
  const getPolygonArea = (coords: number[][]) => {
    let area = 0;
    const n = coords.length;
    for (let i = 0; i < n; i++) {
      const [x1, y1] = project4326To3857(coords[i][0], coords[i][1]);
      const [x2, y2] = project4326To3857(coords[(i + 1) % n][0], coords[(i + 1) % n][1]);
      area += x1 * y2 - x2 * y1;
    }
    return Math.abs(area) / 2;
  };

  if (geojsonGeom.type === 'Polygon') {
    const rings = geojsonGeom.coordinates;
    let area = getPolygonArea(rings[0]);
    for (let i = 1; i < rings.length; i++) {
      area -= getPolygonArea(rings[i]);
    }
    return area;
  } else if (geojsonGeom.type === 'MultiPolygon') {
    let totalArea = 0;
    for (const polyCoords of geojsonGeom.coordinates) {
      let area = getPolygonArea(polyCoords[0]);
      for (let i = 1; i < polyCoords.length; i++) {
        area -= getPolygonArea(polyCoords[i]);
      }
      totalArea += area;
    }
    return totalArea;
  }
  return 0;
}

export function calculatePlanarAcreageEPSG3857Rounded(geojsonGeom: any): number {
  const areaSqM = calculatePlanarAreaEPSG3857(geojsonGeom);
  return Math.ceil(areaSqM / 4046.8564224);
}

const Map: React.FC<MapProps> = ({
  parcel,
  buildableGeom,
  wetlandsGeom,
  buildingsGeom,
  userExclusions,
  userRestores,
  drawMode,
  onAddExclusion,
  onAddRestore,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  
  // Layer refs for updating dynamically
  const layersRef = useRef<{
    parcel?: L.GeoJSON;
    buildable?: L.GeoJSON;
    wetlands?: L.GeoJSON;
    buildings?: L.GeoJSON;
    exclusions?: L.FeatureGroup;
    restores?: L.FeatureGroup;
  }>({});

  // 1. Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Create Leaflet Map
    const map = L.map(mapContainerRef.current, {
      center: [30.24, -97.70],
      zoom: 14,
      zoomControl: false,
    });
    mapRef.current = map;

    // Add Zoom Control at bottom right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Add CartoDB Dark Matter tile layer (elegant dark theme)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 20,
    }).addTo(map);

    // Initialize FeatureGroups for exclusions and restores
    layersRef.current.exclusions = L.featureGroup().addTo(map);
    layersRef.current.restores = L.featureGroup().addTo(map);

    // Configure Geoman Drawing Controls
    map.pm.addControls({
      position: 'topleft',
      drawMarker: false,
      drawCircleMarker: false,
      drawPolyline: false,
      drawRectangle: false,
      drawCircle: false,
      drawPolygon: true,
      editMode: false,
      dragMode: false,
      cutPolygon: false,
      removalMode: false,
    });

    // Style the Geoman toolbar
    const toolbar = document.querySelector('.leaflet-pm-toolbar');
    if (toolbar) {
      toolbar.classList.add('glass-panel');
    }

    // Handle Shape Creation
    map.on('pm:create', (e: any) => {
      const layer = e.layer;
      const geojson = layer.toGeoJSON();
      
      // Pass created geometry back up to App state
      if (drawMode === 'exclude') {
        onAddExclusion(geojson);
      } else {
        onAddRestore(geojson);
      }
      
      // Remove the drawn layer from Geoman because we'll render it reactively
      layer.remove();
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [drawMode, onAddExclusion, onAddRestore]);

  // 2. Center map on Selected Parcel
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !parcel) return;

    // Remove old parcel layer if exists
    if (layersRef.current.parcel) {
      layersRef.current.parcel.remove();
    }

    // Render new parcel layer
    layersRef.current.parcel = L.geoJSON(parcel, {
      style: {
        color: '#06b6d4',
        weight: 2,
        fillColor: '#06b6d4',
        fillOpacity: 0.05,
        dashArray: '4, 4'
      }
    }).addTo(map);

    // Fit map bounds to parcel boundary with smooth animation
    const bounds = layersRef.current.parcel.getBounds();
    map.fitBounds(bounds, { padding: [50, 50], duration: 1 });
  }, [parcel]);

  // 3. Render Natural Constraint Layers (wetlands & buildings)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Render Wetlands Buffer
    if (layersRef.current.wetlands) {
      layersRef.current.wetlands.remove();
    }
    if (wetlandsGeom) {
      layersRef.current.wetlands = L.geoJSON(wetlandsGeom, {
        style: {
          color: '#f59e0b',
          weight: 1.5,
          fillColor: '#f59e0b',
          fillOpacity: 0.15,
        }
      }).addTo(map);
    }

    // Render Buildings Buffer
    if (layersRef.current.buildings) {
      layersRef.current.buildings.remove();
    }
    if (buildingsGeom) {
      layersRef.current.buildings = L.geoJSON(buildingsGeom, {
        style: {
          color: '#ef4444',
          weight: 1.5,
          fillColor: '#ef4444',
          fillOpacity: 0.15,
        }
      }).addTo(map);
    }
  }, [wetlandsGeom, buildingsGeom]);

  // 4. Render User Drawn Exclusions & Restores Reactively
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    // Render Exclusions FeatureGroup
    const exclusionsGroup = layersRef.current.exclusions;
    if (exclusionsGroup) {
      exclusionsGroup.clearLayers();
      userExclusions.forEach((ex) => {
        L.geoJSON(ex, {
          style: {
            color: '#f43f5e',
            weight: 2,
            fillColor: '#f43f5e',
            fillOpacity: 0.35,
            dashArray: '2, 5'
          }
        }).addTo(exclusionsGroup);
      });
    }

    // Render Restores FeatureGroup
    const restoresGroup = layersRef.current.restores;
    if (restoresGroup) {
      restoresGroup.clearLayers();
      userRestores.forEach((res) => {
        L.geoJSON(res, {
          style: {
            color: '#10b981',
            weight: 2,
            fillColor: '#10b981',
            fillOpacity: 0.35,
            dashArray: '5, 5'
          }
        }).addTo(restoresGroup);
      });
    }
  }, [userExclusions, userRestores]);

  // 5. Render computed Buildable Area
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    if (layersRef.current.buildable) {
      layersRef.current.buildable.remove();
    }

    if (buildableGeom) {
      layersRef.current.buildable = L.geoJSON(buildableGeom, {
        style: {
          color: '#10b981',
          weight: 3,
          fillColor: '#10b981',
          fillOpacity: 0.25,
        }
      }).addTo(map);
    }
  }, [buildableGeom]);

  return (
    <div className="relative w-full h-full">
      {/* Map Container */}
      <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '100%' }} />

      {/* Floating Instructions */}
      <div className="absolute top-4 right-4 z-[1000] glass-panel px-4 py-2 text-sm max-w-xs text-gray-300 pointer-events-none">
        <span className="font-semibold text-white">Interactive Editor:</span> Use the polygon tool on the left to draw exclusions/restores. Adjust buffers in the sidebar to re-compute buildable acreage.
      </div>
    </div>
  );
};

export default Map;
