import torch
import torch.nn.functional as F

from app.model.model import BratsUNet

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

_model = None


def _build_model() -> BratsUNet:
    model = BratsUNet(
        in_channels=4,
        n_classes=4,
        n_channels=16,
    )
    model.load_state_dict(torch.load('model.pth', map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model


def preload_model() -> None:
    global _model
    if _model is None:
        _model = _build_model()


def get_model() -> BratsUNet:
    preload_model()
    return _model

def run_inference(tensor):
    model = get_model()
    tensor = tensor.to(DEVICE)
    with torch.no_grad():
        logits = model(tensor)
        probs = F.softmax(logits, dim=1)
        pred = torch.argmax(probs, dim=1)
    return pred.cpu().numpy()
