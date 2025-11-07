# -*- coding: utf-8 -*-
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
import json
import glob
import csv

if len(sys.argv) != 4:
    print("    ")
    print(" ┏────────────────────────────────────────────────────────────┓")
    print(" ┃ Usage: python Revio_run_sav.py \033[94mOption\033[0m \033[93mCSV_PATH\033[0m \033[92mRunDir_PATH\033[0m ┃")
    print(" ┗────────────────────────────────────────────────────────────┛")
    print("    ")
    sys.exit(1)

# arguments
option = int(sys.argv[1]) # 1 = output option1 / 2 = output option2
csv_path = sys.argv[2] # CSV/r84135_20240226_074856_Unaligned_1.csv
run_directories = sys.argv[3] # /ruby/PacBio/Revio/revio_01/r84135_20240226_074856

arg2_run_dir = run_directories.split('/')[5] # r84135_20240226_074856
if option == 1:
    output_file = os.path.join(os.getcwd(), arg2_run_dir + "_Revio_Run_for_PacBio.csv")
elif option == 2:
    output_file = os.path.join(os.getcwd(), arg2_run_dir + "_Revio_Run_for_LIMS.xls")
else:
    print("Invalid option!")
    sys.exit(1)

def where_is_my_data(run_directories, well):
    metadata_paths = []
    sts_paths = []
    report_paths = []
    aws_paths = []

    metadata_paths.extend(glob.glob("{}/{}/metadata/*s?.metadata.xml".format(run_directories, well)))
    sts_paths.extend(glob.glob("{}/{}/metadata/*s?.sts.xml".format(run_directories, well)))
    report_paths.extend(glob.glob("{}/{}/statistics/*s?.reports.zip".format(run_directories, well)))
    aws_paths.extend(glob.glob("{}/{}/hifi_reads/*s?.hifi_reads.bc*.bam".format(run_directories, well)))

    # Replace double slashes with single slash in aws_paths
    aws_paths = [path.replace('//', '/') for path in aws_paths]

    return metadata_paths, sts_paths, report_paths, aws_paths


def extract_sample_stats(sts_path):
    with open(sts_path, 'r') as file:
        xml_string = file.read()
    root = ET.fromstring(xml_string)

    control_read_len_dist = root.find('.//{http://pacificbiosciences.com/PacBioPipelineStats.xsd}ControlReadLenDist')
    sample_size = control_read_len_dist.find('.//{http://pacificbiosciences.com/PacBioBaseDataModel.xsd}SampleSize')
    sample_mean = control_read_len_dist.find('.//{http://pacificbiosciences.com/PacBioBaseDataModel.xsd}SampleMean')

    return sample_size.text, sample_mean.text

def parse_xml_info(metadata_paths):
    tree = ET.parse(metadata_paths)
    root = tree.getroot()
    info_dict = {}

    sample_name = root.find(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}WellSample").attrib["Name"] 
    well_name = root.find(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}ResultsFolder").text.split('/')[1][0:] # r84135_20240311_062102/1_B01/
    well_samples = root.findall(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}WellSample")
    insert_size = root.find(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}InsertSize").text

    for well_sample in well_samples:
        wellsample_name = well_sample.attrib["Name"]
        bio_samples = well_sample.findall(".//{http://pacificbiosciences.com/PacBioSampleInfo.xsd}BioSample")

        for bio_sample in bio_samples:
            biosample_name = bio_sample.attrib["Name"] # S1139
            barcode_name = bio_sample.find(".//{http://pacificbiosciences.com/PacBioSampleInfo.xsd}DNABarcode").attrib["Name"]  # bc2059--bc2059
            unique_id = bio_sample.find(".//{http://pacificbiosciences.com/PacBioSampleInfo.xsd}DNABarcode").attrib["UniqueId"] # uniqueid

            key = (wellsample_name, biosample_name, unique_id)
            info_dict[key] = {'barcode_name': barcode_name, 'unique_id': unique_id}

    return info_dict

