import datetime
import itertools
import os
import subprocess
import stat
import random

import sys


class Metarunner():
    def __init__(self, generate_plan_job_template, generate_run_job_template, meterunner_path, python_script="main.py",
                 singularity_container=None, project_dir=None, add_seq_number=False):
        self.python_script = python_script
        self.add_seq_number = add_seq_number

        self.singularity_container = singularity_container
        self.project_dir = project_dir

        self.meterunner_path = meterunner_path
        self.script_paths = os.path.join(meterunner_path, "runs")
        self.ckpts_paths = os.path.join(meterunner_path, "ckpts")

        self.generate_plan_job_template = generate_plan_job_template
        self.generate_run_job_template = generate_run_job_template

    @classmethod
    def grid_config(cls, map_hp_vals):
        lists = map_hp_vals.values()
        keys = map_hp_vals.keys()
        ret = []
        for config_list_instance in itertools.product(*lists):
            config_instance = {k: v for k, v in zip(keys, config_list_instance)}
            ret.append(config_instance)
        return ret

    def dry_run(self, named_args):
        print(named_args)
        cmd = f"python"
        args = []
        for k, v in named_args.items():
            args.extend([f"--{k}", f"{v}"])

        args = [cmd, self.python_script] + args
        print(" ".join(args))
        # proc_out = subprocess.run(args)

        proc_clamscan = subprocess.Popen(args,
                                         stdout=sys.stdout,
                                         stderr=sys.stderr)
        proc_clamscan.communicate()

        # output = proc_out.stdout.decode("utf-8")
        # print(" ".join(args))

    def run_on_meta(self, config, in_sequence=1, generate_only=False, last_run_ckpts=None, depend_on=None):

        previous_id = 0 if depend_on is None else depend_on

        os.makedirs(self.script_paths, exist_ok=True)
        ids = []

        for j in range(in_sequence):
            now = datetime.datetime.now()
            random_seed = random.randint(0, 65535)
            date_time = now.strftime(f"%Y-%m-%d__%H-%M-%S--{j}-{random_seed}-ckpt")

            if last_run_ckpts is not None:
                config["load_checkpoint_from"] = last_run_ckpts
            print(f"FORCE load ckpts from {last_run_ckpts}")

            metarunner_save = os.path.join(self.ckpts_paths, date_time)
            # os.makedirs(metarunner_save, exist_ok=False)
            if in_sequence > 1:
                config["metarunner_ckpt_dir"] = metarunner_save
                print(f"planing META TASK .. saving ckpts into {metarunner_save}")

            last_run_ckpts = metarunner_save

            rand_suff = ""
            if not generate_only:
                rand_suff = f"_{random.randint(100000, 999999)}"

            job_sript_name = f"job-script_{j}{rand_suff}.sh"
            plan_script_name = f"plan-script_{j}{rand_suff}.sh"

            job_script = os.path.join(self.script_paths, job_sript_name)
            plan_script = os.path.join(self.script_paths, plan_script_name)

            if self.add_seq_number == True:
                config["metarunner_seq_num"] = in_sequence

            # create in-singularity script
            runinng_script = self.generate_run_job_template(config)
            with open(job_script, "w", encoding="utf-8") as in_singularity_fd:
                in_singularity_fd.write(runinng_script)
                if generate_only:
                    print("script in-singularity was generated")
                    print(job_script)
                    # print(in_singularity_script)

            # create main script
            with open(plan_script, "w", encoding="utf-8") as main_script_fd:
                planning_script = self.generate_plan_job_template(job_script)
                main_script_fd.write(planning_script)
                if generate_only:
                    print("main qsub script was generated")
                    print(plan_script, "\n")
                    # print(main_script_content)

            st = os.stat(plan_script)
            os.chmod(plan_script, st.st_mode | stat.S_IEXEC)

            st = os.stat(job_script)
            os.chmod(job_script, st.st_mode | stat.S_IEXEC)

            if generate_only:
                print("\n GENERATE ONLY -- NOT RUNNING")

                print("for interactive run use:")
                if self.singularity_container:
                    print(f"singularity run --nv {self.singularity_container}  {job_script}")
                else:
                    print(f"conda activate .... and run: {job_script}")

                continue

            print("\n\n")
            output = ""
            if previous_id == 0:
                cmd = f"cd {self.meterunner_path}; qsub {plan_script}"
                print(cmd)

                stream = os.popen(cmd)
                output = stream.read()
                ids.append(output)

            else:
                cmd = f"cd {self.meterunner_path}; qsub -W depend=afterany:{previous_id} {plan_script}"
                print(cmd)

                stream = os.popen(cmd)
                output = stream.read()
                ids.append(output)

            print(output, "depending on : ", previous_id)

            # m = JOB_ID_RE.match(output)
            previous_id = output.strip()  # int(m.group())
        print("-------------------\n" + "".join(ids))
