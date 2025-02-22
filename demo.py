import torch
from torch import nn
import train_utils.distributed_utils as utils
from train_utils import train_one_epoch, evaluate, create_lr_scheduler
from drive_dataset import DriveDataset
from src import UNet
import os as os
import numpy as np
from PIL import Image
from torchvision import transforms


if __name__ == '__main__':
    weights_path = "./save_weights/best_model_pure_unet.pth"
    img_path = "./DRIVE/test/images/01_test.tif"
    roi_mask_path = "./DRIVE/test/mask/01_test_mask.gif"
    
    
    assert os.path.exists(weights_path), f"weights {weights_path} not found."
    assert os.path.exists(img_path), f"image {img_path} not found."
    assert os.path.exists(roi_mask_path), f"image {roi_mask_path} not found."
    
    confmat = utils.ConfusionMatrix(2)
    dice = utils.DiceCoefficient(num_classes=2, ignore_index=255)
    
    data_transform = transforms.Compose([transforms.ToTensor(),
                                         transforms.Normalize(mean= (0.709, 0.381, 0.224),
                                                              std= (0.127, 0.079, 0.043))])
    if torch.cuda.is_available():
        device = torch.device(f'cuda:{torch.cuda.device_count()-1}')
    else:
        device = torch.device('cpu')
        
    model = UNet(in_channels=3, num_classes=2, base_c=32)
    model.load_state_dict(torch.load(weights_path, map_location='cpu')['model'])
    model.to(device)
    model.eval()
    
    roi_img = Image.open(roi_mask_path).convert('L')
    roi_img = np.array(roi_img)
    original_img = Image.open(img_path).convert('RGB')
    img = data_transform(original_img).unsqueeze(0)
    img_height, img_width = img.shape[-2:]
    init_img = torch.zeros((1, 3, img_height, img_width), device=device)
    model(init_img)
    output = model(img.to(device))

    prediction = output['out'].argmax(1).squeeze(0)
    prediction = prediction.to("cpu").numpy().astype(np.uint8)
    prediction[prediction == 1] = 255
    prediction[roi_img == 0] = 0
    mask = Image.fromarray(prediction)
    mask.save("test_result.pdf")

           