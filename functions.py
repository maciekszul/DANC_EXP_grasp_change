import os
import os.path as op
import files
import pandas as pd


def secondary_prompt(subject_id, output_folder):
    all_the_files = files.get_files(output_folder, "block", ".csv")[2]
    all_the_files.sort()
    try:
        last_file = all_the_files[-1]
        dem_data = pd.read_csv(last_file)
        age_prev = dem_data.age.unique()[0]
        gender_prev = dem_data.gender.unique()[0]
        block_prev = dem_data.block.unique()[0]
        exp_info = {
            "ID": subject_id,
            "age": age_prev,
            "gender (m/f/o)": gender_prev,
            "block": block_prev + 1
        }
        return exp_info
    except:
        exp_info = {
            "ID": subject_id,
            "age": "ADD_AGE",
            "gender (m/f/o)": "ADD_GENDER",
            "block": 0
        }
        return exp_info
