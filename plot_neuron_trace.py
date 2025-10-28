import os
import numpy as np
from scipy.io import loadmat
from PIL import Image
from scipy.sparse import csc_matrix
import matplotlib
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from Visualization.functions import plot_trace

if __name__ == "__main__":
    seg_out = r"Z:\lk\pico\Experiments\0718_headfixed\m16\17-24-05-295\analysis\seg_results_thresh_pmap_1"
    plot_trace(seg_out + '/seg_results_filtered.mat', 
               seg_out + '/infer_results_filtered.mat', 
               seg_out + '/Neuron_trace/', 
               frame_len = 1000, 
               neuron_step = 100)



