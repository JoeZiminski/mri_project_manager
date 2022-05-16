import os
from nipype.interfaces import fsl
import nipype.interfaces.spm as spm
from nipype.interfaces import afni
import nipype.pipeline.engine as pe
import nipype.interfaces.io as nio
from nipype.interfaces.dcm2nii import Dcm2niix

# Dcm2niix followed by motion correction with SPM, FSL and AFNI
# Also has support for Freesufer and ANTS alignment and many other functions...

in_folder = r"/mnt/zfs/7T_TUNING/tests/nipype_tests/spm_mc/sub-001_ses-001_task-ori_run-001_bold_old"
in_filename = "sub-001_ses-001_task-ori_run-001_bold_old.nii"
in_fullpath = os.path.join(in_folder,
                           in_filename)

# Dcm2niix -------------------------------------------------------------------------------------------------------------

converter = Dcm2niix()
converter.inputs.source_dir = in_fullpath
converter.inputs.output_dir = in_folder
converter.run()

in_folder = r"/mnt/zfs/7T_TUNING/tests/nipype_tests/spm_mc/sub-001_ses-001_task-ori_run-001_bold_old"
in_filename = "sub-001_ses-001_task-ori_run-001_bold_old.nii"
in_fullpath = os.path.join(in_folder,
                           in_filename)

# SPM's Realign --------------------------------------------------------------------------------------------------------
spm_realign = pe.Node(interface=spm.Realign(in_files=in_fullpath,
                                            register_to_mean=True),
                      name="spm_realign")
spm_realign.base_dir = in_folder
spm_realign.run()


# FSL's MCFLIRT --------------------------------------------------------------------------------------------------------
mcflirt = pe.Node(interface=fsl.MCFLIRT(in_file=in_fullpath,
                                        cost="mutualinfo"),
                  name="mcflirt")
mcflirt.base_dir = in_folder
mcflirt.run()

# AFNI's 3dvolreg ------------------------------------------------------------------------------------------------------
volreg = pe.Node(interface=afni.Volreg(in_file=in_fullpath),
                 name="3dvolreg")
volreg.base_dir = in_folder
volreg.run()

