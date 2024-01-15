import cv2
import os
from time import time, sleep
from threading import Thread

class Cam():
    def __init__(self, url, duration, storage_limit, location):
        self._cam = None
        self._frames = []
        self._cache_thread = None        
        self._cache_terminate = False
        self._export_thread = None
        self._should_export = False
        self.videoUrl = url
        self._location = location
        self.videoDuration = duration
        self.vid_storage_limit = storage_limit
        self.curr_vid_id = 1 
        
    def _export(self):
        self._should_export = False
        if self.curr_vid_id == self.vid_storage_limit:
            self.curr_vid_id = 1
        else:
            self.curr_vid_id += 1
        if self._frames == []:
            print('export error: no frames')
            return
        vid = self._frames.copy()
        sleep(self.videoDuration / 2)
        vid += self._frames
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = len(vid) / self.videoDuration
        out = cv2.VideoWriter(f'videos/raw.mp4', fourcc, fps, (640, 480))
        for frame in vid:
            out.write(frame)
        out.release()    
        os.system(f'ffmpeg -y -i videos/raw.mp4 -b:v 300k videos/{self._location}{self.curr_vid_id:02d}.mp4')
        print('export sucess')
        
    def _caching(self):
        if not os.path.exists('videos'):
            os.makedirs('videos')
        self._cam = cv2.VideoCapture(self.videoUrl)
        self._record(self.videoDuration / 2)
        while self._cache_terminate is False:
            ret, frame = self._cam.read()
            self._frames.append(frame)
            self._frames.pop(0)
            if self._should_export:
                if self._export_thread != None and self._export_thread.is_alive():
                        continue
                print('saving video')
                self._export_thread = Thread(target = self._export)
                self._export_thread.start()

    def _record(self, sec):
        start_time = int(time())
        while ( int(time()) - start_time ) <= sec:
            ret, frame = self._cam.read()
            self._frames.append(frame)
    
    def start(self, url=None, dur=None):
        if self._cache_thread != None:
            return
        if url != None:
            self.videoUrl = url
        if dur != None:
            self.videoDuration = dur
        self._cache_terminate = False
        self._cache_thread = Thread(target=self._caching)
        self._cache_thread.start()

    def stop(self):
        if self._cache_thread == None:
            return
        self._cache_terminate = True
        self._cache_thread.join()
        self._cam.release()
        self._frames = []

    def export_video(self):
        self._should_export = True

    def is_started(self):
        return self._cam != None


if __name__ == "__main__":
    cam = Cam('rtsp://lab314:lab314@10.100.2.159:554/stream1', 10, 10, '002')
    cam.start()
    sleep(120)
    cam.export_video()
    sleep(120)
    cam.stop()