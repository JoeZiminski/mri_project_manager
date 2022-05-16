import re
import copy
import subprocess
import os
import glob
import shutil
from functools import wraps
import logging
import datetime
import paramiko
import argparse
from .analysis import mri_preprocessing_wrappers
from .utils import utils
import nipype.pipeline.engine as pe
from nipype.interfaces.dcm2nii import Dcm2niix

class ProjectMaster():
    """
        USEAGE: subclass this and overwrite all attributes with those relevant to your project.
                See projects_config.py for an example. Run with run_project.py that calls
                class methods to download scans from WBIC to hivemind and organise folder
                structure to BIDS.

                For logging to work, the logger must be initialised (self.init_logging)
                with the scan information. Logs are saved to /docs/logs/

                Key public methods download_scans_from_hpc() and move_raw_to_preprocessing()
                handle downloading and moving scans. Methods on this class typically work on an
                per-scan basis e.g. download a single scan, copy a single scan.

                All existing methods should function well but it is also possible to
                customise functionality by subclassing this class's methods.

        NOTES:
            Access of all mutable class attributes should be through getters which return
            copies.
            No need to initialise the __init__() on this class when subclassing.
        """
    def __init__(self):

        self.raw_scans_path = ""
        self.docs_path = ""
        self.logs_path = ""
        self.download_logs_path = ""
        self.slurm_logs_path = ""
        self.data_path = ""
        self.raw_scans_path = ""
        self.preprocessing_path = ""

        self.base_path = ""
        self.project_code = ""
        self.account = ""
        self.server_to_download_to = ""

        self.mrs_scan_details = None
        self.func_scan_details = None
        self.anat_scan_details = None
        self.mpm_scan_details = None
        self.b0_scan_details = None
        self.b1_scan_details = None

#       Scan Parameters ------------------------------------------------------------------------------------------------

        self.num_expected_func_files = None
        self.num_expected_anat_files = None
        self.num_expected_mrs_files = None
        self.num_expected_mpm_files = None
        self.num_expected_b0_files = None
        self.num_expected_b1_files = None

#       Participants ---------------------------------------------------------------------------------------------------

        self._participant_log = {

        "XXXXX": {"sub_id": "sub-XXX",
                  "lab_id": "XXXX",
                  "zk_id": "zkXXwX_XXX"
                  },
     }

# ----------------------------------------------------------------------------------------------------------------------
# Public Methods
# ----------------------------------------------------------------------------------------------------------------------

# Pulling Data from HPC and organising Project Structure
# ----------------------------------------------------------------------------------------------------------------------

    def download_scans_from_hpc(self, wbic_id, scan_info):
        """
        Download a scan from the WBIC to the HPC with WBIC's dcmconv.pl function. This requires a folder
        called "wbic-data" on your rds-ds/user/username/hpc-work HPC directory.

        This data is then this data from the HPC to the hivemind, under the project dir /raw_scans
        and delete from the HPC.

        Testing logs the nubmer of files in each downloadchecks none of the folders are empty.
        All download / copy processes are logged to the /docs/logs log for this scan (see init_logging).
        """
        if self.scan_already_downloaded(scan_info["zk_id"]):
            return False

        self.log(None, "Pulling scans from HPC...")

        self._pull_scans_from_wbic_to_hpc(wbic_id,
                                          scan_info["date"])

        self._pull_scans_from_hpc_to_hivemind(wbic_id,
                                              scan_info["date"])

        self._extract_wbic_data_to_zk_folder(wbic_id,
                                               scan_info["zk_id"])

        download_failed, __ = self._test_download(scan_info["zk_id"],
                                                  save_to_log=True)
        if download_failed:
            return False

        return True

    def move_raw_to_preprocessing(self, wbic_id, sub_info, scan_info):
        """
        Move the relevant raw scans (as specified in self.XXX_scan_details) for a scan
        from the raw_scans dir to the preprocessing/sub/ses dir. If a ses dir already exists
        in preprocessing/sub, it will be skipped.

        Make a session directory in the preprocessing/sub dir for the
        session if it does not exist. Then, the raw_scans dir is searched with
        glob.glob (search string specified in the XXX_scan_details attribute)
        and matches copied to the relevant folder.

        Any runs specified in the "flags" entry of the "scan" dict in
        the participant log will be ignored (see self.participant_log in
        project_configs.py).
        """
        ses_exists = self._check_ses_exists_mkdir_if_not(sub_info["sub_id"], scan_info, log=True)

        for scan_type in ["mrs", "func", "anat", "mpm", "b0", "b1"]:  # TODO: MOVE TO CONFIGS

            if self.check_if_scan_type_is_in_ses_folder(sub_info["sub_id"], scan_info["ses_id"], scan_type):
                continue

            self._copy_data_to_preprocessing(scan_type,
                                             scan_info,
                                             sub_info)

        self._dump_info_file_in_session_dir(wbic_id,
                                            scan_info,
                                            sub_info)
        return True

    def run_scan_sub_order_tests(self, assert_=False):
        """
        Test all datetimes and sub ids in the session text files
        match throughout the project.

        Subjects should be in date order (e.g. the scan datetime for
        sub-001 ses-001 should not be before sub-002 ses-001)

        Sessions for a sub should also be in date order (e.g. sub-001
        ses-001 should not be before sub-001 ses-002)
        """
        error_log = self._test_project_scan_and_ses_ids_match_date_order()

        error_log = "All Tests Passed" if not any(error_log) else error_log
        self.log("Testing sub and ses IDS match datetimes",
                 error_log)

        if assert_:
            assert error_log == "All Tests Passed", error_log

