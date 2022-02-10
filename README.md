# video-quality

video-quality calculates VMAF and (optionally) other video quality metrics for a distorted video relative to a reference video before outputting them in a csv file and providing a summary. It utilises [FFmpeg](https://ffmpeg.org), [FFprobe](https://ffmpeg.org) and [VMAF](https://github.com/Netflix/vmaf) to achieve this.

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



## Simple Usage
The simplist usage case is you have two videos, the original video (reference video) and the transcoded video (distorted video). They are both the same length, and no cropping or scaling has been applied:

`video-quality.py -r reference_video.mkv distorted_video.mkv`

Next, if the distorted video has been cropped:

`video-quality.py -r reference_video.mkv --crop 1920:800:0:140 distorted_video.mkv`

Or if the distorted video is a 30 second clip starting 6600 seconds into the reference video:

`video-quality.py -r reference_video.mkv --position 6600 --duration 30 distorted_video.mkv`

All functionality can be found in the full help:

`video-quality.py --full-help`



## Requirements
- Python 3
- FFmpeg with VMAF
- VMAF models

### Python 3
If you do not already have Python 3 installed you can download it from the official Python website - [https://www.python.org/downloads](https://www.python.org/downloads/). However, I would recommend a different approach.

#### Windows
Use [Anaconda](https://www.anaconda.com), it comes with all the packages you need for this project, plus it is reasonably easy to update and there is a lot of support on the web for it. 

#### MacOS
Use [Homebrew](https://brew.sh). Homebrew is a package manager, which means it is a program that allows you to install other programs. Once you have installed Homebrew, installing Python 3 simply requires you to type the following into a terminal window:

`brew install python3`

#### Linux
If you run Linux you probably already know how to install Python 3. First, there is a good chance it is already installed on your system by default, but if not it will be in your package manager. I am sorry, but there are too many package managers for me to provide a definitive command, but I trust you to work it out.

### FFmpeg with VMAF
This is much simpler than installing Python 3 as the official builds of FFmpeg (linked from the [FFmpeg Downloads](https://ffmpeg.org/download.html) page) all contain VMAF, known as libvmaf. So go to the [FFmpeg Downloads](https://ffmpeg.org/download.html) page and follow the instructions for your operating system.

Be sure to place the FFmpeg and FFprobe files in a directory included in your $PATH, so the system know where to find it. Currently `video-quality.py` will only use the system's FFmpeg and FFprobe.

### VMAF Models
VMAF requires an extra file to perform its analysis, what is called a model file. In the case of VMAF these are json files and they may have been installed alongside FFmpeg. If they were not, they need to be downloaded now.

#### MacOS & Linux
First check to see if the model files have already exist. Check the directory `/usr/local/share/model/`, look for a file named `vmaf_v0.6.1.json`. If it exists, you are good to go. If not, go to the VMAF models [github page](https://github.com/Netflix/vmaf/tree/master/model) and download the model titled `vmaf_v0.6.1.json`. Be careful, there are many different models all with similar names. Once downloaded, move it in to the directory `/usr/local/share/model/`.

#### Windows
This is more tricky. There is no default location for the model files on Windows, so first you will need to decide where to store them. Once you have decided, go to the VMAF models [github page](https://github.com/Netflix/vmaf/tree/master/model) and download the model titled `vmaf_v0.6.1.json`. Be careful, there are many different models all with similar names. Now move it to the directory you had decided upon earlier.

Now, because there is no default location, you will need to tell `video-quality.py` where the model file is every time you run it. To do this you will need to use the `--model` argument followed by the path to the model. One final wrinkle, if you want to use an absolute path you need to read this [VMAF document](https://github.com/Netflix/vmaf/blob/master/resource/doc/ffmpeg.md#note-about-the-model-path-on-windows) first.


## Installation
This is a python script so it does not need to be installed in the conventional sense. Just download it from [GitHub](https://github.com/martinpickett/video-quality), make it executable (`chmod +x video-quality.py` on MacOS or Linux) and move it to a directory included in your $PATH.









