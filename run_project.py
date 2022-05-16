from project_configs import Project

# Setup Project and arguments ------------------------------------------------------------------------------------------

project = Project()

download_from_hpc, move_to_preprocessing, run_dcm2niix, run_recon_all = project.process_args()

if not project.is_initialised():
    project.init_project_directory_tree()

# Iterate through all scans for all participants, skipping if data is already downloaded / copied

participant_log = project.get_participant_log()

for wbic_id in sorted(participant_log.keys()):  # TODO: this is sorted on WBIC ID not sub ID. TODO: reorganise log by sub id
    sub_info = participant_log[wbic_id]

    for scan_info in sub_info["scans"].values():

        project.init_logging(scan_info["date"],
                             scan_info["zk_id"])

# Run based on selected options ----------------------------------------------------------------------------------------

        if sub_info["sub_id"] != "sub-002" and scan_info["ses_id"] != "ses-002":
            continue

        if download_from_hpc:
            if not project.download_scans_from_hpc(wbic_id,
                                                   scan_info):
                continue

        if move_to_preprocessing:
            project.move_raw_to_preprocessing(wbic_id, sub_info, scan_info)

        if run_dcm2niix:
            project.run_dcm2niix(sub_ids=[sub_info["sub_id"]],
                                 ses_ids=[scan_info["ses_id"]],
                                 run_ids=["all"],
                                 scan_names=["mp2rage"])

# Run Tests ------------------------------------------------------------------------------------------------------------

project.run_scan_sub_order_tests()