# Helpers / Getters
# ----------------------------------------------------------------------------------------------------------------------

    def get_participant_log(self):
        """
        Test the participant log to ensure all inputs are formatted correctly
        before returning a copy.
        """
        participant_log = copy.deepcopy(self._participant_log)

        self._test_participant_log(participant_log)

        return participant_log

    def is_initialised(self):
        """
        Check the project directory structure has been initialised
        """
        return os.path.isdir(self.base_path)

    def init_project_directory_tree(self):
        """
        Make all the base directories for the project.
        NOTE: _mkdir will init dir tree, but verbose for clarity here.
        """
        for path in [self.base_path, self.docs_path, self.logs_path,
                     self.download_logs_path, self.slurm_logs_path, self.data_path,
                     self.raw_scans_path, self.preprocessing_path]:
            self._mkdir(path)

    def init_logging(self, date_, zk_id, logging_path=None, log_filename=None):  # TODO: this was originally for downloading only but has been extended. could be neated up with download init calling the relevant filename rather than it assumed as default ehre
        """
        Initialise the logger for the current scan. All logging
        (self.log()) will then be saved to the log in /docs/logs
        with filename formatted "date_zk_id.log".
        """
        if not logging_path:
            logging_path = self.download_logs_path

        if not log_filename:
            log_filename = "_".join([date_, zk_id]) + ".log"

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        log_filename = "_".join([date_, zk_id]) + ".log"
        logging.basicConfig(filename=os.path.join(self.download_logs_path, log_filename),
                            format="%(message)s",
                            level=logging.DEBUG)

        self.log(None, "Logger Initialised...")

    def log(self, title, message):
        """
        Log the message, if title is not None inserted it with banner
        seperated by line breaks. See init_logging for setup.
        INPUTS: title (str) or None, message (str)
        """
        if title:
            now = datetime.datetime.now()
            title = " ".join(["\n",
                              now.ctime(),
                              title])
            message = title + " -------------------------------------------------------------------------------------" \
                              "\n\n" + message

        logging.debug(message)

    def scan_already_downloaded(self, zk_id):
        """
        Download considered successful if data is moved from WBIC
        code folder to zk folder after download as it is the last
        process in self.download_scans_from_hpc()
        """
        putative_zkid_scan_path = os.path.join(self.raw_scans_path,
                                               zk_id)
        return os.path.isdir(putative_zkid_scan_path)

    def get_all_subs_and_ses_in_preprocessing(self):
        """
        Return dict in format {sub-001: [ses-001, ses-002...],
                               sub-002, [ses-...]}
        """
        result = {}

        all_subs_paths = glob.glob(
            os.path.join(self.preprocessing_path, "sub*"))

        for sub_path in all_subs_paths:
            all_session_paths = glob.glob(
                os.path.join(sub_path, "ses-*"))
            sessions = [os.path.basename(ses_path) for ses_path in all_session_paths]
            sub = os.path.basename(sub_path)

            result.update({sub: sessions})

        return result

# ----------------------------------------------------------------------------------------------------------------------
# Private Methods
# ----------------------------------------------------------------------------------------------------------------------

# Pulling Data from HPC
# ----------------------------------------------------------------------------------------------------------------------

    def _pull_scans_from_wbic_to_hpc(self, wbic_id, date_):
        """
        SSH connect to to the HPC and use dcmconv.pl to download scans from WBIC to
        a HPC folder /rds-d5/user/USERNAME/hpc-work/wbic-data.
        """
        command = "module load wbic && " \
                  "cd /rds-d5/user/{0}/hpc-work/wbic-data && " \
                  "/usr/local/software/wbic/bin/dcmconv.pl "  \
                  "-remoteae {1} -id {2} -date {3} -makedir -outtype dicom10 -direct -info -all".format(self.account,
                                                                                                        self.project_code,
                                                                                                        wbic_id,
                                                                                                        date_)
        stdout = self._run_ssh_to_hpc(command)

        self.log("pulled scans from wbic to hpc ",
                 command)
        self.log(None,
                 "project: {0}, wbic_id {1}, date: {2} \n {3}".format(self.project_code,
                                                                      wbic_id,
                                                                      self.account,
                                                                      stdout))

    def _pull_scans_from_hpc_to_hivemind(self, wbic_id, date_):
        """
        SSH connect to HPC and download scans to hivemind. See
        _pull_scans_from_wbic_to_hpc()
        """
        command = "rsync -rsh /rds-d5/user/{0}/hpc-work/wbic-data/{1} {0}@{2}:{3} && " \
                  "rm -rf /rds-d5/user/{0}/hpc-work/wbic-data/{1}".format(self.account,
                                                                          wbic_id,
                                                                          self.server_to_download_to,
                                                                          self.raw_scans_path)

        stdout = self._run_ssh_to_hpc(command)

        self.log("pulled scans from wbic to hpc ",  # NEATEN
                 command)
        self.log(None,
                 "wbic_id {0}, date: {1}, folder: {2} \n {3}".format(wbic_id,
                                                                     date_,
                                                                     self.raw_scans_path,
                                                                     stdout))

    def _run_ssh_to_hpc(self, command):
        """
        Run the command on an SSH connection to the HPC. Try 5 times to connect
        and if not sucessful, assert. If successful, return the stdout from the
        ssh connection.
        """
        max_attempts = 5
        for attempt in range(max_attempts):

            client = self._setup_ssh_to_hpc()

            stdin, stdout, stderr = client.exec_command(command)
            stdout_byte = stdout.read()
            exit_code = stdout.channel.recv_exit_status()  # must come after stdout.read() for large output

            client.close()
            if exit_code == 0:
                return stdout_byte.decode("utf-8")
            else:
                if attempt == 4:
                    error = "subprocess failed in {0} attempts " \
                                  "for command: {1} with error {2}".format(max_attempts,
                                                                           command,
                                                                           stderr.read().decode("utf-8"))
                    self.log("SSH ERROR", error)
                    assert False, error

    def _setup_ssh_to_hpc(self):
        """
        Use paramiko to generate an ssh connection from hivemind to HPC.
        The SSH keys must already be setup and reside in /home/account/.ssh.
        """
        key = paramiko.RSAKey.from_private_key_file("".join(["/home/",
                                                             self.account,
                                                             "/.ssh/id_rsa"]))
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname="login.hpc.cam.ac.uk", username=self.account, pkey=key)

        return client

    def _extract_wbic_data_to_zk_folder(self, wbic_id, zk_id):
        """
        Extract data after downloaded from wbic to ABL standard form with
        zk_id for backups. This is /raw_scans/zk_id/zk_id/scan_dirs.

        For full backup, the common protocol sheet must be included in the
        first level zk_id dir and the second level zk_id dir zipped.
        """

        zk_id_path = os.path.join(self.raw_scans_path, zk_id, zk_id)

        wbic_scan_files_path = glob.glob(os.path.join(self.raw_scans_path, wbic_id, "*"))[0]

        self.log("Extract wbic data to zk folder",
                 "zk_id_path: " + zk_id_path + "\n "
                 "wbic_scan_files_path: " + wbic_scan_files_path)

        self._mkdir(zk_id_path)
        self._move(wbic_scan_files_path,
                   zk_id_path,
                   move_contents_only=True)

        shutil.rmtree(os.path.join(self.raw_scans_path, wbic_id))

