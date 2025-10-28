import os
import json

# Define the paths
# data_paths = ["/mnt/nas/lk/pico/Experiments/maze/20240930maze/8#/calcium01/frames",
#               "/mnt/nas/lk/pico/Experiments/maze/20240930maze/8#/calcium02/frames",
#               "/mnt/nas/lk/pico/Experiments/maze/20240930maze/8#/calcium03/frames"]
# data_paths = ["Z:/lk/pico/Experiments/maze/20240930maze/8#/calcium01/frames",
#               "Z:/lk/pico/Experiments/maze/20240930maze/8#/calcium02/frames",
#               "Z:/lk/pico/Experiments/maze/20240930maze/8#/calcium03/frames"]


# data_paths = [
#                 # "/mnt/nas00/lk/pico/Experiments/Spy/20241209/group1/calcium/frames"
#                 # "/mnt/nas00/lk/pico/Experiments/multimice/20250103multimice5/3#new/frames"
#                 # "/mnt/nas00/lk/pico/Experiments/multimice/20250104multimice5/group1/3#new/frames",
#                 # "/mnt/nas00/lk/pico/Experiments/3D/20241231/calcium/frames",
#                 # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra/calcium/0123_n3_group3/1#/23-33-28-203/frames"
#                 # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra/calcium/0123_n3_group1/1#/20-53-51-241/frames"
#                 # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra_new/calcium/0226_m3_group1/22-33-25-639/frames"
#                 # "/mnt/nas01/LAR/pico/Experiments/habitat_ultra_new/calcium/0228_n3_group1/m3/20-21-35-209/frames"
#                 # "/mnt/nas01/LAR/pico/Experiments/tube_test/0309/152/23-10-04-072/frames"
#                 # "/mnt/nas01/Y/20250313/031305/13-Mar-25/17-11-23-941/frames",
#                 # "/mnt/nas01/Y/20250313/031306/13-Mar-25/17-31-15-355/frames"
#                 # "/mnt/nas00/lk/pico/Experiments/0713_multi_animal_n3/m20/13-Jul-24/22-36-45-789/frames"
#                 # "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/2months/3/frames",
#                 # "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/2months/5/frames",
#                 # "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/2months/106/frames",
#                 # "/mnt/nas01/GL/longterm/long-term_clarity_of_cranial_windows_and_PICO_imaging/mouse6/01-Jan-2000/00-00-00-000/frames",
#                 # "/mnt/nas00/lk/pico/Experiments/acc_test/angular-velocity-test/7_angular/7bright_calcium/frames",
#                 # "/mnt/nas00/lk/pico/Experiments/acc_test/angular-velocity-test/7_angular/7dark_calcium/frames",
#                 # "/mnt/nas00/lk/pico/Experiments/acc_test/angular-velocity-test/16_angular/16dark_calcium/frames",
#                 # "/mnt/nas00/lk/pico/Experiments/acc_test/open-field-test/normal/6calcium/frames",
#                 # "/mnt/nas00/lk/pico/Experiments/acc_test/open-field-test/normal/8calcium/frames", 


#                 "/mnt/nas01/LAR/pico/Experiments/social/148female/0422enrichenvironment/calcium/3/107/frames",
#                 "/mnt/nas01/LAR/pico/Experiments/social/148female/0422enrichenvironment/calcium/5/152/frames",
#                 # "/mnt/nas01/LAR/pico/Experiments/social/148female/0422enrichenvironment/calcium/6/108/frames"
            
                
#               ]
# data_paths = [
    
    
#     # # trial m2-m1
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m2-m1/calcium/2/20-24-21-843/frames",
#     # # trial m1-m3"
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m1-m3/calcium/1/20-41-16-942/frames",
    
#     # # trial m2-m1 additional
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m2-m1_additional/calcium/2/22-15-29-748/frames",
    
#     # # trial m3-m2
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m3-m2/calcium/2/19-50-36-186/frames",
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m3-m2/calcium/2/19-58-58-422/frames",
    
#     # # trial m4-m2
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m4-m2/calcium/2/20-59-32-643/frames",
    
#     # # trial m1-m3 mouse 2 rank 3
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m1-m3/calcium/3/20-41-13-550/frames",
    
