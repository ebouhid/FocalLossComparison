#!/bin/bash

# 651 composition
nohup python deeplab.py --composition 6 5 1 \
--composition_name "All+NDVI" \
--batch_size 64 \
--encoder "resnet50" \
--experiment_name "FocalLoss_Comparison" \
--num_classes 4 \
--device "cuda" \
--gpu_id 0 \
--num_workers 10
