import datetime
import os
import subprocess
import stat
import random

import sys

class Metarunner():
    def __init__(self, shell_template, singularity_template, meterunner_path, python_script="main.py", ):
        self.python_script = python_script

        self.meterunner_path = meterunner_path
        self.script_paths = os.path.join(meterunner_path, "runs")
        self.ckpts_paths = os.path.join(meterunner_path, "ckpts")

        self.generate_shell_script = shell_template
        self.singularity_template = singularity_template

    def dry_run(self, named_args):
        print(named_args)
        cmd = f"python"
        args = []
        for k, v in named_args.items():
            args.extend([f"--{k}", f"{v}"])

        args = [cmd, self.python_script] + args
        print(" ".join(args))
        proc_out = subprocess.run(args)

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
            config["metarunner_ckpt_dir"] = metarunner_save
            print(f"planing META TASK .. saving ckpts into {metarunner_save}")

            last_run_ckpts = metarunner_save

            singularity_script_path = os.path.join(self.script_paths, f"run-in-singularity_{j}.sh")
            main_script_path = os.path.join(self.script_paths, f"run-single_{j}.sh")

            # create in-singularity script
            in_singularity_script = self.singularity_template(config)
            with open(singularity_script_path, "w", encoding="utf-8") as in_singularity_fd:
                in_singularity_fd.write(in_singularity_script)
                if generate_only:
                    print(in_singularity_script)

            # create main script
            with open(main_script_path, "w", encoding="utf-8") as main_script_fd:
                main_script_content = self.generate_shell_script(singularity_script_path)
                main_script_fd.write(main_script_content)
                if generate_only:
                    print(main_script_content)

            st = os.stat(main_script_path)
            os.chmod(main_script_path, st.st_mode | stat.S_IEXEC)

            st = os.stat(singularity_script_path)
            os.chmod(singularity_script_path, st.st_mode | stat.S_IEXEC)
            print("\n\n")
            output = ""
            if previous_id == 0:
                cmd = f"cd {self.meterunner_path}; qsub {main_script_path}"
                print(cmd)
                if not generate_only:
                    stream = os.popen(cmd)
                    output = stream.read()
                    ids.append(output)

            else:
                cmd = f"cd {self.meterunner_path}; qsub -W depend=afterany:{previous_id} {main_script_path}"
                print(cmd)
                if not generate_only:
                    stream = os.popen(cmd)
                    output = stream.read()
                    ids.append(output)

            print(output, "depending on : ", previous_id)

            # m = JOB_ID_RE.match(output)
            previous_id = output.strip()  # int(m.group())
        print("-------------------\n" + "".join(ids))


