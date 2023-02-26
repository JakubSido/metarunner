import itertools
import socket
import sys
from metarunner import Metarunner
import os

print("KERBEROS TICKETS: ", os.system("klist"))

if __name__ == '__main__':

    #PROJECT_DIR = "/storage/brno1-cerit/home/sidoj/prompt"
    PROJECT_DIR = "./"
    MAIN_SCRIPT = "src/example.py"

    # qsub -I -l walltime=24:0:0 -q gpu@meta-pbs.metacentrum.cz -l select=1:ncpus=1:ngpus=1:mem=40000mb:scratch_local=40000mb:cl_adan=True:mpiprocs=1:ompthreads=1
    # singularity run --nv /cvmfs/singularity.metacentrum.cz/NGC/PyTorch\:21.03-py3.SIF  /storage/brno1-cerit/home/sidoj/phd_augmenter

    def generate_plan_job(job_script, script_name="augmenter"):
        return f"""#!/bin/bash
                #PBS -q gpu@cerit-pbs.cerit-sc.cz
                #P-BS -q gpu@meta-pbs.metacentrum.cz
                #PBS -l walltime=0:59:0
                #PBS -l select=1:ncpus=1:ngpus=1:mem=40000mb:scratch_local=40000mb:cl_zia=True
                #P-BS -l select=1:ncpus=1:ngpus=1:mem=40000mb:scratch_local=40000mb:cl_galdor=True
                #PBS -N {script_name}

                /bin/bash {job_script}
                """


    def generate_run_job(named_args, conda_module="prompt"):
        named_params = " ".join(f"--{k} {v}" for k, v in named_args.items())
        return f"""#!/bin/bash
                module add conda-modules

                HOME=/storage/brno1-cerit/home/sidoj/
                conda activate {conda_module}

                export TMPDIR=$SCRATCH

                cd {PROJECT_DIR}
                export PYTHONPATH=$(pwd)
                python {MAIN_SCRIPT} {named_params}
                """


    mr = Metarunner(generate_plan_job, generate_run_job,
                    f"{PROJECT_DIR}/metarunner",
                    project_dir=PROJECT_DIR, python_script=MAIN_SCRIPT
                    )
    map_hp_vals = {
        "a": [
            5,
            1
        ],
        "b": [
            7,
            2
        ],
    }

    confs = Metarunner.grid_config(map_hp_vals)
    print("Len of cons : ", len(confs))
    print(confs)
    input("Press Enter to continue...")
    for config in confs:
        print("planing: ", config)
        # pass
        mr.run_on_meta(config, 
            run_job_kwargs={"conda_module": "prompt"}, 
            plan_job_kwargs={"script_name": f"augmenter-{config['a']}+{config['b']}"}, 
            generate_only=True)
        #mr.run_on_meta(config, generate_only=True)
        #mr.run_on_meta(config)

    # mr.dry_run(config)
