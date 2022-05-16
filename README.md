Automated scan downloading and project organisation

- download data from HPC to hivemind project folder
- organise downloaded data for backups
- copy relevant scans to BIDS format
- options for ignoring bad runs
- logs all processes
- tests for user input, scan ordering

See docs/project_overview.pdf 

Iniitialises a project with the structure:

		./PROJECT/data/raw_scans  
		./PROJECT/data/preprocessing  
		./PROJECT/docs/logs  


USEAGE:

1) First prepare your HPC / Hivemind account for passwordless
   connection and access to the relevant WBIC project (see PREPARATION) below.

2) Fill out the project_configs.py with the data relevant for your project.

3) run with python3 run_project.py -download_from_hpc -move_to_preprocessing
  
   This script will loop through all subjects / sessions specified in project_configs.py
   and download the data from the HPC (-download_from_hpc), then move the relevant
   from scans from /raw_scans/ to preprocessing (-move_to_preprocessing). 

   If a folder with the zk_id (e..g zk21w7_005) already exists in /raw_scans/
   data will not be downloaded. If a matching session already exists in 
   /preprocessing/sub-XXX/ data will not be copied. 

4) If running outside of run_project.py, make sure to init_logging()
   or logs will not be saved correctly.
   

PREPARATION:

1) Setup passworless SSH connection from the hivemind to HPC. The .ssh keys must be stored 
   in your /home directory (this is the default).

   From the hivemind, run:
   
   ssh-keygen -t rsa
   cat ~/.ssh/id_rsa.pub | ssh remote_username@server_ip_address "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"


   You will be asked to fill in your password during initial setup

2) Log onto the HPC and check your project access / WBIC. cd to /rds-d5/user/USERNAME/hpc-work/ and make a folder called wbic-data.
   cd to wbic-data and run:

   module wbic load
   dcmconv.pl -remoteae PROJECT_ID -date YYYYMMDD -makedir -outtype dicom10 -direct -info 

   and try to download a scan. If the download is sucessful, you can delete it from /wbic-data. Do not delete
   /wbic-data as it will be used as the holding folder for downloading scans from HPC.






connect to ssh make rsa key in home dir
make wbic-data and test 
init logging 