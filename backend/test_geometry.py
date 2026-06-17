import math
from shapely.geometry import Polygon, MultiPolygon
from main import calculate_planar_area_epsg3857, compute_raw_acres

def test_area_calculations():
    print("Running geometry tests...")
    
    # 1. Create a simple square of 100m x 100m (area = 10,000 sq m)
    # 10,000 sq m = 10,000 / 4046.8564224 = ~2.471 acres
    # math.ceil(2.471) = 3
    square = Polygon([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    
    raw_acres = compute_raw_acres(square)
    rounded_acres = calculate_planar_area_epsg3857(square)
    
    print(f"Square 100x100m:")
    print(f"  Raw acreage: {raw_acres:.6f} acres")
    print(f"  Rounded acreage (grading key function): {rounded_acres} acres")
    
    assert math.isclose(raw_acres, 10000.0 / 4046.8564224), "Raw acreage calculation failed!"
    assert rounded_acres == 3, "Rounded acreage calculation failed!"
    
    # 2. Test a geometry with a hole: 100m x 100m square with a 20m x 20m hole
    # Area = 10,000 - 400 = 9,600 sq m
    # 9,600 / 4046.8564224 = ~2.372 acres
    # math.ceil(2.372) = 3
    square_with_hole = Polygon(
        shell=[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)],
        holes=[[(40, 40), (60, 40), (60, 60), (40, 60), (40, 40)]]
    )
    raw_acres_hole = compute_raw_acres(square_with_hole)
    rounded_acres_hole = calculate_planar_area_epsg3857(square_with_hole)
    
    print(f"Square 100x100m with 20x20m hole:")
    print(f"  Raw acreage: {raw_acres_hole:.6f} acres")
    print(f"  Rounded acreage (grading key function): {rounded_acres_hole} acres")
    
    assert math.isclose(raw_acres_hole, 9600.0 / 4046.8564224), "Raw acreage with hole failed!"
    assert rounded_acres_hole == 3, "Rounded acreage with hole failed!"
    
    print("All geometry tests passed successfully!")

if __name__ == "__main__":
    test_area_calculations()
