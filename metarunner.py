from dataclasses import dataclass
import datetime
import itertools
import os
from pathlib import Path
import stat
import random

from typing import Dict, List

@dataclass
class MetarunnerArgs:
    metarunner_guid :str
    metarunner_seqid :int

class Metarunner():
    def __init__(self, project_dir, generate_plan_job_template, generate_run_job_template, metarunner_path=None):

        if project_dir is None:
            print("project_dir is not specified ")

        self.project_dir = project_dir

        if metarunner_path is None:
            metarunner_path = os.path.join(project_dir, "metarunner")

        self.meterunner_path = metarunner_path

        self.generate_plan_job_template = generate_plan_job_template
        self.generate_run_job_template = generate_run_job_template

    @classmethod
    def grid_config(cls, map_hp_vals: Dict[str, List], base_config :Dict [str,str] | None = None) -> List[Dict]:
        """
        Generate cartesian product of all hyper-parameters

        :param map_hp_vals: grid to generate cartesian product from
        :return: list of dicts -- all possible combinations of hyper-parameters
        """
        if base_config is None:
            base_config = dict()

        lists = map_hp_vals.values()
        keys = map_hp_vals.keys()
        ret = []
        for config_list_instance in itertools.product(*lists):
            config_instance = base_config.copy()
            config_instance.update({k: v for k, v in zip(keys, config_list_instance)})
            ret.append(config_instance)
        return ret


    def run_on_meta(self, config, in_sequence=1, generate_only=False, depend_on=None, add_run_guid=False, add_run_seq_num=False):
        print("planing job")
        print("KERBEROS TICKETS:")
        os.system("klist")

        previous_id = 0 if depend_on is None else depend_on

        now = datetime.datetime.now()

        date_string = now.strftime(f"%Y-%m-%d")
        time_string = now.strftime(f"%H-%M-%S-%f")
        date_time_string = now.strftime(f"%Y-%m-%d__%H-%M-%S-%f")

        if add_run_guid:
            config["metarunner_guid"] = date_time_string
        
        plan_path = os.path.join(self.meterunner_path,date_string,time_string)
        script_paths =  os.path.join(plan_path, "scripts")
        output_path = os.path.join(plan_path, "outputs")

        os.makedirs(script_paths, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        ids = []

        for j in range(in_sequence):

            job_sript_name = f"{j}_job-script.sh"
            plan_script_name = f"{j}_plan-script.sh"
            
            job_script = os.path.join(script_paths, job_sript_name)
            plan_script = os.path.join(script_paths, plan_script_name)

            if in_sequence > 1:
                if add_run_seq_num:
                    config["metarunner_seqid"] = in_sequence

            # create in-singularity script
            runinng_script = self.generate_run_job_template(config)
            with open(job_script, "w", encoding="utf-8") as in_singularity_fd:
                in_singularity_fd.write(runinng_script)
                if generate_only:
                    print("script in-singularity was generated")
                    print(job_script)

            # create main script
            with open(plan_script, "w", encoding="utf-8") as main_script_fd:
                planning_script = self.generate_plan_job_template(job_script,date_time_string,j)
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

            output_path_j = os.path.join(output_path, f"{j}")
            os.makedirs(output_path_j, exist_ok=True)

            print("\n\n")
            if previous_id == 0:
                cmd = f"cd {output_path_j}; qsub {plan_script}"
            else:
                cmd = f"cd {output_path_j}; qsub -W depend=afterany:{previous_id} {plan_script}"

            print("CMD: ",cmd)

            stream = os.popen(cmd)
            output = stream.read()
            ids.append(output)
            meta_name = f"{j}_{output}"
            Path(os.path.join(plan_path,meta_name)).touch()
            print(output, "depending on : ", previous_id)
            previous_id = output.strip()

        print("-------------------\n" + "".join(ids))