if option == 1:
    if os.path.exists(output_file):
        print("The CSV output file already exists !!")
        sys.exit(1)
    with open(output_file, "w") as f:
        f.write("Order Number,Sample Name,Polymerase Yield,Hifi Bases,Polymerase Read Length,Hifi Read Length,Hifi Read N50,Hifi Read Count,Loading P1 %,Internal Control Read Length,Internal Control Read Count,Path of Hifi BAM (AWS s3)\n")

elif option == 2:
    if os.path.exists(output_file):
        print("The XLS output file already exists !!")
        sys.exit(1)
    with open(output_file, "w") as f:
        f.write("\t\t\t\t\t\tPolymerase Read stat\t\t\tSubread\t\t\t\tProductivity Rate\t\t\tInternal Control\t\t\nWell\tOrder Number\tCustomer Name\tApplication Type\tSample Ref\tSample Name\tYield\tN50\tLength\tYield\tN50\tLength\tCount\tP0(%)\tP1(%)\tP2(%)\tInternal Control Read Count\tInternal Control Read Length\n")


with open(csv_path, 'r') as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)
    csv_contents = list(reader)

    for row in csv_contents:
        run_name_in_csv = row[headers.index('RunName')]  # r84135_20240311_062102
        well_in_csv = row[headers.index('Well')]  # 1_B01
        samplename_in_csv = row[headers.index('SampleID')]  # C004C-1
        sampleref_in_csv = row[headers.index('SampleRef')]  # bc2093
        application_type_in_csv = row[headers.index('ApplicationType')]  # Whole Genome Denovo Sequencing
        customer_name_in_csv = row[headers.index('CustomerName')] 
        project = row[headers.index('Project')] 

        metadata_paths, sts_paths, report_paths, aws_paths = where_is_my_data(run_directories, well_in_csv)

        matching_aws_paths = []
        for path in aws_paths:
            if sampleref_in_csv in path:
                matching_aws_paths.append(path)

        if matching_aws_paths:
            aws_path_modified = matching_aws_paths[0].replace('/data/PacBio/Revio/revio_01/', 's3://precise-sequencing-data/').replace('/data/PacBio/Revio/revio_02/', 's3://precise-sequencing-data/').replace('/data/PacBio/Revio/revio_03/', 's3://precise-sequencing-data/')

            print("======================================================================================================================")
            print("* CSV info -> Well Name : {} :: Sample ID : {} :: Barcode Name : {}".format(well_in_csv, samplename_in_csv, sampleref_in_csv))
            print("======================================================================================================================")

            for metadata_path, sts_path, report_path in zip(metadata_paths, sts_paths, report_paths):
                info_dict = parse_xml_info(metadata_path)
                for (xml_wellsample_name, xml_biosample_name, xml_unique_id), xml_info in info_dict.items():

                    if sampleref_in_csv.startswith(xml_info['barcode_name'][:6]):
                        print("* XML Metadata")
                        print("  - Well Sample Name : {}\n  - Sample ID : {}\n  - Barcode Name : {}\n  - UniqueID : {}\n".format(xml_wellsample_name, xml_biosample_name, xml_info['barcode_name'], xml_unique_id))

                        tree = ET.parse(metadata_path)
                        root = tree.getroot()

                        run_name = root.find(".//{http://pacificbiosciences.com/PacBioDataModel.xsd}Run").attrib["Name"]
                        sample_name = root.find(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}WellSample").attrib["Name"]
                        well_name = root.find(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}ResultsFolder").text
                        well_name_in_metadata = well_name.split('/')[1][0:]
                        well_samples = root.findall(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}WellSample")
                        insert_size = root.find(".//{http://pacificbiosciences.com/PacBioCollectionMetadata.xsd}InsertSize").text

                        Internal_Control_Read_Count, Internal_Control_RL = extract_sample_stats(sts_path)
                        Internal_Control_RL = int(float(Internal_Control_RL))

                        with zipfile.ZipFile(report_path, 'r') as zip_ref:
                            barcode_report = xml_unique_id + "/barcodes.report.json"
                            raw_data_report = "raw_data.report.json"
                            ccs_report = "ccs.report.json"
                            loading_report = "loading.report.json"
                            zip_file_list = zip_ref.namelist()

                            Polymerase_Read_stat_Yield = Polymerase_Read_stat_N50 = Polymerase_Read_stat_Length = Subread_Yield = Subread_N50 = Subread_Length = Productivity_Rate_p0p = Productivity_Rate_p1p = Productivity_Rate_p2p = None

                            if raw_data_report in zip_file_list:
                                with zip_ref.open(raw_data_report) as raw_data:
                                    data = json.load(raw_data)
                                    for attribute in data["attributes"]:
                                        if attribute["name"] == "Polymerase Read Bases":
                                            Polymerase_Read_stat_Yield = attribute["value"]
                                        elif attribute["name"] == "Polymerase read length (N50)":
                                            Polymerase_Read_stat_N50 = attribute["value"]
                                        elif attribute["name"] == "Polymerase Read Length (mean)":
                                            Polymerase_Read_stat_Length = attribute["value"]

                            if barcode_report in zip_file_list:
                                with zip_ref.open(barcode_report) as ccs:
                                    data = json.load(ccs)
                                    for attribute in data["attributes"]:
                                        if attribute["id"] == "ccs_demux_stats.total_number_of_ccs_bases":
                                            Subread_Yield = attribute["value"]
                                        elif attribute["id"] == "ccs_demux_stats.ccs_readlength_n50":
                                            Subread_N50 = attribute["value"]
                                        elif attribute["id"] == "ccs_demux_stats.mean_ccs_readlength":
                                            Subread_Length = attribute["value"]
                                        elif attribute["id"] == "ccs_demux_stats.number_of_ccs_reads":
                                            Subread_Count = attribute["value"]

                            if loading_report in zip_file_list:
                                with zip_ref.open(loading_report) as loading:
                                    data = json.load(loading)
                                    for attribute in data["attributes"]:
                                        if attribute["name"] == "Productive ZMWs":
                                            Productive_ZMWs = attribute["value"]
                                        elif attribute["name"] == "Productivity 0":
                                            Productivity_Rate_p0p = attribute["value"]
                                        elif attribute["name"] == "Productivity 1":
                                            Productivity_Rate_p1p = attribute["value"]
