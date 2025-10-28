# PICO Data Processing Pipeline

This document outlines the data processing pipelines for calcium imaging and calibration/non-calcium imaging using PICO.


## Prerequisites

- All image files are assumed to be in `.tif` format.

## Calcium Imaging Processing Pipeline

The calcium imaging processing pipeline includes the following steps:

1. **Image Loading**
   - Load `.tif` files for processing.
2. **Motion Correction**
   - Correct the motion
3. **Preprocessing for Each File**
   - **Image Cropping:** Crop images to a central 1200 x 1200 area from the original 1200 x 1600 size.
   - **Bad Frame Detection & Replacement:** Identify and replace frames that do not meet quality standards.
   - **Image Intensity Correction:** Adjust the intensity levels of the images for uniformity.
   - **Image Field Distortion Correction:** Correct any field distortion in the images.
4. **Vessel Extraction**
   - Perform vessel extraction. This step is executed only once.
5. **DeepDefinite De-background**
   - Apply DeepDefinite for background removal.
6. **Neuron Segmentation**
   - Segment neurons from the processed images.

## Calibration/Non-Calcium Imaging Processing Pipeline

The calibration/non-calcium imaging processing pipeline includes similar steps with slight adjustments:

1. **Image Loading**
   - Load `.tif` files for processing.
2. **Image Cropping**
   - Crop images to a central 1200 x 1200 area from the original 1200 x 1600 size.
3. **Bad Frame Detection & Replacement**
   - Identify and replace frames that do not meet quality standards.
4. **Image Intensity Correction**
   - Adjust the intensity levels of the images for uniformity.
5. **Image Field Distortion Correction**
   - Correct any field distortion in the images.

## Additional Notes

- Ensure that all `.tif` files are properly named and organized before starting the pipeline to facilitate smooth processing.
- It is recommended to verify the quality of the processed images at various stages of the pipeline to ensure optimal outcomes.