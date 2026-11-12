# ═══════════════════════════════════════════════════════════════════════════════
#  MedScan AI — Medical Reference Database
#  Sources: Your provided data + standard clinical reference ranges
#  (Medscape, Harrison's, Tietz Clinical Chemistry, WHO, ADA, ACC/AHA)
#
#  Structure per test:
#    "STANDARD_NAME": {
#        "aliases"       : [...all alternate names, abbreviations, spellings...],
#        "category"      : "panel name",
#        "unit"          : "standard unit",

import re
#        "male"          : (min, max),   # adult male range
#        "female"        : (min, max),   # adult female range
#        "child"         : (min, max),   # paediatric range (None = use adult)
#        "elderly"       : (min, max),   # 60+ (None = use adult)
#        "critical_low"  : value,        # dangerously low (None if not applicable)
#        "critical_high" : value,        # dangerously high (None if not applicable)
#        "note"          : "clinical note"
#    }
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCE_DB: dict = {

    # ──────────────────────────────────────────────────────────────────────────
    #  COMPLETE BLOOD COUNT (CBC / HAEMATOLOGY)
    # ──────────────────────────────────────────────────────────────────────────

    "Hemoglobin": {
        "aliases": ["Hb", "Hgb", "Haemoglobin", "Hemoglobin Level", "HGB", "H&H"],
        "category": "Complete Blood Count",
        "unit": "g/dL",
        "male":         (13.2, 16.6),
        "female":       (11.6, 15.0),
        "child":        (11.0, 14.0),
        "elderly":      (12.0, 16.0),
        "critical_low": 7.0,
        "critical_high": 20.0,
        "note": "Low = anaemia; High = polycythaemia"
    },
    "Hematocrit": {
        "aliases": ["Hct", "HCT", "Haematocrit", "Packed Cell Volume", "PCV"],
        "category": "Complete Blood Count",
        "unit": "%",
        "male":         (38.3, 48.6),
        "female":       (35.5, 44.9),
        "child":        (33.0, 42.0),
        "elderly":      (35.0, 47.0),
        "critical_low": 20.0,
        "critical_high": 60.0,
        "note": "Percentage of blood volume occupied by RBCs"
    },
    "RBC Count": {
        "aliases": ["RBC", "Red Blood Cell Count", "Red Cell Count", "Erythrocyte Count"],
        "category": "Complete Blood Count",
        "unit": "x10^12/L",
        "male":         (4.35, 5.65),
        "female":       (3.92, 5.13),
        "child":        (3.80, 5.10),
        "elderly":      (3.80, 5.50),
        "critical_low": 2.0,
        "critical_high": 7.0,
        "note": None
    },
    "WBC Count": {
        "aliases": ["WBC", "TLC", "Total Leucocyte Count", "Total Leukocyte Count",
                    "White Blood Cell Count", "White Cell Count", "Leukocyte Count",
                    "Total WBC", "WCC"],
        "category": "Complete Blood Count",
        "unit": "x10^9/L",
        "male":         (4.5, 11.0),
        "female":       (4.5, 11.0),
        "child":        (5.0, 15.0),
        "elderly":      (4.0, 10.5),
        "critical_low": 2.0,
        "critical_high": 30.0,
        "note": "Elevated in infection/inflammation; low in immunosuppression"
    },
    "Platelet Count": {
        "aliases": ["PLT", "Plt", "Platelets", "Thrombocyte Count", "PC",
                    "Platelet", "Blood Platelets"],
        "category": "Complete Blood Count",
        "unit": "x10^9/L",
        "male":         (150, 400),
        "female":       (150, 400),
        "child":        (150, 400),
        "elderly":      (150, 400),
        "critical_low": 50.0,
        "critical_high": 1000.0,
        "note": "< 50 = bleeding risk; > 1000 = thrombosis risk"
    },
    "MCV": {
        "aliases": ["Mean Corpuscular Volume", "Mean Cell Volume"],
        "category": "Complete Blood Count",
        "unit": "fL",
        "male":         (80.0, 100.0),
        "female":       (80.0, 100.0),
        "child":        (70.0, 90.0),
        "elderly":      (80.0, 100.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Low = microcytic (iron def/thalassaemia); High = macrocytic (B12/folate def)"
    },
    "MCH": {
        "aliases": ["Mean Corpuscular Hemoglobin", "Mean Cell Haemoglobin",
                    "Mean Corpuscular Haemoglobin"],
        "category": "Complete Blood Count",
        "unit": "pg",
        "male":         (27.0, 33.0),
        "female":       (27.0, 33.0),
        "child":        (25.0, 31.0),
        "elderly":      (27.0, 33.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "MCHC": {
        "aliases": ["Mean Corpuscular Hemoglobin Concentration",
                    "Mean Cell Haemoglobin Concentration",
                    "Mean Corpuscular Haemoglobin Concentration"],
        "category": "Complete Blood Count",
        "unit": "g/dL",
        "male":         (32.0, 36.0),
        "female":       (32.0, 36.0),
        "child":        (31.0, 36.0),
        "elderly":      (32.0, 36.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "RDW": {
        "aliases": ["Red Cell Distribution Width", "RDW-CV", "RDW-SD"],
        "category": "Complete Blood Count",
        "unit": "%",
        "male":         (11.5, 14.5),
        "female":       (11.5, 14.5),
        "child":        (11.5, 14.5),
        "elderly":      (11.5, 14.5),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in mixed anaemia, iron deficiency"
    },
    "Neutrophils": {
        "aliases": ["Neutrophil Count", "NEUT", "Polymorphs", "PMN",
                    "Segmented Neutrophils", "Segs", "Absolute Neutrophil Count", "ANC"],
        "category": "Differential Count",
        "unit": "%",
        "male":         (50.0, 70.0),
        "female":       (50.0, 70.0),
        "child":        (30.0, 60.0),
        "elderly":      (50.0, 70.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in bacterial infection"
    },
    "Lymphocytes": {
        "aliases": ["Lymphocyte Count", "LYMPH", "Lymphs"],
        "category": "Differential Count",
        "unit": "%",
        "male":         (20.0, 40.0),
        "female":       (20.0, 40.0),
        "child":        (25.0, 50.0),
        "elderly":      (20.0, 40.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in viral infections"
    },
    "Monocytes": {
        "aliases": ["Monocyte Count", "MONO"],
        "category": "Differential Count",
        "unit": "%",
        "male":         (2.0, 8.0),
        "female":       (2.0, 8.0),
        "child":        (2.0, 8.0),
        "elderly":      (2.0, 8.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "Eosinophils": {
        "aliases": ["Eosinophil Count", "EOS", "Eos"],
        "category": "Differential Count",
        "unit": "%",
        "male":         (1.0, 4.0),
        "female":       (1.0, 4.0),
        "child":        (1.0, 5.0),
        "elderly":      (1.0, 4.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in allergies and parasitic infections"
    },
    "Basophils": {
        "aliases": ["Basophil Count", "BASO"],
        "category": "Differential Count",
        "unit": "%",
        "male":         (0.0, 1.0),
        "female":       (0.0, 1.0),
        "child":        (0.0, 1.0),
        "elderly":      (0.0, 1.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "Reticulocytes": {
        "aliases": ["Reticulocyte Count", "Retic", "RETIC"],
        "category": "Complete Blood Count",
        "unit": "%",
        "male":         (0.5, 2.0),
        "female":       (0.5, 2.0),
        "child":        (0.5, 2.5),
        "elderly":      (0.5, 2.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Reflects bone marrow erythropoietic activity"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  COAGULATION
    # ──────────────────────────────────────────────────────────────────────────

    "Prothrombin Time": {
        "aliases": ["PT", "Pro Time", "Prothrombin Time", "PT/INR"],
        "category": "Coagulation",
        "unit": "seconds",
        "male":         (9.4, 12.5),
        "female":       (9.4, 12.5),
        "child":        (9.0, 13.0),
        "elderly":      (9.4, 13.5),
        "critical_low": None,
        "critical_high": 30.0,
        "note": "Measures extrinsic pathway"
    },
    "INR": {
        "aliases": ["International Normalized Ratio", "INR Ratio"],
        "category": "Coagulation",
        "unit": "",
        "male":         (0.8, 1.1),
        "female":       (0.8, 1.1),
        "child":        (0.8, 1.2),
        "elderly":      (0.8, 1.2),
        "critical_low": None,
        "critical_high": 3.5,
        "note": "Target 2.0-3.0 for anticoagulation therapy"
    },
    "APTT": {
        "aliases": ["Activated Partial Thromboplastin Time", "aPTT", "PTT",
                    "Partial Thromboplastin Time", "PTTK"],
        "category": "Coagulation",
        "unit": "seconds",
        "male":         (25.0, 35.0),
        "female":       (25.0, 35.0),
        "child":        (25.0, 35.0),
        "elderly":      (25.0, 38.0),
        "critical_low": None,
        "critical_high": 70.0,
        "note": "Measures intrinsic pathway; elevated in haemophilia/heparin"
    },
    "Fibrinogen": {
        "aliases": ["Fibrinogen Level", "Factor I", "Plasma Fibrinogen"],
        "category": "Coagulation",
        "unit": "mg/dL",
        "male":         (200.0, 400.0),
        "female":       (200.0, 400.0),
        "child":        (150.0, 400.0),
        "elderly":      (200.0, 450.0),
        "critical_low": 100.0,
        "critical_high": None,
        "note": "Low in DIC; elevated in inflammation"
    },
    "D-Dimer": {
        "aliases": ["D Dimer", "DDimer", "D-Dimer Level", "Fibrin Degradation Products"],
        "category": "Coagulation",
        "unit": "µg/L",
        "male":         (0.0, 500.0),
        "female":       (0.0, 500.0),
        "child":        (0.0, 500.0),
        "elderly":      (0.0, 500.0),
        "critical_low": None,
        "critical_high": 1000.0,
        "note": "Elevated in DVT, PE, DIC; non-specific"
    },
    "Bleeding Time": {
        "aliases": ["BT", "Bleeding Time Test"],
        "category": "Coagulation",
        "unit": "minutes",
        "male":         (1.0, 9.0),
        "female":       (1.0, 9.0),
        "child":        (1.0, 9.0),
        "elderly":      (1.0, 9.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  LIVER FUNCTION TESTS (LFT)
    # ──────────────────────────────────────────────────────────────────────────

    "ALT": {
        "aliases": ["Alanine Aminotransferase", "Alanine Transaminase", "SGPT",
                    "Serum Glutamate Pyruvate Transaminase", "GPT"],
        "category": "Liver Function Tests",
        "unit": "U/L",
        "male":         (7.0, 55.0),
        "female":       (7.0, 45.0),
        "child":        (7.0, 45.0),
        "elderly":      (7.0, 40.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "Most liver-specific enzyme; elevated in hepatitis"
    },
    "AST": {
        "aliases": ["Aspartate Aminotransferase", "Aspartate Transaminase", "SGOT",
                    "Serum Glutamate Oxaloacetate Transaminase", "GOT"],
        "category": "Liver Function Tests",
        "unit": "U/L",
        "male":         (8.0, 48.0),
        "female":       (8.0, 43.0),
        "child":        (8.0, 60.0),
        "elderly":      (8.0, 45.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "Also elevated in cardiac/muscle damage"
    },
    "ALP": {
        "aliases": ["Alkaline Phosphatase", "Alk Phos", "AlkPhos"],
        "category": "Liver Function Tests",
        "unit": "U/L",
        "male":         (40.0, 129.0),
        "female":       (35.0, 104.0),
        "child":        (50.0, 350.0),
        "elderly":      (40.0, 150.0),
        "critical_low": None,
        "critical_high": None,
        "note": "High in bone disease, liver disease, pregnancy"
    },
    "GGT": {
        "aliases": ["Gamma Glutamyl Transferase", "Gamma GT", "GGTP",
                    "Gamma Glutamyl Transpeptidase", "GGT Level"],
        "category": "Liver Function Tests",
        "unit": "U/L",
        "male":         (8.0, 61.0),
        "female":       (5.0, 36.0),
        "child":        (5.0, 32.0),
        "elderly":      (8.0, 65.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Sensitive marker for alcohol use and bile duct disease"
    },
    "Total Bilirubin": {
        "aliases": ["Bilirubin Total", "T. Bili", "T Bilirubin", "Bilirubin",
                    "Serum Bilirubin", "Total Serum Bilirubin"],
        "category": "Liver Function Tests",
        "unit": "mg/dL",
        "male":         (0.3, 1.2),
        "female":       (0.3, 1.2),
        "child":        (0.3, 1.0),
        "elderly":      (0.3, 1.2),
        "critical_low": None,
        "critical_high": 15.0,
        "note": "Elevated in jaundice, liver disease, haemolysis"
    },
    "Direct Bilirubin": {
        "aliases": ["Conjugated Bilirubin", "Direct Bili", "D. Bili",
                    "Bilirubin Direct", "DBIL"],
        "category": "Liver Function Tests",
        "unit": "mg/dL",
        "male":         (0.1, 0.3),
        "female":       (0.1, 0.3),
        "child":        (0.0, 0.2),
        "elderly":      (0.1, 0.3),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in obstructive jaundice"
    },
    "Indirect Bilirubin": {
        "aliases": ["Unconjugated Bilirubin", "Indirect Bili", "I. Bili", "IBIL"],
        "category": "Liver Function Tests",
        "unit": "mg/dL",
        "male":         (0.2, 0.9),
        "female":       (0.2, 0.9),
        "child":        (0.2, 0.8),
        "elderly":      (0.2, 0.9),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in haemolysis, Gilbert syndrome"
    },
    "Albumin": {
        "aliases": ["Serum Albumin", "Alb", "ALB"],
        "category": "Liver Function Tests",
        "unit": "g/dL",
        "male":         (3.5, 5.0),
        "female":       (3.5, 5.0),
        "child":        (3.8, 5.4),
        "elderly":      (3.2, 4.6),
        "critical_low": 2.0,
        "critical_high": None,
        "note": "Low in malnutrition, liver disease, nephrotic syndrome"
    },
    "Total Protein": {
        "aliases": ["Serum Total Protein", "TP", "Total Proteins"],
        "category": "Liver Function Tests",
        "unit": "g/dL",
        "male":         (6.4, 8.3),
        "female":       (6.4, 8.3),
        "child":        (6.0, 8.0),
        "elderly":      (6.0, 8.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "Globulin": {
        "aliases": ["Serum Globulin", "Glob"],
        "category": "Liver Function Tests",
        "unit": "g/dL",
        "male":         (2.0, 3.5),
        "female":       (2.0, 3.5),
        "child":        (2.0, 3.5),
        "elderly":      (2.0, 3.5),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "A/G Ratio": {
        "aliases": ["Albumin Globulin Ratio", "AG Ratio"],
        "category": "Liver Function Tests",
        "unit": "",
        "male":         (1.1, 2.5),
        "female":       (1.1, 2.5),
        "child":        (1.1, 2.5),
        "elderly":      (1.1, 2.5),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "Amylase": {
        "aliases": ["Serum Amylase", "AMY", "Pancreatic Amylase"],
        "category": "Liver Function Tests",
        "unit": "U/L",
        "male":         (30.0, 220.0),
        "female":       (30.0, 220.0),
        "child":        (30.0, 100.0),
        "elderly":      (30.0, 220.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "Elevated in pancreatitis, parotitis"
    },
    "Lipase": {
        "aliases": ["Serum Lipase", "LIP"],
        "category": "Liver Function Tests",
        "unit": "U/L",
        "male":         (0.0, 160.0),
        "female":       (0.0, 160.0),
        "child":        (0.0, 100.0),
        "elderly":      (0.0, 160.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "More specific for pancreatitis than amylase"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  KIDNEY / RENAL FUNCTION TESTS (KFT / RFT)
    # ──────────────────────────────────────────────────────────────────────────

    "Creatinine": {
        "aliases": ["Serum Creatinine", "Cr", "SCr", "Creatinine Level"],
        "category": "Kidney Function Tests",
        "unit": "mg/dL",
        "male":         (0.74, 1.35),
        "female":       (0.59, 1.04),
        "child":        (0.20, 0.80),
        "elderly":      (0.70, 1.30),
        "critical_low": None,
        "critical_high": 10.0,
        "note": "Elevated in renal failure; use eGFR for staging"
    },
    "Blood Urea Nitrogen": {
        "aliases": ["BUN", "Urea Nitrogen", "Blood Urea", "Serum Urea Nitrogen"],
        "category": "Kidney Function Tests",
        "unit": "mg/dL",
        "male":         (7.0, 20.0),
        "female":       (7.0, 20.0),
        "child":        (5.0, 18.0),
        "elderly":      (8.0, 23.0),
        "critical_low": None,
        "critical_high": 100.0,
        "note": "Elevated in renal disease, dehydration, high protein diet"
    },
    "Urea": {
        "aliases": ["Serum Urea", "Blood Urea", "Urea Level", "Plasma Urea"],
        "category": "Kidney Function Tests",
        "unit": "mg/dL",
        "male":         (15.0, 45.0),
        "female":       (15.0, 45.0),
        "child":        (10.0, 35.0),
        "elderly":      (17.0, 49.0),
        "critical_low": None,
        "critical_high": 200.0,
        "note": "BUN x 2.14 = Urea"
    },
    "Uric Acid": {
        "aliases": ["Serum Uric Acid", "SUA", "Uric Acid Level", "UA"],
        "category": "Kidney Function Tests",
        "unit": "mg/dL",
        "male":         (3.5, 7.2),
        "female":       (2.6, 6.0),
        "child":        (2.5, 5.5),
        "elderly":      (3.5, 8.0),
        "critical_low": None,
        "critical_high": 12.0,
        "note": "Elevated in gout, renal failure, tumour lysis syndrome"
    },
    "eGFR": {
        "aliases": ["Estimated GFR", "Glomerular Filtration Rate",
                    "Estimated Glomerular Filtration Rate", "GFR"],
        "category": "Kidney Function Tests",
        "unit": "mL/min/1.73m²",
        "male":         (60.0, 120.0),
        "female":       (60.0, 120.0),
        "child":        (80.0, 120.0),
        "elderly":      (45.0, 120.0),
        "critical_low": 15.0,
        "critical_high": None,
        "note": "< 60 = CKD; < 15 = kidney failure"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  ELECTROLYTES
    # ──────────────────────────────────────────────────────────────────────────

    "Sodium": {
        "aliases": ["Na", "Serum Sodium", "Na+", "Sodium Level", "S. Sodium"],
        "category": "Electrolytes",
        "unit": "mEq/L",
        "male":         (136.0, 145.0),
        "female":       (136.0, 145.0),
        "child":        (135.0, 145.0),
        "elderly":      (136.0, 145.0),
        "critical_low": 120.0,
        "critical_high": 160.0,
        "note": "Hyponatraemia < 135; Hypernatraemia > 145"
    },
    "Potassium": {
        "aliases": ["K", "Serum Potassium", "K+", "Potassium Level", "S. Potassium"],
        "category": "Electrolytes",
        "unit": "mEq/L",
        "male":         (3.5, 5.1),
        "female":       (3.5, 5.1),
        "child":        (3.4, 4.7),
        "elderly":      (3.5, 5.1),
        "critical_low": 2.5,
        "critical_high": 6.5,
        "note": "Critical for cardiac rhythm; check in renal disease"
    },
    "Chloride": {
        "aliases": ["Cl", "Serum Chloride", "Cl-", "Chloride Level"],
        "category": "Electrolytes",
        "unit": "mEq/L",
        "male":         (98.0, 107.0),
        "female":       (98.0, 107.0),
        "child":        (98.0, 107.0),
        "elderly":      (98.0, 107.0),
        "critical_low": 80.0,
        "critical_high": 115.0,
        "note": None
    },
    "Bicarbonate": {
        "aliases": ["HCO3", "CO2", "Serum Bicarbonate", "Total CO2", "TCO2",
                    "Bicarb", "HCO3-"],
        "category": "Electrolytes",
        "unit": "mEq/L",
        "male":         (22.0, 29.0),
        "female":       (22.0, 29.0),
        "child":        (20.0, 28.0),
        "elderly":      (22.0, 29.0),
        "critical_low": 10.0,
        "critical_high": 40.0,
        "note": "Low in metabolic acidosis; high in metabolic alkalosis"
    },
    "Calcium": {
        "aliases": ["Total Calcium", "Ca", "Serum Calcium", "Ca2+",
                    "Calcium Level", "S. Calcium"],
        "category": "Electrolytes",
        "unit": "mg/dL",
        "male":         (8.5, 10.5),
        "female":       (8.5, 10.5),
        "child":        (9.0, 11.0),
        "elderly":      (8.5, 10.5),
        "critical_low": 7.0,
        "critical_high": 13.0,
        "note": "Regulated by PTH and Vitamin D"
    },
    "Ionized Calcium": {
        "aliases": ["Free Calcium", "Ionised Calcium", "iCa", "Ionized Ca"],
        "category": "Electrolytes",
        "unit": "mg/dL",
        "male":         (4.5, 5.6),
        "female":       (4.5, 5.6),
        "child":        (4.5, 5.6),
        "elderly":      (4.5, 5.6),
        "critical_low": 3.5,
        "critical_high": 6.5,
        "note": "More accurate than total calcium"
    },
    "Magnesium": {
        "aliases": ["Mg", "Serum Magnesium", "Mg2+", "Magnesium Level"],
        "category": "Electrolytes",
        "unit": "mEq/L",
        "male":         (1.3, 2.1),
        "female":       (1.3, 2.1),
        "child":        (1.5, 2.3),
        "elderly":      (1.3, 2.1),
        "critical_low": 0.5,
        "critical_high": 4.9,
        "note": "Low in malnutrition, alcoholism, diarrhoea"
    },
    "Phosphate": {
        "aliases": ["Phosphorus", "Inorganic Phosphate", "PO4", "P",
                    "Serum Phosphate", "Phosphate Level"],
        "category": "Electrolytes",
        "unit": "mg/dL",
        "male":         (2.5, 4.5),
        "female":       (2.5, 4.5),
        "child":        (4.0, 7.0),
        "elderly":      (2.5, 4.5),
        "critical_low": 1.0,
        "critical_high": 9.0,
        "note": "Elevated in renal failure; low in malnutrition"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  LIPID PANEL
    # ──────────────────────────────────────────────────────────────────────────

    "Total Cholesterol": {
        "aliases": ["Cholesterol", "TC", "Serum Cholesterol", "Total Cholesterol Level",
                    "Cholesterol Total"],
        "category": "Lipid Panel",
        "unit": "mg/dL",
        "male":         (0.0, 200.0),
        "female":       (0.0, 200.0),
        "child":        (0.0, 170.0),
        "elderly":      (0.0, 200.0),
        "critical_low": None,
        "critical_high": 300.0,
        "note": "Desirable < 200; Borderline 200-239; High ≥ 240"
    },
    "LDL Cholesterol": {
        "aliases": ["LDL", "Low Density Lipoprotein", "LDL-C",
                    "LDL Cholesterol Level", "Bad Cholesterol"],
        "category": "Lipid Panel",
        "unit": "mg/dL",
        "male":         (0.0, 100.0),
        "female":       (0.0, 100.0),
        "child":        (0.0, 110.0),
        "elderly":      (0.0, 100.0),
        "critical_low": None,
        "critical_high": 190.0,
        "note": "Optimal < 100; Near optimal 100-129; Borderline 130-159"
    },
    "HDL Cholesterol": {
        "aliases": ["HDL", "High Density Lipoprotein", "HDL-C",
                    "HDL Cholesterol Level", "Good Cholesterol"],
        "category": "Lipid Panel",
        "unit": "mg/dL",
        "male":         (40.0, 60.0),
        "female":       (50.0, 60.0),
        "child":        (40.0, 75.0),
        "elderly":      (40.0, 60.0),
        "critical_low": 25.0,
        "critical_high": None,
        "note": "Protective; > 60 = cardioprotective; < 40 = risk factor"
    },
    "Triglycerides": {
        "aliases": ["TG", "Trig", "TRIG", "Triglyceride Level",
                    "Serum Triglycerides", "Triacylglycerol"],
        "category": "Lipid Panel",
        "unit": "mg/dL",
        "male":         (0.0, 150.0),
        "female":       (0.0, 135.0),
        "child":        (0.0, 100.0),
        "elderly":      (0.0, 150.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "Borderline 150-199; High 200-499; Very high ≥ 500"
    },
    "VLDL Cholesterol": {
        "aliases": ["VLDL", "Very Low Density Lipoprotein", "VLDL-C"],
        "category": "Lipid Panel",
        "unit": "mg/dL",
        "male":         (5.0, 40.0),
        "female":       (5.0, 40.0),
        "child":        (5.0, 40.0),
        "elderly":      (5.0, 40.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Calculated as TG/5"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  BLOOD GLUCOSE / DIABETES PANEL
    # ──────────────────────────────────────────────────────────────────────────

    "Fasting Blood Glucose": {
        "aliases": ["FBS", "Fasting Blood Sugar", "FBG", "Fasting Glucose",
                    "Glucose Fasting", "Blood Glucose Fasting", "FPG"],
        "category": "Diabetes Panel",
        "unit": "mg/dL",
        "male":         (70.0, 100.0),
        "female":       (70.0, 100.0),
        "child":        (60.0, 100.0),
        "elderly":      (70.0, 110.0),
        "critical_low": 50.0,
        "critical_high": 500.0,
        "note": "Prediabetes 100-125; Diabetes ≥ 126 (ADA)"
    },
    "Postprandial Blood Glucose": {
        "aliases": ["PPBS", "PP Blood Sugar", "Post Prandial Glucose",
                    "2 Hour Post Glucose", "RBS", "Random Blood Sugar",
                    "Random Blood Glucose"],
        "category": "Diabetes Panel",
        "unit": "mg/dL",
        "male":         (70.0, 140.0),
        "female":       (70.0, 140.0),
        "child":        (70.0, 140.0),
        "elderly":      (70.0, 160.0),
        "critical_low": 50.0,
        "critical_high": 500.0,
        "note": "2-hour post-meal < 140 = normal; 140-199 = prediabetes; ≥ 200 = diabetes"
    },
    "HbA1c": {
        "aliases": ["Glycated Hemoglobin", "Glycosylated Hemoglobin", "A1c",
                    "Hemoglobin A1c", "HbA1C", "Glycated Haemoglobin"],
        "category": "Diabetes Panel",
        "unit": "%",
        "male":         (4.0, 5.7),
        "female":       (4.0, 5.7),
        "child":        (4.0, 5.7),
        "elderly":      (4.0, 6.5),
        "critical_low": None,
        "critical_high": 14.0,
        "note": "Prediabetes 5.7-6.4%; Diabetes ≥ 6.5% (ADA)"
    },
    "Fasting Insulin": {
        "aliases": ["Insulin Fasting", "Serum Insulin", "Insulin Level"],
        "category": "Diabetes Panel",
        "unit": "µIU/mL",
        "male":         (2.0, 19.6),
        "female":       (2.0, 19.6),
        "child":        (2.0, 13.0),
        "elderly":      (2.0, 19.6),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in insulin resistance; low in T1DM"
    },
    "C-Peptide": {
        "aliases": ["C Peptide", "Connecting Peptide"],
        "category": "Diabetes Panel",
        "unit": "ng/mL",
        "male":         (0.8, 3.1),
        "female":       (0.8, 3.1),
        "child":        (0.5, 2.5),
        "elderly":      (0.8, 3.1),
        "critical_low": None,
        "critical_high": None,
        "note": "Distinguishes T1 from T2 diabetes"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  THYROID FUNCTION TESTS (TFT)
    # ──────────────────────────────────────────────────────────────────────────

    "TSH": {
        "aliases": ["Thyroid Stimulating Hormone", "Thyrotropin",
                    "Thyroid Stimulating Hormone Level", "TSH Level"],
        "category": "Thyroid Function Tests",
        "unit": "µIU/mL",
        "male":         (0.4, 4.5),
        "female":       (0.4, 4.5),
        "child":        (0.7, 6.4),
        "elderly":      (0.4, 6.0),
        "critical_low": 0.01,
        "critical_high": 10.0,
        "note": "Elevated in hypothyroidism; suppressed in hyperthyroidism"
    },
    "Free T4": {
        "aliases": ["FT4", "Free Thyroxine", "Free T4 Level", "fT4",
                    "Free Tetraiodothyronine"],
        "category": "Thyroid Function Tests",
        "unit": "ng/dL",
        "male":         (0.8, 1.8),
        "female":       (0.8, 1.8),
        "child":        (0.9, 2.3),
        "elderly":      (0.8, 1.8),
        "critical_low": 0.5,
        "critical_high": 3.5,
        "note": "Low in hypothyroidism; high in hyperthyroidism"
    },
    "Free T3": {
        "aliases": ["FT3", "Free Triiodothyronine", "Free T3 Level", "fT3"],
        "category": "Thyroid Function Tests",
        "unit": "pg/mL",
        "male":         (2.3, 4.2),
        "female":       (2.3, 4.2),
        "child":        (2.5, 5.7),
        "elderly":      (2.3, 4.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Biologically active form of thyroid hormone"
    },
    "Total T4": {
        "aliases": ["T4", "Thyroxine", "Total Thyroxine", "Serum T4", "T4 Level",
                    "T4 Total", "Thyroxine Total"],
        "category": "Thyroid Function Tests",
        "unit": "µg/dL",
        "male":         (4.5, 12.5),
        "female":       (5.0, 12.0),
        "child":        (6.0, 15.0),
        "elderly":      (4.5, 12.5),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "Total T3": {
        "aliases": ["T3", "Triiodothyronine", "Total Triiodothyronine",
                    "Serum T3", "T3 Level", "T3 Total", "Triiodothyronine Total"],
        "category": "Thyroid Function Tests",
        "unit": "ng/dL",
        "male":         (80.0, 180.0),
        "female":       (80.0, 180.0),
        "child":        (100.0, 260.0),
        "elderly":      (80.0, 180.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Total T3 less useful than Free T3"
    },
    "Anti-TPO": {
        "aliases": ["Anti Thyroid Peroxidase", "TPO Antibody", "Anti-TPO Antibody",
                    "Thyroid Peroxidase Antibody", "ATPO"],
        "category": "Thyroid Function Tests",
        "unit": "IU/mL",
        "male":         (0.0, 34.0),
        "female":       (0.0, 34.0),
        "child":        (0.0, 34.0),
        "elderly":      (0.0, 34.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in Hashimoto's thyroiditis"
    },
    "Anti-TG": {
        "aliases": ["Anti Thyroglobulin", "TG Antibody", "Anti-Thyroglobulin Antibody",
                    "Thyroglobulin Antibody"],
        "category": "Thyroid Function Tests",
        "unit": "IU/mL",
        "male":         (0.0, 115.0),
        "female":       (0.0, 115.0),
        "child":        (0.0, 115.0),
        "elderly":      (0.0, 115.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in Hashimoto's and Graves' disease"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  IRON STUDIES
    # ──────────────────────────────────────────────────────────────────────────

    "Serum Iron": {
        "aliases": ["Iron", "Fe", "Total Serum Iron", "Iron Level", "S. Iron"],
        "category": "Iron Studies",
        "unit": "µg/dL",
        "male":         (60.0, 170.0),
        "female":       (50.0, 150.0),
        "child":        (50.0, 120.0),
        "elderly":      (50.0, 150.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "Low in iron deficiency anaemia"
    },
    "Ferritin": {
        "aliases": ["Serum Ferritin", "Ferritin Level", "Ferritin Serum"],
        "category": "Iron Studies",
        "unit": "ng/mL",
        "male":         (12.0, 300.0),
        "female":       (10.0, 150.0),
        "child":        (7.0, 140.0),
        "elderly":      (12.0, 300.0),
        "critical_low": 7.0,
        "critical_high": 1000.0,
        "note": "Best single test for iron stores; elevated in inflammation"
    },
    "TIBC": {
        "aliases": ["Total Iron Binding Capacity", "Total Iron Binding",
                    "Serum TIBC", "Iron Binding Capacity"],
        "category": "Iron Studies",
        "unit": "µg/dL",
        "male":         (250.0, 370.0),
        "female":       (250.0, 370.0),
        "child":        (250.0, 370.0),
        "elderly":      (250.0, 370.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in iron deficiency; low in iron overload"
    },
    "Transferrin Saturation": {
        "aliases": ["TSAT", "Iron Saturation", "Transferrin Sat",
                    "% Saturation", "Percent Transferrin Saturation"],
        "category": "Iron Studies",
        "unit": "%",
        "male":         (20.0, 50.0),
        "female":       (15.0, 50.0),
        "child":        (20.0, 50.0),
        "elderly":      (15.0, 50.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Low in iron deficiency; high in haemochromatosis"
    },
    "Transferrin": {
        "aliases": ["Serum Transferrin", "Siderophilin"],
        "category": "Iron Studies",
        "unit": "mg/dL",
        "male":         (215.0, 365.0),
        "female":       (215.0, 365.0),
        "child":        (203.0, 362.0),
        "elderly":      (200.0, 360.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  VITAMINS & MINERALS
    # ──────────────────────────────────────────────────────────────────────────

    "Vitamin D": {
        "aliases": ["25-OH Vitamin D", "25 Hydroxyvitamin D",
                    "Vitamin D3", "Cholecalciferol", "Vit D",
                    "25-Hydroxyvitamin D", "Vitamin D 25-OH"],
        "category": "Vitamins & Minerals",
        "unit": "ng/mL",
        "male":         (30.0, 100.0),
        "female":       (30.0, 100.0),
        "child":        (20.0, 100.0),
        "elderly":      (30.0, 100.0),
        "critical_low": 10.0,
        "critical_high": None,
        "note": "Deficiency < 20; Insufficiency 20-30; Optimal 30-60"
    },
    "Vitamin B12": {
        "aliases": ["B12", "Cobalamin", "Cyanocobalamin",
                    "Serum B12", "Vit B12", "Vitamin B-12"],
        "category": "Vitamins & Minerals",
        "unit": "pg/mL",
        "male":         (200.0, 900.0),
        "female":       (200.0, 900.0),
        "child":        (200.0, 900.0),
        "elderly":      (200.0, 900.0),
        "critical_low": 100.0,
        "critical_high": None,
        "note": "Low causes megaloblastic anaemia and neuropathy"
    },
    "Folate": {
        "aliases": ["Folic Acid", "Serum Folate", "Vitamin B9",
                    "Folate Level", "RBC Folate"],
        "category": "Vitamins & Minerals",
        "unit": "ng/mL",
        "male":         (5.0, 25.0),
        "female":       (5.0, 25.0),
        "child":        (5.0, 25.0),
        "elderly":      (5.0, 25.0),
        "critical_low": 3.0,
        "critical_high": None,
        "note": "Low in megaloblastic anaemia; critical in pregnancy"
    },
    "Vitamin A": {
        "aliases": ["Retinol", "Serum Vitamin A", "Vit A"],
        "category": "Vitamins & Minerals",
        "unit": "µg/dL",
        "male":         (32.5, 78.0),
        "female":       (32.5, 78.0),
        "child":        (20.0, 60.0),
        "elderly":      (32.5, 78.0),
        "critical_low": 10.0,
        "critical_high": 200.0,
        "note": "Deficiency causes night blindness"
    },
    "Vitamin C": {
        "aliases": ["Ascorbic Acid", "Serum Vitamin C", "Vit C"],
        "category": "Vitamins & Minerals",
        "unit": "mg/dL",
        "male":         (0.4, 1.5),
        "female":       (0.4, 1.5),
        "child":        (0.4, 1.5),
        "elderly":      (0.4, 1.5),
        "critical_low": 0.1,
        "critical_high": None,
        "note": "Deficiency causes scurvy"
    },
    "Vitamin E": {
        "aliases": ["Alpha Tocopherol", "Serum Vitamin E", "Vit E"],
        "category": "Vitamins & Minerals",
        "unit": "mg/L",
        "male":         (5.7, 19.9),
        "female":       (5.7, 19.9),
        "child":        (3.0, 15.0),
        "elderly":      (5.7, 19.9),
        "critical_low": None,
        "critical_high": None,
        "note": "Antioxidant vitamin"
    },
    "Vitamin K": {
        "aliases": ["Phylloquinone", "Serum Vitamin K", "Vit K"],
        "category": "Vitamins & Minerals",
        "unit": "ng/mL",
        "male":         (0.2, 1.0),
        "female":       (0.2, 1.0),
        "child":        (0.1, 1.0),
        "elderly":      (0.2, 1.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Essential for coagulation factors"
    },
    "Zinc": {
        "aliases": ["Serum Zinc", "Zn", "Zinc Level"],
        "category": "Vitamins & Minerals",
        "unit": "µg/dL",
        "male":         (70.0, 120.0),
        "female":       (70.0, 120.0),
        "child":        (60.0, 120.0),
        "elderly":      (70.0, 120.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Deficiency impairs immunity and wound healing"
    },
    "Copper": {
        "aliases": ["Serum Copper", "Cu", "Copper Level"],
        "category": "Vitamins & Minerals",
        "unit": "µg/dL",
        "male":         (70.0, 140.0),
        "female":       (80.0, 155.0),
        "child":        (20.0, 70.0),
        "elderly":      (70.0, 140.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in Wilson's disease and liver disease"
    },
    "Ceruloplasmin": {
        "aliases": ["Serum Ceruloplasmin", "CP"],
        "category": "Vitamins & Minerals",
        "unit": "mg/dL",
        "male":         (22.0, 58.0),
        "female":       (25.0, 65.0),
        "child":        (20.0, 60.0),
        "elderly":      (22.0, 58.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Low in Wilson's disease; elevated in pregnancy/inflammation"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  CARDIAC MARKERS
    # ──────────────────────────────────────────────────────────────────────────

    "Troponin I": {
        "aliases": ["cTnI", "Cardiac Troponin I", "Troponin-I", "TnI"],
        "category": "Cardiac Markers",
        "unit": "ng/mL",
        "male":         (0.0, 0.04),
        "female":       (0.0, 0.03),
        "child":        (0.0, 0.04),
        "elderly":      (0.0, 0.04),
        "critical_low": None,
        "critical_high": 0.4,
        "note": "Gold standard for MI; elevated 3-4h after chest pain"
    },
    "Troponin T": {
        "aliases": ["cTnT", "Cardiac Troponin T", "Troponin-T", "TnT", "hsTnT"],
        "category": "Cardiac Markers",
        "unit": "ng/mL",
        "male":         (0.0, 0.1),
        "female":       (0.0, 0.1),
        "child":        (0.0, 0.1),
        "elderly":      (0.0, 0.1),
        "critical_low": None,
        "critical_high": 0.5,
        "note": "Elevated in MI, myocarditis, renal failure"
    },
    "CK-MB": {
        "aliases": ["Creatine Kinase MB", "CKMB", "CK MB", "Creatine Kinase-MB"],
        "category": "Cardiac Markers",
        "unit": "U/L",
        "male":         (0.0, 25.0),
        "female":       (0.0, 25.0),
        "child":        (0.0, 25.0),
        "elderly":      (0.0, 25.0),
        "critical_low": None,
        "critical_high": 50.0,
        "note": "Peaks 12-24h after MI; < 5% of total CK is normal"
    },
    "Total CK": {
        "aliases": ["Creatine Kinase", "CK", "CPK", "Total Creatine Kinase",
                    "Creatine Phosphokinase"],
        "category": "Cardiac Markers",
        "unit": "U/L",
        "male":         (39.0, 308.0),
        "female":       (26.0, 192.0),
        "child":        (30.0, 200.0),
        "elderly":      (39.0, 308.0),
        "critical_low": None,
        "critical_high": 1000.0,
        "note": "Elevated in MI, muscle damage, exercise, rhabdomyolysis"
    },
    "LDH": {
        "aliases": ["Lactate Dehydrogenase", "Lactic Dehydrogenase",
                    "LDH Level", "Serum LDH"],
        "category": "Cardiac Markers",
        "unit": "U/L",
        "male":         (100.0, 190.0),
        "female":       (100.0, 190.0),
        "child":        (130.0, 380.0),
        "elderly":      (100.0, 190.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Non-specific; elevated in MI, haemolysis, liver disease"
    },
    "BNP": {
        "aliases": ["Brain Natriuretic Peptide", "B-type Natriuretic Peptide",
                    "NT-proBNP", "Pro-BNP"],
        "category": "Cardiac Markers",
        "unit": "pg/mL",
        "male":         (0.0, 100.0),
        "female":       (0.0, 100.0),
        "child":        (0.0, 100.0),
        "elderly":      (0.0, 200.0),
        "critical_low": None,
        "critical_high": 500.0,
        "note": "Elevated in heart failure; > 100 suggests HF"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  HORMONES
    # ──────────────────────────────────────────────────────────────────────────

    "FSH": {
        "aliases": ["Follicle Stimulating Hormone", "Follicle-Stimulating Hormone",
                    "FSH Level"],
        "category": "Hormones",
        "unit": "IU/L",
        "male":         (1.42, 15.4),
        "female":       (3.5, 12.5),
        "child":        (0.5, 5.0),
        "elderly":      (1.42, 15.4),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in menopause and primary hypogonadism"
    },
    "LH": {
        "aliases": ["Luteinizing Hormone", "Luteinising Hormone", "LH Level"],
        "category": "Hormones",
        "unit": "IU/L",
        "male":         (1.7, 8.6),
        "female":       (2.0, 15.0),
        "child":        (0.5, 3.0),
        "elderly":      (1.7, 8.6),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated at ovulation and in menopause"
    },
    "Testosterone": {
        "aliases": ["Total Testosterone", "Serum Testosterone",
                    "Testosterone Level", "T Level"],
        "category": "Hormones",
        "unit": "ng/dL",
        "male":         (280.0, 1100.0),
        "female":       (15.0, 70.0),
        "child":        (7.0, 130.0),
        "elderly":      (180.0, 800.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Low in hypogonadism; elevated in PCOS (females)"
    },
    "Estradiol": {
        "aliases": ["E2", "Oestradiol", "17-beta Estradiol",
                    "Estradiol Level", "Serum Estradiol"],
        "category": "Hormones",
        "unit": "pg/mL",
        "male":         (10.0, 50.0),
        "female":       (30.0, 400.0),
        "child":        (5.0, 20.0),
        "elderly":      (10.0, 50.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Varies by menstrual phase; low in menopause"
    },
    "Progesterone": {
        "aliases": ["Serum Progesterone", "Progesterone Level"],
        "category": "Hormones",
        "unit": "ng/mL",
        "male":         (0.1, 0.5),
        "female":       (0.1, 25.0),
        "child":        (0.1, 0.5),
        "elderly":      (0.1, 0.5),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in luteal phase and pregnancy"
    },
    "Prolactin": {
        "aliases": ["Serum Prolactin", "PRL", "Prolactin Level"],
        "category": "Hormones",
        "unit": "ng/mL",
        "male":         (3.0, 14.7),
        "female":       (3.0, 27.0),
        "child":        (3.0, 20.0),
        "elderly":      (3.0, 14.7),
        "critical_low": None,
        "critical_high": 200.0,
        "note": "Elevated in pituitary tumour, hypothyroidism, medications"
    },
    "Cortisol": {
        "aliases": ["Serum Cortisol", "Cortisol Level", "Morning Cortisol",
                    "Cortisol AM"],
        "category": "Hormones",
        "unit": "µg/dL",
        "male":         (6.0, 23.0),
        "female":       (6.0, 23.0),
        "child":        (3.0, 21.0),
        "elderly":      (6.0, 23.0),
        "critical_low": 3.0,
        "critical_high": 50.0,
        "note": "Diurnal variation; AM 6-23; PM 2-11 µg/dL"
    },
    "ACTH": {
        "aliases": ["Adrenocorticotropic Hormone", "Adrenocorticotrophin",
                    "Corticotropin", "ACTH Level"],
        "category": "Hormones",
        "unit": "pg/mL",
        "male":         (7.0, 63.0),
        "female":       (6.0, 58.0),
        "child":        (5.0, 46.0),
        "elderly":      (7.0, 63.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in Addison's disease; suppressed in Cushing's"
    },
    "DHEA-S": {
        "aliases": ["Dehydroepiandrosterone Sulfate", "DHEAS", "DHEA Sulfate"],
        "category": "Hormones",
        "unit": "µg/dL",
        "male":         (80.0, 560.0),
        "female":       (35.0, 430.0),
        "child":        (10.0, 200.0),
        "elderly":      (40.0, 300.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Adrenal androgen; elevated in PCOS and adrenal tumours"
    },
    "Growth Hormone": {
        "aliases": ["GH", "Somatotropin", "Human Growth Hormone", "HGH"],
        "category": "Hormones",
        "unit": "ng/mL",
        "male":         (0.0, 5.0),
        "female":       (0.0, 10.0),
        "child":        (0.0, 20.0),
        "elderly":      (0.0, 5.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Fasting levels; elevated in acromegaly"
    },
    "PTH": {
        "aliases": ["Parathyroid Hormone", "Parathormone", "iPTH",
                    "Intact PTH", "PTH Level"],
        "category": "Hormones",
        "unit": "pg/mL",
        "male":         (15.0, 65.0),
        "female":       (15.0, 65.0),
        "child":        (15.0, 65.0),
        "elderly":      (15.0, 75.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Regulates calcium; elevated in hyperparathyroidism"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  TUMOUR MARKERS
    # ──────────────────────────────────────────────────────────────────────────

    "PSA": {
        "aliases": ["Prostate Specific Antigen", "Total PSA", "PSA Level",
                    "Serum PSA"],
        "category": "Tumour Markers",
        "unit": "ng/mL",
        "male":         (0.0, 4.0),
        "female":       (0.0, 0.0),
        "child":        (0.0, 0.0),
        "elderly":      (0.0, 6.5),
        "critical_low": None,
        "critical_high": 10.0,
        "note": "Elevated in prostate cancer, BPH, prostatitis"
    },
    "CEA": {
        "aliases": ["Carcinoembryonic Antigen", "CEA Level"],
        "category": "Tumour Markers",
        "unit": "ng/mL",
        "male":         (0.0, 2.5),
        "female":       (0.0, 2.5),
        "child":        (0.0, 2.5),
        "elderly":      (0.0, 5.0),
        "critical_low": None,
        "critical_high": 10.0,
        "note": "Elevated in colorectal, lung, breast cancers; smokers may have higher levels"
    },
    "AFP": {
        "aliases": ["Alpha Fetoprotein", "Alpha-Fetoprotein", "AFP Level"],
        "category": "Tumour Markers",
        "unit": "ng/mL",
        "male":         (0.0, 8.1),
        "female":       (0.0, 8.1),
        "child":        (0.0, 8.1),
        "elderly":      (0.0, 8.1),
        "critical_low": None,
        "critical_high": 400.0,
        "note": "Elevated in liver cancer, germ cell tumours; normal in pregnancy"
    },
    "CA-125": {
        "aliases": ["Cancer Antigen 125", "CA125", "Ovarian Cancer Marker"],
        "category": "Tumour Markers",
        "unit": "U/mL",
        "male":         (0.0, 35.0),
        "female":       (0.0, 35.0),
        "child":        (0.0, 35.0),
        "elderly":      (0.0, 35.0),
        "critical_low": None,
        "critical_high": 200.0,
        "note": "Ovarian cancer marker; also elevated in endometriosis, fibroids"
    },
    "CA 19-9": {
        "aliases": ["CA19-9", "Carbohydrate Antigen 19-9", "CA19.9"],
        "category": "Tumour Markers",
        "unit": "U/mL",
        "male":         (0.0, 37.0),
        "female":       (0.0, 37.0),
        "child":        (0.0, 37.0),
        "elderly":      (0.0, 37.0),
        "critical_low": None,
        "critical_high": 200.0,
        "note": "Pancreatic and biliary cancer marker"
    },
    "CA 15-3": {
        "aliases": ["CA15-3", "Cancer Antigen 15-3", "Breast Cancer Marker"],
        "category": "Tumour Markers",
        "unit": "U/mL",
        "male":         (0.0, 30.0),
        "female":       (0.0, 30.0),
        "child":        (0.0, 30.0),
        "elderly":      (0.0, 30.0),
        "critical_low": None,
        "critical_high": 100.0,
        "note": "Breast cancer monitoring marker"
    },
    "hCG": {
        "aliases": ["Human Chorionic Gonadotropin", "Beta hCG", "Beta HCG",
                    "B-hCG", "hCG Level", "Pregnancy Hormone"],
        "category": "Tumour Markers",
        "unit": "IU/L",
        "male":         (0.0, 1.4),
        "female":       (0.0, 7.0),
        "child":        (0.0, 1.4),
        "elderly":      (0.0, 7.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in pregnancy and germ cell tumours"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  INFLAMMATORY / AUTOIMMUNE MARKERS
    # ──────────────────────────────────────────────────────────────────────────

    "CRP": {
        "aliases": ["C-Reactive Protein", "C Reactive Protein", "CRP Level",
                    "hs-CRP", "High Sensitivity CRP", "hsCRP"],
        "category": "Inflammatory Markers",
        "unit": "mg/L",
        "male":         (0.0, 5.0),
        "female":       (0.0, 5.0),
        "child":        (0.0, 5.0),
        "elderly":      (0.0, 5.0),
        "critical_low": None,
        "critical_high": 100.0,
        "note": "Acute phase reactant; elevated in infection, inflammation, MI"
    },
    "ESR": {
        "aliases": ["Erythrocyte Sedimentation Rate", "Sedimentation Rate",
                    "Sed Rate", "Westergren ESR"],
        "category": "Inflammatory Markers",
        "unit": "mm/hr",
        "male":         (0.0, 15.0),
        "female":       (0.0, 20.0),
        "child":        (0.0, 10.0),
        "elderly":      (0.0, 30.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Non-specific inflammation marker; elevated in infection, autoimmune"
    },
    "Rheumatoid Factor": {
        "aliases": ["RF", "RA Factor", "Rheumatoid Factor Level", "RF Test"],
        "category": "Autoimmune Panel",
        "unit": "IU/mL",
        "male":         (0.0, 20.0),
        "female":       (0.0, 20.0),
        "child":        (0.0, 20.0),
        "elderly":      (0.0, 20.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in RA; also in other autoimmune diseases"
    },
    "ANA": {
        "aliases": ["Antinuclear Antibody", "Anti Nuclear Antibody",
                    "ANA Titre", "ANA Test"],
        "category": "Autoimmune Panel",
        "unit": "titre",
        "male":         (0.0, 0.0),
        "female":       (0.0, 0.0),
        "child":        (0.0, 0.0),
        "elderly":      (0.0, 0.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Positive (titre ≥ 1:80) in SLE and other autoimmune diseases"
    },
    "Anti-CCP": {
        "aliases": ["Anti Cyclic Citrullinated Peptide", "CCP Antibody",
                    "Anti-CCP Antibody"],
        "category": "Autoimmune Panel",
        "unit": "U/mL",
        "male":         (0.0, 20.0),
        "female":       (0.0, 20.0),
        "child":        (0.0, 20.0),
        "elderly":      (0.0, 20.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Highly specific for rheumatoid arthritis"
    },
    "Procalcitonin": {
        "aliases": ["PCT", "Procalcitonin Level"],
        "category": "Inflammatory Markers",
        "unit": "ng/mL",
        "male":         (0.0, 0.05),
        "female":       (0.0, 0.05),
        "child":        (0.0, 0.05),
        "elderly":      (0.0, 0.05),
        "critical_low": None,
        "critical_high": 10.0,
        "note": "Sepsis marker; > 0.5 suggests bacterial infection; > 2.0 = sepsis"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  BLOOD GAS / ACID-BASE
    # ──────────────────────────────────────────────────────────────────────────

    "Blood pH": {
        "aliases": ["Arterial pH", "pH", "Blood pH Level"],
        "category": "Blood Gas Analysis",
        "unit": "",
        "male":         (7.35, 7.45),
        "female":       (7.35, 7.45),
        "child":        (7.35, 7.45),
        "elderly":      (7.35, 7.45),
        "critical_low": 7.2,
        "critical_high": 7.6,
        "note": "< 7.35 = acidosis; > 7.45 = alkalosis"
    },
    "pO2": {
        "aliases": ["Partial Pressure of Oxygen", "PaO2", "Arterial pO2",
                    "Oxygen Partial Pressure"],
        "category": "Blood Gas Analysis",
        "unit": "mm Hg",
        "male":         (80.0, 100.0),
        "female":       (80.0, 100.0),
        "child":        (80.0, 100.0),
        "elderly":      (70.0, 100.0),
        "critical_low": 55.0,
        "critical_high": None,
        "note": "< 60 = respiratory failure"
    },
    "pCO2": {
        "aliases": ["Partial Pressure of CO2", "PaCO2", "Arterial pCO2",
                    "Carbon Dioxide Partial Pressure"],
        "category": "Blood Gas Analysis",
        "unit": "mm Hg",
        "male":         (35.0, 45.0),
        "female":       (35.0, 45.0),
        "child":        (35.0, 45.0),
        "elderly":      (35.0, 45.0),
        "critical_low": 20.0,
        "critical_high": 70.0,
        "note": "Elevated in respiratory acidosis"
    },
    "Oxygen Saturation": {
        "aliases": ["SpO2", "O2 Saturation", "Pulse Oximetry", "SaO2",
                    "Oxygen Sat"],
        "category": "Blood Gas Analysis",
        "unit": "%",
        "male":         (95.0, 100.0),
        "female":       (95.0, 100.0),
        "child":        (95.0, 100.0),
        "elderly":      (94.0, 100.0),
        "critical_low": 88.0,
        "critical_high": None,
        "note": "< 90 = significant hypoxaemia"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  MISCELLANEOUS / SPECIAL TESTS
    # ──────────────────────────────────────────────────────────────────────────

    "ACE": {
        "aliases": ["Angiotensin Converting Enzyme", "Angiotensin-Converting Enzyme",
                    "ACE Level"],
        "category": "Miscellaneous",
        "unit": "U/L",
        "male":         (8.0, 53.0),
        "female":       (8.0, 53.0),
        "child":        (10.0, 55.0),
        "elderly":      (8.0, 53.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in sarcoidosis, lung disease"
    },
    "Lead": {
        "aliases": ["Blood Lead", "Lead Level", "Serum Lead", "Pb"],
        "category": "Miscellaneous",
        "unit": "µg/dL",
        "male":         (0.0, 10.0),
        "female":       (0.0, 10.0),
        "child":        (0.0, 5.0),
        "elderly":      (0.0, 10.0),
        "critical_low": None,
        "critical_high": 45.0,
        "note": "Any detectable level in children is concerning"
    },
    "Ammonia": {
        "aliases": ["Serum Ammonia", "Blood Ammonia", "NH3"],
        "category": "Miscellaneous",
        "unit": "µg/dL",
        "male":         (10.0, 80.0),
        "female":       (10.0, 80.0),
        "child":        (40.0, 80.0),
        "elderly":      (10.0, 80.0),
        "critical_low": None,
        "critical_high": 100.0,
        "note": "Elevated in hepatic encephalopathy and liver failure"
    },
    "Alpha-1 Antitrypsin": {
        "aliases": ["A1AT", "Alpha 1 Antitrypsin", "AAT"],
        "category": "Miscellaneous",
        "unit": "mg/dL",
        "male":         (85.0, 213.0),
        "female":       (85.0, 213.0),
        "child":        (85.0, 213.0),
        "elderly":      (85.0, 213.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Low in hereditary emphysema and liver disease"
    },

    # ──────────────────────────────────────────────────────────────────────────
    #  URINE ROUTINE (quantitative parameters)
    # ──────────────────────────────────────────────────────────────────────────

    "Urine Specific Gravity": {
        "aliases": ["Specific Gravity", "USG", "SG", "Urine SG"],
        "category": "Urine Analysis",
        "unit": "",
        "male":         (1.005, 1.030),
        "female":       (1.005, 1.030),
        "child":        (1.005, 1.030),
        "elderly":      (1.005, 1.030),
        "critical_low": None,
        "critical_high": None,
        "note": "Low = dilute urine; high = concentrated"
    },
    "Urine pH": {
        "aliases": ["Urinary pH", "pH Urine"],
        "category": "Urine Analysis",
        "unit": "",
        "male":         (4.5, 8.0),
        "female":       (4.5, 8.0),
        "child":        (4.5, 8.0),
        "elderly":      (4.5, 8.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
    "Urine Protein": {
        "aliases": ["Proteinuria", "Urine Albumin", "Microalbuminuria",
                    "Protein Urine", "Albuminuria"],
        "category": "Urine Analysis",
        "unit": "mg/dL",
        "male":         (0.0, 20.0),
        "female":       (0.0, 20.0),
        "child":        (0.0, 20.0),
        "elderly":      (0.0, 20.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in kidney disease, UTI, diabetes"
    },
    "Urine Glucose": {
        "aliases": ["Glucosuria", "Glucose Urine", "Urine Sugar"],
        "category": "Urine Analysis",
        "unit": "mg/dL",
        "male":         (0.0, 15.0),
        "female":       (0.0, 15.0),
        "child":        (0.0, 15.0),
        "elderly":      (0.0, 15.0),
        "critical_low": None,
        "critical_high": None,
        "note": "Elevated in diabetes, pregnancy"
    },
    "Urine Creatinine": {
        "aliases": ["Urinary Creatinine", "24h Urine Creatinine"],
        "category": "Urine Analysis",
        "unit": "mg/dL",
        "male":         (40.0, 300.0),
        "female":       (40.0, 300.0),
        "child":        (40.0, 300.0),
        "elderly":      (40.0, 300.0),
        "critical_low": None,
        "critical_high": None,
        "note": None
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
#  LOOKUP ENGINE
#  Maps every alias → standard test name (case-insensitive)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_lookup() -> dict:
    lookup = {}
    for std_name, info in REFERENCE_DB.items():
        # Standard name itself
        lookup[std_name.lower().strip()] = std_name
        # All aliases
        for alias in info.get("aliases", []):
            lookup[alias.lower().strip()] = std_name
    return lookup

_LOOKUP: dict = _build_lookup()


def _clean(s: str) -> str:
    """Normalise a test name for matching: lowercase, strip punctuation/prefixes."""
    s = s.lower().strip()
    # Remove common Indian lab prefixes: "s.", "serum", "blood", "urine", "plasma"
    s = re.sub(r'^(s\.|serum|blood|plasma|urine|urinary|total|absolute)\s+', '', s)
    # Remove bracketed suffixes like "(alt)", "(ultra sensitive)", "(lft)"
    s = re.sub(r'\s*\([^)]*\)', '', s)
    # Normalise spaces and hyphens
    s = re.sub(r'[\s\-_/]+', ' ', s).strip()
    return s


def find_test(name: str) -> str | None:
    """
    Given any test name string (from a lab report), return the
    standard name from REFERENCE_DB, or None if not found.

    Matching priority (highest → lowest):
      1. Exact match after cleaning
      2. Cleaned name is a known alias key exactly
      3. Best scored partial match (longer alias wins, short aliases ignored)
    """
    if not name:
        return None

    raw_key     = name.lower().strip()
    cleaned_key = _clean(name)

    # Priority 1 — exact raw match
    if raw_key in _LOOKUP:
        return _LOOKUP[raw_key]

    # Priority 2 — exact cleaned match
    if cleaned_key in _LOOKUP:
        return _LOOKUP[cleaned_key]

    # Also try cleaned version of each lookup key
    for alias_key, std_name in _LOOKUP.items():
        if _clean(alias_key) == cleaned_key:
            return std_name

    # Priority 3 — scored partial match
    # Rules to prevent false positives like "pt" matching "sgpt (alt)":
    #   - Alias must be at least 4 characters long to participate
    #   - Prefer the LONGEST matching alias (most specific wins)
    #   - The match must be a whole-word boundary match
    best_std    = None
    best_len    = 0

    for alias_key, std_name in _LOOKUP.items():
        if len(alias_key) < 4:          # skip very short aliases — too ambiguous
            continue

        ck = _clean(alias_key)
        if len(ck) < 3:
            continue

        # Check if cleaned alias is contained in cleaned key (or vice versa)
        # Use word-boundary style: must match whole word segments
        match = False
        if ck == cleaned_key:
            match = True
        elif len(ck) >= 4 and (
            re.search(r'\b' + re.escape(ck) + r'\b', cleaned_key) or
            re.search(r'\b' + re.escape(cleaned_key) + r'\b', ck)
        ):
            match = True

        if match and len(ck) > best_len:
            best_len = len(ck)
            best_std = std_name

    return best_std


def get_reference(test_name: str, gender: str = "male", age: int = 30) -> dict | None:
    """
    Return the reference info for a test.

    Args:
        test_name : name as it appears in the report (will be looked up)
        gender    : 'male' or 'female' (default 'male')
        age       : patient age in years (default 30)

    Returns dict with keys:
        standard_name, category, unit, ref_min, ref_max,
        critical_low, critical_high, note
    Or None if test not found.
    """
    std = find_test(test_name)
    if not std or std not in REFERENCE_DB:
        return None

    info = REFERENCE_DB[std]
    g    = gender.lower() if gender else "male"

    # Select age group
    if age < 18:
        rng = info.get("child") or info.get("male")
    elif age >= 60:
        rng = info.get("elderly") or info.get("male")
    elif g == "female":
        rng = info.get("female") or info.get("male")
    else:
        rng = info.get("male")

    if not rng or len(rng) < 2:
        return None

    return {
        "standard_name":  std,
        "category":       info.get("category", ""),
        "unit":           info.get("unit", ""),
        "ref_min":        rng[0],
        "ref_max":        rng[1],
        "critical_low":   info.get("critical_low"),
        "critical_high":  info.get("critical_high"),
        "note":           info.get("note"),
    }


def check_status(test_name: str, value: float,
                 gender: str = "male", age: int = 30) -> str:
    """
    Given a test name and numeric value, return status string:
    'normal' | 'high' | 'low' | 'borderline' | 'unknown'

    Uses the reference database; falls back to 'unknown' if test not found.
    """
    ref = get_reference(test_name, gender, age)
    if not ref:
        return "unknown"

    lo = ref["ref_min"]
    hi = ref["ref_max"]
    clo = ref["critical_low"]
    chi = ref["critical_high"]

    # Check critical first
    if clo is not None and value <= clo:
        return "low"
    if chi is not None and value >= chi:
        return "high"

    # Borderline = within 5% of either limit
    margin_lo = lo + (hi - lo) * 0.05
    margin_hi = hi - (hi - lo) * 0.05

    if value < lo:
        return "low"
    elif value > hi:
        return "high"
    elif value <= margin_lo or value >= margin_hi:
        return "borderline"
    else:
        return "normal"


def get_all_categories() -> list:
    """Return sorted list of all test categories."""
    return sorted(set(v["category"] for v in REFERENCE_DB.values()))


def get_tests_in_category(category: str) -> list:
    """Return list of standard test names for a given category."""
    return [k for k, v in REFERENCE_DB.items() if v["category"] == category]


def total_tests() -> int:
    """Total number of tests in database."""
    return len(REFERENCE_DB)


def total_aliases() -> int:
    """Total number of name variants in database."""
    return len(_LOOKUP)