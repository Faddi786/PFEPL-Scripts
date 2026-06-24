"""
Convert Ulhas gauges Excel file to gapIt ARFF format and supporting files.
Run: python convert_excel_to_gapit.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Your Excel: use this file (with zeros/empties to be filled by gapIt)
SCRIPT_DIR = Path(__file__).resolve().parent
EXCEL_PATH = SCRIPT_DIR / "input" / "ulhas_gauges.xlsx"
OUTPUT_DIR = SCRIPT_DIR / "gapit" / "ulhas_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Station names from sheet names (Excel columns may vary)
STATIONS = ["titwala", "kaman", "pise", "naldhe", "badlapur"]
# Discharge column name (some sheets have "discharge (m3/sec)" vs "discharge (m3 sec)")
DISC_COLS = ["discharge (m3/sec)", "discharge (m3 sec)"]

def main():
    xl = pd.ExcelFile(EXCEL_PATH)
    
    # Load all sheets and build date -> {station: value} map
    all_dates = set()
    data_by_station = {}
    
    for sheet in STATIONS:
        if sheet not in xl.sheet_names:
            print(f"Warning: sheet '{sheet}' not found, skipping")
            continue
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
        # Find discharge column
        disc_col = None
        for c in DISC_COLS:
            if c in df.columns:
                disc_col = c
                break
        if disc_col is None:
            disc_col = [c for c in df.columns if "discharge" in c.lower()][0]
        
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        df = df.dropna(subset=["date"])
        dates = df["date"].unique()
        data_by_station[sheet] = df.set_index("date")[disc_col]
        all_dates.update(pd.Timestamp(d) for d in dates)
    
    all_dates = sorted(all_dates)
    print(f"Date range: {min(all_dates)} to {max(all_dates)} ({len(all_dates)} days)")
    
    # Build ARFF
    arff_lines = [
        "@relation ulhas_gauges_discharge",
        "",
    ]
    for s in STATIONS:
        arff_lines.append(f"@attribute {s}_val numeric")
    arff_lines.append("@attribute timestamp date dd-MM-yyyy-HH:mm:ss")
    arff_lines.append("")
    arff_lines.append("@data")
    
    # Treat empty and zero as missing (?) so gapIt can fill them
    for d in all_dates:
        row = []
        for s in STATIONS:
            if s in data_by_station and d in data_by_station[s].index:
                v = data_by_station[s].loc[d]
                if pd.isna(v) or (isinstance(v, (int, float)) and v == 0):
                    row.append("?")
                else:
                    row.append(f"{float(v):.6f}")
            else:
                row.append("?")
        ts = d.strftime("%d-%m-%Y-00:00:00")
        row.append(ts)
        arff_lines.append(",".join(row))
    
    arff_path = OUTPUT_DIR / "all_valid_q_series_complete2.arff"
    with open(arff_path, "w") as f:
        f.write("\n".join(arff_lines))
    print(f"Wrote {arff_path}")
    
    # Stations coordinates (placeholder X,Y - replace with real coordinates if available)
    coords_path = OUTPUT_DIR / "stations_coordinates.txt"
    with open(coords_path, "w") as f:
        f.write("STATIONS\tX_LUREF\tY_LUREF\n")
        for i, s in enumerate(STATIONS):
            # Placeholder: use simple grid
            f.write(f"{s}\t{10000 + i*5000}\t{70000 + i*5000}\n")
    print(f"Wrote {coords_path}")
    
    # Minimal knowledge DB (required by gapIt for CBR suggestions)
    kdb_lines = [
        "@relation stream",
        "",
        f"@attribute serieName {{{','.join(s+'_val' for s in STATIONS)}}}",
        "@attribute serieX numeric",
        "@attribute serieY numeric",
        "@attribute gapSize numeric",
        "@attribute gapPosition numeric",
        "@attribute season {Spring,Summer,Autumn,Winter}",
        "@attribute year numeric",
        "@attribute isDuringRising {false,true}",
        "@attribute flow {low,middle,high}",
        "@attribute hasDownstream {false,true}",
        "@attribute hasUpstream {false,true}",
        "@attribute algo {Interpolation,EM,REG,REPTREE,M5P,ZeroR,ANN,NEARESTNEIGHBOUR}",
        "@attribute useDiscretizedTime {false,true}",
        "@attribute useMostSimilar {false,true}",
        "@attribute useNearest {true,false}",
        "@attribute useDownstream {false,true}",
        "@attribute useUpstream {false,true}",
        "@attribute MAE numeric",
        "@attribute RMSE numeric",
        "@attribute RSR numeric",
        "@attribute PBIAS numeric",
        "@attribute NashSutcliffe numeric",
        "@attribute indexOfAgreement numeric",
        "@attribute wasTheBestSolution {false,true}",
        "",
        "@data",
    ]
    # Add minimal cases for each station
    for s in STATIONS:
        x, y = 10000, 70000  # placeholder
        kdb_lines.append(f"{s}_val,{x},{y},2,50,Summer,2010,false,middle,false,false,Interpolation,false,false,true,false,false,0.1,0.1,0.5,0,0.8,0.9,false")
    
    kdb_path = OUTPUT_DIR / "knowledgeDB20-discharge.arff"
    with open(kdb_path, "w") as f:
        f.write("\n".join(kdb_lines))
    print(f"Wrote {kdb_path}")
    
    # Copy map image from sample if exists
    sample_map = SCRIPT_DIR / "gapit" / "data_fake2" / "data_fake2" / "map2.png"
    if sample_map.exists():
        import shutil
        shutil.copy(sample_map, OUTPUT_DIR / "map2.png")
        shutil.copy(sample_map, OUTPUT_DIR / "shapeCountry.jpg")
        print(f"Copied map from sample")
    
    # Create minimal relationships XML (Java serialized GraphTO - simplified)
    # gapIt expects this format. We create nodes only, no edges.
    rel_path = OUTPUT_DIR / "stations_relationships_1.xml"
    rel_content = """<?xml version="1.0" encoding="UTF-8"?>
