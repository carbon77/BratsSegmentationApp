import torch
import torch.nn.functional as F

from app.model.model import BratsUNet

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

model = BratsUNet(
    in_channels=4,
    n_classes=4,
    n_channels=16,
)
model.load_state_dict(torch.load('../model/model.pth', map_location=DEVICE))
model.to(DEVICE)
model.eval()

def run_inference(tensor):
    tensor = tensor.to(DEVICE)
    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1)
        pred = torch.argmax(probs, dim=1)
    return pred.cpu().numpy()