#!/usr/bin/env python3
"""Convert the BraTS PyTorch checkpoint used by this project to ONNX.

Example:
    python scripts/convert_model_to_onnx.py --checkpoint model.pth --output model.onnx
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn


class DoubleConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, num_groups: int = 4):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, 3, padding=1),
            nn.GroupNorm(num_groups, out_channels),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, 3, padding=1),
            nn.GroupNorm(num_groups, out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


class EncoderBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.double_conv = DoubleConv(in_channels, out_channels)
        self.pool = nn.MaxPool3d(2)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        skip = self.double_conv(x)
        x = self.pool(skip)
        return x, skip


class DecoderBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.up = nn.ConvTranspose3d(in_channels, out_channels, 2, stride=2)
        self.double_conv = DoubleConv(in_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        x = torch.cat([skip, x], dim=1)
        return self.double_conv(x)


class UNet(nn.Module):
    def __init__(self, in_channels: int = 4, n_classes: int = 4, n_channels: int = 16):
        super().__init__()
        self.encoder = nn.ModuleList([
            EncoderBlock(in_channels, n_channels),
            EncoderBlock(n_channels, 2 * n_channels),
            EncoderBlock(2 * n_channels, 4 * n_channels),
            EncoderBlock(4 * n_channels, 8 * n_channels),
        ])
        self.bottleneck = DoubleConv(8 * n_channels, 16 * n_channels)
        self.decoder = nn.ModuleList([
            DecoderBlock(16 * n_channels, 8 * n_channels),
            DecoderBlock(8 * n_channels, 4 * n_channels),
            DecoderBlock(4 * n_channels, 2 * n_channels),
            DecoderBlock(2 * n_channels, n_channels),
        ])
        self.out = nn.Conv3d(n_channels, n_classes, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skips = []
        for encoder in self.encoder:
            x, skip = encoder(x)
            skips.append(skip)

        x = self.bottleneck(x)
        for skip, decoder in zip(reversed(skips), self.decoder):
            x = decoder(x, skip)
        return self.out(x)


class BratsUNet(nn.Module):
    def __init__(self, in_channels: int = 4, n_classes: int = 4, n_channels: int = 16):
        super().__init__()
        self.model = UNet(in_channels, n_classes, n_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export BraTS UNet checkpoint to ONNX.")
    parser.add_argument("--checkpoint", type=Path, default=Path("model.pth"), help="Path to the PyTorch state_dict checkpoint.")
    parser.add_argument("--output", type=Path, default=Path("model.onnx"), help="Destination ONNX file.")
    parser.add_argument("--opset", type=int, default=17, help="ONNX opset version.")
    parser.add_argument("--no-verify", action="store_true", help="Skip ONNX Runtime verification after export.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = BratsUNet(in_channels=4, n_classes=4, n_channels=16)
    state_dict = torch.load(args.checkpoint, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    dummy = torch.randn(1, 4, 96, 128, 128, dtype=torch.float32)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model,
        dummy,
        args.output,
        export_params=True,
        opset_version=args.opset,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    )
    print(f"Exported ONNX model to {args.output}")

    if not args.no_verify:
        import onnx
        import onnxruntime as ort

        onnx_model = onnx.load(args.output)
        onnx.checker.check_model(onnx_model)
        session = ort.InferenceSession(str(args.output), providers=["CPUExecutionProvider"])
        output = session.run(None, {"input": dummy.numpy()})[0]
        print(f"Verified ONNX model. Output shape: {output.shape}")


if __name__ == "__main__":
    main()
