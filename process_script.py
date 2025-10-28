# %% [markdown]
# # PICO data processing pipeline
# ####  Authors: Yuanlong Zhang, Mingrui Wang, Lekang Yuan

# %%

# 1. frame time restoration
# 2. add bad frame replacement (done)
# 3. bad frame detection not fully correct, see 41 frame

# %%
import os
import time
from datetime import datetime

import torch
from ultralytics import YOLO

from preprocessing.YOLO_ROI_detection import YOLO_center_detect

# Set environment variables
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_MAX_THREADS'] = '8'

import cv2
import glob
import numpy as np
from scipy.ndimage import gaussian_filter
import matplotlib.pyplot as plt
import tifffile
from tqdm import tqdm
from skimage import io
from scipy.io import savemat, loadmat
import scipy.ndimage as ndi
import logging
from logging.handlers import RotatingFileHandler
from scipy import sparse

# %%
import caiman
from caiman import normcorre_function
from preprocessing import adjust_intensity_image, correct_image, detect_broken_frame, replace_array, get_vessel_mask, visualize_img_and_mask, detect_calcium_center
from deepdefinite import background_rejection
from segmentation import neuron_segmentation, convert_to_sparse, load_sparse_frames_from_mat, save_sparse_frames_to_mat
from Visualization import com, plot_cm, view_patches, nb_view_patches, save_video, filter_masks_by_roundness, plot_trace
import argparse
import math


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def str2tuple(v):
    try:
        return tuple(map(int, v.strip("()").split(',')))
    except ValueError:
        raise argparse.ArgumentTypeError("Tuple of integers expected.")


def arg_parse():
# %%

    parser = argparse.ArgumentParser(description='Process script arguments')
    # flow control
    parser.add_argument('--jump_to_rmbg', type=str2bool, default=False, help='this one assume you have done the MC and want to redo the rest')
    parser.add_argument('--jump_to_seg', type=str2bool, default=False, help='this one assume you have done the RMBG and want to redo the rest')
    parser.add_argument('--jump_to_vis', type=str2bool, default=False, help='this one assume you have done the SEG and want to redo the rest')

    # reading
    parser.add_argument('--set_frame_num', type=int, default=0, help='Define the frame number. If 0, the program will automatically detect the frame number')
    parser.add_argument('--data_path', type=str, default="/mnt/nas01/wy/line/BS/189/22-14-39-494/frames", help='Path to the data directory')
    parser.add_argument('--out_path', type=str, default="/mnt/nas01/wy/line/BS/189/22-14-39-494/Analysis", help='Path to the output directory')

    # motion registration
    parser.add_argument('--fr', type=int, default=10, help='Frame rate')
    parser.add_argument('--mc_chunk_size', type=int, default=1000, help='Chunk size for motion correction')
    parser.add_argument('--save_movie', type=str2bool, default=True, help='Flag to save the motion corrected movie')
    parser.add_argument('--max_shifts', type=str2tuple, default=(100, 100), help='Maximum allowed rigid shift in pixels')
    parser.add_argument('--strides', type=str2tuple, default=(96, 96), help='Create a new patch every x pixels for pw-rigid correction')
    parser.add_argument('--overlaps', type=str2tuple, default=(48, 48), help='Overlap between patches')
    parser.add_argument('--num_frames_split', type=int, default=100, help='Length in frames of each chunk of the movie')
    parser.add_argument('--max_deviation_rigid', type=int, default=3, help='Maximum deviation allowed for patch with respect to rigid shifts')
    parser.add_argument('--pw_rigid', type=str2bool, default=False, help='Flag for performing rigid or piecewise rigid motion correction')
    parser.add_argument('--shifts_opencv', type=str2bool, default=True, help='Flag for correcting motion using bicubic interpolation')
    parser.add_argument('--border_nan', type=str, default='copy', help='Replicate values along the boundary')
    parser.add_argument('--downsample_ratio', type=float, default=0.1, help='Downsample ratio for displaying purpose')

    # preprocessing
    parser.add_argument('--crop_parameter', type=int, nargs='+', default=[153, 303, 1000, 1000], help='Crop parameters')
    parser.add_argument('--intensity_corr_flag', type=str2bool, default=False, help='do or do not conduct intensity correction')
    parser.add_argument('--bad_frame_detect_flag', type=str2bool, default=True, help='do or do not conduct bad_frame_detect_flag')

    # deepdefinite
    parser.add_argument('--up_sample', type=int, default=2, help='Do up sampling for better background rejection')
    parser.add_argument('--rmbg_chunk_size', type=int, default=2000, help='Chunk size for RMBG model')
    parser.add_argument('--rmbg_gsize', type=int, default=6, help='Neuron radius for background rejection')
    parser.add_argument('--ckpt_pth', type=str, default='utils/deepdefinite_ckpt_resize_2.pth', help='Path to the model checkpoint')
    parser.add_argument('--device', type=str, default='cuda', help='Device to use (cuda or cpu)')
    parser.add_argument('--gpu_ids', type=str, default='2', help='GPU ids')

    # segmentation. Note these parameters are for upsample 2 times
    parser.add_argument('--patch_size', type=int, default=500, help='Chopped patch size')
    parser.add_argument('--pixel_size', type=int, default=2, help='Pixel size')
    parser.add_argument('--minArea', type=int, default=45, help='Minimum neuron area')
    parser.add_argument('--avgArea', type=int, default=100, help='Average neuron area')
    parser.add_argument('--thresh_pmap', type=int, default=1, help='Threshold of probability map. Key parameter!')
    parser.add_argument('--thresh_mask', type=float, default=0.5, help='Area threshold for mask')
    parser.add_argument('--thresh_COM0', type=int, default=6, help='Initial merge threshold')
    parser.add_argument('--thresh_COM', type=int, default=9, help='Merge threshold')
    parser.add_argument('--cons', type=int, default=5, help='Minimum consecutive number of frames of active neurons')

    # save video
    parser.add_argument('--avi_quality', type=int, default=100, help='Quality of the saved AVI file')
    args = parser.parse_args()
    return args

