import os
import math
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def make_dim_date(start="2019-01-01", end="2024-12-31"):
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    dates = []
    cur = start_dt
    while cur <= end_dt:
        dates.append(cur)
        cur += timedelta(days=1)

    df = pd.DataFrame({"Date": dates})
    df["DateKey"] = df["Date"].dt.strftime("%Y%m%d").astype(int)
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["MonthName"] = df["Date"].dt.strftime("%b")
    df["Quarter"] = df["Date"].dt.quarter
    return df[["DateKey", "Date", "Year", "Month", "MonthName", "Quarter"]]


def make_dim_circuit(n_circuits=150):
    regions = ["North", "South", "East", "West", "Metro"]
    substations = [f"SUB_{i:03d}" for i in range(1, 51)]
    voltages = [4.16, 12.47, 13.8, 34.5]

    rows = []
    for i in range(1, n_circuits + 1):
        cid = f"CKT_{i:04d}"
        row = {
            "CircuitID": cid,
            "CircuitName": f"Circuit {i}",
            "Substation": random.choice(substations),
            "FeederVoltage": random.choice(voltages),
            "Region": random.choice(regions),
            "CustomerCount": random.randint(300, 5000),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def make_dim_risk_zone():
    rows = [
        (1, "Low Urban", "Low", "Low", "Sparse"),
        (2, "Low Rural", "Low", "Medium", "Medium"),
        (3, "Moderate Wildland", "Medium", "Medium", "High"),
        (4, "High WUI", "High", "High", "High"),
        (5, "Extreme Corridor", "Extreme", "High", "VeryHigh"),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "RiskZoneID",
            "ZoneName",
            "FireRiskCategory",
            "WindRiskCategory",
            "VegetationDensityClass",
        ],
    )


