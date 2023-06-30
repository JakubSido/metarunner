import datetime
import itertools
import os
import stat
import random

from typing import Dict, List


class Metarunner():
    def __init__(self, project_dir, generate_plan_job_template, generate_run_job_template, metarunner_path=None):

        if project_dir is None:
            print("project_dir is not specified ")

        self.project_dir = project_dir

        if metarunner_path is None:
            metarunner_path = os.path.join(project_dir, "metarunner")

        self.meterunner_path = metarunner_path
        self.output_path = os.path.join(metarunner_path, "outputs")
        self.script_paths = os.path.join(metarunner_path, "scripts")

        self.generate_plan_job_template = generate_plan_job_template
        self.generate_run_job_template = generate_run_job_template

    @classmethod
    def grid_config(cls, map_hp_vals: Dict[str, List]) -> List[Dict]:
        """
        Generate cartesian product of all hyper-parameters

        :param map_hp_vals: grid to generate cartesian product from
        :return: list of dicts -- all possible combinations of hyper-parameters
        """
        lists = map_hp_vals.values()
        keys = map_hp_vals.keys()
        ret = []
        for config_list_instance in itertools.product(*lists):
            config_instance = {k: v for k, v in zip(keys, config_list_instance)}
            ret.append(config_instance)
        return ret


    def run_on_meta(self, config, in_sequence=1, generate_only=False, depend_on=None, add_seed_into_config=True):
        print("planing job")
        print("KERBEROS TICKETS:")
        os.system("klist")

        previous_id = 0 if depend_on is None else depend_on

        os.makedirs(self.script_paths, exist_ok=True)
        os.makedirs(self.output_path, exist_ok=True)
        ids = []

        global_random_seed = random.randint(10000, 65535)

        for j in range(in_sequence):
            now = datetime.datetime.now()
            random_seed = f"{global_random_seed}-{j}"
            date_time = now.strftime(f"%Y-%m-%d__%H-%M-%S-%f--{random_seed}")
            if add_seed_into_config:
                config["metarunner_seed"] = random_seed

            job_sript_name = f"job-script_{date_time}.sh"
            plan_script_name = f"plan-script_{date_time}.sh"

            job_script = os.path.join(self.script_paths, job_sript_name)
            plan_script = os.path.join(self.script_paths, plan_script_name)

            if in_sequence > 1:
                config["metarunner_seq_num"] = in_sequence

            # create in-singularity script
            runinng_script = self.generate_run_job_template(config)
            with open(job_script, "w", encoding="utf-8") as in_singularity_fd:
                in_singularity_fd.write(runinng_script)
                if generate_only:
                    print("script in-singularity was generated")
                    print(job_script)

            # create main script
            with open(plan_script, "w", encoding="utf-8") as main_script_fd:
                planning_script = self.generate_plan_job_template(job_script)
                main_script_fd.write(planning_script)
                if generate_only:
                    print("main qsub script was generated")
                    print(plan_script, "\n")

            st = os.stat(plan_script)
            os.chmod(plan_script, st.st_mode | stat.S_IEXEC)

            st = os.stat(job_script)
            os.chmod(job_script, st.st_mode | stat.S_IEXEC)

            if generate_only:
                continue

            print("\n\n")
            if previous_id == 0:
                cmd = f"cd {self.output_path}; qsub {plan_script}"
            else:
                cmd = f"cd {self.output_path}; qsub -W depend=afterany:{previous_id} {plan_script}"

            print("CMD: ",cmd)


            stream = os.popen(cmd)
            output = stream.read()
            ids.append(output)
            print(output, "depending on : ", previous_id)
            previous_id = output.strip()

        print("-------------------\n" + "".join(ids))
