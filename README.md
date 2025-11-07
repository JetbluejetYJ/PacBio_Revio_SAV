
# 🧬 PacBio_Revio_SAV

## 📝 Overview

`Revio_run_sav.py` is a Python script for automated extraction and summarization of key statistics from PacBio Revio sequencing runs.  
It parses run metadata, sample statistics, and report files to generate comprehensive summary tables for downstream analysis or LIMS integration.

- **Supports two output formats:**  
  - PacBio summary CSV  
  - LIMS-ready XLS (tab-delimited)
- **Automates extraction of:**
  - Polymerase and HiFi read statistics
  - Loading metrics (P0, P1, P2 rates)
  - Internal control read stats
  - AWS S3 path for HiFi BAM files

---

## 🚀 Usage

```bash
python Revio_run_sav.py [Option] [CSV_PATH] [RunDir_PATH]
```

### **Arguments**

| Argument      | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| `Option`      | Output type: `1` for PacBio CSV, `2` for LIMS XLS                          |
| `CSV_PATH`    | Path to the sample sheet CSV (e.g., `CSV/r84135_20240226_074856_Unaligned_1.csv`) |
| `RunDir_PATH` | Path to the Revio run directory (e.g., `/STORAGE/PacBio/Revio/revio_01/r84135_20240226_074856`) |

### **Example**

```bash
python Revio_run_sav.py 1 CSV/r84135_20240226_074856_Unaligned_1.csv /STORAGE/PacBio/Revio/revio_01/r84135_20240226_074856
```

---

## 📤 Output Files

Depending on the `Option` argument, the script generates:

- **Option 1:**  
  `[RunName]_Revio_Run_for_PacBio.csv`  
  (Comma-delimited summary for PacBio reporting)

- **Option 2:**  
  `[RunName]_Revio_Run_for_LIMS.xls`  
  (Tab-delimited summary for LIMS upload)

---

## 📑 Output Columns

### Option 1 (CSV)

| Column Name                    | Description                                 |
|------------------------------- |---------------------------------------------|
| Order Number                   | Project or order identifier                 |
| Sample Name                    | Sample name from CSV                        |
| Polymerase Yield               | Total polymerase read bases                 |
| Hifi Bases                     | Total HiFi (CCS) bases                      |
| Polymerase Read Length         | Mean polymerase read length                 |
| Hifi Read Length               | Mean HiFi read length                       |
| Hifi Read N50                  | N50 of HiFi reads                           |
| Hifi Read Count                | Number of HiFi reads                        |
| Loading P1 %                   | Productive ZMWs (P1) percentage             |
| Internal Control Read Length   | Mean internal control read length           |
| Internal Control Read Count    | Internal control read count                 |
| Path of Hifi BAM (AWS s3)      | S3 path to HiFi BAM file                    |

### Option 2 (LIMS XLS)

Includes all above, plus:

- Well, Customer Name, Application Type, Sample Ref, Productivity Rate (P0, P1, P2), etc.

---

## 🛠️ Script Workflow

1. **Input Validation:**  
   Checks for correct arguments and output file existence.

2. **Data Extraction:**  
   - Locates relevant XML, ZIP, and BAM files for each well/sample.
   - Parses XML for sample and barcode metadata.
   - Extracts statistics from JSON reports inside ZIPs.

3. **Summary Table Generation:**  
   - Compiles all metrics into the selected output format.
   - Handles missing data and mismatches with informative errors.

4. **Output:**  
   - Writes summary to CSV or tab-delimited XLS file.

---

## 📁 Example Directory Structure

```plaintext
/home/PacBio/Revio/
├── revio_01/
│   ├── r84135_20250101_000001/
│   │   ├── 1_A01/
│   │   │   ├── metadata/
│   │   │   ├── statistics/
│   │   │   └── hifi_reads/
│   │   └── ...
├── revio_02/
│   ├── r84135_20250101_000002/
│   │   ├── 1_A01/
│   │   │   ├── metadata/
│   │   │   ├── statistics/
│   │   │   └── hifi_reads/
│   │   └── ...
├── CSV/
│   ├── r84135_20240226_074856_Unaligned_1.csv
├── Script/
└─────  Revio_run_sav.py
```

---

## 📝 Notes

- The sample sheet CSV must contain columns: `RunName`, `Well`, `SampleID`, `SampleRef`, `ApplicationType`, `CustomerName`, `Project`.
- The script expects standard PacBio Revio directory and file naming conventions.
- For any issues or questions, please open an issue on this repository.

---

## 🧮 Calculation Methods

### 1. Loading P1% (Productive ZMWs Rate)

The loading efficiency (especially P1%) for PacBio Revio is calculated as follows:

$$
\text{Loading P1\%} = \frac{\text{Productivity 1}}{\text{Productive ZMWs}} \times 100
$$

- **Productivity 1**: Value extracted from loading.report.json ("Productivity 1")
- **Productive ZMWs**: Value extracted from loading.report.json ("Productive ZMWs")

### 2. Other Key Statistics

- **Polymerase Yield**: Total polymerase read bases, from raw_data.report.json ("Polymerase Read Bases")
- **Polymerase Read Length (mean)**: Mean polymerase read length, from raw_data.report.json
- **HiFi Bases**: Total HiFi (CCS) bases, from barcodes.report.json ("total_number_of_ccs_bases")
- **HiFi Read Length (mean)**: Mean HiFi read length, from barcodes.report.json
- **HiFi Read N50**: N50 of HiFi reads, from barcodes.report.json
- **HiFi Read Count**: Number of HiFi reads, from barcodes.report.json
- **Internal Control Read Length**: Mean internal control read length, from sts.xml ("SampleMean")
- **Internal Control Read Count**: Internal control read count, from sts.xml ("SampleSize")

### 3. Q20% (General FASTQ Quality Metric Example)

Although Q20% is not directly included in PacBio Revio reports, the general formula for Q20% in FASTQ quality statistics is:

$$
\text{Q20\%} = \frac{\text{Number of Q} \geq 20 \text{ bases}}{\text{Total bases}} \times 100
$$

- **Number of Q ≥ 20 bases**: Number of bases with Phred quality score ≥ 20
- **Total bases**: Total number of bases

---
## ⚠️ Troubleshooting

- If the output file already exists, the script will exit to prevent overwriting.
- If sample/barcode matching fails, the script will print an error and remove the incomplete output file.

---
