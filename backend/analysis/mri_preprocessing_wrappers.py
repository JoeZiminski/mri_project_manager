import subprocess

def passed_and_true(arg, kwargs):
    return arg in kwargs and kwargs[arg]

def passed_and_false(arg, kwargs):
    return arg in kwargs and not kwargs[arg]

# dcm2nii
# ----------------------------------------------------------------------------------------------------------------------

def dcm2nii(subject_folder, **kwargs):
    """
    Wrapper around Chris Rordens dcm2nii. Requires dcm2nii installed and TODO: ON PATH NAME.
    Tested on version 2May2016.

    Called with relevant keyword arguments and argument type, if keyword argument is not provided
    default is used.

    e.g. dcm2nii(anonymize=False, skip_initial=10, spm_2=True)

    Arguments described below,in order:
        python_arg; dcm2nii equivalent; input type; default

    dim4; -4; True or False; (default True)
    create_planar_rgb_images; -3; True or False; (default False)
    anonymize; -a; True or False; (default True)
    load_from_inifile; -b; False or str; (default False)
    collapse_input_folder; -c; True or False; (default True)
    date_in_filename; -d; True or False; (default True)
    events_in_filename; -e; True or False; (default True)
    source_in_filename; -f; True or False; (default True)
    gzip_output; -g; True or False; (default True)
    id_in_filename; -i; True or False; (default True)
    skip_initial; -k; integer; (default 0)
    planar_rgb; -l; True or False; (default False)
    hdr_img_pair; -n ; True or False (default False, will convert to .nii)
    output_directory=False,
    protocol_in_filename=True,
    reorient_to_nearest_orthogonal=False,
    spm_2=False,
    text_report=False,
    convert_every_image=True,
    reorient_and_crop=False
    """
    dcm2nii_command = get_dcm2nii_call(subject_folder, **kwargs)
    print(dcm2nii_command)
    subprocess.run(dcm2nii_command,
                   shell=True)

def format_as_str(str_):
    """
    Format in double-string for linux calls
    """
    return "\'" + str(str_) + "\'"

def get_dcm2niix_args(output_directory, **kwargs):  # TODO: switch to nipype
    args = ""

    args += "-f %f "  # for now just set the output filename to the folder name as default ans take no other options. TODO: move to nipype
    args += "-o {0}".format(output_directory)
    return args






# Depreciated

def get_dcm2nii_args(**kwargs):  # TODO: source_in_filename does not take #True argument, only str or false
    """
    Make arguments list based on kwargs. See dcm2nii()
    Tested in XXX
    """
    args = ""

    args += " -4 N" if passed_and_false("dim4", kwargs) else " -4 Y"
    args += " -3 Y" if passed_and_true("create_planar_rgb_images", kwargs) else " -3 N"
    args += " -a N" if passed_and_false("anonymize", kwargs) else " -a Y"
    args += " -b " + kwargs["load_from_inifile"] if "load_from_inifile" in kwargs and type(kwargs["load_from_inifile"]) == str else ""
    args += " -c N" if passed_and_false("collapse_input_folder", kwargs) else " -c Y"
    args += " -d N" if passed_and_false("date_in_filename", kwargs) else " -d Y"
    args += " -e N" if passed_and_false("events_in_filename", kwargs) else " -e Y"
    args += " -f Y" if passed_and_true("source_in_filename", kwargs) else " -f N"
    args += " -g N" if passed_and_false("gzip_output", kwargs) else " -g Y"
    args += " -i Y" if passed_and_true("id_in_filename", kwargs) else " -i N"
    args += " -k " + str(kwargs["skip_initial"]) if "skip_initial" in kwargs else " -k 0"
    args += " -l Y" if passed_and_true("planar_rgb", kwargs) else " -l N"
    args += " -n N" if passed_and_true("hdr_img_pair", kwargs) else " -n Y"
    args += " -o " + str(kwargs["output_directory"]) if "output_directory" in kwargs and type(kwargs["output_directory"]) == str else ""
    args += " -p N" if passed_and_false("protocol_in_filename", kwargs) else " -p Y"
    args += " -r Y" if passed_and_true("reorient_to_nearest_orthogonal", kwargs) else " -r N"
    args += " -s Y" if passed_and_true("spm_2", kwargs) else " -s N"
    args += " -t Y" if passed_and_true("text_report", kwargs) else " -t N"
    args += " -v N" if passed_and_false("convert_every_image", kwargs) else " -v Y"
    args += " x Y" if passed_and_true("reorient_and_crop", kwargs) else " -x N"

    return args