#     # # trial m3-m2 mouse 2 rank 3
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m3-m2/calcium/3/19-50-34-479/frames",
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m3-m2/calcium/3/19-58-56-617/frames",
    
#     # # trial m4-m3 mouse 2 rank 3
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m4-m3/calcium/3/20-11-35-380/frames",
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m4-m3/calcium/3/20-12-34-909/frames",
    
#     # # trial m1-m4 mouse 3 rank 2
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m1-m4/calcium/4/19-14-01-316/frames",
    
#     # # trial m1-m4 additional
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m1-m4_additional/calcium/4/22-29-31-552/frames",
    
#     # # trial m4-m2 mouse 3 rank 2
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m4-m2/calcium/4/20-59-02-032/frames",
    
#     # # trial m4-m3 mouse 3 rank 2
#     # "/mnt/nas01/LAR/pico/Experiments/tube_test/20250413/trial_m4-m3/calcium/4/20-09-49-657/frames"

#     # "/mnt/nas00/lk/pico/Experiments/acc_test/angular-velocity-test/16_angular/16dark_calcium/frames"

#     # "/mnt/nas01/zyx/3d/12-may-25/17-53-11-888/frames",
#     # "/mnt/nas01/zyx/3d/12-may-25/18-20-57-983/frames"

#     # "/mnt/nas01/LAR/autism/mice51/17-May-25/21-03-35-302/frames",
#     # "/mnt/nas00/lk/pico/Experiments/acc_test/angular-velocity-test/16_angular/16dark_calcium/frames"

#     # "/mnt/nas01/zwh/bbt/3MOUSE/30-Mar-25/21-27-20-946/frames",
#     # "/mnt/nas01/zwh/bbt/5MOUSE/30-Mar-25/23-42-57-913/frames",
#     # "/mnt/nas01/zwh/bbt3/10-Jun-25/18-18-13-140/frames",

#     "/mnt/nas01/LAR/pico/Experiments/social/autismmale/250614test/frames"


# ]

import os

# root_dir = "/mnt/nas01/LAR/pico/Experiments/hierarchy/SAM_train/148d/fed/0515"  
# root_dir = "/mnt/nas01/LAR/pico/Experiments/hierarchy/two_mice/20250626_fed_cage2"

# root_dir = "/mnt/nas01/LAR/pico/Experiments/hierarchy/two_mice/20250704_tube_cage2/group4/calcium"


# data_paths = []

# for dirpath, dirnames, filenames in os.walk(root_dir):
#     if os.path.basename(dirpath) == 'frames':
#         data_paths.append(dirpath)


# data_paths = [
#     # "/mnt/nas01/zyx/3d/tail_suspension/calcium/frames",
#     # "/mnt/nas01/zyx/3d/balanced_beam/0703/trial1/calcium/frames",
#     # "/mnt/nas01/zyx/3d/balanced_beam/0703/trial2/calcium/frames",
#     # "/mnt/nas01/LAR/pico/Experiments/FST/250720/calcium/00-22-39-076/frames"
#     "Y:\LAR\pico\Experiments\habitat_ultra_new\calcium\0228_n3_group1\m5\20-21-43-661/frames",
#     "Y:\zwh\BBT\5MOUSE\30-Mar-25\23-42-57-913/frames",
#     "Y:\LAR\pico\Experiments\social\148female\0426ee\calcium\152\26-Apr-25\01-22-48-154\frames",
#     "Y:\zwh\21-Jul-25\mouse5\17-20-02-201/frames",

#     ]

data_paths = [

    # r"Y:\LAR\pico\Experiments\social\148female\0426ee\calcium\152\26-Apr-25\01-22-48-154\frames",
    # r"Y:\zwh\21-Jul-25\mouse5\17-20-02-201\frames",

    # r"Y:\lk\pico\Experiments\multimice\20250103multimice5\5#new\frames",
    "/mnt/nas01/wy/line/BS/189/22-14-39-494/frames",
   

]


# data_paths = [p.replace("Y:", "/mnt/nas00").replace("\\", "/") for p in paths]

for path in data_paths:
    print(path)


out_paths = [datapath.replace("frames", "Analysis") for datapath in data_paths]


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
    with open('params.json', 'r') as json_file:
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
    # params['set_frame_num'] = 4000

    params['gpu_ids'] = 0

    # Run the command
    command = f"""
                    python process_script.py \
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





