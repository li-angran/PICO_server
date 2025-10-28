import os
import json


import os
import re
from collections import defaultdict

root_dir = r"/mnt/nas01/LAR/pico/Experiments/tube_test/20250408"
out_put_dir = r"/mnt/nas01/LAR/pico/Experiments/tube_test/20250408/Analysis"


tmp = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    for dirname in dirnames:

        if dirname.endswith('frames'):

            # print(os.path.join(dirpath, dirname))
            tmp.append(os.path.join(dirpath, dirname))

# Regular expression to match the "calcium" folder followed by a number (1, 2, 3, or 4)
pattern = r"/calcium/(\d)/"

# Create a dictionary to store grouped paths based on the number after "calcium"
grouped_paths = defaultdict(list)

# Group the paths
for path in tmp:
    match = re.search(pattern, path)
    if match:
        calcium_num = match.group(1)  # Get the number after "calcium"
        grouped_paths[calcium_num].append(path)

# Output the grouped paths
for calcium_num, group in grouped_paths.items():
    print(f"Paths for calcium {calcium_num}:")
    for path in group:
        print(f"  {path}")
    print()  # For spacing between groups


# if detect and run unprocessed image, set only_detect = False, else True
only_detect = False

for calcium_num, group in grouped_paths.items():
    print(f"--------------------------------{group} processing begin!--------------------------------")

    # Load parameters
    with open('params.json', 'r') as json_file:
        params = json.load(json_file)
    
    out_path = os.path.join(out_put_dir, f"m{calcium_num}")
    print(out_path)
    params['gpu_ids'] = 6

    # Run the command
    command = f"""
                    python process_script_tube_test.py \
                   --jump_to_rmbg {params['jump_to_rmbg']} \
                   --jump_to_seg {params['jump_to_seg']} \
                   --jump_to_vis {params['jump_to_vis']} \
                   --set_frame_num {params['set_frame_num']} \
                   --data_path {" ".join(group)} \
                   --out_path {out_path} \
                   --fr {params['fr']} \
                   --mc_chunk_size {params['mc_chunk_size']} \
                   --save_movie {params['save_movie']} \
                   --max_shifts "{params['max_shifts']}" \
                   --strides "{params['strides']}" \
                   --overlaps "{params['overlaps']}" \
                   --num_frames_split {params['num_frames_split']} \
                   --max_deviation_rigid {params['max_deviation_rigid']} \
                   --pw_rigid {params['pw_rigid']} \
                   --shifts_opencv {params['shifts_opencv']} \
                   --border_nan {params['border_nan']} \
                   --downsample_ratio {params['downsample_ratio']} \
                   --crop_parameter {params['crop_parameter']} \
                   --intensity_corr_flag {params['intensity_corr_flag']} \
                   --bad_frame_detect_flag {params['bad_frame_detect_flag']} \
                   --up_sample {params['up_sample']} \
                   --rmbg_chunk_size {params['rmbg_chunk_size']} \
                   --rmbg_gsize {params['rmbg_gsize']} \
                   --ckpt_pth {params['ckpt_pth']} \
                   --device {params['device']} \
                   --gpu_ids {params['gpu_ids']} \
                   --patch_size {params['patch_size']} \
                   --pixel_size {params['pixel_size']} \
                   --minArea {params['minArea']} \
                   --avgArea {params['avgArea']} \
                   --thresh_pmap {params['thresh_pmap']} \
                   --thresh_mask {params['thresh_mask']} \
                   --thresh_COM0 {params['thresh_COM0']} \
                   --thresh_COM {params['thresh_COM']} \
                   --cons {params['cons']}
            """
    
    # Add the paths as separate arguments
    for path in group:
        command += f" --data_path {path}"

    if only_detect == False:
        os.system(command)
    print(f"--------------------------------{group} processing completed!--------------------------------")
