# station_impact_heatmap.py
import geopandas as gpd
import pandas as pd
import folium
import branca.colormap as cm

# ---------- 1. Load MARTA stops GeoJSON ----------
stops_gdf = gpd.read_file("Data/Data.geojson")

# Expect columns: stop_name, geometry, etc.
stops_gdf["stop_name_upper"] = stops_gdf["stop_name"].str.upper()

# ---------- 2. Define your station impact data ----------
# Tiers from your description:
# Tier 1 - Highest Priority (>80% probability OR >1,500 trips)
# Tier 2 - High Priority (50-80% probability OR 500-1,500 trips)
# Tier 3 - Moderate Priority (20-50% probability OR 200-500 trips)

station_impacts = [
    {
        "label": "Edgewood/Candler Park",
        "stop_name_exact": "EDGEWOOD-CANDLER PARK STATION",
        "tier": 1,
        "pred_pct_change": 110.2,
        "abs_change": 665,
        "prob_signif": 90.9,
        "distance_to_venue_m": 7715,
    },
    {
        "label": "Vine City",
        "stop_name_exact": "VINE CITY STATION",
        "tier": 1,
        "pred_pct_change": 96.7,
        "abs_change": 1612,
        "prob_signif": 13.2,
        "distance_to_venue_m": 7716,
    },
    {
        "label": "Dome/GWCC",
        # Current name in the stops file:
        "stop_name_exact": "GWCC-CNN CENTER STATION",
        "tier": 1,
        "pred_pct_change": 66.9,
        "abs_change": 1854,
        "prob_signif": 6.7,
        "distance_to_venue_m": 7716,
    },
    {
        "label": "Doraville",
        "stop_name_exact": "DORAVILLE STATION",
        "tier": 1,
        "pred_pct_change": None,  # not provided explicitly
        "abs_change": None,       # not provided explicitly
        "prob_signif": 81.9,
        "distance_to_venue_m": None,
    },
    {
        "label": "Avondale",
        "stop_name_exact": "AVONDALE STATION",
        "tier": 2,
        "pred_pct_change": None,
        "abs_change": 394,
        "prob_signif": 78.9,
        "distance_to_venue_m": None,
    },
    {
        "label": "H.E. Holmes",
        "stop_name_exact": "HAMILTON E HOLMES STATION",
        "tier": 2,
        "pred_pct_change": None,
        "abs_change": 481,
        "prob_signif": 57.1,
        "distance_to_venue_m": None,
    },
    {
        "label": "East Lake",
        "stop_name_exact": "EAST LAKE STATION",
        "tier": 2,
        "pred_pct_change": 82.0,
        "abs_change": 577,
        "prob_signif": 32.9,
        "distance_to_venue_m": 7715,
    },
    {
        "label": "Inman Park",
        "stop_name_exact": "INMAN PARK-REYNOLDSTOWN STATION",
        "tier": 3,
        "pred_pct_change": 31.4,
        "abs_change": 395,
        "prob_signif": 20.4,
        "distance_to_venue_m": 7716,
    },
]

impacts_df = pd.DataFrame(station_impacts)

# ---------- 3. Join impact data to station coordinates ----------
def get_station_coords(stop_name_exact: str):
    """
    Find the main station point by exact stop_name match.
    Falls back to first matching row if multiple.
    """
    mask = stops_gdf["stop_name_upper"] == stop_name_exact.upper()
    subset = stops_gdf.loc[mask]
    if subset.empty:
        return None, None
    # If multiple (loops, etc.), take centroid of all points
    geom = subset.geometry.unary_union
    # unary_union can be a point already or a collection
    if geom.geom_type == "Point":
        lon, lat = geom.x, geom.y
    else:
        # For MultiPoint/etc., use centroid
        centroid = geom.centroid
        lon, lat = centroid.x, centroid.y
    return lon, lat

lons = []
lats = []
for _, row in impacts_df.iterrows():
    lon, lat = get_station_coords(row["stop_name_exact"])
    lons.append(lon)
    lats.append(lat)

impacts_df["lon"] = lons
impacts_df["lat"] = lats

# Drop any stations we couldn't locate
impacts_df = impacts_df.dropna(subset=["lon", "lat"])

# ---------- 4. Build a color scale for increase/decrease ----------
# We'll use predicted % change if available; otherwise fallback to scaled abs_change.
# Red = increase, white = neutral, blue = decrease.
def compute_impact_value(row):
    if pd.notna(row["pred_pct_change"]):
        return row["pred_pct_change"]
    # If we only know absolute change (assume increase is positive)
    if pd.notna(row["abs_change"]):
        return row["abs_change"]
    # If no numeric impact, treat as 0 (white)
    return 0.0

impacts_df["impact_value"] = impacts_df.apply(compute_impact_value, axis=1)

max_abs = max(abs(impacts_df["impact_value"]).max(), 1.0)  # avoid division by zero

# Symmetric around zero so that 0 = white
impact_colormap = cm.LinearColormap(
    colors=["blue", "white", "red"],
    vmin=-max_abs,
    vmax=max_abs,
)

# ---------- 5. Create Folium map centered on Atlanta ----------
default_lat = 33.7490
default_lon = -84.3880

if not impacts_df.empty:
    center_lat = impacts_df["lat"].mean()
    center_lon = impacts_df["lon"].mean()
else:
    center_lat, center_lon = default_lat, default_lon

m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="cartodbpositron")

# ---------- 6. Add station circles ----------
for _, row in impacts_df.iterrows():
    impact = row["impact_value"]
    color = impact_colormap(impact)

    # Radius scales with absolute change if available; otherwise a default
    if pd.notna(row["abs_change"]):
        radius = 6 + 24 * (abs(row["abs_change"]) / (impacts_df["abs_change"].abs().max() or 1))
    else:
        radius = 10

    tier = row["tier"]
    tier_label = {1: "Tier 1 – Highest Priority",
                  2: "Tier 2 – High Priority",
                  3: "Tier 3 – Moderate Priority"}.get(tier, f"Tier {tier}")

    popup_html = f"""
    <b>{row['label']}</b><br>
    {tier_label}<br><br>
    <b>Predicted % change:</b> {row['pred_pct_change'] if pd.notna(row['pred_pct_change']) else 'N/A'}%<br>
    <b>Predicted absolute increase:</b> {row['abs_change'] if pd.notna(row['abs_change']) else 'N/A'} trips<br>
    <b>Probability of significance:</b> {row['prob_signif']}%<br>
    <b>Distance to venue:</b> {row['distance_to_venue_m'] if pd.notna(row['distance_to_venue_m']) else 'N/A'} m<br>
    """

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(popup_html, max_width=300),
    ).add_to(m)

# Add legend
impact_colormap.caption = "Predicted impact (blue = decrease, white = baseline, red = increase)"
impact_colormap.add_to(m)

# ---------- 7. Save map ----------
m.save("station_impact_map.html")
print("Saved interactive map to station_impact_map.html")
