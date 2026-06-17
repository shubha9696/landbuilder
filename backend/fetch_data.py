import os
import json
import urllib.request
import urllib.parse

# Coordinates bounding box in Austin, Texas.
# This bbox covers a region near Colorado River / Hornsby Bend / Roy G Guerrero Park, which contains a good mix of parcels, wetlands, and buildings.
BBOX = {
    "xmin": -97.685,
    "ymin": 30.235,
    "xmax": -97.665,
    "ymax": 30.255
}

# Travis County Central Appraisal District (TCAD) parcels
PARCELS_URL = "https://gis.traviscountytx.gov/server1/rest/services/Boundaries_and_Jurisdictions/TCAD_public/MapServer/0/query"

# USFWS Wetlands
WETLANDS_URL = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query"

# City of Austin Building Footprints (from their public ArcGIS service)
BUILDINGS_URL = "https://services.arcgis.com/aU6lHlvch55ss87S/ArcGIS/rest/services/Building_Footprints/FeatureServer/0/query"

def fetch_geojson(base_url, bbox, name):
    print(f"Fetching {name} data...")
    # Setup query parameters
    params = {
        "where": "1=1",
        "geometry": json.dumps({
            "xmin": bbox["xmin"],
            "ymin": bbox["ymin"],
            "xmax": bbox["xmax"],
            "ymax": bbox["ymax"],
            "spatialReference": {"wkid": 4326}
        }),
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": "4326",
        "outSR": "4326",
        "f": "geojson",
        "outFields": "*"
    }
    
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url, 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            features = data.get("features", [])
            print(f"Successfully fetched {len(features)} features for {name}.")
            return data
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Try fetching with current bbox
    parcels = fetch_geojson(PARCELS_URL, BBOX, "Parcels")
    wetlands = fetch_geojson(WETLANDS_URL, BBOX, "Wetlands")
    buildings = fetch_geojson(BUILDINGS_URL, BBOX, "Buildings")
    
    # If any failed or returned empty, we try a fallback bbox (another area in East Austin)
    fallback_bbox = {
        "xmin": -97.715,
        "ymin": 30.245,
        "xmax": -97.695,
        "ymax": 30.265
    }
    
    if not parcels or not parcels.get("features"):
        print("Retrying Parcels with fallback BBOX...")
        parcels = fetch_geojson(PARCELS_URL, fallback_bbox, "Parcels (Fallback)")
    if not wetlands or not wetlands.get("features"):
        print("Retrying Wetlands with fallback BBOX...")
        wetlands = fetch_geojson(WETLANDS_URL, fallback_bbox, "Wetlands (Fallback)")
    if not buildings or not buildings.get("features"):
        print("Retrying Buildings with fallback BBOX...")
        buildings = fetch_geojson(BUILDINGS_URL, fallback_bbox, "Buildings (Fallback)")
        
    # Save the data
    if parcels:
        with open(os.path.join(data_dir, "parcels.geojson"), "w") as f:
            json.dump(parcels, f, indent=2)
    if wetlands:
        with open(os.path.join(data_dir, "wetlands.geojson"), "w") as f:
            json.dump(wetlands, f, indent=2)
    if buildings:
        with open(os.path.join(data_dir, "buildings.geojson"), "w") as f:
            json.dump(buildings, f, indent=2)

    print("Data download completed!")

if __name__ == "__main__":
    main()
