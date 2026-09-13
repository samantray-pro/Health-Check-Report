import re
from datetime import datetime

# Standard clinical dictionary for normalizing medical lab tests and providing default cutoffs
BIOMARKER_DICTIONARY = {
    # Glycemic / Diabetic Panel
    "hba1c": {"name": "HbA1c (Glycosylated Hemoglobin)", "category": "Diabetes & Glycemic", "unit": "%", "ref": "< 5.7", "min": 4.0, "max": 5.6},
    "glycosylated hemoglobin": {"name": "HbA1c (Glycosylated Hemoglobin)", "category": "Diabetes & Glycemic", "unit": "%", "ref": "< 5.7", "min": 4.0, "max": 5.6},
    "fasting blood sugar": {"name": "Glucose - Fasting", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "70 - 99", "min": 70, "max": 99},
    "glucose - fasting": {"name": "Glucose - Fasting", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "70 - 99", "min": 70, "max": 99},
    "glucose fasting": {"name": "Glucose - Fasting", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "70 - 99", "min": 70, "max": 99},
    "glucose postprandial": {"name": "Glucose Postprandial (PPBS)", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "70 - 140", "min": 70, "max": 140},
    "ppbs": {"name": "Glucose Postprandial (PPBS)", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "70 - 140", "min": 70, "max": 140},
    "estimated average glucose": {"name": "Estimated Average Glucose (eAG)", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "", "min": None, "max": None},
    "average blood glucose": {"name": "Estimated Average Glucose (eAG)", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "", "min": None, "max": None},
    "mean blood glucose": {"name": "Estimated Average Glucose (eAG)", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "", "min": None, "max": None},
    "eag": {"name": "Estimated Average Glucose (eAG)", "category": "Diabetes & Glycemic", "unit": "mg/dL", "ref": "", "min": None, "max": None},

    # Complete Blood Count (CBC)
    "hemoglobin": {"name": "Hemoglobin", "category": "Complete Blood Count (CBC)", "unit": "g/dL", "ref": "12.0 - 15.0", "min": 12.0, "max": 15.0},
    "haemoglobin": {"name": "Hemoglobin", "category": "Complete Blood Count (CBC)", "unit": "g/dL", "ref": "12.0 - 15.0", "min": 12.0, "max": 15.0},
    "rbc": {"name": "RBC Count", "category": "Complete Blood Count (CBC)", "unit": "10^6", "ref": "4.5 - 5.5", "min": 4.5, "max": 5.5},
    "rbc count": {"name": "RBC Count", "category": "Complete Blood Count (CBC)", "unit": "10^6", "ref": "4.5 - 5.5", "min": 4.5, "max": 5.5},
    "pcv": {"name": "PCV (Packed Cell Volume)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "40 - 54", "min": 40, "max": 54},
    "packed cell volume": {"name": "PCV (Packed Cell Volume)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "40 - 54", "min": 40, "max": 54},
    "packed cells volume": {"name": "PCV (Packed Cell Volume)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "40 - 54", "min": 40, "max": 54},
    "hct": {"name": "HCT (Hematocrit)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "36 - 46", "min": 36, "max": 46},
    "mcv": {"name": "MCV", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "83 - 101", "min": 83, "max": 101},
    "mch": {"name": "MCH", "category": "Complete Blood Count (CBC)", "unit": "pg", "ref": "27 - 32", "min": 27, "max": 32},
    "mchc": {"name": "MCHC", "category": "Complete Blood Count (CBC)", "unit": "g/dL", "ref": "31.5 - 34.5", "min": 31.5, "max": 34.5},
    "rdw-cv": {"name": "RDW-CV", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "11.5 - 14.0", "min": 11.5, "max": 14.0},
    "rdw-sd": {"name": "RDW-SD", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "39 - 46", "min": 39, "max": 46},
    "total leucocyte count": {"name": "Total WBC Count", "category": "Complete Blood Count (CBC)", "unit": "cells/cumm", "ref": "4000 - 10000", "min": 4000, "max": 10000},
    "total wbc count": {"name": "Total WBC Count", "category": "Complete Blood Count (CBC)", "unit": "cells/cumm", "ref": "4000 - 10000", "min": 4000, "max": 10000},
    "neutrophils": {"name": "Neutrophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "40 - 80", "min": 40, "max": 80},
    "neutrophiles": {"name": "Neutrophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "40 - 80", "min": 40, "max": 80},
    "lymphocytes": {"name": "Lymphocytes", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "20 - 40", "min": 20, "max": 40},
    "monocytes": {"name": "Monocytes", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "2 - 10", "min": 2, "max": 10},
    "eosinophils": {"name": "Eosinophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "1 - 6", "min": 1, "max": 6},
    "basophils": {"name": "Basophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "0 - 2", "min": 0, "max": 2},
    "absolute neutrophil count": {"name": "Absolute Neutrophil Count", "category": "Complete Blood Count (CBC)", "unit": "/cumm", "ref": "2000 - 7000", "min": 2000, "max": 7000},
    "absolute lymphocyte count": {"name": "Absolute Lymphocyte Count", "category": "Complete Blood Count (CBC)", "unit": "/cumm", "ref": "710 - 4530", "min": 710, "max": 4530},
    "absolute monocyte count": {"name": "Absolute Monocyte Count", "category": "Complete Blood Count (CBC)", "unit": "/cumm", "ref": "200 - 1000", "min": 200, "max": 1000},
    "absolute eosinophil count": {"name": "Absolute Eosinophil Count", "category": "Complete Blood Count (CBC)", "unit": "/cumm", "ref": "20 - 500", "min": 20, "max": 500},
    "absolute basophil count": {"name": "Absolute Basophil Count", "category": "Complete Blood Count (CBC)", "unit": "/cumm", "ref": "20 - 100", "min": 20, "max": 100},
    "platelet count": {"name": "Platelet Count", "category": "Complete Blood Count (CBC)", "unit": "cells/cumm", "ref": "150000 - 410000", "min": 150000, "max": 410000},
    "platelets count": {"name": "Platelet Count", "category": "Complete Blood Count (CBC)", "unit": "cells/cumm", "ref": "150000 - 410000", "min": 150000, "max": 410000},
    "mpv": {"name": "MPV", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "6.5 - 12.0", "min": 6.5, "max": 12.0},
    "pdw": {"name": "PDW", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "9.0 - 17.0", "min": 9.0, "max": 17.0},
    "pct": {"name": "PCT (Plateletcrit)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "0.1 - 0.6", "min": 0.1, "max": 0.6},
    "pct (plateletcrit)": {"name": "PCT (Plateletcrit)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "0.1 - 0.6", "min": 0.1, "max": 0.6},
    "pdw (plt. distr width)": {"name": "PDW (Platelet Distribution Width)", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "11 - 22", "min": 11, "max": 22},

    # Blood Smear & Morphology
    "rbc morphology": {"name": "RBC Morphology", "category": "Blood Smear & Morphology", "unit": "", "ref": "Normocytic normochromic", "min": None, "max": None},
    "wbc morphology": {"name": "WBC Morphology", "category": "Blood Smear & Morphology", "unit": "", "ref": "Normal", "min": None, "max": None},
    "platelet morphology": {"name": "Platelet Morphology", "category": "Blood Smear & Morphology", "unit": "", "ref": "Adequate", "min": None, "max": None},

    # Coagulation & Hemostasis
    "bleeding time": {"name": "Bleeding Time", "category": "Coagulation & Hemostasis", "unit": "min", "ref": "1 - 5", "min": 1.0, "max": 5.0},
    "clotting time": {"name": "Clotting Time", "category": "Coagulation & Hemostasis", "unit": "min", "ref": "4 - 10", "min": 4.0, "max": 10.0},
    "prothrombin time test": {"name": "Prothrombin Time (PT) Test", "category": "Coagulation & Hemostasis", "unit": "Seconds", "ref": "11.0 - 15.0", "min": 11.0, "max": 15.0},
    "prothrombin time control": {"name": "Prothrombin Time Control", "category": "Coagulation & Hemostasis", "unit": "Seconds", "ref": "0 - 14.8", "min": 0, "max": 14.8},
    "international normalised ratio": {"name": "International Normalized Ratio (INR)", "category": "Coagulation & Hemostasis", "unit": "Ratio", "ref": "0.8 - 1.2", "min": 0.8, "max": 1.2},
    "international normalized ratio": {"name": "International Normalized Ratio (INR)", "category": "Coagulation & Hemostasis", "unit": "Ratio", "ref": "0.8 - 1.2", "min": 0.8, "max": 1.2},
    "inr": {"name": "International Normalized Ratio (INR)", "category": "Coagulation & Hemostasis", "unit": "Ratio", "ref": "0.8 - 1.2", "min": 0.8, "max": 1.2},
    "pt, isi": {"name": "PT - ISI", "category": "Coagulation & Hemostasis", "unit": "", "ref": "", "min": None, "max": None},
    "fibrinogen": {"name": "Fibrinogen", "category": "Coagulation & Hemostasis", "unit": "mg/dL", "ref": "150 - 400", "min": 150, "max": 400},
    "specimen": {"name": "Specimen Type", "category": "Coagulation & Hemostasis", "unit": "", "ref": "", "min": None, "max": None},

    # Inflammatory & Cardiac Profile
    "erythrocyte sedimentation": {"name": "Erythrocyte Sedimentation Rate (ESR)", "category": "Cardiac & Inflammation", "unit": "mm/hr", "ref": "0 - 19", "min": 0, "max": 19},
    "erythrocyte sedimentation rate": {"name": "Erythrocyte Sedimentation Rate (ESR)", "category": "Cardiac & Inflammation", "unit": "mm/hr", "ref": "0 - 19", "min": 0, "max": 19},
    "c-reactive protein": {"name": "C-Reactive Protein (Quantitative)", "category": "Cardiac & Inflammation", "unit": "mg/L", "ref": "0 - 3.3", "min": 0, "max": 3.3},
    "crp hs ( high sensitive )": {"name": "High Sensitivity CRP (hs-CRP)", "category": "Cardiac & Inflammation", "unit": "mg/L", "ref": "0 - 5.0", "min": 0, "max": 5.0},
    "high sensitivity crp": {"name": "High Sensitivity CRP (hs-CRP)", "category": "Cardiac & Inflammation", "unit": "mg/L", "ref": "0 - 3.0", "min": 0, "max": 3.0},
    "lipoprotein (a)": {"name": "Lipoprotein (a)", "category": "Cardiac & Inflammation", "unit": "mg/dL", "ref": "0 - 29.99", "min": 0, "max": 29.99},
    "homocysteine": {"name": "Homocysteine", "category": "Cardiac & Inflammation", "unit": "umol/L", "ref": "<= 14.9", "min": 0, "max": 14.9},
    "apolipoprotein - a1": {"name": "Apolipoprotein - A1", "category": "Cardiac & Inflammation", "unit": "mg/dL", "ref": "76 - 214", "min": 76, "max": 214},
    "apolipoprotein - b": {"name": "Apolipoprotein - B", "category": "Cardiac & Inflammation", "unit": "mg/dL", "ref": "46 - 142", "min": 46, "max": 142},
    "apolipoprotein b/a1 ratio": {"name": "Apolipoprotein B/A1 Ratio", "category": "Cardiac & Inflammation", "unit": "Ratio", "ref": "0.35 - 0.98", "min": 0.35, "max": 0.98},

    # Iron Studies
    "iron serum": {"name": "Iron Serum", "category": "Iron Studies", "unit": "µg/dL", "ref": "50 - 170", "min": 50, "max": 170},
    "total iron binding capacity": {"name": "Total Iron Binding Capacity (TIBC)", "category": "Iron Studies", "unit": "µg/dL", "ref": "250 - 460", "min": 250, "max": 460},
    "unsaturated iron binding capacity": {"name": "Unsaturated Iron Binding Capacity (UIBC)", "category": "Iron Studies", "unit": "µg/dL", "ref": "120 - 470", "min": 120, "max": 470},
    "transferrin saturation": {"name": "Transferrin Saturation", "category": "Iron Studies", "unit": "%", "ref": "16 - 50", "min": 16, "max": 50},
    "transferrin": {"name": "Transferrin", "category": "Iron Studies", "unit": "mg/dL", "ref": "200 - 360", "min": 200, "max": 360},
    "ferritin": {"name": "Ferritin", "category": "Iron Studies", "unit": "ng/mL", "ref": "10 - 291", "min": 10, "max": 291},

    # Kidney Health (KFT / RFT)
    "creatinine": {"name": "Serum Creatinine", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "0.55 - 1.02", "min": 0.55, "max": 1.02},
    "sr. creatinine": {"name": "Serum Creatinine", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "0.9 - 1.3", "min": 0.9, "max": 1.3},
    "blood urea nitrogen": {"name": "Blood Urea Nitrogen (BUN)", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "9.0 - 23.0", "min": 9.0, "max": 23.0},
    "urea": {"name": "Blood Urea", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "19.26 - 49.22", "min": 19.26, "max": 49.22},
    "uric acid": {"name": "Uric Acid", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "2.7 - 6.1", "min": 2.7, "max": 6.1},
    "sodium": {"name": "Serum Sodium", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "135 - 145", "min": 135, "max": 145},
    "potassium": {"name": "Serum Potassium", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "3.5 - 5.1", "min": 3.5, "max": 5.1},
    "chloride": {"name": "Serum Chloride", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "98 - 107", "min": 98, "max": 107},
    "urine sodium": {"name": "Urine Sodium", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "40 - 220", "min": 40, "max": 220},
    "urine potassium": {"name": "Urine Potassium", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "25 - 125", "min": 25, "max": 125},
    "urine chloride": {"name": "Urine Chloride", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "100 - 250", "min": 100, "max": 250},
    "bun/creatinine ratio": {"name": "BUN/Creatinine Ratio", "category": "Kidney Function (KFT)", "unit": "Ratio", "ref": "12 - 20", "min": 12, "max": 20},
    "glomerular filtration rate": {"name": "Glomerular Filtration Rate (eGFR)", "category": "Kidney Function (KFT)", "unit": "mL/min/1.73m2", "ref": ">= 90", "min": 90, "max": 200},
    "e gfr": {"name": "Glomerular Filtration Rate (eGFR)", "category": "Kidney Function (KFT)", "unit": "mL/min/1.73m2", "ref": ">= 90", "min": 90, "max": 200},
    "microalbumin-urine": {"name": "Microalbumin - Urine", "category": "Kidney Function (KFT)", "unit": "mg/L", "ref": "< 30", "min": 0, "max": 30.0},
    "albumin/creatinine ratio ( spot urine )": {"name": "Albumin/Creatinine Ratio (ACR)", "category": "Kidney Function (KFT)", "unit": "mg/gm", "ref": "0 - 30", "min": 0, "max": 30.0},
    "albumin/creatinine ratio": {"name": "Albumin/Creatinine Ratio (ACR)", "category": "Kidney Function (KFT)", "unit": "mg/gm", "ref": "0 - 30", "min": 0, "max": 30.0},
    "urine creatinine": {"name": "Urine Creatinine", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "40 - 278", "min": 40, "max": 278},
    "urine albumin": {"name": "Urine Albumin", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "< 2.0", "min": 0, "max": 2.0},

    # Lipid Profile
    "cholesterol - total": {"name": "Total Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 200", "min": 100, "max": 199.9},
    "total cholesterol": {"name": "Total Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 200", "min": 100, "max": 199.9},
    "triglycerides": {"name": "Triglycerides", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 150", "min": 50, "max": 149.9},
    "triglyceride": {"name": "Triglycerides", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 150", "min": 50, "max": 149.9},
    "cholesterol - hdl": {"name": "HDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": ">= 50", "min": 50, "max": 100},
    "hdl cholesterol": {"name": "HDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": ">= 50", "min": 50, "max": 100},
    "cholesterol - ldl": {"name": "LDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 100", "min": 50, "max": 99.9},
    "ldl- cholesterol": {"name": "LDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 100", "min": 50, "max": 99.9},
    "non hdl cholesterol": {"name": "Non-HDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 130", "min": 50, "max": 129.9},
    "cholesterol- vldl": {"name": "VLDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 30", "min": 5, "max": 30},
    "vldl cholesterol": {"name": "VLDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 30", "min": 5, "max": 30},
    "cholesterol : hdl cholesterol": {"name": "Cholesterol / HDL Ratio", "category": "Lipid Profile", "unit": "Ratio", "ref": "3.0 - 4.5", "min": 3.0, "max": 4.5},
    "cholesterol / hdl ratio": {"name": "Cholesterol / HDL Ratio", "category": "Lipid Profile", "unit": "Ratio", "ref": "< 4.5", "min": 0, "max": 4.5},
    "ldl : hdl cholesterol": {"name": "LDL / HDL Ratio", "category": "Lipid Profile", "unit": "Ratio", "ref": "2.0 - 2.5", "min": 2.0, "max": 2.5},
    "ldl/hdl ratio": {"name": "LDL / HDL Ratio", "category": "Lipid Profile", "unit": "Ratio", "ref": "< 3.0", "min": 0, "max": 3.0},

    # Liver Function (LFT)
    "bilirubin - total": {"name": "Total Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.3 - 1.2", "min": 0.3, "max": 1.2},
    "total bilirubin": {"name": "Total Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.3 - 1.2", "min": 0.3, "max": 1.2},
    "bilirubin-direct": {"name": "Direct Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.0 - 0.3", "min": 0.0, "max": 0.3},
    "direct bilirubin": {"name": "Direct Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.0 - 0.4", "min": 0.0, "max": 0.4},
    "indirect bilirubin": {"name": "Indirect Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "< 1.1", "min": 0.0, "max": 1.1},
    "protein, total": {"name": "Total Protein", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "6.4 - 8.3", "min": 6.4, "max": 8.3},
    "total protein": {"name": "Total Protein", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "6.4 - 8.3", "min": 6.4, "max": 8.3},
    "albumin": {"name": "Albumin", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "3.5 - 5.2", "min": 3.5, "max": 5.2},
    "serum albumin": {"name": "Albumin", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "3.5 - 5.2", "min": 3.5, "max": 5.2},
    "globulin": {"name": "Globulin", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "1.5 - 3.0", "min": 1.5, "max": 3.0},
    "a/g ratio": {"name": "A/G Ratio", "category": "Liver Function (LFT)", "unit": "Ratio", "ref": "1.2 - 2.2", "min": 1.2, "max": 2.2},
    "sgot": {"name": "SGOT (AST)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 35", "min": 0, "max": 35},
    "aspartate transaminase": {"name": "SGOT (AST)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 35", "min": 0, "max": 35},
    "sgpt": {"name": "SGPT (ALT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 45", "min": 0, "max": 45},
    "alanine transaminase": {"name": "SGPT (ALT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 45", "min": 0, "max": 45},
    "sgot/sgpt": {"name": "SGOT / SGPT Ratio", "category": "Liver Function (LFT)", "unit": "Ratio", "ref": "0.7 - 1.4", "min": 0.7, "max": 1.4},
    "alkaline phosphatase": {"name": "Alkaline Phosphatase (ALP)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "40 - 129", "min": 40, "max": 129},
    "gamma glutamyltransferase": {"name": "Gamma-Glutamyl Transferase (GGT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "10 - 45", "min": 10, "max": 45},
    "gamma gt report": {"name": "Gamma-Glutamyl Transferase (GGT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "10 - 45", "min": 10, "max": 45},
    "gamma": {"name": "Gamma-Glutamyl Transferase (GGT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "10 - 45", "min": 10, "max": 45},

    # Pancreas, Bone & Minerals
    "lipase": {"name": "Lipase", "category": "Hormones & Immunology", "unit": "U/L", "ref": "0 - 64", "min": 0, "max": 64},
    "amylase": {"name": "Amylase", "category": "Hormones & Immunology", "unit": "U/L", "ref": "25 - 86", "min": 25, "max": 86},
    "calcium": {"name": "Calcium", "category": "Vitamins & Minerals", "unit": "mg/dL", "ref": "8.8 - 10.2", "min": 8.8, "max": 10.2},
    "phosphorus": {"name": "Phosphorus", "category": "Vitamins & Minerals", "unit": "mg/dL", "ref": "2.4 - 5.1", "min": 2.4, "max": 5.1},
    "vitamin d": {"name": "Vitamin D (25-OH)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": "30 - 100", "min": 30, "max": 100},
    "vitamin d3": {"name": "Vitamin D (25-OH)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": "30 - 100", "min": 30, "max": 100},
    "vitamin b12": {"name": "Vitamin B12", "category": "Vitamins & Minerals", "unit": "pg/mL", "ref": "211 - 911", "min": 211, "max": 911},
    "vitamin b9": {"name": "Vitamin B9 (Folic Acid)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": ">= 5.38", "min": 5.38, "max": 100},
    "folic acid": {"name": "Vitamin B9 (Folic Acid)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": ">= 5.38", "min": 5.38, "max": 100},

    # Thyroid Function
    "t3, total": {"name": "Total T3", "category": "Thyroid Profile", "unit": "ng/mL", "ref": "0.60 - 1.81", "min": 0.60, "max": 1.81},
    "t4, total": {"name": "Total T4", "category": "Thyroid Profile", "unit": "µg/dL", "ref": "4.5 - 12.6", "min": 4.5, "max": 12.6},
    "thyroid stimulating hormone": {"name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Profile", "unit": "uIU/mL", "ref": "0.3 - 4.5", "min": 0.3, "max": 4.5},
    "thyroid stimulating": {"name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Profile", "unit": "uIU/mL", "ref": "0.3 - 4.5", "min": 0.3, "max": 4.5},
    "tsh": {"name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Profile", "unit": "uIU/mL", "ref": "0.3 - 4.5", "min": 0.3, "max": 4.5},
    "free t4": {"name": "Free T4", "category": "Thyroid Profile", "unit": "pg/mL", "ref": "9.0 - 17.5", "min": 9.0, "max": 17.5},
    "free t3": {"name": "Free T3", "category": "Thyroid Profile", "unit": "pg/mL", "ref": "2.00 - 4.20", "min": 2.00, "max": 4.20},

    # Prenatal / NIPT Screening
    "free beta hcg": {"name": "Free Beta hCG", "category": "Hormones & Immunology", "unit": "ng/mL", "ref": "", "min": None, "max": None},
    "fb-hcg": {"name": "Free Beta hCG", "category": "Hormones & Immunology", "unit": "ng/mL", "ref": "", "min": None, "max": None},

    # Immunology, Serology, Arthritis & Hormones
    "rheumatoid factor": {"name": "Rheumatoid Factor - Quantitative (RF)", "category": "Hormones & Immunology", "unit": "IU/mL", "ref": "0 - 14", "min": 0, "max": 14},
    "ra factor (qualitative)": {"name": "RA Factor (Qualitative)", "category": "Hormones & Immunology", "unit": "", "ref": "Negative", "min": None, "max": None},
    "anti hbs titer": {"name": "Anti HBs Titer", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": "0 - 10.0", "min": 0, "max": 10.0},
    "hcv card": {"name": "HCV Card (Antibody)", "category": "Hormones & Immunology", "unit": "", "ref": "Non Reactive", "min": None, "max": None},
    "psa (prostate specific antigen)-total": {"name": "PSA Total", "category": "Hormones & Immunology", "unit": "ng/mL", "ref": "0 - 4.0", "min": 0, "max": 4.0},
    "immunoglobulin e": {"name": "Immunoglobulin E (IgE) Total", "category": "Hormones & Immunology", "unit": "IU/mL", "ref": "0 - 158", "min": 0, "max": 158},
    "follicle stimulating": {"name": "Follicle Stimulating Hormone (FSH)", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": ">= 0.01", "min": 23.0, "max": 116.3},
    "follicle stimulating hormone": {"name": "Follicle Stimulating Hormone (FSH)", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": ">= 0.01", "min": 23.0, "max": 116.3},
    "luteinizing hormone": {"name": "Luteinizing Hormone (LH)", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": ">= 0.09", "min": 7.9, "max": 53.8},
    "prolactin": {"name": "Prolactin", "category": "Hormones & Immunology", "unit": "ng/mL", "ref": "1.8 - 29.2", "min": 1.8, "max": 20.3},

    # Urine Routine - Physical & Chemical
    "colour": {"name": "Urine Colour", "category": "Urine Routine Examination", "unit": "", "ref": "Pale Yellow", "min": None, "max": None},
    "appearance": {"name": "Urine Appearance", "category": "Urine Routine Examination", "unit": "", "ref": "Clear", "min": None, "max": None},
    "specific gravity": {"name": "Urine Specific Gravity", "category": "Urine Routine Examination", "unit": "", "ref": "1.005 - 1.030", "min": 1.005, "max": 1.030},
    "urine protein": {"name": "Urine Protein", "category": "Urine Routine Examination", "unit": "", "ref": "Absent", "min": None, "max": None},
    "urine glucose": {"name": "Urine Glucose", "category": "Urine Routine Examination", "unit": "", "ref": "Absent", "min": None, "max": None},
    "bile pigments": {"name": "Urine Bile Pigments", "category": "Urine Routine Examination", "unit": "", "ref": "Absent", "min": None, "max": None},
    "bile salt": {"name": "Urine Bile Salt", "category": "Urine Routine Examination", "unit": "", "ref": "Absent", "min": None, "max": None},
    "ketones, urine": {"name": "Urine Ketones", "category": "Urine Routine Examination", "unit": "", "ref": "Absent", "min": None, "max": None},
    "urobilinogen": {"name": "Urobilinogen", "category": "Urine Routine Examination", "unit": "", "ref": "Normal (<1 mg/dl)", "min": None, "max": None},
    "reaction (ph)": {"name": "Urine Reaction (pH)", "category": "Urine Routine Examination", "unit": "", "ref": "4.6 - 8.0", "min": 4.6, "max": 8.0},

    # Urine Routine - Microscopic
    "pus cells": {"name": "Urine Pus Cells", "category": "Urine Routine Examination", "unit": "/HPF", "ref": "1 - 2", "min": 0, "max": 2.0},
    "epithelial cells": {"name": "Urine Epithelial Cells", "category": "Urine Routine Examination", "unit": "/HPF", "ref": "1 - 2", "min": 0, "max": 2.0},
    "rbcs": {"name": "Urine RBCs", "category": "Urine Routine Examination", "unit": "/HPF", "ref": "Absent", "min": None, "max": None},
    "urine crystal": {"name": "Urine Crystals", "category": "Urine Routine Examination", "unit": "/HPF", "ref": "Absent", "min": None, "max": None},
    "casts": {"name": "Urine Casts", "category": "Urine Routine Examination", "unit": "/HPF", "ref": "Absent", "min": None, "max": None},
    "bacteria": {"name": "Urine Bacteria", "category": "Urine Routine Examination", "unit": "/HPF", "ref": "Absent", "min": None, "max": None},
}

# Aliases sorted longest-first for word-boundary matching, precomputed once since the
# dictionary above is static (was being re-sorted on every parsed biomarker).
SORTED_BIOMARKER_ALIASES = sorted(BIOMARKER_DICTIONARY.items(), key=lambda x: len(x[0]), reverse=True)

# Standard qualitative clinical result tokens
QUAL_TOKENS = [
    "Non Reactive", "Non-Reactive", "Reactive",
    "Negative", "Positive", "Weakly Positive",
    "Absent", "Present",
    "Pale Yellow", "Yellow", "Straw", "Amber", "Reddish",
    "Clear", "Hazy", "Turbid", "Slightly Hazy",
    "Normocytic normochromic", "Normocytic hypochromic", "Microcytic hypochromic",
    "increase in monocytes", "Adequate", "Reduced",
    "Acidic", "Alkaline", "Neutral", "Normal", "Plasma"
]

# Exact test-name matches that are always noise (legend labels, risk-summary rows,
# stray single words from garbled multi-column/infographic layouts) rather than biomarkers.
# Checked as a whole-string match against the candidate's cleaned name, so it only ever
# rejects a name that IS one of these words/phrases outright, never a name containing one.
BLACKLIST_EXACT_NAMES = {
    'normal', 'abnormal', 'high', 'low', 'average', 'control', 'diabetes',
    'impaired fasting', 'prediabetes', 'pre-diabetes', 'panic value', 'critical value',
    'action suggested', 'target goals of', 'target goal', 'goal of therapy',
    'therapeutic goals', 'therapeutic goal', 'excellent control', 'good control',
    'fair control', 'poor control', 'borderline', 'desirable', 'optimal',
    'concentration is', 'carrier proteins leaving', 'at risk', 'reference group',
    'negative', 'positive', 'reactive', 'range', 'even', 'upto', 'up to', 'elevated',
}

# Common English function words. A genuine clinical test name is never built out of these
# (they're all short compound nouns/abbreviations), so a candidate name containing one as a
# standalone word is almost always a fragment of narrative/comment text that slipped past the
# other filters. Only applied when the name has no dictionary match of its own to overrule it -
# see the self-check script for the assertion that this never collides with a real biomarker name.
STOPWORDS = {
    'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'and', 'or',
    'is', 'are', 'was', 'were', 'as', 'by', 'from', 'that', 'this', 'these', 'those',
    'during', 'after', 'before', 'between', 'among', 'around', 'about', 'if',
    'than', 'then', 'so', 'such', 'which', 'who', 'whom', 'because', 'due', 'per',
}

# A candidate name that, once normalized, IS one of these unit tokens rather than containing
# one alongside a real name - a leftover fragment from a garbled multi-column value row.
UNIT_ONLY_NORMALIZED_KEYS = {
    'mgdl', 'gdl', 'ngml', 'pgml', 'ul', 'mmoll', 'meql', 'mgl', 'ratio', 'fl',
    'hpf', 'lpf', 'cellscumm', 'miuml', 'uiuml', 'mmhr', 'umoll', 'mggm', 'ngdl',
}

# Qualitative tokens that only ever make sense for a serology/antibody-style result. Unlike
# "Acidic"/"Alkaline" (legitimate alternate reporting for a numeric pH test) or "Clear"/"Hazy",
# these can never be a genuine reading for a biomarker that has a numeric min/max range.
SEROLOGY_ONLY_TOKENS = {'reactive', 'non reactive', 'non-reactive', 'positive', 'weakly positive'}

def get_test_category(test_name: str) -> str:
    """Returns the standardized clinical organ/panel category for any biomarker."""
    if not test_name:
        return "General / Other"
    
    clean = test_name.strip()
    norm = re.sub(r'[^a-z0-9]', '', clean.lower())
    
    # 1. Check exact or alias dictionary matches
    for alias, meta in BIOMARKER_DICTIONARY.items():
        alias_norm = re.sub(r'[^a-z0-9]', '', alias)
        name_norm = re.sub(r'[^a-z0-9]', '', meta["name"].lower())
        if norm == alias_norm or norm == name_norm:
            return meta.get("category", "General / Other")
            
    # 2. Heuristic keyword matches
    lower = clean.lower()
    if any(k in lower for k in ["coagulation", "bleeding time", "clotting time", "prothrombin", "pt inr", "inr", "fibrinogen", "specimen", "isi"]):
        return "Coagulation & Hemostasis"
    if any(k in lower for k in ["rbc morphology", "wbc morphology", "platelet morphology", "blood smear", "morphology"]):
        return "Blood Smear & Morphology"
    if any(k in lower for k in [
        "urine colour", "urine appearance", "specific gravity", "urine protein", "urine glucose", 
        "bile pigment", "bile salt", "ketone", "urobilinogen", "reaction (ph)", "pus cell", 
        "epithelial cell", "urine rbc", "urine crystal", "casts", "bacteria", "urine routine"
    ]):
        return "Urine Routine Examination"
    if any(k in lower for k in ["glucose", "sugar", "hba1c", "ppbs", "fbs", "insulin", "eag"]):
        return "Diabetes & Glycemic"
    if any(k in lower for k in [
        "hemoglobin", "rbc", "wbc", "platelet", "mcv", "mch", "mchc", "rdw", 
        "neutrophil", "lymphocyte", "monocyte", "eosinophil", "basophil", 
        "leucocyte", "leukocyte", "hematocrit", "hct", "mpv", "pdw", "pct"
    ]):
        return "Complete Blood Count (CBC)"
    if any(k in lower for k in ["cholesterol", "triglyceride", "hdl", "ldl", "vldl", "lipid"]):
        return "Lipid Profile"
    if any(k in lower for k in [
        "bilirubin", "sgot", "sgpt", "alt", "ast", "alkaline phosphatase", "alp", 
        "ggt", "glutamyl", "protein, total", "albumin", "globulin", "a/g ratio", "transaminase"
    ]):
        return "Liver Function (LFT)"
    if any(k in lower for k in [
        "creatinine", "urea", "bun", "uric acid", "egfr", "glomerular", 
        "sodium", "potassium", "chloride", "kft", "rft", "microalbumin", "acr"
    ]):
        return "Kidney Function (KFT)"
    if any(k in lower for k in ["thyroid", "tsh", "t3", "t4"]):
        return "Thyroid Profile"
    if any(k in lower for k in ["vitamin", "calcium", "phosphorus", "mineral", "folic"]):
        return "Vitamins & Minerals"
    if any(k in lower for k in ["iron", "ferritin", "tibc", "uibc", "transferrin"]):
        return "Iron Studies"
    if any(k in lower for k in ["crp", "hs-crp", "homocysteine", "lipoprotein (a)", "apolipoprotein", "esr", "sedimentation"]):
        return "Cardiac & Inflammation"
    if any(k in lower for k in ["fsh", "lh", "prolactin", "rheumatoid", "ra factor", "ige", "hormone", "amylase", "lipase", "immunoglobulin", "psa", "hbs", "hcv"]):
        return "Hormones & Immunology"

    return "General / Other"

def get_test_panel(test_name: str, category: str = None) -> str:
    """Returns the standardized clinical test panel (e.g. CBC sub-panels, LFT, Lipid, Renal, etc.)."""
    if not test_name:
        return category or "General / Other"

    clean = test_name.strip()
    norm = re.sub(r'[^a-z0-9]', '', clean.lower())

    # Exact or keyword mapping to the 25 standard clinical panels
    if norm in ["bleedingtime"]:
        return "Bleeding Time"
    if norm in ["clottingtime"]:
        return "Clotting Time"
    if norm in ["hemoglobin", "haemoglobin", "rbc", "rbccount", "pcv", "packedcellvolume", "pcvpackedcellvolume", "packedcellsvolume", "mcv", "mch", "mchc", "rdwcv", "rdwsd", "rdw", "hct", "hematocrit"]:
        return "CBC (5 Parts) - RBC"
    if norm in ["totalwbccount", "totalleucocytecount", "wbccount", "tlc"]:
        return "CBC - WBC"
    if norm in ["neutrophils", "neutrophiles", "lymphocytes", "eosinophils", "monocytes", "basophils"]:
        return "CBC - Differential"
    if norm in ["absoluteneutrophilcount", "absolutelymphocytecount", "absoluteeosinophilcount", "absolutemonocytecount", "absolutebasophilcount", "anc", "alc", "aec", "amc"]:
        return "CBC - Absolute Counts"
    if norm in ["plateletcount", "plateletscount", "mpv", "pctplateletcrit", "pct", "pdw", "pdwplateletdistributionwidth", "plateletdistributionwidth"]:
        return "CBC - Platelet Parameters"
    if norm in ["rbcmorphology", "wbcmorphology", "plateletmorphology", "bloodsmear", "bloodsmearexamination", "peripheralsmear"]:
        return "CBC - Blood Smear"
    if norm in ["esr", "erythrocytesedimentationrateesr", "erythrocytesedimentationrate"]:
        return "Haematology"
    if norm in ["specimen", "specimetype", "specimentype", "prothrombintimepttest", "pttest", "prothrombintimecontrol", "ptcontrol", "internationalnormalizedratioinr", "inr", "ptisi", "ptinr"]:
        return "PT INR - Prothrombin Time"
    if norm in ["fibrinogen"]:
        return "Fibrinogen"
    if norm in ["bloodureanitrogenbun", "bun", "serumcreatinine", "creatinine", "uricacid", "calcium", "microalbuminurine", "albumincreatinineratioacr", "urinecreatinine", "urinealbumin", "buncreatinineratio", "urea", "egfr", "glomerularfiltrationrate"]:
        return "Biochemistry (Renal)"
    if norm in ["totalbilirubin", "directbilirubin", "indirectbilirubin", "sgotast", "sgptalt", "sgot", "sgpt", "sgotsgptratio", "alkalinephosphatasealp", "totalprotein", "albumin", "globulin", "agratio", "gammaglutamyltransferaseggt", "ggt", "proteintotal", "serumalbumin"]:
        return "Biochemistry (Liver)"
    if norm in ["serumsodium", "serumpotassium", "serumchloride", "sodium", "potassium", "chloride"]:
        return "Biochemistry (Electrolytes)"
    if norm in ["lipase", "amylase"]:
        return "Biochemistry (Enzymes)"
    if norm in ["totalcholesterol", "cholesteroltotal", "triglycerides", "triglyceride", "hdlcholesterol", "cholesterolhdl", "ldlcholesterol", "cholesterolldl", "vldlcholesterol", "cholesterolvldl", "nonhdlcholesterol", "cholesterolhdlratio", "ldlhdlratio"]:
        return "Lipid Profile"
    if norm in ["glucosefasting", "fastingbloodsugar", "glucosepostprandialppbs", "ppbs", "hba1cglycosylatedhemoglobin", "hba1c", "glycosylatedhemoglobin", "estimatedaverageglucoseeag", "averagebloodglucose", "meanbloodglucose", "eag"]:
        return "Diabetes Monitoring"
    if norm in ["serumiron", "iron", "totalironbindingcapacitytibc", "tibc", "transferrinsaturation", "ferritin", "uibc", "transferrin"]:
        return "Iron Studies"
    if norm in ["thyroidstimulatinghormonetsh", "tsh", "freet3", "freet4", "totalt3", "totalt4", "t3", "t4"]:
        return "Immunoassay / Thyroid"
    if norm in ["vitamind25oh", "vitamind", "vitamind3", "vitaminb12", "vitaminb9folicacid", "folicacid"]:
        return "Vitamins"
    if norm in ["urinecolour", "urineappearance", "specificgravity", "urinespecificgravity"]:
        return "Urine Routine - Physical"
    if norm in ["urinereactionph", "reactionph", "urineprotein", "urineglucose", "urineketones", "ketonebodies", "urinebilesalt", "bilesalts", "urinebilepigments", "bilepigments", "urobilinogen"]:
        return "Urine Routine - Chemical"
    if norm in ["puscellswbc", "urinepuscells", "puscells", "epithelialcells", "urineepithelialcells", "redbloodcells", "urinerbcs", "crystals", "urinecrystals", "casts", "urinecasts", "bacteria", "urinebacteria"]:
        return "Urine Routine - Microscopic"
    if norm in ["antihbstiter", "hcvcardantibody", "hbsag", "antihcv", "hiv12", "hiv", "hcv", "hbs"]:
        return "Infectious Disease Serology"
    if norm in ["highsensitivitycrphscrp", "hscrp", "rafactorqualitative", "rafactor", "rheumatoidfactor", "crpcreactiveprotein", "crp"]:
        return "Inflammatory Markers"
    if "psa" in norm:
        return "Special Chemistry / Markers"

    if category and category != "General / Other":
        return category

    return "General / Other"

def determine_clinical_flag(value: float, ref_str: str, meta: dict = None) -> str:
    """Calculates whether value is NORMAL, HIGH, or LOW based on reference range."""
    if ref_str:
        # Range: e.g. 12.0 - 15.0 or 70 - 99
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)', ref_str)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            if value < low:
                return "LOW"
            elif value > high:
                return "HIGH"
            return "NORMAL"

        # Upper bound: e.g. < 200, <= 199.9, <30
        lt_match = re.search(r'<[=\s]*(\d+(?:\.\d+)?)', ref_str)
        if lt_match:
            cutoff = float(lt_match.group(1))
            if value > cutoff:
                return "HIGH"
            return "NORMAL"

        # Lower bound: e.g. > 40, >= 49.5, >= 0.01
        gt_match = re.search(r'>[=\s]*(\d+(?:\.\d+)?)', ref_str)
        if gt_match:
            cutoff = float(gt_match.group(1))
            if value < cutoff:
                return "LOW"
            return "NORMAL"

    # Fallback to dictionary metadata if available
    if meta:
        min_v = meta.get("min")
        max_v = meta.get("max")
        if min_v is not None and value < min_v:
            return "LOW"
        if max_v is not None and value > max_v:
            return "HIGH"

    return "NORMAL"

# Backward compatibility alias
determine_flag = determine_clinical_flag

def extract_date_from_text(text: str) -> str:
    """Extracts test collection date from report."""
    date_patterns = [
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',                                       # 04/09/2026
        r'\b(\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4})\b', # 04 Sep 2026
        r'\b(\d{1,2}[/-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/-]\d{4})\b', # 04/Sep/2026
        r'\b(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b',                                     # 2026-09-04
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2})\b',                                       # 04/09/26
    ]

    for pat in date_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            raw_str = match.group(1).replace('/', '-').replace('.', '-')
            for fmt in ("%d-%m-%Y", "%d-%b-%Y", "%d %b %Y", "%d-%B-%Y", "%d %B %Y", "%Y-%m-%d", "%d-%m-%y"):
                try:
                    dt = datetime.strptime(raw_str, fmt)
                    if 2000 <= dt.year <= 2035:
                        return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

    return datetime.now().strftime("%Y-%m-%d")

def parse_lab_data(text: str):
    """
    Comprehensive lab test parser that extracts ALL biomarkers from clinical reports.
    Combines universal multi-pattern extraction with clinical dictionary normalization.
    Supports Star Health reports, Thyrocare, and all standard laboratory formats.
    """
    extracted_date = extract_date_from_text(text)
    candidates = {}

    expanded_units = (
        r'(mg/dL|mg/dl|gm/dL|gm/dl|g/dL|g/dl|mili/cu\.mm|%|fL|fl|f\s*l|pg/mL|pg/ml|pg|'
        r'10\^6|10\^3/[µu\?]L|10\^3/[µu\?]l|cells/cumm|cells/cu\.mm|/\s*cumm|/\s*cu\.mm|'
        r'/\s*HPF|/\s*hpf|/\s*LPF|/\s*lpf|U/L|u/l|uIU/m[lL]|uiu/ml|ulU/m[lL]|ulu/ml|'
        r'ng/m[lL]|ng/ml|ng/dL|ng/dl|[µu\?]g/d[lL]|[µu\?]g/dl|mEq/L|meq/l|mmol/L|mmol/l|'
        r'mL/min/1\.73m2|Ratio|ratio|umol/L|umol/l|mm/hr|mIU/mL|miu/ml|IU/mL|iu/ml|mg/L|mg/l|'
        r'mg/gm|mg/g|Seconds|seconds|Sec|sec|MINUTES|Minutes|minutes|MIN|min)'
    )

    # Patterns indicating document/patient metadata or non-test sections
    METADATA_LINE_PATTERNS = [
        r'\b(?:lab\s*visit\s*id|collection\s*date|barcode\s*id|order\s*id)\b',
        r'\b(?:customer\s*name|patient\s*name|referred\s*by|sample\s*type)\b',
        r'\b(?:report\s*date|report\s*status|po\s*no|registered\s*on)\b',
        r'\b(?:age\s*[/]\s*gender|age\s*[/]\s*sex|patient\s*id|uhid)\b',
        r'\b(?:bill\s*no|receipt\s*no|dr\.|mbbs|nabl\s*cert)\b',
        r'\b(?:performed\s*at|address\s*:|page\s*\d+\s*of\s*\d+)\b',
        r'\b(?:scan\s*for\s*digital|disclaimer\s*:)\b'
    ]

    # Narrative/sentence markers - lines containing these are explanatory text, not test rows
    SENTENCE_VERB_PATTERNS = [
        r'\b(?:measures|levels|regardless|intake|affects|population)\b',
        r'\b(?:protective|recommended|guidelines|treatment|screening)\b',
        r'\b(?:lifestyle|initiated|target|targets|according\s*to)\b',
        r'\b(?:diagnosed|associated\s*with|indicates|suggests|evaluated)\b',
        r'\b(?:undergoes|responsible\s*for|consists\s*of|formula|equation)\b',
        r'\b(?:analytical\s*and\s*biological\s*variation|repeat\s*testing)\b',
        r'\b(?:risk\s*factor|risk\s*groups?|consensus\s*statement)\b',
        r'\b(?:have\s*it|before\s*meal|after\s*meal|healthy\s*individuals)\b',
        r'\b(?:carried\s*out|seen\s*in|prone\s*to|linked\s*to|vital\s*to)\b'
    ]

    # Reference interval classification labels (NOT biomarker test names)
    REFERENCE_LABEL_PATTERNS = [
        r'^(?:low|high|moderate|very\s*high|extreme)\s*risk\b',
        r'^(?:desirable|optimal|borderline|above\s*desirable)\b',
        r'^(?:moderate\s*\(borderline\)|low\s*\(desirable\))\b',
        r'^\(?\s*(?:males?|females?|adults?|children|pediatric|infants?)\b',
        r'^(?:bio\.?\s*ref|biological|reference\s*interval|decision\s*value)\b',
        r'^(?:target\s*goals?|goal\s*of\s*therapy|therapeutic\s*goals?)\b'
    ]

    # Standalone comment/note section header regex
    COMMENT_START_REGEX = re.compile(
        r'^(?:comment|comments|note|notes|clinical\s+significance|interpretation|disclaimer|methodology)\s*:',
        re.I
    )

    # Diagnostic section / Table headers that reset comment block
    SECTION_RESET_REGEX = re.compile(
        r'^(?:test\s+name|biochemistry|haematology|hematology|clinical\s+pathology|serology|immunology|immunoassay|lipid\s+profile|complete\s+blood\s+count|urine\s+routine|coagulation)\b',
        re.I
    )

    lines = text.splitlines()

    # Detect if report uses star prefix for test rows (Star Health format)
    star_test_count = sum(1 for l in lines if re.match(r'^\*\s+[A-Za-z].*?\s+(?:\d+|Absent|Pale|Clear|Negative|Non Reactive|Normocytic|Plasma|Acidic)', l.strip()))
    is_star_report = star_test_count >= 15

    in_comment_block = False

    for i, orig_line in enumerate(lines):
        clean_l = orig_line.strip()
        if not clean_l:
            continue

        # Check section boundaries
        if COMMENT_START_REGEX.search(clean_l):
            in_comment_block = True
            continue

        if SECTION_RESET_REGEX.search(clean_l):
            in_comment_block = False
            continue

        # In standard reports, skip anything inside comment / disclaimer blocks
        if in_comment_block and not is_star_report:
            # Check if line looks like a known test from dictionary
            first_word = clean_l.split()[0] if clean_l.split() else ''
            norm_test_check = re.sub(r'[^a-z0-9]', '', first_word.lower())
            has_known_test = any(norm_test_check == re.sub(r'[^a-z0-9]', '', k) for k in BIOMARKER_DICTIONARY.keys())
            if not has_known_test:
                continue
            else:
                in_comment_block = False

        # Ignore metadata header lines
        if any(re.search(pat, clean_l, re.I) for pat in METADATA_LINE_PATTERNS):
            continue

        # Ignore numbered footnote lines and clinical interpretation guidelines
        if re.match(r'^\s*\d+[\.\)]\s+[A-Z]', clean_l):
            continue
        if re.match(r'^\*?\s*Relative to young adult level', clean_l, re.I):
            continue
        if re.search(r'Pre Diabetes Clinical Decision value', clean_l, re.I):
            continue
        if clean_l.startswith('%'):
            continue

        # In a Star Health report, every valid test row starts with an asterisk
        if is_star_report:
            if not clean_l.startswith('*'):
                continue
            line_content = clean_l[1:].strip()
        else:
            line_content = clean_l

        # Rejoin a decimal value's trailing digit(s) when a PDF kerning glitch inserted a
        # stray space mid-number right before the unit (e.g. "106.0 0 mg/dL" -> "106.00 mg/dL");
        # otherwise Pattern B below matches only the stray "0" as the value.
        line_content = re.sub(r'(\b\d+\.\d)\s+(\d+)\s+([a-zA-Z%])', r'\1\2 \3', line_content)

        # Normalize spacing inside units
        norm_line = re.sub(r'(\b\d+\.?\d*)\s*(mg|g)\s*/\s*(dl|dL)', r'\1 \2/dL', line_content)
        norm_line = re.sub(r'(\b\d+\.?\d*)\s*(cells)\s*/\s*(cumm|cu\.mm)', r'\1 cells/cumm', norm_line)
        norm_line = re.sub(r'(\b\d+\.?\d*)\s*/\s*(cumm|cu\.mm)', r'\1 / cumm', norm_line)
        norm_line = re.sub(r'(\b\d+\.?\d*)\s*(mg)\s*/\s*(gm|g)', r'\1 mg/gm', norm_line)
        norm_line = re.sub(r'(\b\d+\.?\d*)\s*ulU/m[lL]', r'\1 uIU/mL', norm_line, flags=re.I)

        # 1. Pattern A: Time Format (MIN + SEC, e.g. '2 MIN 46 SEC')
        time_m = re.search(r'(\d+)\s*(?:MIN|min|Minutes|minutes)\s+(\d+)\s*(?:SEC|sec|Seconds|seconds)', norm_line)
        if time_m:
            mins = int(time_m.group(1))
            secs = int(time_m.group(2))
            val_num = round(mins + secs / 60.0, 2)
            val_str = f"{mins} MIN {secs} SEC"
            test_part = norm_line[:time_m.start()].strip()
            after_part = norm_line[time_m.end():].strip()
            ref_match = re.search(r'(\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?)', after_part)
            ref_str = ref_match.group(1).strip() if ref_match else ""
            _store_candidate(candidates, test_part, val_num, val_str, "min", ref_str)
            continue

        # 2. Pattern B: Standard & Expanded Units with Number
        m = re.search(rf'(?<![a-zA-Z])([<>]?=?\s*\d+(?:\.\d+)?)\s*{expanded_units}(?:\s|$|[,;])', norm_line)
        if m:
            val_str = m.group(1).strip().replace(' ', '')
            unit_str = m.group(2).strip()
            test_part = norm_line[:m.start()].strip()
            after_part = norm_line[m.end():].strip()

            clean_name = re.sub(r'^[\s\*\-\•\–\d\.]+', '', test_part).strip()
            clean_name = re.sub(r'[\:\,\-\–\>\<\=]+$', '', clean_name).strip()
            clean_name = re.sub(r'\s+\d+(?:\.\d+)?$', '', clean_name).strip()

            # A test name left with an unmatched opening paren wrapped onto the next physical
            # line (e.g. "PAPP-A (Pregnancy Associated Plasma" / "Protein)"). Reattach the
            # short trailing fragment, but only when it can't be anything else: no digits (a
            # genuine continuation of a name, not a value row) and not metadata/comment/section text.
            if clean_name.count('(') > clean_name.count(')') and i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if (nxt and len(nxt) <= 25 and not re.search(r'\d', nxt)
                        and not any(re.search(pat, nxt, re.I) for pat in METADATA_LINE_PATTERNS)
                        and not COMMENT_START_REGEX.search(nxt) and not SECTION_RESET_REGEX.search(nxt)):
                    clean_name = f"{clean_name} {nxt}"

            lower_name = clean_name.lower()

            # Filter out narrative sentences and explanatory bullets
            if any(re.search(pat, norm_line, re.I) for pat in SENTENCE_VERB_PATTERNS):
                continue

            # Filter out reference range labels (e.g. 'Low risk>', '(males')
            if any(re.search(pat, lower_name) for pat in REFERENCE_LABEL_PATTERNS):
                continue

            if len(clean_name) >= 2 and len(clean_name) <= 60 and not any(p in clean_name for p in [';', '!', '?', '=']):
                if not any(sw in f" {lower_name} " for sw in [' is ', ' are ', ' was ', ' were ', ' should ', ' may ', ' because ', ' reflects ']):
                    try:
                        val_num = float(re.sub(r'[<>=]', '', val_str))
                        ref_match = re.search(r'([<>]?=?\s*\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?)?|<=?\s*\d+(?:\.\d+)?|>=?\s*\d+(?:\.\d+)?)', after_part)
                        ref_str = ref_match.group(1).strip() if ref_match else ''
                        _store_candidate(candidates, clean_name, val_num, val_str, unit_str, ref_str)
                        continue
                    except ValueError:
                        pass

        # 3. Pattern C: Microscopic Range (e.g. '1 - 2 /HPF')
        micro_m = re.search(r'(\d+\s*[-–]\s*\d+)\s*(/HPF|/hpf|/LPF|/lpf)', norm_line)
        if micro_m:
            val_str = micro_m.group(1).strip()
            unit_str = micro_m.group(2).strip()
            test_part = norm_line[:micro_m.start()].strip()
            clean_name = re.sub(r'^[\s\*\-\•\–\d\.]+', '', test_part).strip()
            clean_name = re.sub(r'[\:\,\-\–]+$', '', clean_name).strip()
            parts = re.split(r'[-–]', val_str)
            val_num = float(parts[-1].strip())
            _store_candidate(candidates, clean_name, val_num, val_str, unit_str, val_str)
            continue

        # 4. Pattern D: Qualitative & Textual Tests (e.g. Absent, Clear, Normocytic normochromic, Negative)
        if not any(re.search(pat, norm_line, re.I) for pat in SENTENCE_VERB_PATTERNS):
            matched_qual = None
            filtered_tokens = [tok for tok in QUAL_TOKENS if tok.lower() not in ['plasma', 'serum']]
            if is_star_report or 'specimen' in clean_l.lower():
                filtered_tokens.extend(['Plasma', 'Serum'])

            for token in sorted(filtered_tokens, key=len, reverse=True):
                token_m = re.search(r'\b' + re.escape(token) + r'\b', norm_line, re.IGNORECASE)
                if token_m:
                    test_part = norm_line[:token_m.start()].strip()
                    clean_name = re.sub(r'^[\s\*\-\•\–\d\.]+', '', test_part).strip()
                    clean_name = re.sub(r'[\:\,\-\–]+$', '', clean_name).strip()
                    if len(clean_name.split()) <= 6 and 2 <= len(clean_name) <= 50:
                        if not any(w in clean_name.lower() for w in ['interpretation', 'method', 'sample', 'end of report', 'note', 'page', 'comment']):
                            matched_qual = (clean_name, token, norm_line[token_m.end():].strip())
                            break
            if matched_qual:
                t_name, tok, after = matched_qual
                ref_match = re.search(r'\b(Absent|Clear|Pale Yellow|Normocytic normochromic|Adequate|Negative|Non Reactive|Normal)\b', after, re.I)
                ref_str = ref_match.group(1) if ref_match else ""
                _store_candidate(candidates, t_name, 0.0, tok, "", ref_str, is_qual=True)
                continue

        # 5. Pattern E: Unitless numeric tests (INR, Specific Gravity, PT ISI, Ratios, Urine Albumin)
        unitless_m = re.search(r'\b(\d+(?:\.\d+)?)\b', norm_line)
        if unitless_m:
            v_str = unitless_m.group(1)
            test_part = norm_line[:unitless_m.start()].strip()
            clean_name = re.sub(r'^[\s\*\-\•\–\d\.]+', '', test_part).strip()
            clean_name = re.sub(r'[\:\,\-\–]+$', '', clean_name).strip()
            after_part = norm_line[unitless_m.end():].strip()
            lower_tp = clean_name.lower()

            if re.search(r'\b(ratio|inr|isi|specific\s+gravity|urine\s+albumin|urine\s+creatinine)\b', lower_tp):
                if not any(meta_k in lower_tp for meta_k in ['visit', 'collection', 'date', 'barcode', 'order', 'patient', 'customer']):
                    # Same narrative-sentence guard Patterns B/D apply - this one was missing it,
                    # which let explanatory comment lines (e.g. "...Ratio: Typically <1 in
                    # healthy individuals...") through as if they were a test row.
                    if not any(re.search(pat, norm_line, re.I) for pat in SENTENCE_VERB_PATTERNS):
                        ref_match = re.search(r'([<>]?=?\s*\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?)?)', after_part)
                        ref_str = ref_match.group(1).strip() if ref_match else ''
                        _store_candidate(candidates, clean_name, float(v_str), v_str, "Ratio" if 'ratio' in lower_tp else "", ref_str)
                        continue

    return extracted_date, list(candidates.values())

def _store_candidate(candidates: dict, raw_name: str, val_num: float, val_str: str, unit_str: str, ref_str: str, is_qual: bool = False):
    """Helper to standardize candidate biomarker naming, unit, flags, and storage."""
    clean_name = re.sub(r'[\:\,\-\–]+$', '', raw_name).strip()
    norm_key = re.sub(r'[^a-z0-9]', '', clean_name.lower())
    if not norm_key:
        return

    # Reject candidates that are structurally never a real biomarker name, regardless of
    # which pattern produced them - this is the single choke point all patterns funnel through.
    if clean_name.lower() in BLACKLIST_EXACT_NAMES:
        return
    if re.search(r'\d\s*:\s*\d', clean_name):
        # A digit:digit ratio ("1:5738", "<1:10000") is a genetic-screening risk score, not a
        # lab value - real biomarkers never format this way. Catches multi-column PDF layouts
        # (e.g. an NIPT risk-summary table) that collapse two grid columns onto one text line.
        return
    if norm_key in UNIT_ONLY_NORMALIZED_KEYS:
        # The "name" is just a unit token (e.g. "µg/dL") - a leftover fragment from a
        # multi-column value row where the real name ended up on a different line/column.
        return

    # Standardize presentation of unit
    u_lower = unit_str.lower()
    if '10^3' in unit_str: unit = '10^3/µL'
    elif '10^6' in unit_str: unit = '10^6'
    elif 'cells/cumm' in u_lower or 'cells/cu.mm' in u_lower: unit = 'cells/cumm'
    elif '/cumm' in u_lower or '/ cumm' in u_lower: unit = '/cumm'
    elif 'hpf' in u_lower: unit = '/HPF'
    elif u_lower in ['seconds', 'sec']: unit = 'Seconds'
    elif u_lower in ['minutes', 'min']: unit = 'min'
    elif u_lower in ['fl', 'f l']: unit = 'fL'
    elif u_lower in ['mg/dl', 'mg/dl']: unit = 'mg/dL'
    elif u_lower in ['g/dl', 'gm/dl']: unit = 'g/dL'
    elif u_lower == 'mg/gm': unit = 'mg/gm'
    elif u_lower in ['ng/ml']: unit = 'ng/mL'
    elif u_lower in ['pg/ml']: unit = 'pg/mL'
    elif u_lower in ['pg']: unit = 'pg'
    elif u_lower in ['u/l']: unit = 'U/L'
    elif 'uiu' in u_lower or 'ulu' in u_lower: unit = 'uIU/mL'
    elif 'miu' in u_lower: unit = 'mIU/mL'
    elif u_lower == 'mmol/l': unit = 'mmol/L'
    elif u_lower == 'mm/hr': unit = 'mm/hr'
    elif u_lower == 'mg/l': unit = 'mg/L'
    elif u_lower == 'ratio': unit = 'Ratio'
    elif unit_str == '%': unit = '%'
    else: unit = unit_str

    display_name = clean_name
    dict_meta = None

    # Disambiguate single-word urine routine tests from blood tests
    if norm_key == "protein":
        dict_meta = BIOMARKER_DICTIONARY.get("urine protein")
        display_name = dict_meta["name"] if dict_meta else "Urine Protein"
    elif norm_key == "glucose" and is_qual:
        dict_meta = BIOMARKER_DICTIONARY.get("urine glucose")
        display_name = dict_meta["name"] if dict_meta else "Urine Glucose"
    else:
        # 1. Exact match against dictionary keys
        for alias, meta in BIOMARKER_DICTIONARY.items():
            alias_norm = re.sub(r'[^a-z0-9]', '', alias)
            if norm_key == alias_norm:
                dict_meta = meta
                display_name = meta['name']
                if not ref_str and meta.get('ref'):
                    ref_str = meta['ref']
                if not unit and meta.get('unit'):
                    unit = meta['unit']
                break

        # 2. Word-boundary regex match if no exact match found
        if not dict_meta:
            # A name containing a bare function word (article/preposition/conjunction) and not
            # already recognized outright is a narrative fragment, not a biomarker - reject
            # before attempting a fuzzy match instead of risking a wrong dictionary hit.
            name_words = re.findall(r"[a-z0-9']+", clean_name.lower())
            if any(w in STOPWORDS for w in name_words):
                return

            # A parenthetical is almost always an explanatory gloss of the core name (e.g.
            # "Vitamin D3 (25 Hydroxy Cholecalciferal)"), not extra content that should count
            # against the ratio check below - measure specificity against the name outside it.
            core_norm_key = re.sub(r'[^a-z0-9]', '', re.sub(r'\([^)]*\)', '', clean_name).lower()) or norm_key

            for alias, meta in SORTED_BIOMARKER_ALIASES:
                alias_norm = re.sub(r'[^a-z0-9]', '', alias)
                # Require the alias to cover at least half of the candidate's core name, not
                # just appear somewhere inside it - otherwise a short generic alias like
                # "albumin" hijacks an unrelated compound name like "Microalbumin-Albumin" (a
                # urine test, not the serum one), keeping the extracted unit/range under the
                # wrong label.
                if len(alias_norm) < 0.5 * len(core_norm_key):
                    continue
                if re.search(r'\b' + re.escape(alias) + r'\b', clean_name.lower()):
                    dict_meta = meta
                    display_name = meta['name']
                    if not ref_str and meta.get('ref'):
                        ref_str = meta['ref']
                    if not unit and meta.get('unit'):
                        unit = meta['unit']
                    break

    if is_qual and dict_meta and dict_meta.get('min') is not None and val_str.lower() in SEROLOGY_ONLY_TOKENS:
        # A serology-style token ("Reactive", "Positive"...) resolved to an inherently numeric
        # biomarker (has a min/max range, e.g. ESR in mm/hr) - a garbled cross-column match, not
        # a real reading. Narrower than "no qualitative value on a numeric test" in general,
        # since some numeric tests (pH, specific gravity) are legitimately reported either way.
        return

    # Flag calculation
    if is_qual:
        tok_lower = val_str.lower()
        if any(bad in tok_lower for bad in ['reactive', 'positive', 'abnormal', 'hazy', 'turbid', 'increased', 'reduced']):
            if 'non reactive' in tok_lower or 'non-reactive' in tok_lower:
                flag = 'NORMAL'
            else:
                flag = 'ABNORMAL'
        else:
            flag = 'NORMAL'
    else:
        flag = determine_clinical_flag(val_num, ref_str, dict_meta)

    category = dict_meta.get('category') if dict_meta else get_test_category(display_name)
    panel = dict_meta.get('panel') if (dict_meta and 'panel' in dict_meta) else get_test_panel(display_name, category)
    store_key = re.sub(r'[^a-z0-9]', '', display_name.lower())

    cand_data = {
        'test_name': display_name,
        'raw_name': clean_name,
        'category': category,
        'panel': panel,
        'value': val_num,
        'value_str': val_str,
        'unit': unit,
        'reference_range': ref_str,
        'flag': flag
    }

    if store_key not in candidates:
        candidates[store_key] = cand_data
    else:
        existing = candidates[store_key]
        # A bare number with no dash/comparator ("1.02") isn't a valid reference-range shape -
        # never let it "enrich" an existing blank-ref entry, since that's exactly what a stray
        # number leaking in from an adjacent PDF column looks like.
        ref_looks_like_range = bool(re.search(r'[-–<>]', ref_str))
        if (existing['value'] == 0.0 and val_num > 0.0) or (not existing['reference_range'] and ref_str and ref_looks_like_range):
            candidates[store_key] = cand_data
