import urllib.request
import json

def test_api():
    print("Testing local API endpoints...")
    
    # 1. Test GET /api/parcels
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/parcels")
        with urllib.request.urlopen(req) as res:
            parcels = json.loads(res.read().decode())
            print(f"GET /api/parcels: SUCCESS (Found {len(parcels)} parcels)")
            assert len(parcels) > 0, "No parcels returned"
            first_parcel_id = parcels[0]["id"]
    except Exception as e:
        print(f"GET /api/parcels failed: {e}")
        return False

    # 2. Test POST /api/analyze
    try:
        payload = {
            "parcel_id": first_parcel_id,
            "wetland_buffer_feet": 100.0,
            "building_buffer_feet": 50.0,
            "user_exclusions": {"type": "FeatureCollection", "features": []},
            "user_restores": {"type": "FeatureCollection", "features": []}
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/analyze",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode())
            print("POST /api/analyze: SUCCESS")
            
            # Assert metrics keys
            metrics = result.get("metrics", {})
            print("Metrics:", metrics)
            assert "parcel_acres" in metrics
            assert "wetlands_removed_acres" in metrics
            assert "buildings_removed_acres" in metrics
            assert "final_buildable_acres" in metrics
            
            # Assert geometries keys
            geometries = result.get("geometries", {})
            assert "buildable" in geometries
            assert "wetlands_clipped" in geometries
            
            # Assert type of acreage
            assert isinstance(metrics["final_buildable_acres"], int), "Final buildable acreage must be an integer!"
            
            print("API integration tests passed successfully!")
            return True
    except Exception as e:
        print(f"POST /api/analyze failed: {e}")
        return False

if __name__ == "__main__":
    test_api()
