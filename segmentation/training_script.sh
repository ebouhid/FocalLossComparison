#!/bin/bash

# 8 bands (All + NDVI) composition
nohup python deeplab.py --composition 6 5 1 \
--composition_name "All+NDVI" \
--batch_size 64 \
--encoder "resnet50" \
--experiment_name "Tri_Class_Baseline" \
--num_classes 4