# Copying data from raw scans to preprocessing
# ----------------------------------------------------------------------------------------------------------------------

    def _check_ses_exists_mkdir_if_not(self, sub_id, scan_info, log=False):
        """
        Session is assumed to exist if a ses-XXX dir is found in preprocessing/sub-XXX dire
        return True / False if session does / does not exist.
        Log result if flag TRUE.
        """
        ses_path = os.path.join(self.preprocessing_path,
                                sub_id,
                                scan_info["ses_id"])
        ses_exists = os.path.isdir(ses_path)

        if log:
            if ses_exists :
                pass
  #              self.log("Session already exists", TODO: think about this, can't log beause we want to skip scans when calling --move_to_preprocessing silently. But it is useful to have this log?
   #                      "{0} for {1} was not created as it already exists".format(scan_info["ses_id"],
    #                                                                               sub_id))
            else:
                self.log("Creating new session file",
                         "existing {0} dir for {1}, {2} was not found. Creating dir.".format(sub_id,
                                                                                             scan_info["ses_id"],
                                                                                             scan_info["zk_id"]))
        return ses_exists

    def check_if_scan_type_is_in_ses_folder(self, sub_id, ses_id, scan_type):
        """
        Check if the scan is already copied into the ses path e.g. preprocessing/sub-001/ses-001/func
        Used to skip already-downloaded scans
        """
        scan_type_path = os.path.join(self.preprocessing_path,
                                     sub_id,
                                     ses_id,
                                     scan_type)
        return os.path.isdir(scan_type_path)

    def _copy_data_to_preprocessing(self, scan_type, scan_info, sub_info):
        """
        Function to coordinate data copying from raw_scans to BIDS in preprocessing.
        see self.move_raw_to_preprocessing()

        scan_type: "mrs", "func", "anat" or "mpm", "b0", "b1"

        TODO: bit repetitive as if raw scans dir is not present it will log the same response
        many times, but do not want to take this a level up to download_and_copy as bnecomes too verbose.
        """
        scan_details, num_expected_files = self._get_scan_details_and_expeced_num(scan_type)

        if scan_details:

            raw_scan_folder = os.path.join(self.raw_scans_path, scan_info["zk_id"])

            if os.path.isdir(raw_scan_folder):

                self.log("Copying raw {0} data to preprocessing folder".format(scan_type),
                         "Copying: {0}, {1}, {2}, {3}\n".format(scan_type,
                                                                scan_info["zk_id"],
                                                                sub_info["sub_id"],
                                                                scan_info["ses_id"]))

                self._copy_data_from_raw_scans_to_preprocessing(scan_info,
                                                                sub_info["sub_id"],
                                                                scan_details,
                                                                scan_type,
                                                                num_expected_files)
            else:
                self.log("Copying raw {0} data to preprocessing folder".format(scan_type),
                         "no raw scans found for {0}, no data copied".format(scan_info["zk_id"]))


    def check_for_duplicate_str_in_list(self, list_):
        """
        Set() function will remove any duplicates
        """
        return len(list_) == len(set(list_))


    def _copy_data_from_raw_scans_to_preprocessing(self,  # TODO: will pprobably end up needing to write a function to unpack scan details
                                                   scan_info,
                                                   sub_id,
                                                   scan_details,
                                                   data_name,
                                                   num_expected_files):
        """
        see  see self.move_raw_to_preprocessing()
        """
        preprocessing_raw_data_path = os.path.join(self.preprocessing_path,
                                                   sub_id,
                                                   scan_info["ses_id"],
                                                   data_name, "raw")

        for scan_name in scan_details.keys():

            sequence_search_str = scan_details[scan_name]["search_str"]
            task_name = scan_details[scan_name]["task_name"]

            search_path_str = os.path.join(self.raw_scans_path,
                                           scan_info["zk_id"], scan_info["zk_id"],  # zk_id twice for backups organisation
                                           sequence_search_str)

            ordered_scan_run_paths = sorted(glob.glob(search_path_str))

            if any(ordered_scan_run_paths) and \
                    self.check_for_duplicate_str_in_list(ordered_scan_run_paths):
                self.log(None, "WARNING! Duplicate run detected in raw scans for " + scan_name)

            saved_run_idx = 0
            for true_run_idx, raw_data_to_copy in enumerate(ordered_scan_run_paths):  # TODO: own function?

                if "flags" in scan_info:
                    if self._skip_run_based_on_flags(scan_info, true_run_idx, data_name):
                        continue

                bids_file_name = self._get_bids_filename(sub_id, scan_info["ses_id"], task_name,
                                                         saved_run_idx, scan_name)
                destination_path = os.path.join(preprocessing_raw_data_path,
                                                bids_file_name)

                self._copy_dir_contents(raw_data_to_copy,
                                        destination_path)

                self._test_and_log_expected_file_number(destination_path,
                                                       num_expected_files)

                saved_run_idx += 1

    def _skip_run_based_on_flags(self, scan_info, run_idx, data_name):  # TEST!!!!
        """
        Runs to skip copying are set in the "flags" entry of the "scan" dict field
        in self.participant log. All
        """
        scan_specific_flags = [flag for flag in scan_info["flags"] if data_name in flag]

        if any(scan_specific_flags):

            runs_to_ignore = [flag.split("_")[2].lstrip("0") for flag in scan_specific_flags]  # ignore leading zeros in case the user input as "001" format

            if str(run_idx + 1) in runs_to_ignore:  # TODO: does this fail the case where run=1 and runs to ingore contains ["10"]. Shouldnt but check

                self.log(None,
                          "Did not copy run {0} for scan {1} "
                          "based on the flags {2}".format(run_idx + 1,
                                                          scan_info["zk_id"],
                                                          scan_specific_flags))
                return True
        return False

    def _dump_info_file_in_session_dir(self, wbic_id, scan_info, sub_info):
        """
        Write a file to a ses-XXX dir containing all information about the
        sub / session. This file is used for tests on the scan datetime.
        """
        ses_path = os.path.join(self.preprocessing_path,
                                sub_info["sub_id"],
                                scan_info["ses_id"])

        if os.path.isdir(ses_path):

            info = "project_code: {0}\n" \
                   "wbic_id: {1}\n" \
                   "sub_id: {2}\n" \
                   "ses_id {3}\n" \
                   "zk_id: {4}\n" \
                   "scan_date: {5}\n" \
                   "scan_start_time: {6}\n" \
                   "\nDo not edit this file".format(self.project_code,
                                                    wbic_id,
                                                    sub_info["sub_id"],
                                                    scan_info["ses_id"],
                                                    scan_info["zk_id"],
                                                    scan_info["date"],
                                                    scan_info["time_start"])

            filename = scan_info["ses_id"] + "_info.txt"

            with open(os.path.join(
                                   ses_path, filename), "w") as file:
                file.write(info)

