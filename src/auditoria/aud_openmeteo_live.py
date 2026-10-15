"""Contraste Open-Meteo: repite llamadas y compara con ficheros guardados; verifica afirmaciones del registro."""
import json, requests, time
import numpy as np
R = "data/raw/"
def J(p): return json.load(open(R+p, encoding="utf-8"))
hist = J("openmeteo_lagos_enol.json"); H = hist["daily"]
for fecha in ("2022-03-15", "2024-08-10", "2025-12-25"):
    r = requests.get("https://historical-forecast-api.open-meteo.com/v1/forecast", params={
        "latitude": 43.27, "longitude": -4.99, "start_date": fecha, "end_date": fecha, "timezone": "Europe/Madrid",
        "daily": ",".join(k for k in H if k != "time")}, timeout=120)
    time.sleep(2)
    if r.status_code != 200: print(fecha, "HTTP", r.status_code, r.text[:200]); continue
    live = r.json()["daily"]; i = H["time"].index(fecha)
    dif = {k: (live[k][0], H[k][i]) for k in live if k != "time" and live[k][0] != H[k][i]}
    print("hist lagos_enol", fecha, "elev", r.json().get("elevation"), "diferencias:", dif or "ninguna")
# Previous runs, covadonga, 1 dia
P = J("openmeteo_previous_covadonga.json")["hourly"]
r = requests.get("https://previous-runs-api.open-meteo.com/v1/forecast", params={
    "latitude": 43.31, "longitude": -5.05, "start_date": "2025-07-20", "end_date": "2025-07-20", "timezone": "Europe/Madrid",
    "hourly": "temperature_2m,temperature_2m_previous_day1,precipitation_previous_day2,wind_gusts_10m_previous_day3"}, timeout=120)
print("previous status", r.status_code)
if r.status_code == 200:
    lv = r.json()["hourly"]; idx = [P["time"].index(t) for t in lv["time"]]
    for k in lv:
        if k == "time": continue
        print("  previous", k, "iguales:", all(lv[k][j] == P[k][idx[j]] for j in range(24)))
# afirmaciones del registro
E = J("openmeteo_archive_covadonga.json")["daily"]; HC = J("openmeteo_covadonga.json")["daily"]
t = np.array(HC["time"]); 
def arr(d, k): return np.array(d[k], dtype=float)
m_pre = t < "2022-11-10"
print("dias antes de 2022-11-10:", int(m_pre.sum()))
for k in ("precipitation_sum", "precipitation_hours", "weather_code", "wind_speed_10m_max", "wind_gusts_10m_max", "temperature_2m_max", "sunshine_duration"):
    a, b = arr(HC, k), arr(E, k)
    print(f"  {k}: dias identicos a ERA5 antes 2022-11-10 = {int((a[m_pre]==b[m_pre]).sum())}/{int(m_pre.sum())}; despues = {int((a[~m_pre]==b[~m_pre]).sum())}/{int((~m_pre).sum())}")
a, b = arr(HC, "temperature_2m_max"), arr(E, "temperature_2m_max")
print("Tmax sesgo total %.2f MAE %.2f; >=2022-11-10 %.2f/%.2f; antes %.2f/%.2f" % ((a-b).mean(), abs(a-b).mean(), (a-b)[~m_pre].mean(), abs(a-b)[~m_pre].mean(), (a-b)[m_pre].mean(), abs(a-b)[m_pre].mean()))
a, b = arr(HC, "precipitation_sum"), arr(E, "precipitation_sum")
print("Prec sesgo %.2f MAE %.2f corr %.2f medias %.2f / %.2f" % ((a-b).mean(), abs(a-b).mean(), np.corrcoef(a, b)[0, 1], a.mean(), b.mean()))
# previous: nulos tras 2024-01-22
tt = np.array(P["time"])
for k in P:
    if k == "time": continue
    v = np.array([x is None for x in P[k]])
    if v.any(): 
        n_post = int(v[tt >= "2024-01-22T00:00"].sum()); 
        if n_post: print("  nulos tras 2024-01-22:", k, n_post)
print("fin nulos previous")
# ultimo dia (parcial?) 2026-10-15 en hist
print("ultimo dia hist covadonga:", {k: HC[k][-1] for k in HC}, "\n penultimo:", {k: HC[k][-2] for k in HC})
