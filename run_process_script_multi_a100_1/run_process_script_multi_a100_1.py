import os
import json

# data_paths = [
#     #"/mnt/nas00/lk/pico/Experiments/multimice/20250103multimice5/5#new/frames"
#                 # "/mnt/nas00/lk/pico/Experiments/multimice/20250104multimice5/group1/5#new/frames",
# # "/mnt/nas00/lk/pico/Experiments/multimice/20250104multimice5/group2/5#new/frames",
# # "/mnt/nas00/lk/pico/Experiments/tail_suspension/20250105/6#/calcium/frames"
# # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra/calcium/0123_n3_group3/3#/23-37-15-109/frames"
# # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra_new/calcium/0226_m7_group1/23-19-38-901/frames"
# # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra_new/calcium/0228_n3_group1/m5/20-21-43-661/frames"
# # "/mnt/nas01/LAR/pico/Experiments/tube_test/0309/159/23-10-06-685/frames"
# # "/mnt/nas01/Y/0311/11-Mar-25/23-42-48-079/frames",
# # "/mnt/nas01/Y/20250312/5/12-Mar-25/19-15-10-096/frames"
# # "/mnt/nas01/LAR/pico/Experiments/FaceCamera/0314/calcium/22-50-05-862/frames"

# # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m3-m4_additional/calcium/3/22-01-34-096_quanchengweimie/frames",
# # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m3-m4_additional/calcium/4/22-01-32-245_quanchengweiduan/frames"
# # "/mnt/nas00/lk/pico/Experiments/acc_test/angular-velocity-test/16_angular/16dark_calcium/frames"
# # "/mnt/nas01/LAR/autism/mice66/17-May-25/20-17-11-617/frames"

# # "/mnt/nas01/zwh/Y/p/20250609/09-Jun-25/20-23-34-642/frames",
# # "/mnt/nas01/zwh/Y/2025031406/14-Mar-25/23-54-02-356/frames"
#     "/mnt/nas01/LAR/pico/Experiments/social/autismmale/250614/group2/calcium/1/frames",
#     "/mnt/nas01/LAR/pico/Experiments/social/autismmale/250614/group2/calcium/4/frames",
#     "/mnt/nas01/LAR/pico/Experiments/social/autismmale/250614/group1/calcium/4/frames",
#     "/mnt/nas01/LAR/pico/Experiments/social/autismmale/250614/group3/calcium/1/frames",
#     "/mnt/nas01/LAR/pico/Experiments/social/autismmale/250614/group3/calcium/4/frames",


#               ]

import os

# # root_dir = "/mnt/nas01/LAR/pico/Experiments/tube_test/20250620_cage3"  # 替换为你的根目录路径
# root_dir  = "/mnt/nas01/LAR/pico/Experiments/hierarchy/two_mice/20250706_tube_cage3/group4/calcium"


# data_paths = []

# for dirpath, dirnames, filenames in os.walk(root_dir):
#     if os.path.basename(dirpath) == 'frames':
#         data_paths.append(dirpath)

# data_paths = [
#     "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/6mice/09-Jun-25/21-00-07-629/frames",
#     "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/mouse65/frames",
    
#     ]

paths = [
    # r"Y:\LAR\pico\Experiments\habitat_ultra_new\calcium\0228_n3_group1\m5\20-21-43-661\frames",
    # r"Y:\zwh\BBT\5MOUSE\30-Mar-25\23-42-57-913\frames",
    #  "Y:/wy/line/BS/189/move/21-34-04-723/frames",
     "Y:/wy/line/AS/208/D1/20-32-25-483/frames"

]
data_paths = [p.replace("Y:", "/mnt/nas01").replace("\\", "/") for p in paths]

for path in data_paths:
    print(path)



out_paths = [datapath.replace("frames", "Analysis_longterm") for datapath in data_paths]


def count_files_in_directory(directory):
    """Count the number of files in a given directory."""
    if os.path.exists(directory):
        return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    return 0


def check_analysis_status(out_path, data_path):
    """Check the progress of the analysis and determine the steps to execute."""
    frames_count = count_files_in_directory(data_path)
    jump_to_rmbg, jump_to_seg, jump_to_vis = False, False, False

    analysis_dir = os.path.join(out_path, "preprocess")
    rmbg_dir = os.path.join(out_path, "rmbg", "all")
    seg_results_dir = os.path.join(out_path, "seg_results_thresh_pmap_1")

    # Check if the preprocessing images are available
    if count_files_in_directory(analysis_dir) == frames_count and \
            os.path.exists(os.path.join(out_path, "vessel_image.tif")) and \
            os.path.exists(os.path.join(out_path, "vessel_mask.tif")):
        print(f"Preprocessing completed, setting jump_to_rmbg=True")
        jump_to_rmbg = True

    # Check if the rmbg step is completed
    if count_files_in_directory(rmbg_dir) == frames_count:
        print(f"RMBG completed, setting jump_to_seg=True")
        jump_to_seg = True

    # Check if the segmentation step is completed
    if os.path.exists(os.path.join(seg_results_dir, "seg_results.mat")) and \
            os.path.exists(os.path.join(seg_results_dir, "infer_results.mat")) and \
            os.path.exists(os.path.join(seg_results_dir, "cm.mat")):
        print(f"Segmentation completed, setting jump_to_vis=True")
        jump_to_vis = True

    # Check if the process is fully completed
    if os.path.exists(os.path.join(seg_results_dir, "seg_results_filtered.mat")) and \
            os.path.exists(os.path.join(seg_results_dir, "infer_results_filtered.mat")) and \
            os.path.exists(os.path.join(seg_results_dir, "cm_filtered.mat")):
        print(f"Processing already completed, no further execution required.")
        return None, None, None

    return jump_to_rmbg, jump_to_seg, jump_to_vis

# if detect and run unprocessed image, set only_detect = False, else True
only_detect = False

for data_path, out_path in zip(data_paths, out_paths):
    print(f"--------------------------------{data_path} processing begin!--------------------------------")

    # Load parameters
    with open('../params.json', 'r') as json_file:
        params = json.load(json_file)

    # Check if Analysis directory exists
    if not os.path.exists(out_path):
        print(f"{out_path} does not exist, setting all jumps to False and running the process.")
        jump_to_rmbg, jump_to_seg, jump_to_vis = False, False, False
    else:
        jump_to_rmbg, jump_to_seg, jump_to_vis = check_analysis_status(out_path, data_path)

    if jump_to_rmbg is None:
        print(f"Skipping processing for {data_path} as it is already completed.")
        continue

    # Update the params based on the checks
    params['jump_to_rmbg'] = jump_to_rmbg
    params['jump_to_seg'] = jump_to_seg
    params['jump_to_vis'] = jump_to_vis
    params['gpu_ids'] = 0
    params["ckpt_pth"] = "/data/home/angran/BBNC/code/PICO_ca_processing/utils/deepdefinite_ckpt_resize_2.pth"
    # params['set_frame_num']=4000

    # if data_path == "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/6mice/09-Jun-25/21-00-07-629/frames" or "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/mouse65/frames":
    #     params['set_frame_num']=2900

    # Run the command
    command = f"""
                    python ../process_script.py \
                   --jump_to_rmbg {params['jump_to_rmbg']} \
                   --jump_to_seg {params['jump_to_seg']} \
                   --jump_to_vis {params['jump_to_vis']} \
                   --set_frame_num {params['set_frame_num']} \
                   --data_path  {data_path} \
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

    if only_detect == False:
        os.system(command)
    print(f"--------------------------------{data_path} processing completed!--------------------------------")