# ----------------------------------------------------------------------------------------------------------------------
# Preprocessing - Run Commands
# ----------------------------------------------------------------------------------------------------------------------

    def run_recon_all(self, sub_ids, ses_ids, run_ids, scan_names, scan_types, **kwargs):
        """
        """
        run_func = self.get_recon_all_func(kwargs)
        self._run_preprocessing_job(run_func, sub_ids, ses_ids, run_ids, scan_names, scan_types)

    def run_dcm2niix(self, sub_ids, ses_ids, run_ids, scan_names, scan_types, **kwargs):  # need to be careful specified keyworks do not overlap with nipype keywords
        """
        """
        run_func = self.get_dcm2niix_func(kwargs)
        self._run_preprocessing_job(run_func, sub_ids, ses_ids, run_ids, scan_names, scan_types)

    def get_recon_all_func(self, kwargs):  # TODO: use ke and mengxin options!
        """
        """
        def run_recon_all_func(preprocessing_path, sub_id, ses_id, scan_types, bids_name, kwargs=kwargs):  # TODO: ensure scan type is anat
            from nipype.interfaces.freesurfer import ReconAll
            source_dir = os.path.join(preprocessing_path, sub_id, ses_id, scan_types, 'nii', bids_name)  # TODO: check if file already exists! for all!

            reconall_node = pe.Node(name='reconall_node',
                                    interface=ReconAll(subject_id=sub_id,
                                                       directive="all",
                                                       subjects_dir=source_dir,
                                                       T1_files=os.path.join(source_dir, bids_name + ".nii.gz")))

            workflow = pe.Workflow(name='reconall')
            workflow.base_dir = source_dir
            workflow.add_nodes([reconall_node])
            workflow.run(plugin="SLURMGraph", plugin_args = {'dont_resubmit_completed_jobs': True})

        return run_recon_all_func

    def get_dcm2niix_func(self, kwargs):
        """
        """
        def run_dcm2niix_func(preprocessing_path, sub_id, ses_id, scan_types, bids_name, kwargs=kwargs):

            source_dir = os.path.join(preprocessing_path, sub_id, ses_id, scan_types, 'raw', bids_name)
            output_dir = os.path.join(preprocessing_path, sub_id, ses_id, scan_types, 'nii', bids_name)
            self._mkdir(output_dir)

            out_filename = bids_name if "out_filename" not in kwargs else kwargs["out_filename"]
            dcm2niix_node = pe.Node(name='dcm2niix_node',
                                    interface=Dcm2niix(out_filename=out_filename,
                                    source_dir=source_dir,
                                    output_dir=output_dir))

            workflow = pe.Workflow(name='dcm2niix')
            workflow.base_dir = output_dir
            workflow.add_nodes([dcm2niix_node])
            workflow.run(plugin="SLURMGraph", plugin_args = {'dont_resubmit_completed_jobs': True})

        return run_dcm2niix_func