def make_dim_pole(dim_circuit, dim_risk_zone, n_poles=15000):
    materials = ["Wood", "Steel", "Composite"]
    access_types = ["Roadside", "Backyard", "Off-road"]
    rows = []
    risk_zone_ids = dim_risk_zone["RiskZoneID"].tolist()

    for i in range(1, n_poles + 1):
        pole_id = f"P_{i:07d}"
        circuit = dim_circuit.sample(1).iloc[0]
        base_lat = 40 + (hash(circuit["Region"]) % 5)
        base_lon = -120 + (hash(circuit["Region"]) % 5)
        lat = base_lat + np.random.normal(0, 0.1)
        lon = base_lon + np.random.normal(0, 0.1)

        row = {
            "PoleID": pole_id,
            "CircuitID": circuit["CircuitID"],
            "Latitude": round(lat, 6),
            "Longitude": round(lon, 6),
            "Material": random.choice(materials),
            "Height": random.randint(30, 75),
            "InstallYear": random.randint(1965, 2022),
            "AccessType": random.choice(access_types),
            "RiskZoneID": random.choice(risk_zone_ids),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def sample_date_keys(dim_date, n):
    return dim_date["DateKey"].sample(n, replace=True).values


def random_time_str():
    h = random.randint(0, 23)
    m = random.randint(0, 59)
    return f"{h:02d}:{m:02d}"


def make_fact_outage(dim_date, dim_circuit, dim_pole, n_outages=8000):
    cause_codes = ["TREES", "EQUIP_FAIL", "ANIMALS", "WEATHER", "FIRE_PREVENT", "OTHER"]
    weather_types = ["None", "Wind", "Storm", "Snow", "HeatWave"]

    rows = []
    date_keys = sample_date_keys(dim_date, n_outages)
    for i in range(1, n_outages + 1):
        outage_id = f"OUT_{i:07d}"
        circuit = dim_circuit.sample(1).iloc[0]
        if random.random() < 0.7:
            pole = dim_pole[dim_pole["CircuitID"] == circuit["CircuitID"]].sample(1).iloc[0]
            pole_id = pole["PoleID"]
        else:
            pole_id = None

        cause = random.choices(
            cause_codes, weights=[0.35, 0.2, 0.1, 0.2, 0.05, 0.1], k=1
        )[0]
        weather = (
            random.choice(["Wind", "Storm", "Snow"])
            if cause in ["WEATHER", "TREES"]
            else random.choice(weather_types)
        )

        start_key = int(date_keys[i - 1])
        minutes = max(5, int(np.random.exponential(90)))
        end_date_key = start_key

        cust = max(1, int(np.random.exponential(circuit["CustomerCount"] / 10)))
        is_planned = cause in ["EQUIP_FAIL", "OTHER"] and random.random() < 0.2
        is_fire_prev = cause == "FIRE_PREVENT"

        rows.append(
            {
                "OutageID": outage_id,
                "CircuitID": circuit["CircuitID"],
                "PoleID": pole_id,
                "StartDateKey": start_key,
                "StartTime": random_time_str(),
                "EndDateKey": end_date_key,
                "EndTime": random_time_str(),
                "CauseCode": cause,
                "WeatherEventType": weather,
                "CustomersAffected": cust,
                "MinutesOut": minutes,
                "IsPlanned": is_planned,
                "IsWildfirePrevention": is_fire_prev,
            }
        )

    return pd.DataFrame(rows)


def make_fact_trouble_call(dim_date, fact_outage):
    caller_types = ["Residential", "Commercial", "Industrial"]
    channels = ["Phone", "Web", "MobileApp"]
    dispositions = ["OutageReported", "Duplicate", "InfoOnly"]

    rows = []
    call_id = 1
    for _, out_row in fact_outage.iterrows():
        n_calls = np.random.poisson(lam=2)
        for _ in range(n_calls):
            offset = random.randint(-1, 1)
            date_key = int(out_row["StartDateKey"])
            year = date_key // 10000
            month = (date_key // 100) % 100
            day = date_key % 100
            call_date = datetime(year, month, day) + timedelta(days=offset)
            call_date_key = int(call_date.strftime("%Y%m%d"))

            rows.append(
                {
                    "TroubleCallID": f"TC_{call_id:07d}",
                    "OutageID": out_row["OutageID"],
                    "CircuitID": out_row["CircuitID"],
                    "CallDateKey": call_date_key,
                    "CallTime": random_time_str(),
                    "CallerType": random.choice(caller_types),
                    "CallChannel": random.choice(channels),
                    "CallDisposition": random.choices(
                        dispositions, weights=[0.7, 0.2, 0.1], k=1
                    )[0],
                }
            )
            call_id += 1

    return pd.DataFrame(rows)


def make_fact_vegetation_inspection(dim_date, dim_pole, avg_years_between=3):
    rows = []
    insp_id = 1
    date_keys = dim_date["DateKey"].values
    years = dim_date["Year"].values

    for _, pole in dim_pole.iterrows():
        n_insp = max(1, int(len(np.unique(years)) / avg_years_between))
        insp_dates = np.random.choice(date_keys, size=n_insp, replace=False)

        for dk in insp_dates:
            clearance = max(0.0, np.random.normal(6, 3))
            hazard = clearance < 3 or random.random() < 0.05
            priority = (
                random.choice(["P1", "P2"])
                if hazard
                else random.choice(["P3", "P4"])
            )
            compliant = clearance >= 4 and not hazard

            rows.append(
                {
                    "InspectionID": f"INSP_{insp_id:08d}",
                    "PoleID": pole["PoleID"],
                    "CircuitID": pole["CircuitID"],
                    "InspectionDateKey": int(dk),
                    "TreeClearanceFeet": round(clearance, 2),
                    "HazardTreeFlag": hazard,
                    "PriorityCode": priority,
                    "ComplianceFlag": compliant,
                }
            )
            insp_id += 1

    return pd.DataFrame(rows)


def make_fact_veg_work(dim_date, fact_insp, dim_pole):
    work_types = ["Trim", "Remove", "Mow", "Patrol"]
    contractors = ["TreeCo", "GreenLine", "SafeSpan", "ClearPath"]

    rows = []
    work_id = 1

    hazard_insp = fact_insp[fact_insp["HazardTreeFlag"]].copy()
    hazard_insp = hazard_insp.sample(frac=0.7, random_state=42)

    for _, row in hazard_insp.iterrows():
        pole = dim_pole[dim_pole["PoleID"] == row["PoleID"]].iloc[0]
        insp_str = str(int(row["InspectionDateKey"]))
        year = int(insp_str[:4])
        month = int(insp_str[4:6])
        day = int(insp_str[6:])
        insp_date = datetime(year, month, day)
        offset = random.randint(-30, 90)
        work_date = insp_date + timedelta(days=offset)
        work_date_key = int(work_date.strftime("%Y%m%d"))

        span_feet = max(10, np.random.normal(80, 30))
        cost = span_feet * np.random.uniform(8, 20)

        rows.append(
            {
                "WorkOrderID": f"WO_{work_id:08d}",
                "PoleID": row["PoleID"],
                "CircuitID": pole["CircuitID"],
                "WorkDateKey": work_date_key,
                "WorkType": random.choice(work_types),
                "SpanFeetTreated": round(span_feet, 1),
                "CostUSD": round(cost, 2),
                "ContractorName": random.choice(contractors),
            }
        )
        work_id += 1

    return pd.DataFrame(rows)


def make_dictionaries():
    cause_codes = pd.DataFrame(
        [
            ("TREES", "Tree or vegetation contact"),
            ("EQUIP_FAIL", "Equipment failure"),
            ("ANIMALS", "Animal interference"),
            ("WEATHER", "Weather-related"),
            ("FIRE_PREVENT", "PSPS / fire prevention"),
            ("OTHER", "Other / unknown"),
        ],
        columns=["CauseCode", "Description"],
    )
    weather_types = pd.DataFrame(
        [
            ("None", "No significant weather"),
            ("Wind", "High winds"),
            ("Storm", "Thunderstorm"),
            ("Snow", "Snow / ice"),
            ("HeatWave", "Extreme heat"),
        ],
        columns=["WeatherEventType", "Description"],
    )
    priority_codes = pd.DataFrame(
        [
            ("P1", "Immediate hazard"),
            ("P2", "High priority"),
            ("P3", "Routine"),
            ("P4", "Low / monitor"),
        ],
        columns=["PriorityCode", "Description"],
    )
    return cause_codes, weather_types, priority_codes


def main():
    base_dir = "data"
    raw_dir = os.path.join(base_dir, "raw")
    dict_dir = os.path.join(base_dir, "dictionaries")
    ensure_dir(raw_dir)
    ensure_dir(dict_dir)

    dim_date = make_dim_date()
    dim_circuit = make_dim_circuit()
    dim_risk_zone = make_dim_risk_zone()
    dim_pole = make_dim_pole(dim_circuit, dim_risk_zone)

    fact_outage = make_fact_outage(dim_date, dim_circuit, dim_pole)
    fact_trouble = make_fact_trouble_call(dim_date, fact_outage)
    fact_insp = make_fact_vegetation_inspection(dim_date, dim_pole)
    fact_veg_work = make_fact_veg_work(dim_date, fact_insp, dim_pole)

    dim_date.to_csv(os.path.join(raw_dir, "dim_date.csv"), index=False)
    dim_circuit.to_csv(os.path.join(raw_dir, "dim_circuit.csv"), index=False)
    dim_pole.to_csv(os.path.join(raw_dir, "dim_pole.csv"), index=False)
    dim_risk_zone.to_csv(os.path.join(raw_dir, "dim_risk_zone.csv"), index=False)

    fact_outage.to_csv(os.path.join(raw_dir, "fact_outage.csv"), index=False)
    fact_trouble.to_csv(os.path.join(raw_dir, "fact_trouble_call.csv"), index=False)
    fact_insp.to_csv(os.path.join(raw_dir, "fact_vegetation_inspection.csv"), index=False)
    fact_veg_work.to_csv(os.path.join(raw_dir, "fact_veg_work.csv"), index=False)

    cause_codes, weather_types, priority_codes = make_dictionaries()
    cause_codes.to_csv(os.path.join(dict_dir, "cause_codes.csv"), index=False)
    weather_types.to_csv(os.path.join(dict_dir, "weather_event_types.csv"), index=False)
    priority_codes.to_csv(os.path.join(dict_dir, "veg_priority_codes.csv"), index=False)

    print("Synthetic data generated under data/raw and data/dictionaries")


if __name__ == "__main__":
    main()
