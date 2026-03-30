import torch
import torch.nn as nn

class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels, num_groups=4):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv3d(in_channels, out_channels, 3, padding=1),
            nn.GroupNorm(num_groups, out_channels),
            nn.ReLU(inplace=True),
            nn.Conv3d(out_channels, out_channels, 3, padding=1),
            nn.GroupNorm(num_groups, out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.layers(x)


class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.double_conv = DoubleConv(in_channels, out_channels)
        self.pool = nn.MaxPool3d(2)

    def forward(self, x):
        skip = self.double_conv(x)
        x = self.pool(skip)
        return x, skip


class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.up = nn.ConvTranspose3d(in_channels, out_channels, 2, stride=2)
        self.double_conv = DoubleConv(in_channels, out_channels)

    def forward(self, x, skip):
        x = self.up(x)
        x = torch.cat([skip, x], dim=1)
        return self.double_conv(x)


class UNet(nn.Module):
    def __init__(self, in_channels=4, n_classes=4, n_channels=32):
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

    def forward(self, x):
        skips = []
        for enc in self.encoder:
            x, skip = enc(x)
            skips.append(skip)

        x = self.bottleneck(x)
        skips.reverse()

        for skip, dec in zip(skips, self.decoder):
            x = dec(x, skip)

        return self.out(x)

class BratsUNet(nn.Module):
    def __init__(self, in_channels=4, n_classes=4, n_channels=16):
        super().__init__()
        self.model = UNet(in_channels, n_classes, n_channels)

    def forward(self, x):
        return self.model(x)