# ----------------------------------------------------------------------------------------------------------------------  # TODO: unit test
# Preprocessing - Run Commands
# ----------------------------------------------------------------------------------------------------------------------

    def _run_preprocessing_job(self, command_func, sub_ids, ses_ids, run_ids, scan_names, scan_types, slurm=True, parallel=False, log=False, **kwargs):  # TODO: rename scan_type to scan_types
        """
        note will ignore sessions that do not exist. Make a log?
        """
        # TODO: cannot run parallel and without slurm
        sub_ids, ses_ids, run_ids, scan_names, scan_types = self._process_all_job_args(sub_ids, ses_ids, run_ids, scan_names, scan_types)
        nii_or_raw = "raw" if "dcm2nii" in command_func.__name__ else "nii"

        for sub_id in sub_ids:

            if ses_ids == ["all"]:
                ses_ids = self.get_all_ses_for_sub(sub_id)

            for ses_id in ses_ids:

                if not self.sub_has_ses(sub_id, ses_id):  # TEST
                    continue

                for scan_type in scan_types:

                    for scan_name in scan_names:

                        if not self.ses_has_at_least_one_scan_name_run(sub_id, ses_id, scan_type, nii_or_raw, scan_name):
                            continue

                        if run_ids == ["all"]:
                            run_ids = self.get_all_runs_in_folder(sub_id, ses_id, scan_type, nii_or_raw, scan_name)

                        for run_id in run_ids:
                            if not self.ses_has_run(sub_id, ses_id, scan_type, nii_or_raw, scan_name, run_id):
                                continue

                            scan_details, __ = self._get_scan_details_and_expeced_num(scan_type)
                            task_name = scan_details[scan_name]["task_name"]  # mixing tasks and scan_names is not supported
                            run_idx = int(run_id[4:]) - 1  # TODO: fix _get_bids_filename?
                            bids_name = self._get_bids_filename(sub_id, ses_id, task_name, run_idx, scan_name)

                            ##### NEW FUNCTION
                            command = command_func(self.preprocessing_path, sub_id, ses_id, scan_type, bids_name)  # TODO: pipe output

                  #          if log_filepath:
                   #             open_type = "w" if not os.path.isfile(log_filepath) else "a"
                    #            with open(log_filepath, open_type) as f:
                     #               f.write(output_str)
                      #              f.write("\n")
                       #         f.close()  # necessary?
                        #    else:
                         #       print(output_str)

    #                        if slurm:
     #                           all_commands_to_run += command + " &\n"
      #                          ntasks += 1
       #                     else:
        #                        log_filepath = os.path.join(self.preprocessing_path, sub_id, "mri_command_logs.log") if log else None
         #                       self._run_subprocess(command, log_filepath)

         #   if slurm:
          #      job_name = "recon_all" + "_" + datetime.datetime.now().strftime("%m%d%Y_%H%M")  # TODO: FIX NAME !!
           #     utils.run_command_with_slurm(job_name, self.slurm_logs_path, self.slurm_logs_path, ntasks, all_commands_to_run)

    def _run_subprocess(self, command, log_filepath=False):  # TODO: MOVE TO UTILS, CHANGE NAME OF UTILS MODULE TO ONE BASED AROUND RUNNING COMMANDS.
        """
        DOC where from
        """
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        while True:
            output = process.stdout.readline()

            if output == '' and process.poll() is not None:
                break

            if output:
                output_str = output.strip().decode()

                if log_filepath:
                    open_type = "w" if not os.path.isfile(log_filepath) else "a"
                    with open(log_filepath, open_type) as f:
                        f.write(output_str)
                        f.write("\n")
                    f.close()  # necessary?
                else:
                    print(output_str)
        rc = process.poll()
        return rc

