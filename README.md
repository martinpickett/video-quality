# video-quality

video-quality calculates VMAF and other video quality metrics for a distorted video relative to a reference video. It utilises FFmpeg, FFprobe and VMAF to achieve this.

## Features
- Different quality metrics
	- VMAF
	- PSNR
	- SSIM
	- MS-SSIM
- Support for distorted videos that are clips of the reference video
- Support for distorted videos that are cropped relative to the reference video


## Limitations
- Only supports FHD (1080p) video
	- Has a crop feature deigned for the removal of black bars, not content
- Requires a version of FFmpeg with VMAF support