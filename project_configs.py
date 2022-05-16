from project_master import ProjectMaster
import os
import re

class Project(ProjectMaster):
    """
    Setup the participant information for automatic downloading and preprocessing
    of data for auto_preprocess_wbic_scans.py

    PROJECT SETTINGS:

        base_path:                Base directory for the folder
        project_code:             WBIC project code for the project
        account:                  User ID. This should be the same for the Hivemind / HPC / WBIC
        scanner_format:           Format of scanner output files e.g. ".dcm" for dicom
        server_to_download_to:    name of the server to download scans to from HPC e.g. "abg-hivemind.psychol.private.cam.ac.uk"

        _scan_details:            A dict containing details on the relevant scans to copy from raw_scans to
                                  preprocessing. They key is used as he last entry of the BIDS folder name,
                                  and the task field is used as the task field on the BIDS folder name. The
                                  search_str is the string used to glob.glob to search for the folder in the downloaded
                                  raw_scans. It can be formatted with glob.glob's search options (these are different to
                                  regexp, see the documentation).

                                  An entry exists for mrs_, anat_, func_ mpms_ - if not collecting scans of this type,
                                  use None.

        num_expected_files:       The number of expected files in the raw_scans folder, which would match volumes
                                  for func and spectra for mrs. These are used for tests during copy to preprocessing
                                  dir and if the num_expected_files does not match the actual downlaoded files
                                  a error message is shown on the log.

    PARTICIPANT INPUT:

        The key is the WBIC ID. This is the 5 digit number assigned to the participant by the WBIC.
        It is the code which the HPC / WBIC servers use to indicate the data set.

    """
    def __init__(self):
        super(ProjectMaster, self)

#       Project Settings -----------------------------------------------------------------------------------------------

        self.base_path = "/mnt/zfs/GP_7T-EEG_2022"
        self.project_code = "P00461"
        self.account = "jjz33"
        self.scanner_format = ".dcm"
        self.server_to_download_to = "abg-hivemind.psychol.private.cam.ac.uk"

        self.mrs_scan_details = {"slaser":
                                  {"search_str": "*_sLaser_W*Pad_LongTE",
                                   "task_name": "ori"},
                                 }

        self.func_scan_details = {"fleet_mb": {"search_str": "*_cmrr_mbep2d_bold_FLEET_MB3_run?",
                                               "task_name": "gp"},
                                  "fleet_sbref": {"search_str": "*_cmrr_mbep2d_bold_FLEET_MB3_run?_SBRef",
                                                "task_name": "gp"},
                                  "fleet_mb_inv": {"search_str": "*_cmrr_mbep2d_bold_FLEET_MB3_run?_invPE",
                                               "task_name": "gp"},
                                  "fleet_sbref_inv": {"search_str": "*_cmrr_mbep2d_bold_FLEET_MB3_run?_invPE_SBRef",
                                                   "task_name": "gp"},
                                  }

        self.anat_scan_details = {"mp2rage":
                                      {"search_str": "*mp2rage_sag_p2_0.65mm_UNI_Images",
                                       "task_name": "gp"},
                                  }

        self.mpm_scan_details = None

        self.b0_scan_details = {"b0":
                                      {"search_str": "*gre_b0map_more_slices",
                                      "task_name": "gp"},
                                }

        self.b1_scan_details = {"b1":
                                   {"search_str": "*b1_mapping_2mm",
                                    "task_name": "gp"},
                                }


#       Scan Parameters ------------------------------------------------------------------------------------------------
        self.num_expected_func_files = 178
        self.num_expected_anat_files = 240
        self.num_expected_mrs_files = 136      # TODO: handle scenario with two different MRS (v1 and thalamus) scans
        self.num_expected_mpm_files = None
        self.num_expected_b0_files = 1
        self.num_expected_b1_files = 1

#       Participants ---------------------------------------------------------------------------------------------------

        self._participant_log = {

            "33871": {"sub_id": "sub-001",
                      "lab_id": "3603",
                      "scans": {"scan_1": {"date": "20220414",      # This scan was written off due to poor shimming.
                                           "ses_id": "ses-001",     # We used second slot for testing the shimming.
                                           "zk_id": "zk22w7_044",
                                           "time_start": "09:30",
                                           "flags": [],
                                       },
                                },
                     },
            }

#       Default Attributes ---------------------------------------------------------------------------------------------

        self.docs_path = os.path.join(self.base_path, "docs")
        self.logs_path = os.path.join(self.docs_path, "logs")
        self.download_logs_path = os.path.join(self.logs_path, "download")
        self.slurm_logs_path = os.path.join(self.logs_path, "slurm")
        self.data_path = os.path.join(self.base_path, "data", "mri")
        self.raw_scans_path = os.path.join(self.data_path, "raw_scans")
        self.preprocessing_path = os.path.join(self.data_path, "preprocessing")