# Check Arguments ------------------------------------------------------------------------------------------------------

    def _process_all_job_args(self, sub_ids, ses_ids, run_ids, scan_names, scan_types):  # CHANGE RUN NUM TO RUN_ID
        """

        """
        for id in [sub_ids, ses_ids, run_ids, scan_names]:
            assert type(id) == list, "Input type must be list for sub, ses, run and scan names"

        sub_ids = self.check_and_process_sub_args(sub_ids)
        ses_ids = self.process_mixed_list_of_ids(ses_ids, "ses-")
        run_ids = self.process_mixed_list_of_ids(run_ids, "run-")

        if scan_types == ["all"]:
            scan_types = ["func", "anat", "b0", "b1"]  # TODO: move to configs

        return sub_ids, ses_ids, run_ids, scan_names, scan_types

    def check_and_process_sub_args(self, sub_ids):
        all_subs = [val["sub_id"] for val in self._participant_log.values()]
        all_subs.reverse()  # comes out high-to-low from dict

        if sub_ids[0] == "all":
            sub_ids = all_subs

        all_sub_ids = self.process_mixed_list_of_ids(sub_ids, "sub-")
        assert set(all_subs).intersection(set(all_sub_ids)), "Ensure specified sub id are in the participant log"

        return all_sub_ids

    def process_mixed_list_of_ids(self, list_of_ids, prefix):
        """
        process mixed list e.g. list_of_ids=["sub-001", "2", "5:10"]
        prefix is the id prefix e.g. "sub-", "ses-", "run-"

        if id is in the form "3" or "5:6" expand_range_job_input returns
        the fully formatted id e.g [sub-003] or ["sub-005", "sub-006"]
        otherwise the user-input str (e..g "sub-010" is checked for formatting

        igore "all" keyword as this is handlede later
        """
        if list_of_ids[0] == "all":
            return list_of_ids

        all_ids = []
        for id in list_of_ids:
            if ":" in id or id.isnumeric():
                id = self.expand_range_job_input(id, prefix)
            else:
                assert self._ids_properly_formatted([id], prefix), "Ensure " + prefix + "are properly formatted"
            all_ids.append(id) if type(id) != list else all_ids.extend(id)  # user input is str, format input is list

        return all_ids

    def _ids_properly_formatted(self, test_ids, prefix):
        """
        Check that all ids in a list are properly formatted, could be:
        prefix len = num chars in prefix i.e. "sub-" == 4
        num_start:num_start + 2 == expected number, hard coded at 3 e.g. sub-001
        sub_id e.g. sub-001, first_4_chars="sub-"

        ses_id e.g ses-001, first_4_chars="ses-"
        """
        prefix_len = len(prefix)
        id_len = len(prefix) + 3
        num_start = prefix_len + 1

        is_formatted = []
        for id in test_ids:
            is_formatted.append(len(id) == id_len and id[0:prefix_len] == prefix and id[num_start:num_start+2].isnumeric())

        return all(is_formatted)

    def expand_range_job_input(self, id_range, prefix):
        """
        id_range: specified as list "X:X" e.g. ["1:5"] or single nuimber "!"
        prefix: prefix for the info type, e.g. "sub-", "ses-", "run-"
        also works for single number input.
        """
        if ":" in id_range:
            partitioned_ids = id_range.partition(":")
            assert len(partitioned_ids) == 3, "ensure input contains only a single : e.g. 1:5"
            first_id, __, last_id = partitioned_ids
        else:
            first_id = last_id = id_range # if it is just a number

        ids = []  # cannot use list comp because of prefix var scope (I don't think)
        for num in range(int(first_id), int(last_id) + 1):
            ids.append(prefix + "{:03}".format(num))

        return ids

# Check sessions / runs exist ------------------------------------------------------------------------------------------

    def sub_has_ses(self, sub_id, ses_id):
        return os.path.isdir(
                             os.path.join(self.preprocessing_path, sub_id, ses_id))

    def ses_has_run(self, sub_id, ses_id, scan_type, nii_or_raw, scan_name, run_id):
        run_ids = self.get_all_runs_in_folder(sub_id, ses_id, scan_type, nii_or_raw, scan_name)
        return run_id in run_ids

    def get_all_runs_in_folder(self, sub_id, ses_id, scan_type, nii_or_raw, scan_name):
        scans_dir = os.path.join(self.preprocessing_path, sub_id, ses_id, scan_type, nii_or_raw)  # DUPLY
        runs_fullpath = glob.glob(scans_dir + "/*" + scan_name)
        runs_filenames = [os.path.split(fullpaths)[-1] for fullpaths in runs_fullpath]
        run_ids = [filename.split("_")[3] for filename in runs_filenames]  # bids means that run num is 4th entry in filename separated by _
        return run_ids

    def ses_has_at_least_one_scan_name_run(self, sub_id, ses_id, scan_type, nii_or_raw, scan_name):
        """
        Check a run of scans has at least oen scan with the scan name e.g.
        scan_type = "func"
        scan_name = "vaso"
        Check there is at least one run with bids foldername ending in vaso if the dir
        preprocessing/sub_id/ses_id/scan_type/..
        """
        scans_dir = os.path.join(self.preprocessing_path, sub_id, ses_id, scan_type, nii_or_raw)
        runs = glob.glob(scans_dir + "/*" + scan_name)  # DUPLY
        return any(runs)

    def get_all_ses_for_sub(self, sub_id):
        ses_full_filepaths = glob.glob(os.path.join(self.preprocessing_path, sub_id, "*"))
        ses_folders = [os.path.split(filepath)[-1] for filepath in ses_full_filepaths]
        ses_folders.reverse()
        return ses_folders

