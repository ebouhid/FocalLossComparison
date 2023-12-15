from torch.utils.data import Dataset
import os
from PIL import Image
import numpy as np
import cv2


class XinguDataset(Dataset):
    def __init__(self,
                 scenes_dir,
                 masks_dir,
                 composition,
                 regions,
                 patch_size,
                 stride_size,
                 transforms=None):
        self.composition = composition
        self.patch_size = patch_size
        self.stride_size = stride_size

        self.img_path = scenes_dir
        self.msk_path = masks_dir

        self.image_paths = sorted(os.listdir(self.img_path))
        self.mask_paths = sorted(os.listdir(self.msk_path))

        self.images = []
        self.masks = []

        self.regions = regions
        self.transforms = transforms
        self.angle_inc = 45

        # load scenes
        for img_scene in self.image_paths:
            id = int((img_scene.split('_')[-1].split('.')[0])[1:])
            if id in regions:
                # get file extension
                ext = img_scene.split('.')[-1]
                if ext == 'npy':
                    self.images.append(
                    np.load(os.path.join(self.img_path, img_scene)))
                elif ext == 'png':
                    self.images.append(
                    np.asarray(
                        Image.open(os.path.join(self.img_path, img_scene))))
                else:
                    raise Exception('Invalid file extension')

        for msk_scene in self.mask_paths:
            id = int((msk_scene.split('_')[-1].split('.')[0])[1:])
            if id in regions:
                self.masks.append(
                    np.load(os.path.join(self.msk_path, msk_scene)).squeeze())

        # patchify
        self.img_patches = []
        self.msk_patches = []

        for image in self.images:
            height, width, _ = image.shape
            for i in range(0, height, self.stride_size):
                if (i + self.patch_size) > height:
                    continue
                for j in range(0, width, self.stride_size):
                    if (j + self.patch_size) > width:
                        continue
                    patch_image = image[i:i + self.patch_size,
                                        j:j + self.patch_size, :]
                    # image augmentation goes here
                    height_p, width_p = patch_image.shape[:2]
                    # rotation
                    angle = 0
                    if self.transforms is not None:
                        while angle < 360:
                            rot_matrix = cv2.getRotationMatrix2D(
                                (width_p / 2, height_p / 2), angle, 1.5)
                            patch_image_rot = cv2.warpAffine(
                                patch_image, rot_matrix, (width_p, height_p))
                            angle += self.angle_inc
                            self.img_patches.append(
                                patch_image_rot.transpose(2, 0, 1))
                    else:
                        self.img_patches.append(patch_image.transpose(2, 0, 1))

        for mask in self.masks:
            height, width = mask.shape
            for i in range(0, height, self.stride_size):
                if i + self.patch_size > height:
                    continue
                for j in range(0, width, self.stride_size):
                    if j + self.patch_size > width:
                        continue
                    patch_mask = mask[i:i + self.patch_size,
                                      j:j + self.patch_size]
                    # mask augmentation goes here
                    height_p, width_p = patch_image.shape[:2]
                    angle = 0
                    if self.transforms is not None:
                        while angle < 360:
                            rot_matrix = cv2.getRotationMatrix2D(
                                (width_p / 2, height_p / 2), angle, 1.5)
                            patch_mask_rot = cv2.warpAffine(
                                patch_mask, rot_matrix, (width_p, height_p))
                            angle += self.angle_inc
                            n_values = 4
                            patch_mask_rot = np.eye(n_values)[patch_mask_rot]
                            self.msk_patches.append(patch_mask_rot)
                    else:
                        n_values = 4
                        patch_mask = np.eye(n_values)[patch_mask]
                        self.msk_patches.append(patch_mask)

        assert len(self.images) == len(self.masks)
        assert len(self.img_patches) == len(self.msk_patches)

    def __len__(self):
        return len(self.img_patches)

    def __getitem__(self, idx):
        # get selected patches
        image = self.img_patches[idx]
        mask = self.msk_patches[idx]

        # create composition
        nbands = len(self.composition)
        combination = np.zeros((nbands, ) + image.shape[1:])

        for i in range(nbands):
            combination[i, :, :] = image[(self.composition[i] - 1), :, :]

        combination = np.float32(combination) / 255

        mask = np.float32(mask)
        mask = mask.transpose(2, 0, 1)

        combination = combination.astype(np.float32)

        return combination, mask
