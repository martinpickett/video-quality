#!/usr/bin/env python3

import os
from subprocess import run, PIPE, check_output
from argparse import ArgumentParser
import re
import shlex
import csv
import sys

version = f"""\
{os.path.basename(__file__)} 2022.02.10
Martin Pickett
"""

help = f"""\
Calculates frame-by-frame VMAF score for a distorted video relative to a 
reference video and saves results in a CSV file.

Usage: {os.path.basename(__file__)} [OPTIONS...] DISTORTED-VIDEO(S)

Input Options:
-r,   --reference PATH      path to reference video file
-n,   --dry-run             print FFmpeg command and exit
      --position SECONDS    the time in the reference video to start from
      --duration SECONDS    duration of clip from reference video
      --crop WIDTH:HEIGHT:X:Y
                            crop value of distorted video relative to reference
                                video. TOP:BOTTOM:LEFT:RIGHT crop format also
                                accepted

Additional Quality Metrics:
      --psnr                enables computing PSNR
      --ssim                enables computing SSIM
      --ms-ssim             enables computing MS-SSIM
"""

helpFull = f"""\
VMAF options:
      --model PATH          path to VMAF model 
                             (default: /usr/local/share/model/vmaf_v0.6.1.json)
      --subsample INT       set interval for frame subsampling (default: 1)
      --threads INT         set the number of threads used (default: 1)
"""

helpBottom = f"""\
Other options:
-h,   --help                print help message and exit
      --full-help           print full help message and exit
      --version             print version information and exit
    
Requires FFprobe and FFmpeg with VMAF support.
"""

