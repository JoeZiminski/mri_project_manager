import os
import subprocess

def run_command_with_slurm(job_name, output_filepath, errors_filepath, ntasks, commands_to_run):
    slurm_job_str = generate_slurm_job_command(job_name, output_filepath, errors_filepath, ntasks, commands_to_run)
    slurm_bash_filepath = save_slurm_bash_script(output_filepath, job_name, slurm_job_str)
    subprocess.call("sbatch " + slurm_bash_filepath,
                    shell=True)


def save_slurm_bash_script(filepath, filename, contents):

    filename = filename + ".sh" if filename[-3:] != ".sh" else filename
    slurm_bash_filepath = os.path.join(filepath,
                                       filename)
    with open(slurm_bash_filepath, "w") as file:
        file.write(contents)

    return slurm_bash_filepath

def generate_slurm_job_command(job_name, output_filepath, errors_filepath, ntasks, commands_to_run):
    """
    --job_name name of the job
    --output %A means slurm job ID and %a means array index and %t is task number
    --error #! Errors filename:
    --ntasks #! Number of tasks (for single core jobs always leave this at 1)
    --nodes #! Number of nodes to be allocated for the job (always leave this at 1)
    --cpus-per-task #! How many many cores will be allocated per task? (for single core jobs always leave this at 1)
    --time #! How much wallclock time will be required?
    """
    slurm_job_str = ("#!/bin/bash\n"
                     "\n"
                     "#SBATCH --job-name={job_name}\n"
                     "#SBATCH --output={output_filepath}/{job_name}_%A_%a_%t.out\n"
                     "#SBATCH --error={errors_filepath}/{job_name}_%A_%a.err\n"
                     "#SBATCH --ntasks={ntasks}\n"
                     "#SBATCH --ntasks-per-node={ntasks}\n"
                     "#SBATCH --nodes=1\n"
                     "#SBATCH --cpus-per-task=1\n"
                     "#SBATCH --time=100-23:59:00\n"
                     "\n"
                     "#! Always keep the following echo commands to monitor CPU, memory usage\n"
                     "echo \"SLURM_MEM_PER_CPU: $SLURM_MEM_PER_CPU\"\n"
                     "echo \"SLURM_MEM_PER_NODE: $SLURM_MEM_PER_NODE\"\n"
                     "echo \"SLURM_JOB_NUM_NODES: $SLURM_JOB_NUM_NODES\"\n"
                     "echo \"SLURM_NNODES: $SLURM_NNODES\"\n"
                     "echo \"SLURM_NTASKS: $SLURM_NTASKS\"\n"
                     "echo \"SLURM_CPUS_PER_TASK: $SLURM_CPUS_PER_TASK\"\n"
                     "echo \"SLURM_JOB_CPUS_PER_NODE: $SLURM_JOB_CPUS_PER_NODE\"\n"
                     "\n"
                     "{commands_to_run}\n"
                     "\n"
                     "wait\n"
                     "echo \"finished\"\n"
                     "\n"
                     "").format(job_name=job_name,
                                output_filepath=output_filepath,
                                errors_filepath=errors_filepath,
                                ntasks=ntasks,
                                commands_to_run=commands_to_run,
                         )
    return slurm_job_str
