import os
import time
import datetime
import tifffile
import numpy as np
import torch
from .utils import crop_patches, concat_patches, save_video
from .model import BG_Rejection

from tqdm import tqdm

def background_rejection(
                         video,
                         gsize = 6, # neuron radius
                         ckpt_pth = '',
                         patch_size ='(128, 128, 128)', # background rejection patch size
                         stride_size = '(96, 96, 96)', # background rejection stride size
                         batch_size = 4,
                         device = 'cuda', # utilize GPU or CPU
                         gpu_ids ='0', # GPU ids
                         output_dir = '',
                         in_channels = 1,
                         out_channels = 1,
                         f_maps = 32):
    
    # restrict the devices
    os.environ["CUDA_VISIBLE_DEVICES"] = gpu_ids
    device = torch.device(device)

    # mkdir
    os.makedirs(os.path.join(output_dir, 'bg'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'rmbg'), exist_ok=True)
        

    # load model and pretrained weights
    net = BG_Rejection(in_channels=in_channels, out_channels=out_channels, f_maps=f_maps,
                       gsize=gsize, infer=True)
    if torch.cuda.device_count() > 1:
        net = torch.nn.DataParallel(net)
    net.to(device)
    
    # checkpoint = torch.load(ckpt_pth, map_location='cpu')
    # net.load_state_dict(checkpoint['net'])

    # checkpoint = torch.load(ckpt_pth, map_location='cpu',)
    # new_state_dict = {}
    # for k, v in checkpoint['net'].items():
    #     new_key = "module." + k
    #     new_state_dict[new_key] = v
    # net.load_state_dict(new_state_dict)
    checkpoint = torch.load(ckpt_pth, map_location='cpu')

    try:
        # Attempt to load the checkpoint directly
        net.load_state_dict(checkpoint['net'])
    except:
        # If there's a KeyError, adjust the keys by adding "module." prefix
        new_state_dict = {}
        for k, v in checkpoint['net'].items():
            new_key = "module." + k
            new_state_dict[new_key] = v
        net.load_state_dict(new_state_dict)

    # patching
    patch_size = eval(patch_size)
    stride_size = eval(stride_size)
    overlap_size = (patch_size[0] - stride_size[0],
                    patch_size[1] - stride_size[1],
                    patch_size[2] - stride_size[2])


    # load data
    # image_list_path = glob.glob(os.path.join(dataset_dir, '*.tif*'))
    
    # # TODO pay attention to the sort
    
    # # load the image to the RAM, T x H x W format
    # image_list = [tifffile.imread(image).astype(np.float32) for image in image_list_path]
    video = np.stack(video, axis=0) # not normalized to 0-1
    frameN = video.shape[0]
    
    with torch.no_grad():
        net.eval()

        start_time = time.time()
        origin_shape = video.shape

        # preprocessing
        video_mean = np.mean(video, axis=0, keepdims=True)
        video = video - video_mean
        
        # patch chopping
        video_patches, patch_num = crop_patches(video, patch_size, stride_size)
        iter_num = len(video_patches) // batch_size if len(video_patches) % batch_size == 0 else len(
            video_patches) // batch_size + 1

        bg_patches = []
        neuron_patches = []
        for j in range(iter_num):
            input = torch.as_tensor(video_patches[j * batch_size:(j + 1) * batch_size],
                                    dtype=torch.float32, device=device).unsqueeze(1)
            out_bg, out_neuron = net(input)

            out_bg = out_bg.squeeze(1)
            out_neuron = out_neuron.squeeze(1)

            bg_patches.append(out_bg.detach().cpu().numpy().astype(np.float16))
            neuron_patches.append(out_neuron.detach().cpu().numpy().astype(np.float16))

            left_time = datetime.timedelta(seconds=int((time.time() - start_time) / (iter_num + j + 1) * ((iter_num - j - 1))))
            print('[Inference Video] [Pacthes: %d/%d] [ETA: %s]' % (j + 1, iter_num, str(left_time)))

        # do the stitching
        bg_patches = np.concatenate(bg_patches, axis=0)
        neuron_patches = np.concatenate(neuron_patches, axis=0)

        out_bg = concat_patches(bg_patches, origin_shape, patch_num, patch_size, stride_size, overlap_size)
        out_neuron = concat_patches(neuron_patches, origin_shape, patch_num, patch_size, stride_size,
                                            overlap_size)
        # save file
        out_bg = (out_bg + video_mean).clip(0, 255)
        out_neuron = out_neuron.clip(0, 255)
        
        
        # save video trunks
        for i in tqdm(range(frameN)):
            # note the clip is necessary, as the output may have negative values
            # tifffile.imwrite(os.path.join(output_dir, 'bg', 'frame_'+str(i)+'.tif'), out_bg[i].clip(0, 255).astype(np.uint8))
            tifffile.imwrite(os.path.join(output_dir, 'rmbg', 'frame_'+str(i)+'.tif'), out_neuron[i].clip(0, 255).astype(np.uint8))
 
        save_video(out_bg, 30, os.path.join(output_dir, 'bg', 'bg.avi'))
        save_video(out_neuron,  30, os.path.join(output_dir, 'rmbg.avi'))
        
        return out_bg, out_neuron


