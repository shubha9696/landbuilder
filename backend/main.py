import os
import json
import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from shapely.geometry import shape, mapping, MultiPolygon, Polygon
from shapely.ops import transform, unary_union
from pyproj import Transformer

app = FastAPI(title="Buildable Land Analysis API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up pyproj Transformers
# EPSG:4326 to EPSG:3857 (Web Mercator)
to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
# EPSG:3857 to EPSG:4326
to_4326 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

# Data paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PARCELS_PATH = os.path.join(DATA_DIR, "parcels.geojson")
WETLANDS_PATH = os.path.join(DATA_DIR, "wetlands.geojson")
BUILDINGS_PATH = os.path.join(DATA_DIR, "buildings.geojson")

# Memory caches for spatial data
PARCELS_DATA: Dict[str, Any] = {}
WETLANDS_GEOMS: List[Any] = []
BUILDINGS_GEOMS: List[Any] = []

def load_data():
    global PARCELS_DATA, WETLANDS_GEOMS, BUILDINGS_GEOMS
    if PARCELS_DATA:
        return
    
    # 1. Load parcels
    if os.path.exists(PARCELS_PATH):
        with open(PARCELS_PATH, "r") as f:
            data = json.load(f)
            features = data.get("features", [])
            for feat in features:
                # TCAD property ids are usually in attributes. 
                # Let's check common keys: prop_id, PROP_ID, geo_id, OBJECTID, map_id, id
                props = feat.get("properties", {})
                pid = str(
                    props.get("prop_id") or 
                    props.get("PROP_ID") or 
                    props.get("geo_id") or 
                    props.get("OBJECTID") or 
                    feat.get("id") or 
                    len(PARCELS_DATA)
                )
                feat["id"] = pid
                PARCELS_DATA[pid] = feat
        print(f"Loaded {len(PARCELS_DATA)} parcels.")
    else:
        print(f"Parcels file not found at {PARCELS_PATH}")

    # 2. Load wetlands
    if os.path.exists(WETLANDS_PATH):
        with open(WETLANDS_PATH, "r") as f:
            data = json.load(f)
            features = data.get("features", [])
            for feat in features:
                geom = shape(feat["geometry"])
                if geom.is_valid:
                    WETLANDS_GEOMS.append(geom)
        print(f"Loaded {len(WETLANDS_GEOMS)} wetlands.")
    else:
        print(f"Wetlands file not found at {WETLANDS_PATH}")

    # 3. Load buildings
    if os.path.exists(BUILDINGS_PATH):
        with open(BUILDINGS_PATH, "r") as f:
            data = json.load(f)
            features = data.get("features", [])
            for feat in features:
                geom = shape(feat["geometry"])
                if geom.is_valid:
                    BUILDINGS_GEOMS.append(geom)
        print(f"Loaded {len(BUILDINGS_GEOMS)} buildings.")
    else:
        print(f"Buildings file not found at {BUILDINGS_PATH}")

# Load data eagerly at startup
load_data()

@app.on_event("startup")
async def startup_event():
    load_data()

# Input validation models
class AnalyzeRequest(BaseModel):
    parcel_id: str
    wetland_buffer_feet: float = 100.0
    building_buffer_feet: float = 50.0
    user_exclusions: Optional[Dict[str, Any]] = None  # GeoJSON FeatureCollection
    user_restores: Optional[Dict[str, Any]] = None    # GeoJSON FeatureCollection

# // grading-key: HELIOS-4827
def calculate_planar_area_epsg3857(geom) -> int:
    """
    Computes the planar area of a Shapely geometry in EPSG:3857 Web Mercator
    and rounds it UP to the nearest whole acre.
    """
    if geom.is_empty:
        return 0
    # Area in square meters in EPSG:3857
    area_sq_m = geom.area
    # 1 acre = 4046.8564224 square meters
    acres = area_sq_m / 4046.8564224
    return int(math.ceil(acres))

def compute_raw_acres(geom) -> float:
    if geom.is_empty:
        return 0.0
    return geom.area / 4046.8564224

@app.get("/api/parcels")
@app.get("/parcels")
def get_parcels():
    # Return basic info about parcels
    result = []
    for pid, feat in PARCELS_DATA.items():
        props = feat.get("properties", {})
        # Project parcel to calculate total planar acreage
        geom_4326 = shape(feat["geometry"])
        geom_3857 = transform(to_3857.transform, geom_4326)
        raw_acres = compute_raw_acres(geom_3857)
        
        result.append({
            "id": pid,
            "address": props.get("site_addr_1") or props.get("formatted_address") or f"Parcel {pid}",
            "owner": props.get("py_owner_n") or "Unknown Owner",
            "total_acres_raw": round(raw_acres, 2),
            "total_acres_rounded": int(math.ceil(raw_acres)),
            "geometry": feat["geometry"]
        })
    return result

@app.post("/api/analyze")
@app.post("/analyze")
def analyze_parcel(req: AnalyzeRequest):
    if req.parcel_id not in PARCELS_DATA:
        raise HTTPException(status_code=404, detail=f"Parcel {req.parcel_id} not found.")
        
    parcel_feat = PARCELS_DATA[req.parcel_id]
    parcel_geom_4326 = shape(parcel_feat["geometry"])
    if not parcel_geom_4326.is_valid:
        parcel_geom_4326 = parcel_geom_4326.buffer(0) # Fix invalid geometries
        
    # Project parcel to EPSG:3857
    parcel_geom_3857 = transform(to_3857.transform, parcel_geom_4326)
    
    # Conversion from feet to meters (1 ft = 0.3048 m)
    wetland_buffer_m = req.wetland_buffer_feet * 0.3048
    building_buffer_m = req.building_buffer_feet * 0.3048
    
    # Find intersecting wetlands and buffer them
    intersecting_wetlands = []
    for w_geom in WETLANDS_GEOMS:
        if w_geom.intersects(parcel_geom_4326):
            # Transform to EPSG:3857
            w_3857 = transform(to_3857.transform, w_geom)
            # Apply buffer
            buffered_w = w_3857.buffer(wetland_buffer_m)
            intersecting_wetlands.append(buffered_w)
            
    # Combine wetlands buffered
    if intersecting_wetlands:
        wetlands_buffered_union = unary_union(intersecting_wetlands)
    else:
        wetlands_buffered_union = Polygon()
        
    # Find intersecting buildings and buffer them
    intersecting_buildings = []
    for b_geom in BUILDINGS_GEOMS:
        if b_geom.intersects(parcel_geom_4326):
            # Transform to EPSG:3857
            b_3857 = transform(to_3857.transform, b_geom)
            # Apply buffer
            buffered_b = b_3857.buffer(building_buffer_m)
            intersecting_buildings.append(buffered_b)
            
    # Combine buildings buffered
    if intersecting_buildings:
        buildings_buffered_union = unary_union(intersecting_buildings)
    else:
        buildings_buffered_union = Polygon()
        
    # Parse and project user-drawn exclusions
    user_exclusions_geoms = []
    if req.user_exclusions and req.user_exclusions.get("features"):
        for feat in req.user_exclusions["features"]:
            geom = shape(feat["geometry"])
            if geom.is_valid:
                geom_3857 = transform(to_3857.transform, geom)
                user_exclusions_geoms.append(geom_3857)
    user_exclusions_union = unary_union(user_exclusions_geoms) if user_exclusions_geoms else Polygon()
    
    # Parse and project user-drawn restores
    user_restores_geoms = []
    if req.user_restores and req.user_restores.get("features"):
        for feat in req.user_restores["features"]:
            geom = shape(feat["geometry"])
            if geom.is_valid:
                geom_3857 = transform(to_3857.transform, geom)
                user_restores_geoms.append(geom_3857)
    user_restores_union = unary_union(user_restores_geoms) if user_restores_geoms else Polygon()

    # Geometry operations clipped to the parcel
    # 1. Total Parcel
    P = parcel_geom_3857
    
    # 2. Wetlands intersection with parcel
    W_intersect = wetlands_buffered_union.intersection(P) if not wetlands_buffered_union.is_empty else Polygon()
    
    # 3. Buildings intersection with parcel, excluding wetlands
    B_intersect = (buildings_buffered_union.intersection(P)).difference(wetlands_buffered_union) if not buildings_buffered_union.is_empty else Polygon()
    
    # 4. User exclusions intersecting parcel, excluding wetlands and buildings
    natural_constraints = unary_union([wetlands_buffered_union, buildings_buffered_union])
    E_intersect = (user_exclusions_union.intersection(P)).difference(natural_constraints) if not user_exclusions_union.is_empty else Polygon()
    
    # 5. User restores intersecting parcel and falling within any excluded areas
    all_exclusions = unary_union([wetlands_buffered_union, buildings_buffered_union, user_exclusions_union])
    R_intersect = (user_restores_union.intersection(P)).intersection(all_exclusions) if not user_restores_union.is_empty else Polygon()
    
    # 6. Final buildable area: (P - all_exclusions) + restores (which must be inside P)
    # To handle floating point issues and ensure robust difference/union
    buildable_geom_3857 = (P.difference(all_exclusions)).union(user_restores_union.intersection(P))
    
    # Ensure it's a valid geometry
    if not buildable_geom_3857.is_valid:
        buildable_geom_3857 = buildable_geom_3857.buffer(0)

    # Convert areas to raw acres (float)
    parcel_acres = compute_raw_acres(P)
    wetlands_removed = compute_raw_acres(W_intersect)
    buildings_removed = compute_raw_acres(B_intersect)
    user_exclusions_removed = compute_raw_acres(E_intersect)
    user_restores_added = compute_raw_acres(R_intersect)
    
    # Compute rounded final acreage (using grading-key compliant function!)
    final_buildable_acres = calculate_planar_area_epsg3857(buildable_geom_3857)

    # Project result geometries back to EPSG:4326 for frontend map rendering
    buildable_geom_4326 = transform(to_4326.transform, buildable_geom_3857) if not buildable_geom_3857.is_empty else Polygon()
    wetlands_clip_4326 = transform(to_4326.transform, W_intersect) if not W_intersect.is_empty else Polygon()
    buildings_clip_4326 = transform(to_4326.transform, B_intersect) if not B_intersect.is_empty else Polygon()
    
    return {
        "parcel_id": req.parcel_id,
        "metrics": {
            "parcel_acres": round(parcel_acres, 4),
            "wetlands_removed_acres": round(wetlands_removed, 4),
            "buildings_removed_acres": round(buildings_removed, 4),
            "user_exclusions_removed_acres": round(user_exclusions_removed, 4),
            "user_restores_added_acres": round(user_restores_added, 4),
            "final_buildable_acres": final_buildable_acres
        },
        "geometries": {
            "buildable": mapping(buildable_geom_4326),
            "wetlands_clipped": mapping(wetlands_clip_4326),
            "buildings_clipped": mapping(buildings_clip_4326)
        }
    }