def main():
	#####################
	##### ARGUMENTS #####
	#####################
	parser = ArgumentParser(add_help=False)
	parser.add_argument("file", nargs="+")
	parser.add_argument("-n", "--dry-run", action="store_true", default=False)
	parser.add_argument("-r", "--reference", type=str)
	parser.add_argument("--position", type=int)
	parser.add_argument("--duration", type=int)
	parser.add_argument("--crop", type=str)
	parser.add_argument("--psnr", action="store_true", default=False)
	parser.add_argument("--ssim", action="store_true", default=False)
	parser.add_argument("--ms-ssim", action="store_true", default=False)
	parser.add_argument("--model", type=str)
	parser.add_argument("--subsample", type=int)
	parser.add_argument("--threads", type=int)
	parser.add_argument("-h", "--help", action="store_true", default=False)
	parser.add_argument("--full-help", action="store_true", default=False)
	parser.add_argument("--version", action="store_true", default=False)
	args = parser.parse_args()


	#########################
	##### PERIPHERAL FEATURES
	#########################
	# Print version and exit
	if args.version:
		print(version)
		exit()

	# Print help and exit
	if args.help:
		print(help)
		print(helpBottom)
		exit()

	# Print full help and exit
	if args.full_help:
		print(help)
		print(helpFull)
		print(helpBottom)
		exit()
	
	
	#############################
	##### TOOL VERIFICATION #####
	#############################
	# Check existence of FFmpeg
	tools = {
		"FFmpeg": ["ffmpeg", "-version"],
		"FFprobe": ["ffprobe", "-version"],
		"VMAF": ["ffmpeg", "-filters", "|", "grep", "libvmaf"]
	}
	for tool, command in tools.items():
		print(f"Verifying \"{tool}\" availability...")
		try:
			run(command, stdout=PIPE, stderr=PIPE).check_returncode()
		except:
			exit(f"\"{tool}\" not found")


	##########################
	##### SCANNING MEDIA #####
	##########################
	print("Scanning media...")
	
	# Check video file names
	if not os.path.exists(args.reference):
		exit(f"Error, reference video file {args.reference} does not exist")
	for f in args.file:
		if not os.path.exists(f):
			exit(f"Error, distorted video file {f} does not exist")
	
	# Reference video length, width & height
	refLength = float(check_output([ "ffprobe", "-v", "quiet", "-i", args.reference, "-select_streams", "v:0", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1" ]))
	refWidth = int(check_output([ "ffprobe", "-v", "error", "-i", args.reference, "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "default=noprint_wrappers=1:nokey=1" ]))
	refHeight = int(check_output([ "ffprobe", "-v", "error", "-i", args.reference, "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1" ]))

	# Distorted videos length, width & height	
	numInputs = len(args.file)
	distLength = [0]*numInputs
	distWidth = [0]*numInputs
	distHeight = [0]*numInputs
	for i, f in enumerate(args.file):
		distLength[i] = float(check_output([ "ffprobe", "-v", "quiet", "-i", f, "-select_streams", "v:0", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1" ]))
		distWidth[i] = int(check_output([ "ffprobe", "-v", "error", "-i", f, "-select_streams", "v:0", "-show_entries", "stream=width", "-of", "default=noprint_wrappers=1:nokey=1" ]))
		distHeight[i] = int(check_output([ "ffprobe", "-v", "error", "-i", f, "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1" ]))
	
	
	#################################
	##### ARGUMENT VERIFICATION #####
	#################################
	print("Verifying arguments...")

	# Check position is between 0 and reference file length minus duration
	if not 0 < args.position < refLength - args.duration:
		print(f"Position ({args.position}s) and Duration ({args.duration}s) invalid")
		print(f"Total time exceeds length of reference video")
		exit()

	# Convert between HandBrake and FFmpeg style crops if necessary
	cropString = f"{refWidth}:{refHeight}:0:0"
	if args.crop:
		crop = [0]*4
		max_x = refWidth/4
		max_y = refHeight/4
		pattern = re.compile("([0-9]+):([0-9]+):([0-9]+):([0-9]+)")
		match = pattern.match(args.crop)
		if match:
			crop[0], crop[1], crop[2], crop[3] = match.groups()
			crop = [int(x) for x in crop]
			if crop[2] <= max_x and crop[3] <= max_x and crop[0] <= max_y and crop[1] <= max_y:
				print("Interpreting crop geometry as TOP:BOTTOM:LEFT:RIGHT values...")
				width = refWidth - (crop[2] + crop[3])
				height = refHeight - (crop[0] + crop[1])
				x = crop[2]
				y = crop[0]
				crop[0] = width
				crop[1] = height
				crop[2] = x
				crop[3] = y
		else:
			exit(f"Invalid crop: {args.crop}")
		cropString = f"{crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}"
		
		# Check if detected crop is different from distorted videos size
		for i, (W, H) in enumerate(zip(distWidth, distHeight)):
			if crop[0] != W or crop[1] != H:
				print(f"Crop mismatch between reference video and distorted video: {args.file[i]}")
				print(f"Reference video: {crop[0]}x{crop[1]}")
				print(f"Distorted video: {W}x{H}")
				exit()

	# Verify model file exists
	if args.model:
		if not os.path.exists(args.model):
			exit(f"Model file does not exists: {args.model}")

	# Quality metrics dictionary
	# Key: Display Name; Value: [command, csv_name, csv_column, accuracy, values]
	qualityMetrics = {"VMAF": ["", "vmaf", 0, 2]}
	if args.psnr:
		qualityMetrics["PSNR"] = [":psnr=1", "psnr", 0, 2]
	if args.ssim:
		qualityMetrics["SSIM"] = [":ssim=1", "ssim", 0, 4]
	if args.ms_ssim:
		qualityMetrics["MS-SSIM"] = [":ms_ssim=1", "ms_ssim", 0, 4]
		
	# Verify output files do not already exist
	vmafOut = []
	for f in args.file:
		vmafOut.append(os.path.splitext(os.path.basename(f))[0] + "-quality.csv")
		if not args.dry_run and os.path.exists(vmafOut[-1]):
			exit(f"Output file already exists: {vmafOut[-1]}")


	############################
	##### VMAF CALCULATION #####
	############################
	
	# Loop over all inputs
	for i, f in enumerate(args.file):
		# FFmpeg Filter String
		# --------------------
		# 
		# Distorted video filters
		distortedVideoPrep = "[0:v]setpts=PTS-STARTPTS[dist]; "

		# Reference video filters
		referenceVideoPrep = "[1:v]crop=" + cropString + ",setpts=PTS-STARTPTS[ref]; "

		# VMAF filter string
		vmafFilterString = f"[dist][ref]libvmaf=log_fmt=csv:log_path={vmafOut[i]}"
	
		# Optional libvmaf features
		if args.model:
			vmafFilterString += f":model_path={args.model}"
		if args.subsample:
			vmafFilterString += f":n_subsample={args.subsample}"
		if args.threads:
			vmafFilterString += f":n_threads={args.threads}"

		# Optional quality metrics
		for key, value in qualityMetrics.items():
			if not key == "VMAF":
				vmafFilterString += value[0]

		# Assemble final filter string
		filterString = distortedVideoPrep + referenceVideoPrep + vmafFilterString


		# FFmpeg Command Generation
		#--------------------------
		#
		# FFmpeg command beginning
		ffmpegCommand = [ "ffmpeg", "-hide_banner", "-v", "fatal", "-stats" ]
	
		# FFmpeg command distorted input
		distortedInput = [ "-i", f ]
		ffmpegCommand += distortedInput
	
		# FFmpeg command reference input
		referenceInput = []
		if args.position:
			referenceInput += [ "-ss", str(args.position) ]
		if args.duration:
			referenceInput += [ "-t", str(args.duration) ]
		referenceInput += [ "-i", args.reference ]
		ffmpegCommand += referenceInput

		# Assemble FFmpeg command	
		filterInput = [ "-filter_complex", filterString ]
		ffmpegCommand += filterInput
	
		# FFmpeg command output
		outputCommands = [ "-f", "null", "-" ]
		ffmpegCommand += outputCommands

		# Run FFmpeg Command
		#-------------------
		#
		print()
		print(" ".join(map(lambda x: shlex.quote(x), ffmpegCommand)))
		print()
# 		if args.dry_run:
# 			continue
# 		else:
# 			a = run(ffmpegCommand)

	# Calculate Average Quality Metrics
	#----------------------------------
	#
	fileDictionary = {}
	for f in vmafOut:
		# Create empty resultsDictionary
		resultsDictionary = {}
		for key in qualityMetrics:
			resultsDictionary[key] = [0,[]]

		# open vmafFile and read as a csv
		with open(f, "r") as csvFile:
			csvReader = csv.reader(csvFile, delimiter = ',')

			# extract column header row
			columnNames = []
			for row in csvReader:
				columnNames = row
				break

			# Find column index for each quality values
			toRemove = []
			for key, value in resultsDictionary.items():
				try:
					value[0] = columnNames.index(qualityMetrics[key][1])
				except:
					print(f"Warning: Could not find {key} in results")
					toRemove.append(key)
					
			# Remove quality metrics not detected in output file
			for i in toRemove:
				resultsDictionary.pop(i)

			# Read rest of CSV file and store results
			for row in csvReader:
				for value in resultsDictionary.values():
					q = row[value[0]].strip()
					try:
						q = float(q)
						value[1].append(q)
					except:
						pass

			# Store resultsDictionary in fileDictionary
			fileDictionary[f.replace("-quality.csv","")] = resultsDictionary
			
	# Calculate and print quality averages
	print()
	for filename, results in fileDictionary.items():
		print(filename)
		for key, value in results.items():
			if len(value[1]) == 0:
				continue
			value[1].sort()
			meanQuality = sum(value[1]) / len(value[1])
			nthPercentileIndex = int(0.05 * len(value[1]))
			nthPercentileValue = value[1][nthPercentileIndex]
			precision = qualityMetrics[key][3]
			a = f"Mean Average {key}:".ljust(22)
			b = f"{meanQuality:<10.{precision}f}".ljust(12)
			print(f"{a}{b}5th Percentile: {nthPercentileValue:.{precision}f}")

			

	# Exit if dry-run argument used
	if args.dry_run:
		exit()


if __name__ == "__main__":
	main()





































