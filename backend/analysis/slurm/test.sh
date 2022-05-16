#!/bin/bash
#!
#! Example SLURM job script for hivemind
#!
#!

#! Name of the job:
#SBATCH --job-name=""

#! Output filename:
#! %A means slurm job ID and %a means array index
#SBATCH --output=""

#! Errors filename:
#SBATCH --error=""

#! Number of tasks (for single core jobs always leave this at 1)
#SBATCH --ntasks=1

#! Number of nodes to be allocated for the job (always leave this at 1)
#SBATCH --nodes=1

#! How many many cores will be allocated per task? (for single core jobs always leave this at 1)
#SBATCH --cpus-per-task=1

#! How much wallclock time will be required?
#SBATCH --time=23:59:00

#! Always keep the following echo commands to monitor CPU, memory usage
echo "SLURM_MEM_PER_CPU: $SLURM_MEM_PER_CPU"
echo "SLURM_MEM_PER_NODE: $SLURM_MEM_PER_NODE"
echo "SLURM_JOB_NUM_NODES: $SLURM_JOB_NUM_NODES"
echo "SLURM_NNODES: $SLURM_NNODES"
echo "SLURM_NTASKS: $SLURM_NTASKS"
echo "SLURM_CPUS_PER_TASK: $SLURM_CPUS_PER_TASK"
echo "SLURM_JOB_CPUS_PER_NODE: $SLURM_JOB_CPUS_PER_NODE"
#! Launch the executable (bash script, freesurfer, matlab etc)
# 


#!/bin/bash
#!
#! Example SLURM job script for hivemind
#!
#!

#! Name of the job:
#SBATCH --job-name=""

#! Output filename:
#! %A means slurm job ID and %a means array index
#SBATCH --output=""

#! Errors filename:
#SBATCH --error=""

#! Number of tasks (for single core jobs always leave this at 1)
#SBATCH --ntasks=1

#! Number of nodes to be allocated for the job (always leave this at 1)
#SBATCH --nodes=1

#! How many many cores will be allocated per task? (for single core jobs always leave this at 1)
#SBATCH --cpus-per-task=1

#! How much wallclock time will be required?
#SBATCH --time=23:59:00

#! Always keep the following echo commands to monitor CPU, memory usage
echo "SLURM_MEM_PER_CPU: $SLURM_MEM_PER_CPU"
echo "SLURM_MEM_PER_NODE: $SLURM_MEM_PER_NODE"
echo "SLURM_JOB_NUM_NODES: $SLURM_JOB_NUM_NODES"
echo "SLURM_NNODES: $SLURM_NNODES"
echo "SLURM_NTASKS: $SLURM_NTASKS"
echo "SLURM_CPUS_PER_TASK: $SLURM_CPUS_PER_TASK"
echo "SLURM_JOB_CPUS_PER_NODE: $SLURM_JOB_CPUS_PER_NODE"
#! Launch the executable (bash script, freesurfer, matlab etc)
#