<java version="1.7" class="java.beans.XMLDecoder">
 <object class="lu.lippmann.cdb.models.GraphTO">
  <void property="graphId"><long>1</long></void>
  <void property="operations">
   <void method="add">
    <object class="lu.lippmann.cdb.models.history.GraphOperation">
     <void property="operation">
      <object class="java.lang.Enum" method="valueOf">
       <class>lu.lippmann.cdb.models.history.Operation</class>
       <string>NODE_ADDED</string>
      </object>
     </void>
     <void property="parameters">
      <object class="java.util.ArrayList">
       <void method="add">
        <object class="lu.lippmann.cdb.models.CNode">
         <void property="id"><long>1</long></void>
         <void property="name"><string>titwala</string></void>
        </object>
       </void>
       <void method="add"><double>100.0</double></void>
       <void method="add"><double>100.0</double></void>
      </object>
     </void>
    </object>
   </void>
   <void method="add">
    <object class="lu.lippmann.cdb.models.history.GraphOperation">
     <void property="operation">
      <object class="java.lang.Enum" method="valueOf">
       <class>lu.lippmann.cdb.models.history.Operation</class>
       <string>NODE_ADDED</string>
      </object>
     </void>
     <void property="parameters">
      <object class="java.util.ArrayList">
       <void method="add">
        <object class="lu.lippmann.cdb.models.CNode">
         <void property="id"><long>2</long></void>
         <void property="name"><string>kaman</string></void>
        </object>
       </void>
       <void method="add"><double>200.0</double></void>
       <void method="add"><double>200.0</double></void>
      </object>
     </void>
    </object>
   </void>
   <void method="add">
    <object class="lu.lippmann.cdb.models.history.GraphOperation">
     <void property="operation">
      <object class="java.lang.Enum" method="valueOf">
       <class>lu.lippmann.cdb.models.history.Operation</class>
       <string>NODE_ADDED</string>
      </object>
     </void>
     <void property="parameters">
      <object class="java.util.ArrayList">
       <void method="add">
        <object class="lu.lippmann.cdb.models.CNode">
         <void property="id"><long>3</long></void>
         <void property="name"><string>pise</string></void>
        </object>
       </void>
       <void method="add"><double>300.0</double></void>
       <void method="add"><double>300.0</double></void>
      </object>
     </void>
    </object>
   </void>
   <void method="add">
    <object class="lu.lippmann.cdb.models.history.GraphOperation">
     <void property="operation">
      <object class="java.lang.Enum" method="valueOf">
       <class>lu.lippmann.cdb.models.history.Operation</class>
       <string>NODE_ADDED</string>
      </object>
     </void>
     <void property="parameters">
      <object class="java.util.ArrayList">
       <void method="add">
        <object class="lu.lippmann.cdb.models.CNode">
         <void property="id"><long>4</long></void>
         <void property="name"><string>naldhe</string></void>
        </object>
       </void>
       <void method="add"><double>400.0</double></void>
       <void method="add"><double>400.0</double></void>
      </object>
     </void>
    </object>
   </void>
   <void method="add">
    <object class="lu.lippmann.cdb.models.history.GraphOperation">
     <void property="operation">
      <object class="java.lang.Enum" method="valueOf">
       <class>lu.lippmann.cdb.models.history.Operation</class>
       <string>NODE_ADDED</string>
      </object>
     </void>
     <void property="parameters">
      <object class="java.util.ArrayList">
       <void method="add">
        <object class="lu.lippmann.cdb.models.CNode">
         <void property="id"><long>5</long></void>
         <void property="name"><string>badlapur</string></void>
        </object>
       </void>
       <void method="add"><double>500.0</double></void>
       <void method="add"><double>500.0</double></void>
      </object>
     </void>
    </object>
   </void>
  </void>
 </object>
</java>
"""
    with open(rel_path, "w") as f:
        f.write(rel_content)
    print(f"Wrote {rel_path}")
    
    # Empty second relationships file (gapIt expects two paths)
    rel2_path = OUTPUT_DIR / "stations_relationships_2.xml"
    with open(rel2_path, "w") as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<java version="1.7" class="java.beans.XMLDecoder">
 <object class="lu.lippmann.cdb.models.GraphTO">
  <void property="graphId"><long>2</long></void>
  <void property="operations"/>
 </object>
</java>
""")
    print(f"Wrote {rel2_path}")
    
    print("\nDone! Run gapit/run.bat to open gapIt with the prepared data.")

if __name__ == "__main__":
    main()