#                                            for table in data["tables"]:
#                                                for column in table["columns"]:
#                                                    if column["header"] == "P1 (%)":
#                                                        Loading_p1p = round(column["values"][0], 2)
                                        elif attribute["name"] == "Productivity 2":
                                            Productivity_Rate_p2p = attribute["value"]

                                Productive_ZMWs = float(Productive_ZMWs)
                                Loading_p1p = round((Productivity_Rate_p1p / Productive_ZMWs) * 100, 2)


                        with open(output_file, "a") as f:
                            if option == 1:
                                f.write("{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                                    project, samplename_in_csv,
                                    Polymerase_Read_stat_Yield, Subread_Yield,
                                    Polymerase_Read_stat_Length, Subread_Length, Subread_N50,Subread_Count, Loading_p1p,
                                    Internal_Control_RL, Internal_Control_Read_Count,
                                    aws_path_modified))
                            elif option == 2:
                                f.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                                    well_in_csv, project, customer_name_in_csv,
                                    application_type_in_csv, sampleref_in_csv, samplename_in_csv,
                                    Polymerase_Read_stat_Yield, Polymerase_Read_stat_N50, Polymerase_Read_stat_Length,
                                    Subread_Yield, Subread_N50, Subread_Length, Subread_Count,
                                    Productivity_Rate_p0p, Productivity_Rate_p1p, Productivity_Rate_p2p,
                                    Internal_Control_Read_Count, Internal_Control_RL
                                ))
                        break
        else:
            print("CSV 데이터의 {} 와 일치하는 {} 가 {} 에 존재하지 않습니다." .format(samplename_in_csv, sampleref_in_csv,run_name_in_csv))
            os.remove(output_file)
            sys.exit(1)

if option == 1:
    print("Revio run SAV create completed(option1) !! ::" + " "+sys.argv[2] + ":::" + sys.argv[3])
elif option == 2:
    print("Revio run SAV create completed(option2) !! ::" + " "+sys.argv[2] + ":::" + sys.argv[3])
