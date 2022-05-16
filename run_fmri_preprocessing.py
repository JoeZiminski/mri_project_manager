from glob import glob
from backend.project_master import ProjectMaster
from os.path import join, basename
import shutil

base_path = ""
utils = ProjectMaster()

base_path = r"/mnt/zfs/GP_7T-EEG_2022/data/mri/preprocessing"

subjects = ["sub-001"]
sessions = ["ses-001", "ses-002"]
fmri_runs = 4

# first put each EPI run into its own folder
for sub in subjects:
    for ses in sessions:

        ses_path = join(base_path, sub, ses, "func")

        full_filepaths = glob(join(ses_path, "raw", "*run-???*"))
        file_names = [basename(path) for path in full_filepaths]

        runs = [bids_name.split('_')[3] for bids_name in file_names]
        unique_runs = list(set(runs))

        for run_ in unique_runs:

            run_nii_folder = join(ses_path, "nii", run_)
            utils._mkdir(run_nii_folder)

            runs_to_copy = [file_name for file_name in file_names if run_ in file_name]

            for run_to_copy in runs_to_copy:

                command = "Dimon -infile_prefix '{0}/*.dcm' -gert_create_dataset -gert_write_as_nifti -use_obl_origin -gert_outdir {1} -gert_to3d_prefix {2}".format(join(ses_path, "raw", run_to_copy), run_nii_folder, run_to_copy)

                utils._run_subprocess(command, log_filepath=False)

                breakpoint()
      #          for run_to_copy in runs_to_copy:
       #             utils._copy_dir_contents(join(ses_path, "raw", run_to_copy),
        #                                     join(run_nii_folder, run_nii_folder, run_to_copy),
         #                                    log=False)









from nipype.interfaces import afni
qwarp = afni.QwarpPlusMinus()

