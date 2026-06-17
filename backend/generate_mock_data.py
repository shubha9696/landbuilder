import os
import json

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    # Base coordinates in East Austin (near Colorado River)
    # Lat: ~30.25, Lon: ~-97.70
    
    # 1. Generate Parcels
    # We will create 4 realistic, irregular parcels
    parcels = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "parcel_101",
                "properties": {
                    "prop_id": "parcel_101",
                    "site_addr_1": "9400 River Road, Austin, TX 78725",
                    "py_owner_n": "RIVER BEND VENTURES LLC",
                    "description": "Large agricultural and creek-adjacent tract with significant wetlands."
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.705, 30.245],
                        [-97.700, 30.246],
                        [-97.698, 30.242],
                        [-97.699, 30.238],
                        [-97.706, 30.240],
                        [-97.705, 30.245]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "parcel_102",
                "properties": {
                    "prop_id": "parcel_102",
                    "site_addr_1": "9502 Colorado Bend, Austin, TX 78725",
                    "py_owner_n": "AUSTIN ECO-DEVELOPMENT INC",
                    "description": "Commercial-zoned parcel containing existing structures and partial flood zone."
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.698, 30.242],
                        [-97.693, 30.243],
                        [-97.692, 30.239],
                        [-97.697, 30.237],
                        [-97.698, 30.242]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "parcel_103",
                "properties": {
                    "prop_id": "parcel_103",
                    "site_addr_1": "1200 Walnut Creek Way, Austin, TX 78725",
                    "py_owner_n": "WALNUT CREEK HOLDINGS",
                    "description": "Linear parcel running along the eastern boundary, perfect for conservation easements."
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.700, 30.246],
                        [-97.695, 30.247],
                        [-97.693, 30.243],
                        [-97.698, 30.242],
                        [-97.700, 30.246]
                    ]]
                }
            },
            {
                "type": "Feature",
                "id": "parcel_104",
                "properties": {
                    "prop_id": "parcel_104",
                    "site_addr_1": "9105 Blue Lagoon Dr, Austin, TX 78725",
                    "py_owner_n": "SARA & DAVID MILLER",
                    "description": "Smaller residential acreage parcel with a large domestic building."
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.706, 30.240],
                        [-97.699, 30.238],
                        [-97.700, 30.235],
                        [-97.707, 30.236],
                        [-97.706, 30.240]
                    ]]
                }
            }
        ]
    }

    # 2. Generate Wetlands
    # Irregular wetlands, one meandering creek crossing multiple parcels and a pond.
    wetlands = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "WETLAND_TY": "Freshwater Forested/Shrub Wetland",
                    "SYSTEM": "Palustrine",
                    "description": "Meandering creek bed wetland area"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.704, 30.247],
                        [-97.702, 30.244],
                        [-97.697, 30.241],
                        [-97.694, 30.240],
                        [-97.694, 30.238],
                        [-97.696, 30.239],
                        [-97.699, 30.241],
                        [-97.703, 30.243],
                        [-97.705, 30.246],
                        [-97.704, 30.247]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "WETLAND_TY": "Freshwater Pond",
                    "SYSTEM": "Palustrine",
                    "description": "Isolated depression wetland / stock pond"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.695, 30.242],
                        [-97.694, 30.242],
                        [-97.694, 30.241],
                        [-97.695, 30.241],
                        [-97.695, 30.242]
                    ]]
                }
            }
        ]
    }

    # 3. Generate Buildings
    # A few building footprints that represent existing infrastructure.
    buildings = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "building": "residential",
                    "height": 8.5,
                    "description": "Main residential estate house"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.704, 30.238],
                        [-97.703, 30.238],
                        [-97.703, 30.237],
                        [-97.704, 30.237],
                        [-97.704, 30.238]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "building": "commercial",
                    "height": 12.0,
                    "description": "Industrial warehouse building"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.695, 30.239],
                        [-97.693, 30.239],
                        [-97.693, 30.238],
                        [-97.695, 30.238],
                        [-97.695, 30.239]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "building": "barn",
                    "height": 6.0,
                    "description": "Agricultural storage barn"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-97.703, 30.244],
                        [-97.702, 30.244],
                        [-97.702, 30.243],
                        [-97.703, 30.243],
                        [-97.703, 30.244]
                    ]]
                }
            }
        ]
    }

    with open(os.path.join(data_dir, "parcels.geojson"), "w") as f:
        json.dump(parcels, f, indent=2)
    with open(os.path.join(data_dir, "wetlands.geojson"), "w") as f:
        json.dump(wetlands, f, indent=2)
    with open(os.path.join(data_dir, "buildings.geojson"), "w") as f:
        json.dump(buildings, f, indent=2)

    print("Successfully generated realistic sample GIS layers!")

if __name__ == "__main__":
    main()
