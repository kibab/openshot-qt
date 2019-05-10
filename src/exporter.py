#!/usr/bin/env python3

import openshot  # Python module for libopenshot (required video editing module installed separately)

import sys
import json

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter

from argparse import ArgumentParser, REMAINDER
from classes import project_data
from classes.logger import log

# OpenshotExporter creates an exporter based on the specified project.
class OpenshotExporter():

    def __init__(self, project, output_file_path):

        self.app = QApplication([])
        self.project = project
        self.output_file_path = output_file_path
        self.check_project()

        # Get some settings from the project
        fps = project.get(["fps"])
        width = project.get(["width"])
        height = project.get(["height"])
        sample_rate = project.get(["sample_rate"])
        channels = project.get(["channels"])
        channel_layout = project.get(["channel_layout"])

        # Create an instance of a libopenshot Timeline object
        self.timeline = openshot.Timeline(width, height, openshot.Fraction(fps["num"], fps["den"]), sample_rate, channels,
                                          channel_layout)

        # XXX Do I need this at all? We load JSON project data and reinitialize everything from there?
        self.timeline.info.channel_layout = channel_layout
        self.timeline.info.has_audio = True
        self.timeline.info.has_video = True
        self.timeline.info.video_length = 99999
        self.timeline.info.duration = 999.99
        self.timeline.info.sample_rate = sample_rate
        self.timeline.info.channels = channels

        # Open the timeline reader
        json_timeline = json.dumps(project._data)
        self.timeline.SetJson(json_timeline)
        self.timeline.Open()
        log.info("Loaded timeline")

        
        log.info("video length: %d", self.timeline.info.video_length)
        log.info("video sample rate: %d", self.timeline.info.sample_rate)

        video_settings = { "vcodec" : "libx264",
                           "fps": {"num" : 30, "den": 1},
                           "pixel_ratio": {"num" : 1, "den": 1},
                           "width": 1280,
                           "height": 720,
                           "video_bitrate": 15000000, # int(self.convert_to_bytes(self.txtVideoBitRate.text()))
                           "start_frame": 1,
                           "end_frame": 300
#                           "end_frame": 4092
        }

        audio_settings = {"acodec": "aac",
                          "sample_rate": 48000,
                          "channels": 2,
                          "channel_layout": 3,
                          "audio_bitrate": 192000 # int(self.convert_to_bytes(self.txtAudioBitrate.text()))
            }

        # Set MaxSize (so we don't have any downsampling)
        self.timeline.SetMaxSize(video_settings.get("width"), video_settings.get("height"))

        # Set lossless cache settings (temporarily)
        export_cache_object = openshot.CacheMemory(500)
        self.timeline.SetCache(export_cache_object)

        w = openshot.FFmpegWriter(output_file_path)
        w.SetVideoOptions(True,
                          video_settings.get("vcodec"),
                          openshot.Fraction(video_settings.get("fps").get("num"),
                                            video_settings.get("fps").get("den")),
                          video_settings.get("width"),
                          video_settings.get("height"),
                          openshot.Fraction(video_settings.get("pixel_ratio").get("num"),
                                            video_settings.get("pixel_ratio").get("den")),
                          False,
                          False,
                          video_settings.get("video_bitrate"))

        w.SetAudioOptions(True,
                          audio_settings.get("acodec"),
                          audio_settings.get("sample_rate"),
                          audio_settings.get("channels"),
                          audio_settings.get("channel_layout"),
                          audio_settings.get("audio_bitrate"))

        w.PrepareStreams()

        # Open the writer
        w.Open()

        for frame in range(video_settings.get("start_frame"), video_settings.get("end_frame") + 1):
            log.info("Getting frame #%d", frame)
            frame_obj = self.timeline.GetFrame(frame)
            img = frame_obj.GetImage()
            log.info(img)
            qp = QPainter()
            qp.begin(img)
#            frame_obj.Display()

            w.WriteFrame(frame_obj)
            log.info("Processed frame %d", frame)

        w.Close()

    def check_project(self):
        log.info("Performing sanity checks on the project")


def main():
    from classes import info
    print("Loaded modules from current directory: %s" % info.PATH)

    """"Initialize settings (not implemented) and create main window/application."""

    parser = ArgumentParser(description = 'OpenShot version ' + info.SETUP['version'])
    parser.add_argument('-p', '--project', dest='project_path', help='Project file to load.')
    parser.add_argument('-o', '--outfile', dest='output_file_path', help='File to write the output to.')
    parser.add_argument('remain', nargs=REMAINDER)

    args = parser.parse_args()

    project = project_data.ProjectDataStore()
    project.load(args.project_path, export_mode=True)

    exporter = OpenshotExporter(project, args.output_file_path)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
