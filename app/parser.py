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

    # Complete Blood Count (CBC)
    "hemoglobin": {"name": "Hemoglobin", "category": "Complete Blood Count (CBC)", "unit": "g/dL", "ref": "12.0 - 15.0", "min": 12.0, "max": 15.0},
    "rbc": {"name": "RBC Count", "category": "Complete Blood Count (CBC)", "unit": "mili/cu.mm", "ref": "3.8 - 4.8", "min": 3.8, "max": 4.8},
    "hct": {"name": "HCT (Hematocrit)", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "36 - 46", "min": 36, "max": 46},
    "mcv": {"name": "MCV", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "83 - 101", "min": 83, "max": 101},
    "mch": {"name": "MCH", "category": "Complete Blood Count (CBC)", "unit": "pg", "ref": "27 - 32", "min": 27, "max": 32},
    "mchc": {"name": "MCHC", "category": "Complete Blood Count (CBC)", "unit": "g/dL", "ref": "31.5 - 34.5", "min": 31.5, "max": 34.5},
    "rdw-cv": {"name": "RDW-CV", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "11.5 - 14.0", "min": 11.5, "max": 14.0},
    "total leucocyte count": {"name": "Total Leucocyte Count (WBC)", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "4.0 - 10.0", "min": 4.0, "max": 10.0},
    "neutrophils": {"name": "Neutrophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "40 - 80", "min": 40, "max": 80},
    "lymphocytes": {"name": "Lymphocytes", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "20 - 40", "min": 20, "max": 40},
    "monocytes": {"name": "Monocytes", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "2 - 10", "min": 2, "max": 10},
    "eosinophils": {"name": "Eosinophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "1 - 6", "min": 1, "max": 6},
    "basophils": {"name": "Basophils", "category": "Complete Blood Count (CBC)", "unit": "%", "ref": "0 - 2", "min": 0, "max": 2},
    "absolute neutrophil count": {"name": "Absolute Neutrophil Count", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "2 - 7", "min": 2, "max": 7},
    "absolute lymphocyte count": {"name": "Absolute Lymphocyte Count", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "1 - 3", "min": 1, "max": 3},
    "absolute monocyte count": {"name": "Absolute Monocyte Count", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "0.2 - 1.0", "min": 0.2, "max": 1.0},
    "absolute eosinophil count": {"name": "Absolute Eosinophil Count", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "0.02 - 0.5", "min": 0.02, "max": 0.5},
    "absolute basophil count": {"name": "Absolute Basophil Count", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "0.02 - 0.1", "min": 0.02, "max": 0.1},
    "platelet count": {"name": "Platelet Count", "category": "Complete Blood Count (CBC)", "unit": "10^3/µL", "ref": "150 - 410", "min": 150, "max": 410},
    "mpv": {"name": "MPV", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "6.5 - 12.0", "min": 6.5, "max": 12.0},
    "pdw": {"name": "PDW", "category": "Complete Blood Count (CBC)", "unit": "fL", "ref": "9.0 - 17.0", "min": 9.0, "max": 17.0},

    # Inflammatory & Cardiac Profile
    "erythrocyte sedimentation": {"name": "Erythrocyte Sedimentation Rate (ESR)", "category": "Cardiac & Inflammation", "unit": "mm/hr", "ref": "0 - 19", "min": 0, "max": 19},
    "erythrocyte sedimentation rate": {"name": "Erythrocyte Sedimentation Rate (ESR)", "category": "Cardiac & Inflammation", "unit": "mm/hr", "ref": "0 - 19", "min": 0, "max": 19},
    "c-reactive protein": {"name": "C-Reactive Protein (Quantitative)", "category": "Cardiac & Inflammation", "unit": "mg/L", "ref": "0 - 3.3", "min": 0, "max": 3.3},
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
    "ferritin": {"name": "Ferritin", "category": "Iron Studies", "unit": "ng/mL", "ref": "10 - 291", "min": 10, "max": 291},

    # Kidney Health (KFT / RFT)
    "creatinine": {"name": "Serum Creatinine", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "0.55 - 1.02", "min": 0.55, "max": 1.02},
    "blood urea nitrogen": {"name": "Blood Urea Nitrogen (BUN)", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "9.0 - 23.0", "min": 9.0, "max": 23.0},
    "urea": {"name": "Blood Urea", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "19.26 - 49.22", "min": 19.26, "max": 49.22},
    "uric acid": {"name": "Uric Acid", "category": "Kidney Function (KFT)", "unit": "mg/dL", "ref": "2.7 - 6.1", "min": 2.7, "max": 6.1},
    "sodium": {"name": "Serum Sodium", "category": "Kidney Function (KFT)", "unit": "mEq/L", "ref": "136 - 145", "min": 136, "max": 145},
    "potassium": {"name": "Serum Potassium", "category": "Kidney Function (KFT)", "unit": "mEq/L", "ref": "3.5 - 5.1", "min": 3.5, "max": 5.1},
    "chloride": {"name": "Serum Chloride", "category": "Kidney Function (KFT)", "unit": "mmol/L", "ref": "98 - 107", "min": 98, "max": 107},
    "bun/creatinine ratio": {"name": "BUN/Creatinine Ratio", "category": "Kidney Function (KFT)", "unit": "Ratio", "ref": "12 - 20", "min": 12, "max": 20},
    "glomerular filtration rate": {"name": "Glomerular Filtration Rate (eGFR)", "category": "Kidney Function (KFT)", "unit": "mL/min/1.73m2", "ref": ">= 90", "min": 90, "max": 200},
    "e gfr": {"name": "Glomerular Filtration Rate (eGFR)", "category": "Kidney Function (KFT)", "unit": "mL/min/1.73m2", "ref": ">= 90", "min": 90, "max": 200},

    # Lipid Profile
    "cholesterol - total": {"name": "Total Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 200", "min": 100, "max": 199.9},
    "triglycerides": {"name": "Triglycerides", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 150", "min": 50, "max": 149.9},
    "cholesterol - hdl": {"name": "HDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": ">= 50", "min": 50, "max": 100},
    "cholesterol - ldl": {"name": "LDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 100", "min": 50, "max": 99.9},
    "non hdl cholesterol": {"name": "Non-HDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 130", "min": 50, "max": 129.9},
    "cholesterol- vldl": {"name": "VLDL Cholesterol", "category": "Lipid Profile", "unit": "mg/dL", "ref": "< 30", "min": 5, "max": 30},
    "cholesterol : hdl cholesterol": {"name": "Cholesterol / HDL Ratio", "category": "Lipid Profile", "unit": "Ratio", "ref": "3.0 - 4.0", "min": 3.0, "max": 4.0},
    "ldl : hdl cholesterol": {"name": "LDL / HDL Ratio", "category": "Lipid Profile", "unit": "Ratio", "ref": "2.0 - 2.5", "min": 2.0, "max": 2.5},

    # Liver Function (LFT)
    "bilirubin - total": {"name": "Total Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.3 - 1.2", "min": 0.3, "max": 1.2},
    "bilirubin-total": {"name": "Total Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.3 - 1.2", "min": 0.3, "max": 1.2},
    "bilirubin-direct": {"name": "Direct Bilirubin", "category": "Liver Function (LFT)", "unit": "mg/dL", "ref": "0.0 - 0.3", "min": 0.0, "max": 0.3},
    "protein, total": {"name": "Total Protein", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "5.7 - 8.2", "min": 5.7, "max": 8.2},
    "albumin": {"name": "Albumin", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "3.2 - 4.8", "min": 3.2, "max": 4.8},
    "globulin": {"name": "Globulin", "category": "Liver Function (LFT)", "unit": "g/dL", "ref": "2.3 - 4.1", "min": 2.3, "max": 4.1},
    "a/g ratio": {"name": "A/G Ratio", "category": "Liver Function (LFT)", "unit": "Ratio", "ref": "0.8 - 1.9", "min": 0.8, "max": 1.9},
    "sgot": {"name": "SGOT (AST)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 34", "min": 0, "max": 34},
    "aspartate transaminase": {"name": "SGOT (AST)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 34", "min": 0, "max": 34},
    "sgpt": {"name": "SGPT (ALT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "10 - 49", "min": 10, "max": 49},
    "alanine transaminase": {"name": "SGPT (ALT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "10 - 49", "min": 10, "max": 49},
    "sgot/sgpt": {"name": "SGOT / SGPT Ratio", "category": "Liver Function (LFT)", "unit": "Ratio", "ref": "0.7 - 1.4", "min": 0.7, "max": 1.4},
    "alkaline phosphatase": {"name": "Alkaline Phosphatase (ALP)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "46 - 116", "min": 46, "max": 116},
    "gamma glutamyltransferase": {"name": "Gamma-Glutamyl Transferase (GGT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 38", "min": 0, "max": 38},
    "gamma": {"name": "Gamma-Glutamyl Transferase (GGT)", "category": "Liver Function (LFT)", "unit": "U/L", "ref": "< 38", "min": 0, "max": 38},

    # Pancreas, Bone & Minerals
    "lipase": {"name": "Lipase", "category": "Hormones & Immunology", "unit": "U/L", "ref": "12 - 53", "min": 12, "max": 53},
    "amylase": {"name": "Amylase", "category": "Hormones & Immunology", "unit": "U/L", "ref": "30 - 118", "min": 30, "max": 118},
    "calcium": {"name": "Calcium", "category": "Vitamins & Minerals", "unit": "mg/dL", "ref": "8.6 - 10.0", "min": 8.6, "max": 10.0},
    "phosphorus": {"name": "Phosphorus", "category": "Vitamins & Minerals", "unit": "mg/dL", "ref": "2.4 - 5.1", "min": 2.4, "max": 5.1},
    "vitamin d": {"name": "Vitamin D (25-OH)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": "30 - 100", "min": 30, "max": 100},
    "vitamin b12": {"name": "Vitamin B12", "category": "Vitamins & Minerals", "unit": "pg/mL", "ref": "211 - 911", "min": 211, "max": 911},
    "vitamin b9": {"name": "Vitamin B9 (Folic Acid)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": ">= 5.38", "min": 5.38, "max": 100},
    "folic acid": {"name": "Vitamin B9 (Folic Acid)", "category": "Vitamins & Minerals", "unit": "ng/mL", "ref": ">= 5.38", "min": 5.38, "max": 100},

    # Thyroid Function
    "t3, total": {"name": "Total T3", "category": "Thyroid Profile", "unit": "ng/mL", "ref": "0.60 - 1.81", "min": 0.60, "max": 1.81},
    "t4, total": {"name": "Total T4", "category": "Thyroid Profile", "unit": "µg/dL", "ref": "4.5 - 12.6", "min": 4.5, "max": 12.6},
    "thyroid stimulating hormone": {"name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Profile", "unit": "uIU/mL", "ref": "0.55 - 4.78", "min": 0.55, "max": 4.78},
    "thyroid stimulating": {"name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Profile", "unit": "uIU/mL", "ref": "0.55 - 4.78", "min": 0.55, "max": 4.78},
    "tsh": {"name": "Thyroid Stimulating Hormone (TSH)", "category": "Thyroid Profile", "unit": "uIU/mL", "ref": "0.55 - 4.78", "min": 0.55, "max": 4.78},
    "free t4": {"name": "Free T4", "category": "Thyroid Profile", "unit": "ng/dL", "ref": "0.89 - 1.76", "min": 0.89, "max": 1.76},
    "free t3": {"name": "Free T3", "category": "Thyroid Profile", "unit": "pg/mL", "ref": "2.3 - 4.2", "min": 2.3, "max": 4.2},

    # Immunology, Arthritis & Hormones
    "rheumatoid factor": {"name": "Rheumatoid Factor - Quantitative (RF)", "category": "Hormones & Immunology", "unit": "IU/mL", "ref": "0 - 14", "min": 0, "max": 14},
    "immunoglobulin e": {"name": "Immunoglobulin E (IgE) Total", "category": "Hormones & Immunology", "unit": "IU/mL", "ref": "0 - 158", "min": 0, "max": 158},
    "follicle stimulating": {"name": "Follicle Stimulating Hormone (FSH)", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": ">= 0.01", "min": 23.0, "max": 116.3},
    "follicle stimulating hormone": {"name": "Follicle Stimulating Hormone (FSH)", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": ">= 0.01", "min": 23.0, "max": 116.3},
    "luteinizing hormone": {"name": "Luteinizing Hormone (LH)", "category": "Hormones & Immunology", "unit": "mIU/mL", "ref": ">= 0.09", "min": 7.9, "max": 53.8},
    "prolactin": {"name": "Prolactin", "category": "Hormones & Immunology", "unit": "ng/mL", "ref": "1.8 - 29.2", "min": 1.8, "max": 20.3}
}

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
    if any(k in lower for k in ["glucose", "sugar", "hba1c", "ppbs", "fbs", "insulin", "eag"]):
        return "Diabetes & Glycemic"
    if any(k in lower for k in [
        "hemoglobin", "rbc", "wbc", "platelet", "mcv", "mch", "mchc", "rdw", 
        "neutrophil", "lymphocyte", "monocyte", "eosinophil", "basophil", 
        "leucocyte", "leukocyte", "hematocrit", "hct", "mpv", "pdw"
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
        "sodium", "potassium", "chloride", "kft", "rft"
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
    if any(k in lower for k in ["fsh", "lh", "prolactin", "rheumatoid", "ige", "hormone", "amylase", "lipase", "immunoglobulin"]):
        return "Hormones & Immunology"

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
    Combines universal pattern extraction (for 70+ tests) with clinical dictionary normalization.
    """
    extracted_date = extract_date_from_text(text)
    candidates = {}

    unit_regex = (
        r'(mg/dL|mg/dl|g/dL|g/dl|mili/cu\.mm|%|fL|fl|f\s*l|pg/mL|pg/ml|pg|'
        r'10\^3/[µu\?]L|10\^3/[µu\?]l|U/L|u/l|uIU/m[lL]|uiu/ml|ng/m[lL]|ng/ml|ng/dL|ng/dl|'
        r'[µu\?]g/d[lL]|[µu\?]g/dl|mEq/L|meq/l|mmol/L|mmol/l|mL/min/1\.73m2|Ratio|ratio|'
        r'umol/L|umol/l|mm/hr|mIU/mL|miu/ml|IU/mL|iu/ml|mg/L|mg/l)'
    )

    sentence_markers = [
        'level of', 'have it', 'before meal', 'after meal', 'less than', 'more than',
        'low risk', 'high risk', 'affects', 'higher in', 'values above', 'seen in',
        'concentrations', 'patients with', 'prevalence of', 'confers', 'variation',
        'is secreted', 'pulses', 'belong to', 'males', 'females', 'equation',
        'measurement is', 'quickly as', 'unexplained', 'healthy individuals',
        'source', 'guidelines', 'adapted', 'disclaimer', 'customer name', 'dr.', 'mbbs',
        'nabl certificate', 'scan for digital'
    ]

    lines = text.splitlines()

    for i, orig_line in enumerate(lines):
        # Clean space-separated numbers like '107.0 0'
        line = re.sub(r'(\b\d+\.\d)\s+(\d+)\s+([a-zA-Z%])', r'\1\2 \3', orig_line)

        # Look for value + unit with negative lookbehind so A1 in 'Apo B/A1 Ratio' is not matched
        m = re.search(rf'(?<![a-zA-Z])([<>]?=?\s*\d+(?:\.\d+)?)\s*{unit_regex}(?:\s|$|[,;])', line)
        if m:
            val_str = m.group(1).strip().replace(' ', '')
            unit_str = m.group(2).strip()
            test_part = line[:m.start()].strip()
            after_part = line[m.end():].strip()

            # Two-line wrapped table header detection
            if len(test_part) < 2 and i > 0:
                prev = lines[i - 1].strip()
                if not any(sm in prev.lower() for sm in sentence_markers):
                    test_part = prev
                    # Check if next line contains second part of wrapped test name
                    if i + 1 < len(lines):
                        nxt = lines[i + 1].strip()
                        if nxt and len(nxt) < 35 and not any(sm in nxt.lower() for sm in sentence_markers):
                            if not re.search(r'\d', nxt) and not nxt.startswith('('):
                                test_part = f"{test_part} {nxt}"

            clean_name = re.sub(r'^[\s\*\-\•\–\d\.]+', '', test_part).strip()
            clean_name = re.sub(r'[\:\,\-\–]+$', '', clean_name).strip()
            clean_name = re.sub(r'\s+\d+(?:\.\d+)?$', '', clean_name).strip()

            lower_name = clean_name.lower()
            if len(clean_name) < 2 or len(clean_name) > 60:
                continue
            if any(sm in lower_name for sm in sentence_markers):
                continue
            if any(p in clean_name for p in [';', '!', '?', '=']):
                continue
            if clean_name.startswith('(') and clean_name.endswith(')'):
                continue
            if not re.search(r'[a-zA-Z]', clean_name):
                continue
            if re.match(r'^(?:of\b|are\b|higher\b|should\b|in\b|hence\b|belong\b|confers\b|or above\b|and\b)', after_part, re.IGNORECASE):
                continue

            # Standardize unit presentation
            u_lower = unit_str.lower()
            if '10^3' in unit_str: unit = '10^3/µL'
            elif u_lower in ['fl', 'f l']: unit = 'fL'
            elif u_lower == 'mg/dl': unit = 'mg/dL'
            elif u_lower == 'g/dl': unit = 'g/dL'
            elif u_lower == 'ng/ml': unit = 'ng/mL'
            elif u_lower == 'ng/dl': unit = 'ng/dL'
            elif u_lower == 'pg/ml': unit = 'pg/mL'
            elif u_lower == 'pg': unit = 'pg'
            elif 'ug/d' in u_lower or 'µg/d' in u_lower or '?g/d' in u_lower: unit = 'µg/dL'
            elif u_lower == 'u/l': unit = 'U/L'
            elif 'uiu' in u_lower: unit = 'uIU/mL'
            elif 'miu' in u_lower: unit = 'mIU/mL'
            elif u_lower == 'iu/ml': unit = 'IU/mL'
            elif u_lower == 'meq/l': unit = 'mEq/L'
            elif u_lower == 'mmol/l': unit = 'mmol/L'
            elif u_lower == 'umol/l': unit = 'umol/L'
            elif u_lower == 'mm/hr': unit = 'mm/hr'
            elif u_lower == 'mg/l': unit = 'mg/L'
            elif u_lower == 'ratio': unit = 'Ratio'
            elif u_lower == 'mili/cu.mm': unit = 'mili/cu.mm'
            elif 'ml/min' in u_lower: unit = 'mL/min/1.73m2'
            elif unit_str == '%': unit = '%'
            else: unit = unit_str

            # Reference range extraction
            ref_match = re.search(r'([<>]?=?\s*\d+(?:\.\d+)?\s*(?:[-–]\s*\d+(?:\.\d+)?)?|<=?\s*\d+(?:\.\d+)?|>=?\s*\d+(?:\.\d+)?)', after_part)
            ref_str = ref_match.group(1).strip() if ref_match else ''

            # Canonical dictionary mapping (match longest aliases first with word boundaries)
            display_name = clean_name
            dict_meta = None
            norm_key = re.sub(r'[^a-z0-9]', '', lower_name)

            sorted_aliases = sorted(BIOMARKER_DICTIONARY.items(), key=lambda x: len(x[0]), reverse=True)
            for alias, meta in sorted_aliases:
                alias_norm = re.sub(r'[^a-z0-9]', '', alias)
                if norm_key == alias_norm or re.search(r'\b' + re.escape(alias) + r'\b', lower_name):
                    meta_unit = meta.get('unit', '')
                    if not meta_unit or meta_unit.lower() in unit.lower() or unit.lower() in meta_unit.lower() or unit == 'Ratio':
                        dict_meta = meta
                        display_name = meta['name']
                        if not ref_str and meta.get('ref'):
                            ref_str = meta['ref']
                        break

            clean_val = re.sub(r'[<>=]', '', val_str)
            try:
                val_num = float(clean_val)
                flag = determine_clinical_flag(val_num, ref_str, dict_meta)

                store_key = re.sub(r'[^a-z0-9]', '', display_name.lower())
                category = dict_meta.get('category') if dict_meta else get_test_category(display_name)

                cand_data = {
                    'test_name': display_name,
                    'raw_name': clean_name,
                    'category': category,
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
                    # Update if current has non-zero or richer reference range
                    if (existing['value'] == 0.0 and val_num > 0.0) or (not existing['reference_range'] and ref_str):
                        candidates[store_key] = cand_data
            except ValueError:
                pass

    return extracted_date, list(candidates.values())
