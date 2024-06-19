from datetime import datetime, timedelta
from metarunner import Metarunner, MetarunnerArgs
import os

print("KERBEROS TICKETS: ", os.system("klist"))


if __name__ == "__main__":
    home_dir =  "/storage/plzen1/home/sidoj"
    metarunner_root = f"{home_dir}/projects/sph_data_downloader"
    time_str = "0:04:00"
    time_obj = datetime.strptime(time_str, '%H:%M:%S')
    total_seconds = timedelta(hours=time_obj.hour, minutes=time_obj.minute, seconds=time_obj.second).total_seconds()
    seconds_for_data_bck = 2*60
    
    # PBS -q gpu@cerit-pbs.cerit-sc.cz
    def plan_script(script_path, run_guid, run_seq_id, data_dir):
        return f"""#!/bin/bash
                #PBS -q iti@pbs-m1.metacentrum.cz
                #PBS -l select=1:ncpus=4:mem=40gb:scratch_local=40gb

                #PBS -l walltime={time_str}
                #PBS -N sph-d-{run_guid}-{run_seq_id}
                
                source ~/.bashrc   #for bck_folder init

                cleanup(){{
                    echo 'Running cleanup'
                    bck_folder $SCRATCHDIR {data_dir}
                    exit
                }}

                # timeout for enough time at the end of the job ({seconds_for_data_bck} seconds)
                timeout -s SIGKILL {total_seconds-seconds_for_data_bck} /bin/bash -c 'HOME={home_dir} {script_path}'

                echo "job was killed by me or just ending to cleanup"
                cleanup
                """

    def generate_run_job(named_args):
        db_file_name = os.path.basename(named_args['file'])
        hdf5_file_name = f"{db_file_name.split('.')[0]}.hdf5"
    
        return f"""#!/bin/bash
                
                
                module add mambaforge

                mamba create -p $SCRATCHDIR/sph_clone --clone /storage/plzen1/home/sidoj/tools/miniconda/envs/sphincter
                conda activate $SCRATCHDIR/sph_clone

                export TMPDIR=$SCRATCHDIR

                cd {metarunner_root}
                cp {named_args['file']} $SCRATCHDIR/{db_file_name}
            
                python /storage/brno2/home/sidoj/projects/sph_data_downloader/src/download/sql_to_hdf5.py $SCRATCHDIR/{db_file_name} $SCRATCHDIR{hdf5_file_name}
                rm $SCRATCHDIR/{db_file_name}

                echo "job script ending..."        
                """

    mr = Metarunner(metarunner_root, plan_script, generate_run_job)



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
        print("planing")
        # mr.run_on_meta(config, generate_only=True)
        mr.run_on_meta(config)
        break