# ----------------------------------------------------------------------------------------------------------------------
# Utils - Can move these to dedicated module when large enough
# ----------------------------------------------------------------------------------------------------------------------

    def process_args(self):
        """
        Process the flags for run_project.py. See project README.md for details on usage.
        TODO: can move
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-download_from_hpc", "--download_from_hpc",
                            action="store_true",
                            help="Flag to download raw scans from HPC to the raw scans folder and format for ABL backups")

        parser.add_argument("-move_to_preprocessing", "--move_to_preprocessing",
                            action="store_true",
                            help="Flag to copy relevant scan files from raw scans to preprocessing directory, "
                                 "see project configs, 'scan_details' fields for more info. ")

        parser.add_argument("-run_recon_all", "--run_recon_all",
                            action="store_true",
                            help="Flag to run Freesurfers recon_all command on anatomical scans")

        parser.add_argument("-run_dcm2niix", "--run_dcm2niix",
                            action="store_true",
                            help="Flag to run dcm2niix on all scans")

        args_dict = parser.parse_args()

        args = [v for __, v in sorted(vars(args_dict).items())]  # sort dict alphabetically, be careful with order if adding new flags
        download_from_hpc, move_to_preprocessing, run_dcm2niix, run_recon_all = args  # could * expand, but better to be explicit about output order

        return download_from_hpc, move_to_preprocessing, run_dcm2niix, run_recon_all


    def _get_scan_details_and_expeced_num(self, scan_type):
        scans_infos = {"mrs": [self.mrs_scan_details, self.num_expected_mrs_files],
                       "func": [self.func_scan_details, self.num_expected_func_files],
                       "anat": [self.anat_scan_details, self.num_expected_anat_files],
                       "mpm": [self.mpm_scan_details, self.num_expected_anat_files],
                       "b0": [self.b0_scan_details, self.num_expected_b0_files],
                       "b1": [self.b1_scan_details, self.num_expected_b1_files],
        }
        scan_details, expected_num_files = scans_infos[scan_type]

        return scan_details, expected_num_files

    def _copy_dir_contents(self, source_path, destination_path, log=True):
        """
        Call linux os directly to copy files and log the process.

        Could not get shutil.copy / copytree to work, "operation not permitted".
        """
        self._mkdir(destination_path)
        source_path_contents = source_path + "/*"
        subprocess.run(" ".join(["cp", source_path_contents, destination_path]),
                       shell=True)

        if log:
            self.log(None,
                     "copied from: {0} \ncopied to: {1}".format(source_path_contents,
                                                                destination_path))

    def _move(self, dir_to_move, destination_path, move_contents_only=False):
        """
        Call linux os directly to move files and log the results.
        """
        if move_contents_only:
            dir_to_move = dir_to_move + "/*"

        subprocess.run([" ".join(["mv", dir_to_move, destination_path])],
                       shell=True)

        self.log(None,
                 "moved from: " + dir_to_move +
                 "\nmoved to: " + destination_path)

    def _mkdir(self, dir):
        if not os.path.isdir(dir):
            os.makedirs(dir)

    def _get_bids_filename(self, sub_id, ses_id, task_name, run_idx, scan_name):
        """
        Return a filename in BIDS format e.g:
            sub-002_task-ori_run-1_bold_ptx
        """
        run_name = "run-{:03}".format(int(run_idx) + 1)
        bids_file_name = "_".join([sub_id, ses_id, "task-" + task_name, run_name, scan_name])
        return bids_file_name

    def _extract_date_time_from_sub_info_file(self, full_filepath):
        """
        Date the date and time from session ses-XXX_info.txt file and return as python datetime
        """
        with open(full_filepath, "r") as file:
            data = file.read()

        search_date = re.search(r"\d{8}", data)
        search_time = re.search(r"\d\d:\d\d", data)

        combined_date_time = search_date.group() + " " + search_time.group()
        scan_datetime = datetime.datetime.strptime(combined_date_time, "%Y%m%d %H:%M")

        return scan_datetime

    def _glob_one_result(self, search_str):
        """
        Return glob checked for only one result - log and error if less or more.
        """
        path = glob.glob(search_str)

        if len(path) != 1:
            error_message =" ".join(["ERROR: less / more than one file found for ",
                                     search_str])
            self.log("ERROR",
                     error_message)
            assert False, error_message

        return path[0]

# ----------------------------------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------------------------------

    def _test_participant_log(self, participant_log):  # TODO: why not on class attribute?
        """
        Test all entries on the participant  are correct format
        """
        self._test_no_scan_id_are_duplicate(participant_log)

        for wbic_id in participant_log.keys():

            assert wbic_id.isnumeric(), "WBIC ID must be all numbers for wbic_id: " + wbic_id
            assert len(wbic_id) == 5, "WBIC ID must be 5 digits for wbic_id: " + wbic_id

            sub_id = participant_log[wbic_id]["sub_id"]
            assert len(sub_id) == 7, "sub ID is too long (should be sub-XXX) for wbic_id: " + wbic_id
            assert sub_id[0:4] == "sub-", "sub_id does not start with 'sub-' for wbic_id: " + wbic_id
            assert sub_id[4:7].isnumeric(), "sub_id must end in three numbers for wbic_id: " + wbic_id

            lab_id = participant_log[wbic_id]["lab_id"]
            assert len(lab_id), "lab_id is not 4 digits for wbic_id: " + wbic_id
            assert lab_id.isnumeric(), "lab_id is not intergers for wbic_id: " + wbic_id

            for scan_info in participant_log[wbic_id]["scans"].values():

                zk_id = scan_info["zk_id"]

                assert len(zk_id) == 10, "zk_id is not 10 numbers / letters long for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)
                assert zk_id[7:10].isnumeric(), "zk id does not end in 3 numbers for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)

                pattern = re.compile("zk\d\dw[3, 7]_\d\d\d")
                assert pattern.match(zk_id), "zk_id is in the wrong format for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)

                ses_id = scan_info["ses_id"]  # TODO: duplicated from new method ##############################################################################
                assert ses_id[0:4] == "ses-", "ses id does not begin 'ses-' for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)
                assert ses_id[4:7].isnumeric(), "last three digits for ses_id are not numeric for for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)

                date_ = scan_info["date"]
                date_format = "%Y%m%d"
                assert type(date_) == str, "scan date must be string " + zk_id
                assert datetime.datetime.strptime(date_, date_format), "scan date must be formatted YYYYMMDD for " \
                                                                       "for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                            zk_id)

                time_start = scan_info["time_start"]
                pattern = re.compile("\d\d:\d\d")
                assert pattern.match(time_start), "start_time is not formatted corrected for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                             zk_id)

                if "flags" in scan_info:
                    for flag in scan_info["flags"]:
                        ignore_,  scan_name, run_to_ignore = flag.split("_")

                        assert ignore_ == "ignore", "flags: 'ignore' is not spelled correctly for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)
                        assert scan_name in ["mrs", "func", "anat", "mpm", "b0", "b1"], "flags; scan type is not correct for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)
                        assert run_to_ignore.isnumeric(), "flags: run to ignore is not an interger for wbic_id: {0}, zk_id {1}".format(wbic_id,
                                                                                                                     zk_id)

    def _test_no_scan_id_are_duplicate(self,participant_log):
        """

        """
        all_zk_id = []

        for wbic_id in participant_log.keys():
            for scan_info in participant_log[wbic_id]["scans"].values():

               all_zk_id.append(scan_info["zk_id"])

        duplicates = []  # list comp not working due to scope issue
        for id in all_zk_id:
            if all_zk_id.count(id) > 1:
                duplicates.append(id)

        assert not any(duplicates), "Duplicates zk id detected, check participant log carefully for: {0}".format(duplicates)

    def _test_download(self, zk_id, save_to_log=False):
        """
        Check every downloaded folder for the subject for scanner_format (e.g. .dcm). Log the nubmer of .dcm in every
        folder and show a fail messaage if any dir is empty of the scanner_format
        """
        fail_flag = False
        all_dirs = sorted(glob.glob(os.path.join(self.raw_scans_path, zk_id, zk_id, "*")))

        if not all_dirs or not self.scan_already_downloaded(zk_id):
            log_ = "Test Download: no files found for {0}".format(zk_id)
            fail_flag = True

        else:
            # Iterate through all downloaded folder, get number of files and check at least 1
            # and log result
            log_ = ""
            for dir in all_dirs:

                files_in_dir = sorted(glob.glob(
                                                os.path.join(dir, "*" + self.scanner_format)))

                num_files = len(files_in_dir)
                num_files_format_with_5_spaces = "{:<5}".format(num_files)

                log_ += "{0} {1} in dir: {2}\n".format(num_files_format_with_5_spaces,
                                                             self.scanner_format.upper(),
                                                             os.path.basename(dir))
                if num_files == 0:
                    fail_flag = True

            if fail_flag:
                log_ += "DOWNLOAD FAILED: Some directories are empty of {0}" \
                        " for {1}. No further processing will be done\n".format(self.scanner_format.upper(),
                                                                                zk_id)
            else:
                log_ += "All directories have at least one {0} for {1}\n".format(self.scanner_format.upper(),
                                                                                 zk_id)

        if save_to_log:
            self.log("Download Check",
                      log_)

        return fail_flag, log_

    def _test_and_log_expected_file_number(self, destination_path, num_expected_files):
        """

        """
        if num_expected_files:

            num_copied_files = len(glob.glob(os.path.join(destination_path, "*")))
            if num_copied_files != num_expected_files:
                self.log(None, "WARNING: Only {0} scans in {1} but expecting {2}\n".format(num_copied_files,
                                                                                           destination_path,
                                                                                           num_expected_files))
            else:
                self.log(None,
                         "".join(["scan has the expected number of files: ",
                                  str(num_expected_files),
                                  "\n"])
                         )

    def _test_all_subs_are_in_correct_order(self):   # Run a motion correction in ANFI / SPM. Meet with Avraam
        """
        Iterate through all subjects in order and check the date / time of the first scan
        is after that of the preceding subject.
        """
        all_subs = self.get_all_subs_and_ses_in_preprocessing()
        all_sub_ids = sorted(all_subs.keys())

        all_sub_datetimes = []
        for sub_id in all_sub_ids:

            first_ses_info_path = self._glob_one_result(
                                                       os.path.join(self.preprocessing_path,
                                                                    sub_id, "ses-001", "ses-001_info.txt"))

            scan_datetime = self._extract_date_time_from_sub_info_file(
                                                                      first_ses_info_path)

            all_sub_datetimes.append(scan_datetime)

        bad_subs = self._test_datetimes_are_in_order(all_sub_datetimes,
                                                     list(all_sub_ids))

        return bad_subs

    def _test_all_sessions_are_in_correct_order(self):

        all_subs = self.get_all_subs_and_ses_in_preprocessing()
        all_sub_ids = sorted(all_subs.keys())

        bad_subs = []
        for idx, sub_id in enumerate(sorted(all_sub_ids)):

            ses_datetimes = []
            all_ses_ids = sorted(all_subs[sub_id])
            for ses_id in all_ses_ids:

                ses_info_path = self._glob_one_result(
                                                      os.path.join(self.preprocessing_path,
                                                                   sub_id, ses_id, ses_id + "_info.txt"))
                ses_datetimes.append(
                                     self._extract_date_time_from_sub_info_file(ses_info_path))

            bad_ses = self._test_datetimes_are_in_order(ses_datetimes,
                                                        all_ses_ids)

            if bad_ses:
                bad_subs.append([sub_id, bad_ses])

        return bad_subs

    def _test_datetimes_are_in_order(self, all_scan_datetimes, sub_ids):
        """
        "Find any datetime that is out of increasing order and return the corresponding subs. TODO: own function
        INPUT: all_scan_datimes is list of datetimes, subids is list of corresponding sub_ids
        """
        check = [date1 == date2 for date1, date2 in zip(sorted(all_scan_datetimes),
                                                        all_scan_datetimes)]
        error_idx = [idx for idx, bool_ in enumerate(check) if bool_ is False]

        bad_subs = [sub_ids[idx] for idx in error_idx] if error_idx else []

        return bad_subs

    def _test_project_scan_and_ses_ids_match_date_order(self):
        """

        """
        sub_ids_out_of_datetime_order = self._test_all_subs_are_in_correct_order()

        log_ = ""
        if any(sub_ids_out_of_datetime_order):
            log_ += "ERROR: The following sub_ids do not " \
                    "match scan times {0}\n".format(sub_ids_out_of_datetime_order)

        subs_with_ses_ids_out_of_order = self._test_all_sessions_are_in_correct_order()

        if any(subs_with_ses_ids_out_of_order):
            log_ += "ERROR: The following sessions are not in " \
                    "correct order{0}\n".format(subs_with_ses_ids_out_of_order)

        return log_









