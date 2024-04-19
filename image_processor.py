#!/usr/bin/env python

# import cv2
# from threading import Thread
# from threading import Lock
import threading


import os
import sys



                                                                                                                                                                                        |
                                                                                                                                                                                        |
                                                                                                                                                                                        |
                                                                                                                                                                                        |
           +------------------------------+              +-----------------------------------+                                                                                          |
           |                              |              |                                   |              +------------------------------------------------+                          |
           |                              |              |                                   |              |                                                |                          |
           +------------------------------+              |                                   |              |                                                |                          |
           +------------------------------+              |                                   |              |                                                |                          |
           |                              |              +-----------------------------------+              +------------------------------------------------+                          |
           |                              |                                                                +---------------------------------------------------+                        |
           +------------------------------+                                                                |                                                   |                        |
                                                                                                           |                                                   |                        |
                                                                                                           |                                                   |                        |
           +------------------------------+                                                                |                                                   |                        |
           |                              |                                                                |                                                   |                        |
           |                              |                                                                +---------------------------------------------------+                        |
           |                              |                                                                                                                                             |
           |                              |                                                                                                                                             |
           |                              |                                                                                                                                             |
           +------------------------------+                                                                                                                                             |
                                                                                                                                                                                        |




class ImageFetcher:
    def __init__(self):
        self.class_name = "ImageFetcher"
        self.__local_cache = []
        self.__queue_lock = threading.Lock()

        print("ImageFetcher")

    # def FetchImage(self):
    #     pass

    # def GetImage(self):
    #     pass

    def DequeueImage(self):
        '''Lock queue, and pop 1 element if there are, return None if not exist'''

        image = None
        with self.__queue_lock:
            if len(self.__local_cache) > 0:
                image = self.__local_cache.pop(0)
                # return image
            else:
                image = None
                # return None
        return image
        # some_lock.acquire()
        # try:
        #     # do something...
        # finally:
        #     some_lock.release()
        # return None

    def GetImageCount(self):
        '''Lock queue, and return length of queue'''
        image = None
        length = None
        with self.__queue_lock:
            length = len(self.__local_cache)
        return length


class ImageFetcherDisk(ImageFetcher):
    def __init__(self):
        super().__init__()
        print("ImageFetcherDisk")

        # ImageFetcher.__init__(self)
        # pass

    def FetchImage(self):
        pass


class ImageFetcherCamera(ImageFetcher):
    def __init__(self):
        print("ImageFetcherCamera")
        # pass

    def FetchImage(self):
        pass


class ImageDistributor:
    def __init__(self):
        pass


class ImageProcessor:
    def __init__(self):
        pass


class ImageProcessorCpu(ImageProcessor):
    def __init__(self):
        super().__init__()
        pass


class ImageProcessorGpu(ImageProcessor):
    def __init__(self):
        super().__init__()
        # pass


if __name__ == '__main__':
    fetcher = ImageFetcherDisk()

    print("*************** after class creation")
    print(fetcher.class_name)
    print("init")