# def setup_logger(out_path):
#     """
#     Sets up a logger with file handling, log rotation, and optional matplotlib suppression.
#
#     Args:
#         out_path: The directory where the log file will be created.
#     """
#
#     # Configure the logger
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s',
#         handlers=[
#             logging.FileHandler(f"{out_path}/logger.txt"),
#             logging.StreamHandler()
#         ]
#     )
#
#     # Optionally suppress matplotlib font manager messages
#     logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
#
#     return logging.getLogger(__name__)

def setup_logger(out_path):
    """
    Sets up a logger with file handling, log rotation, and optional matplotlib suppression.

    Args:
        out_path: The directory where the log file will be created.
    """

    # Optionally suppress matplotlib font manager messages
    logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(f"{out_path}/log_file.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger



def PICO_processing(args):

    # %% [markdown]
    # flow control
    jump_to_rmbg = args.jump_to_rmbg
    if jump_to_rmbg:
        jump_to_seg = args.jump_to_seg
        if jump_to_seg:
            jump_to_vis = args.jump_to_vis
        else:
            jump_to_vis = False
    else:
        jump_to_seg = False
        jump_to_vis = False
        
        
    # read
    set_frame_num = args.set_frame_num
    out_path = args.out_path
    data_path = args.data_path
    
    # motion correction
    fr = args.fr
    mc_chunk_size = args.mc_chunk_size
    save_movie = args.save_movie
    max_shifts = args.max_shifts
    strides = args.strides
    overlaps = args.overlaps
    num_frames_split = args.num_frames_split
    max_deviation_rigid = args.max_deviation_rigid
    pw_rigid = args.pw_rigid
    shifts_opencv = args.shifts_opencv
    border_nan = args.border_nan
    downsample_ratio = args.downsample_ratio

    # preprocessing
    crop_parameter = args.crop_parameter
    intensity_corr_flag = args.intensity_corr_flag
    bad_frame_detect_flag = args.bad_frame_detect_flag
    # deepdefinite
    up_sample = args.up_sample
    if up_sample > 1:
        up_sample_flag = True
    else:
        up_sample_flag = False
    rmbg_chunk_size = args.rmbg_chunk_size
    rmbg_gsize = args.rmbg_gsize
    ckpt_pth = args.ckpt_pth
    device = args.device
    gpu_ids = args.gpu_ids

    # segmentation
    patch_size = args.patch_size
    pixel_size = args.pixel_size
    minArea = args.minArea
    avgArea = args.avgArea
    thresh_pmap = args.thresh_pmap
    thresh_mask = args.thresh_mask
    thresh_COM0 = args.thresh_COM0
    thresh_COM = args.thresh_COM
    cons = args.cons

    # save
    avi_quality = args.avi_quality
        
    # %%
    mc_out = os.path.join(out_path, 'mc')
    preprocess_out = os.path.join(out_path, 'preprocess')
    rmbg_out = os.path.join(out_path, 'rmbg')
    seg_out = os.path.join(out_path, f'seg_results_thresh_pmap_{thresh_pmap}')

    os.makedirs(mc_out, exist_ok=True)
    os.makedirs(rmbg_out, exist_ok=True)
    os.makedirs(preprocess_out, exist_ok=True)
    os.makedirs(seg_out, exist_ok=True)

    # %% print all parameeters to the log file
    logger = setup_logger(out_path)
    logger.debug('Logger initialized. out_path: %s', out_path)  # Debug message to verify setup

    logger.info('=======> Arguments <=======')

    start_time = datetime.now()
    logger.info(f'start time: {start_time}')

    for arg in vars(args):
        logger.info(f'{arg}: {getattr(args, arg)}')

    if set_frame_num == 0: # we don't know the frame number
        frame_num = len(glob.glob(data_path + '/*.jpg'))
        print(frame_num)
    else:
        frame_num = set_frame_num

    if not jump_to_rmbg:
        # determine good frames and read
        flag_array = []
        video = []
        logger.info('=======>bad frame detection<=======\n')
        # read and preprocess. This will take a while
        for i in tqdm(range(0, frame_num)):
            path = os.path.join(data_path, 'frame_'+str(i)+'.jpg')
            img = cv2.imread(path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            video.append(img)
            if bad_frame_detect_flag:
                flag = detect_broken_frame(img)
            else:
                flag = False
            
            flag_array.append(flag)
            if flag:
                print(f'Broken frame detected at frame_{str(i)}.jpg')

    # if not jump_to_rmbg:
    #     # determine good frames and read
    #     flag_array = []
    #     video = []
    #     logger.info('=======>bad frame detection<=======\n')
    #     # read and preprocess. This will take a while
    #     previous_frame = None  # Variable to store the previous frame
    #     for i in tqdm(range(0, frame_num)):
    #         path = os.path.join(data_path, 'frame_' + str(i) + '.jpg')
            
    #         try:
    #             img = cv2.imread(path)
    #             if img is None:
    #                 raise ValueError("Failed to load image.")  # Handling for invalid image
            
    #             img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
    #             # Check if the frame is all black (i.e., all pixel values are 0)
    #             if np.mean(img)<8:
    #                 if previous_frame is not None:
    #                     print(f"All-black frame detected at frame_{str(i)}. Replacing with the previous frame.")
    #                     img = previous_frame  # Replace the current frame with the previous one
    #                 else:
    #                     print(f"All-black frame detected at frame_{str(i)}. No previous frame available.")
            
    #         except cv2.error as e:
    #             # Handle corrupt JPEG data error
    #             print(f"Corrupt JPEG data at frame_{str(i)}. Replacing with the previous frame.")
    #             if previous_frame is not None:
    #                 img = previous_frame  # Replace with previous frame if corrupt
    #             else:
    #                 img = np.zeros_like(img)  # Handle case if no previous frame available (you could use a blank frame)
            
    #         video.append(img)
            
    #         if bad_frame_detect_flag:
    #             flag = detect_broken_frame(img)
    #         else:
    #             flag = False
            
    #         flag_array.append(flag)
    #         if flag:
    #             print(f'Broken frame detected at frame_{str(i)}.jpg')
            
    #         # Store the current frame as the previous one for the next iteration
    #         previous_frame = img

        # now print correct reading list
        replace_item = replace_array(flag_array)
        print(replace_item)

        for item in replace_item:
            bad_idx, good_idx = item[0], item[1]
            video[bad_idx] = video[good_idx].copy()


        # save the corrected video
        save_video(video, fr, out_path + '/badframe_replaced.avi', quality=avi_quality)

        #  MC
        logger.info('=======>motion correction<=======\n')
        
        N_chunk = math.ceil(len(video) / mc_chunk_size)
        template = None
        mc_video = []
        c, dview, n_processes = caiman.cluster.setup_cluster(
            backend='local', n_processes=24, single_thread=False)

        for i in tqdm(range(N_chunk)):
            image_stack = np.stack(video[i*mc_chunk_size:(i+1)*mc_chunk_size], axis=0)
            # Print the shape of the resulting stack
            print(image_stack.shape)

            tmp_outpath = f'{mc_out}/chunk_{i}'
            os.makedirs(tmp_outpath, exist_ok = True)

            # call function
            m_nonrig, bord_px_rig, bord_px_els, template = normcorre_function(video=image_stack, # a numpy array of the video
                                fr=fr,
                                max_shifts=max_shifts, 
                                strides=strides, 
                                overlaps=overlaps, 
                                max_deviation_rigid= max_deviation_rigid, 
                                shifts_opencv=shifts_opencv, 
                                border_nan=border_nan, 
                                downsample_ratio=downsample_ratio,
                                outpath=tmp_outpath,
                                template=template,
                                save_movie=save_movie,
                                dview=dview)
            
            frames_list = [m_nonrig[i] for i in range(m_nonrig.shape[0])]
            mc_video.extend(frames_list)

        caiman.stop_server(dview=dview)
        # replace the original video with the motion corrected video
        video = mc_video
        # clear the memory
        del mc_video

        # save video
        save_video(video, fr, out_path + '/mc.avi', quality=avi_quality)

        # save all mc video
        tmp_outpath = f'{mc_out}/all'
        os.makedirs(tmp_outpath, exist_ok = True)
        for i, frame in tqdm(enumerate(video)): # save back to a list
            # save
            tifffile.imwrite(os.path.join(tmp_outpath, 'frame_'+str(i)+'.tif'),  frame.astype(np.uint8))  # Save as TIFF file


        logger.info('=======>do upsampling<=======\n')
        # intensity correction from good frame no.1
        if intensity_corr_flag:
            tmp_img = video[0]
            weight_map, I_change = adjust_intensity_image(tmp_img)
        else:
            weight_map = np.ones_like(video[0], dtype=np.float64)
            I_change = 1

        # load precalibrated distortion correction map
        # Correction_Map = np.load('utils/CorrectionMap.npz')
        Correction_Map = np.load('/data/home/angran/BBNC/code/PICO_ca_processing/utils/CorrectionMap.npz')
        error_XX_new = Correction_Map['error_XX_new']
        error_YY_new = Correction_Map['error_YY_new']
        

        fig, ax = plt.subplots(1, 2, figsize=(10, 5))
        ax[0].imshow(error_XX_new)
        ax[1].imshow(error_XX_new)

        # intensity uniformity
        logger.info('=======>field distortion correction and intensity uniformity<=======\n')
        video_preprocessed = []  # stored in a list
        max_v = 0

        logger.info(f"Former crop_parameter is {args.crop_parameter}" )

        # model = YOLO("utils/yolo_v8s.pt")
        model = YOLO("/data/home/angran/BBNC/code/PICO_ca_processing/utils/yolo_v8s.pt")
        crop_parameter_init = crop_parameter.copy()

        img_change_frame = video[0].astype(np.float64) * weight_map
        img_change_frame = correct_image(img_change_frame, error_XX_new, error_YY_new)
        img_change_frame = cv2.normalize(img_change_frame, None, 0, 255, cv2.NORM_MINMAX)
        img_change_frame = img_change_frame.astype(np.uint8)

        # frame_0 = cv2.imread(os.path.join(data_path, "frame_0.jpg"), cv2.IMREAD_GRAYSCALE)

        crop_parameter = YOLO_center_detect(model, img_change_frame, crop_parameter_init, output_dir=out_path)

        logger.info(f"Corrected crop_parameter is as follows: {crop_parameter}")

        del model

        for frame in tqdm(video):
            # print(f'Processing frame {i}')
            # adjust illumination
            img_change_frame = frame.astype(np.float64) * weight_map
            
            # distortion correction, no upsampling here
            img_change_frame = correct_image(img_change_frame, error_XX_new, error_YY_new)

            # crop image
            img_change_frame = img_change_frame[crop_parameter[0]:crop_parameter[0]+crop_parameter[2], 
                                                crop_parameter[1]:crop_parameter[1]+crop_parameter[3]]
            
            if up_sample_flag: # TODO
                # do upsampling, 2 times larger
                tmp_img = img_change_frame.astype(np.float32)
                tmp_img = cv2.resize(tmp_img, (tmp_img.shape[1]*up_sample, tmp_img.shape[0]*up_sample), 
                                        interpolation=cv2.INTER_CUBIC)
                tmp_img = tmp_img.astype(np.float16)
            else:
                tmp_img = img_change_frame.astype(np.float16)
            video_preprocessed.append(tmp_img) # do not using float32 to save memory
            
            # update max value
            max_v = max(max_v, np.max(img_change_frame))
            
        # release the ram
        del video
        # save preprocessed video

        logger.info('=======>save preprocessed video<=======\n')
        for i, frame in tqdm(enumerate(video_preprocessed)): # save back to a list
            # save
            norm_frame = (frame / max_v) * 255 # keep it in uint8
            tifffile.imwrite(os.path.join(preprocess_out, 'frame_'+str(i)+'.tif'),  norm_frame.astype(np.uint8))  # Save as TIFF file
            video_preprocessed[i] = norm_frame

    
        # save video
        save_video(video_preprocessed, fr, out_path + '/preprocessed.avi', quality=avi_quality)

        # %% get vessel mask
        logger.info('=======>get vessel mask<=======\n')
        norm_img = np.array(video_preprocessed[0]).astype(np.float32)
        norm_img = norm_img / norm_img.max()
        # vessel_img, vessel_mask = get_vessel_mask(norm_img , 'utils/vessel_model.pt')
        vessel_img, vessel_mask = get_vessel_mask(norm_img, '/data/home/angran/BBNC/code/PICO_ca_processing/utils/vessel_model.pt')

        # visualization
        visualize_img_and_mask(vessel_img, vessel_mask, save_path=os.path.join(out_path, 'vessel_mask.png'))
        plt.close()

        tifffile.imwrite(os.path.join(out_path, 'vessel_mask.tif'), ((vessel_mask > 0) * 255).astype(np.uint8))
        tifffile.imwrite(os.path.join(out_path, 'vessel_image.tif'), (vessel_img*255).astype(np.uint8))
  
        # %%
        logger.info(f'video_preprocessed: list, {video_preprocessed[0].dtype}')
        logger.info(f'vessel_mask: dtype {vessel_mask.dtype}, min {vessel_mask.min()}, max {vessel_mask.max()}')

        # %% [markdown]
        # # DeepDefinite 

        # %%
        # do the background subtraction
        
        del video_preprocessed
    else:

        logger.info('MC processing jumped. loading preprocessed video<=======\n')
        # load vessel image and vessel mask
        vessel_img = cv2.imread(os.path.join(out_path, 'vessel_image.tif'), cv2.IMREAD_GRAYSCALE).astype(np.float16)
        vessel_mask = cv2.imread(os.path.join(out_path, 'vessel_mask.tif'), cv2.IMREAD_GRAYSCALE).astype(np.float32)
        vessel_mask = vessel_mask / 255
    
    logger.info('=======>background subtraction<=======\n')
    
    tmp_outpath = f'{preprocess_out}'
    tif_files = glob.glob(os.path.join(tmp_outpath, '*.tif'))    
    rmbg_chunk_num = math.ceil(len(tif_files) / rmbg_chunk_size)  
    if not jump_to_seg:
        # still, we chop it to chunks
        for i in tqdm(range(rmbg_chunk_num)):
            tmp_output_dir = os.path.join(rmbg_out, f'chunk_{i}')
            os.makedirs(tmp_output_dir, exist_ok=True)
            
            # load preprocessed video
            tmp_video = []
            logger.info(f'=======>background subtraction: chunk {i} loading<=======\n')
            for j in range(i * rmbg_chunk_size, (i + 1) * rmbg_chunk_size):
                if j >= len(tif_files): # safeguard
                    break
                path = os.path.join(tmp_outpath, 'frame_'+str(j)+'.tif')
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float16)
                tmp_video.append(img)
                
            # do the model
            logger.info(f'=======>background subtraction: chunk {i} processing<=======\n')
            _, _ = background_rejection(
                                    video = tmp_video, # where the cleared data stored
                                    gsize = rmbg_gsize, # neuron radius
                                    device = device, # utilize GPU or CPU
                                    gpu_ids =gpu_ids, # GPU ids
                                    ckpt_pth = ckpt_pth, # model path
                                    output_dir = tmp_output_dir # output directory
                                    )
        # if i == 0:
        #     neuron_video = tmp_neuron_video
        # else:
        #     neuron_video = np.concatenate((neuron_video, tmp_neuron_video), axis=0)

    #
    # read all
    if not jump_to_vis:
        for i in tqdm(range(rmbg_chunk_num)):
            tmp_output_dir = os.path.join(rmbg_out, f'chunk_{i}/rmbg')
            tmp_tif_files = glob.glob(os.path.join(tmp_output_dir, '*.tif'))

            # load preprocessed video
            tmp_video = []
            logger.info(f'=======>reload background subtraction: chunk {i} loading<=======\n')
            for j in range(len(tmp_tif_files)):
                path = os.path.join(tmp_output_dir, 'frame_'+str(j)+'.tif')
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE).astype(np.float16)
                tmp_video.append(img)
                
            # list to array
            tmp_neuron_video = np.array(tmp_video)
            if i == 0:
                neuron_video = tmp_neuron_video
            else:
                neuron_video = np.concatenate((neuron_video, tmp_neuron_video), axis=0)
                
        del tmp_video
        del tmp_neuron_video
    
    # %% save rmbg video
    if not jump_to_seg:
        # save video
        if not jump_to_seg:
            save_video(neuron_video, fr, out_path + '/rmbg.avi', quality=avi_quality)

        logger.info('=======>save RMBG video<=======\n')
        tmp_outpath = f'{rmbg_out}/all'
        os.makedirs(tmp_outpath, exist_ok = True)
        for i, frame in tqdm(enumerate(neuron_video)): # save back to a list
            tifffile.imwrite(os.path.join(tmp_outpath, 'frame_'+str(i)+'.tif'),  frame.astype(np.uint8))  # Save as TIFF file
        

    # %% [markdown]
    # # Segmentation
    # %%
    # do the segmentation. We have to do patch based segmentation
    # A is a N x H x W array, where N is the number of neurons, H and W are the height and width of the frames.
    # C is a N x T array, where N is the number of neurons, T is the frame number.
    logger.info('=======>segmentation<=======\n')
    
    # %% 
    # Iterate over patches
    if not jump_to_vis: # flow control
        _, d1, d2, = neuron_video.shape
        begin_to_concat = False

        for i in range(0, d1, patch_size):
            for j in range(0, d2, patch_size):
                logger.info(f'=======>segment patch {i},{j}<=======\n')
                # Extract patch
                patch = neuron_video[:, i:i+patch_size, j:j+patch_size]
                tmp_seg_out = os.path.join(seg_out, f'patch_{i}_{j}')
                os.makedirs(tmp_seg_out, exist_ok=True)
                A_tmp, C_tmp = neuron_segmentation(patch,
                                    tmp_seg_out,
                                    pixel_size = pixel_size,
                                    minArea = minArea,
                                    avgArea = avgArea,
                                    thresh_pmap = thresh_pmap,
                                    thresh_mask = thresh_mask,
                                    thresh_COM0 = thresh_COM0,
                                    thresh_COM = thresh_COM,
                                    cons = cons)

                if isinstance(A_tmp, np.ndarray):
                    # enhance A_tmp to a global size
                    A_tmp2 = np.zeros([A_tmp.shape[0], d1, d2], dtype=bool)
                    A_tmp2[:, i:i+patch_size, j:j+patch_size] = A_tmp

                    if not begin_to_concat:
                        A = A_tmp2
                        C = C_tmp
                        begin_to_concat = True

                    else:
                        A = np.concatenate((A, A_tmp2), axis=0)
                        C = np.concatenate((C, C_tmp), axis=0)
        # %%
        logger.info(f"A.shape: {A.shape}")
        logger.info(f"A.dtype: {A.dtype}")
        logger.info(f"C.shape: {C.shape}")
        logger.info(f"C.dtype: {C.dtype}")


        # %%
        # calculate center of these neuorns
        logger.info('=======>calculate center of these neuorns<=======\n')
        d1 = A.shape[2] # x, width
        d2 = A.shape[1] # y, height
        A_2d = A.reshape(A.shape[0], -1).T
        cm_chunk = 1000
        cm_chunk_num = math.ceil(A_2d.shape[1] / cm_chunk)
        for i in tqdm(range(cm_chunk_num)):
            cm_tmp = com(A=A_2d[:, i*cm_chunk:(i+1)*cm_chunk].astype(np.float32), d1 = d1, d2 = d2) # A no longer be a boolen array
            if i == 0:
                cm = cm_tmp
            else:
                cm = np.concatenate((cm, cm_tmp), axis=0)

        # important: cm is (x, y) but not (h, w). TODO check!
        # save A and C and cm
        del A_2d
        sparse_frames = convert_to_sparse(A)
        assert A.shape[0] == C.shape[0]
        save_sparse_frames_to_mat(sparse_frames, seg_out + '/seg_results.mat')
        savemat(seg_out + '/infer_results.mat', {'C': C})
        savemat(seg_out + '/cm.mat', {'cm': cm})
        
        result_name = seg_out + '/SEG_SUM.png'
        mask_sum = np.sum(A, axis=0).astype('uint8')
        mask_sum = mask_sum * int(255/np.max(mask_sum))
        io.imsave(result_name, mask_sum)
    
    else:
        logger.info('=======>loading segmentation results<=======\n')
        # load A
        A = load_sparse_frames_from_mat(filename=seg_out + '/seg_results.mat')
        A = np.array(A)
        d1 = A.shape[2] # x, width
        d2 = A.shape[1] # y, height
        # load C
        C = loadmat(seg_out + '/infer_results.mat')['C']
        # load cm
        cm = loadmat(seg_out + '/cm.mat')['cm']
        cm_chunk = 1000
    # %%
    # visualize cm
    # Plotting
    logger.info('=======>visualization<=======\n')
    
    plot_cm(cm, d1, d2, save_path=os.path.join(seg_out, 'cm.png'), save_svg_path=os.path.join(seg_out, 'cm.svg'))
    plt.pause(5)
    plt.close()
    # %%
    # revise the segments without the vessel contamination
    invalid_idx = []
    vessel_mask_resize = cv2.resize(vessel_mask, (d1, d2), interpolation=cv2.INTER_NEAREST) # so the size does not matter
    # do not using interpolation=cv2.INTER_CUBIC, since we are dealing with binary mask
    
    # remove small, disconnected regions
    min_size = 300
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(vessel_mask_resize.astype(np.uint8))
    filtered_mask = np.zeros_like(vessel_mask_resize)
    # Iterate over the connected components
    for label in range(1, num_labels):  # Skip background (label 0)
        if stats[label, cv2.CC_STAT_AREA] >= min_size:
            filtered_mask[labels == label] = 1  # Keep the region
            
    vessel_mask_resize = filtered_mask
    tifffile.imwrite(os.path.join(out_path, 'vessel_mask_clean.tif'), ((vessel_mask_resize > 0) * 255).astype(np.uint8))
 
    # do some dilating
    vessel_mask_resize = cv2.dilate(vessel_mask_resize.astype(np.float32), np.ones((7, 7), np.uint8), iterations=1)
    tifffile.imwrite(os.path.join(out_path, 'vessel_mask_dilate.tif'), ((vessel_mask_resize > 0) * 255).astype(np.uint8))

    for i in range(len(cm)):
        if vessel_mask_resize[int(cm[i][1]), int(cm[i][0])] > 0: # note cm is (x, y) but not (h, w)
            invalid_idx.append(i)
  
    del cm
    
    # %%
    A_filtered = np.delete(A, invalid_idx, axis=0)
    C_filtered = np.delete(C, invalid_idx, axis=0)
    
    # %% additional shape filtering
    invalid_idx2 = filter_masks_by_roundness(A_filtered, max_axis_ratio=3, min_occupancy=0.5) # TODO test
    
    A_filtered = np.delete(A_filtered, invalid_idx2, axis=0)
    C_filtered = np.delete(C_filtered, invalid_idx2, axis=0)
    
    # save filtered segments
    result_name = seg_out + '/SEG_SUM_filtered.png'
    mask_sum = np.sum(A_filtered, axis=0).astype('uint8')
    mask_sum = mask_sum * int(255/np.max(mask_sum))
    io.imsave(result_name, mask_sum)
    # %%
    A_2d_filtered = A_filtered.reshape(A_filtered.shape[0], -1).T
    
    cm_chunk_num = math.ceil(A_2d_filtered.shape[1] / cm_chunk)
    for i in tqdm(range(cm_chunk_num)):
        cm_tmp = com(A=A_2d_filtered[:, i*cm_chunk:(i+1)*cm_chunk].astype(np.float32), d1 = d1, d2 = d2) # A no longer be a boolen array
        if i == 0:
            cm_filtered = cm_tmp
        else:
            cm_filtered = np.concatenate((cm_filtered, cm_tmp), axis=0)
            
    plot_cm(cm_filtered, d1, d2, save_path=os.path.join(seg_out, 'cm_wo_vessel.png'), save_svg_path=os.path.join(seg_out, 'cm_wo_vessel.svg'))
    plt.pause(5)
    plt.close()
    # %%
    # comparison
    visualize_img_and_mask(vessel_img.astype(np.float32), np.sum(A, axis=0).astype(np.float32), 
                           np.sum(A_filtered, axis=0).astype(np.float32),
                           save_path=os.path.join(seg_out, 'neuron_mask.png'),
                           save_svg_path=os.path.join(seg_out, 'neuron_mask.svg')
                           )
    plt.pause(5)
    plt.close()
    # %%
    # save A and C and cm
    sparse_frames = convert_to_sparse(A_filtered)
    save_sparse_frames_to_mat(sparse_frames, seg_out + '/seg_results_filtered.mat')
    savemat(seg_out + '/infer_results_filtered.mat', {'C': C_filtered})
    savemat(seg_out + '/cm_filtered.mat', {'cm': cm_filtered})
    # %% [markdown]
    # # Visualize and save

    # %%
    # visualize and save. This can take a very long time

    #%% plot the temporal signals
    # nframes = len(neuron_video)
    # YrA = np.reshape(neuron_video, (nframes, d1 * d2))
    # YrA = np.transpose(YrA)
    # b = np.zeros((d1 * d2, 1), dtype = 'float32')
    # f = np.zeros((1, len(neuron_video)), dtype = 'float32')
    logger.info('Plotting Traces.....................\n')
    plot_trace(seg_out + '/seg_results_filtered.mat', 
               seg_out + '/infer_results_filtered.mat', 
               seg_out + '/Neuron_trace/', 
               frame_len = 1000, 
               neuron_step = 100)

    end_time = datetime.now()

    logger.info(f'end time: {end_time}')
    logger.info(f'{end_time-start_time} spent for {frame_num} calcium processing.')
    
 
if __name__ == '__main__':
    # parsing
    args = arg_parse()

    # run
    PICO_processing(args)