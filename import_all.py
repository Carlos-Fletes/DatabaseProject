import subprocess
import sys

commands = [
    ["python", "-u", "import_osm_parks.py"],
    ["python", "-u", "import_osm_restaurants.py"],
    ["python", "-u", "import_osm_schools.py"],
    ["python", "-u", "import_census_counties.py"],
    ["python", "-u", "import_fema_risk.py"],
]

for cmd in commands:
    print(f"\nRunning: {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd="/app")
    if result.returncode != 0:
        print(f"Failed: {' '.join(cmd)}", flush=True)
        sys.exit(result.returncode)
    print(f"Done: {' '.join(cmd)}", flush=True)

print("\nAll imports complete.", flush=True)