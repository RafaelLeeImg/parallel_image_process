#!/usr/bin/env python

# import cv2
# from threading import Thread
# from threading import Lock
import threading
from threading import Thread
import os
import sys
from typing import Optional
from typing import List
from typing import Set
from typing import NoReturn

import signal

#                +--------------------------+              +--------------------------+                +--------------------------+
#                |  ImageFetcherCamera      |              |  ImageDistributor        |                |  ImageProcessorCpu       |
#                |                          |              |                          |                |                          |
#                |                          |              |                          |                |                          |
#                |                          |              |                          |                |                          |
#                |                          |              |                          |                |                          |
#                |                          |              |                          |                |                          |
#                +--------------------------+              +--------------------------+                +--------------------------+
#
#                +--------------------------+                                                          +--------------------------+
#                |  ImageFetcherDisk        |                                                          |  ImageProcessorGpu       |
#                |                          |                                                          |                          |
#                |                          |                                                          |                          |
#                |                          |                                                          |                          |
#                |                          |                                                          |                          |
#                |                          |                                                          |                          |
#                +--------------------------+                                                          +--------------------------+
#


# gloabl variables
image_queue_max_length = 10
thread_shall_stop = False

# https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
def signal_handler(sig, frame):
    # print('You pressed Ctrl+C!')
    global thread_shall_stop
    thread_shall_stop = True
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

class Image:
    def __init__(self, name: Optional[str] = None, content: Optional[bytes] = None) -> None:
        if name:
            self.filename = name

    def SetContent(self, content: bytes) -> None:
        self.content = content

    def SetName(self, name: str) -> None:
        self.filename = name

    def Name(self) -> str:
        return self.filename


class ImageFetcher:
    global image_queue_max_length
    # image_queue_max_length =
    # queue_lock = threading.Lock()  # static variable, class variable

    def __init__(self) -> None:
        self.class_name = "ImageFetcher"
        self.local_cache: List[Image] = []
        self.queue_lock = threading.Lock()
        print("ImageFetcher")

    # def FetchImage(self):
    #     pass

    # def GetImage(self):
    #     pass

    def DequeueImage(self) -> Optional[Image]:
        '''Lock queue, and pop 1 element if there are, return None if not exist'''

        image: Optional[Image] = None
        with self.queue_lock:
            if len(self.local_cache) > 0:
                image = self.local_cache.pop(0)
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

    def GetImageCount(self) -> int:
        '''Lock queue, and return length of queue'''
        image: Optional[Image] = None
        length = None
        with self.queue_lock:
            length = len(self.local_cache)
        return length


class ImageFetcherDisk(ImageFetcher):
    def __init__(self, disk_path: str) -> None:
        print("ImageFetcherDisk")
        self.__sent: Set[str] = set([])
        self.__path: str = disk_path
        super().__init__()

    def FetchImage(self) -> int:
        '''check image count and fill queue with Image elements'''
        def filter_filename(name: str) -> bool:
            if (name[-4:] == '.png' or name[-5:] == '.jpeg' or name[-4:] == '.jpg' or name[-4:] == '.svg') and os.path.isfile(os.path.join(self.__path, name)):
                return True
            else:
                return False

        files: List[str] = os.listdir(self.__path)
        list(filter(filter_filename, files))
        files_filtered: filter[str] = filter(filter_filename, files)
        not_sent = list(set(files_filtered) - self.__sent)
        not_sent.sort()
        cnt = self.GetImageCount()
        if cnt < image_queue_max_length:
            with self.queue_lock:
                required = image_queue_max_length - cnt
                # while required > 0 and len(not_sent) > 0:
                #     self.local_cache.append()
                for i in range(required):
                    if not_sent[i]:
                        image = Image()
                        image.SetName(not_sent[i])
                        with open(os.path.join(self.__path, image.Name()), 'rb') as fr:
                            image.SetContent(fr.read())
                        self.local_cache.append(image)
                    else:
                        return i
                return i
        else:
            return 0


class ImageFetcherCamera(ImageFetcher):
    def __init__(self) -> None:
        print("ImageFetcherCamera")
        # pass

    def FetchImage(self):
        pass


class ImageDistributor:
    def __init__(self, fetchers) -> None:
        return


class ImageProcessor:
    def __init__(self, directory: str) -> None:
        self.lock = threading.Lock()
        self.queue: List[Image] = []
        self.path = directory


class ImageProcessorCpu(ImageProcessor):
    def __init__(self, directory: str) -> None:
        super().__init__(directory)

    def Process(self) -> None:
        '''process image and write to file'''
        image: Optional[Image] = None
        with self.lock:
            if len(self.queue) > 0:
                image = self.queue.pop(0)
                if image:
                    print(image.filename)
                    print(len(image.content))
                else:
                    raise ValueError('Image in queue cannot be None')
        if image:
            with open(os.path.join(self.path, image.filename), 'wb') as fw:
                fw.write(image.content)

    # TODO: why return type is not None nor NoReturn
    def Push(self, image: Optional[Image]):  # ??????????????? -> None:
        if image:
            with self.lock:
                self.queue.append(image)

    def GetQueueLength(self) -> int:
        with self.lock:
            return len(self.queue)


class ImageProcessorGpu(ImageProcessor):
    def __init__(self, directory) -> None:
        super().__init__(directory)

    def Process(self) -> None:
        pass

if __name__ == '__main__':
    fetcher = ImageFetcherDisk(r'/dev/shm/d/')
    fetcher2 = ImageFetcherDisk(r'/dev/shm/d/1')

    processor_1 = ImageProcessorCpu(r'/dev/shm/unzip/del/del_image_processor_test')
    processor_1.GetQueueLength()


    t = Thread(target=print, args=[1])


    print("*************** after class creation")
    print("    fetcher.GetImageCount()")
    print(fetcher.GetImageCount())
    print("    fetcher.FetchImage()")
    print(fetcher.FetchImage())
    print("    fetcher.GetImageCount()")
    print(fetcher.GetImageCount())
    print("    fetcher.DequeueImage()")
    print(fetcher.DequeueImage())
    print("    fetcher.DequeueImage()")
    print(fetcher.DequeueImage())
    print("    fetcher.FetchImage()")
    print(fetcher.FetchImage())
    print("    fetcher.DequeueImage()")
    print(fetcher.DequeueImage())
    print("    fetcher.DequeueImage()")
    print(fetcher.DequeueImage())
    print("    fetcher.DequeueImage()")
    print(fetcher.DequeueImage())
    print("    fetcher.GetImageCount()")
    print(fetcher.GetImageCount())
    print("    fetcher.FetchImage()")
    print(fetcher.FetchImage())
    print("    fetcher.FetchImage()")
    print(fetcher.FetchImage())
    print("    fetcher.class_name")
    print(fetcher.class_name)

    # print("    fetcher.queue_lock")
    # print(fetcher.queue_lock)

    print("*************** after class creation")
    print("    fetcher2.GetImageCount()")
    print(fetcher2.GetImageCount())
    print("    fetcher2.FetchImage()")
    print(fetcher2.FetchImage())
    print("    fetcher2.GetImageCount()")
    print(fetcher2.GetImageCount())
    print("    fetcher2.DequeueImage()")
    print(fetcher2.DequeueImage())
    print("    fetcher2.DequeueImage()")
    print(fetcher2.DequeueImage())
    print("    fetcher2.FetchImage()")
    print(fetcher2.FetchImage())
    print("    fetcher2.DequeueImage()")
    print(fetcher2.DequeueImage())
    print("    fetcher2.DequeueImage()")
    print(fetcher2.DequeueImage())
    print("    fetcher2.DequeueImage()")
    print(fetcher2.DequeueImage())
    print("    fetcher2.GetImageCount()")
    print(fetcher2.GetImageCount())
    print("    fetcher2.FetchImage()")
    print(fetcher2.FetchImage())
    print("    fetcher2.FetchImage()")
    print(fetcher2.FetchImage())
    print("    fetcher2.class_name")
    print(fetcher2.class_name)


    print("    processor_1.GetQueueLength()")
    print(processor_1.GetQueueLength())

    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()

    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()

    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()
    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()
    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()
    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()
    print("    processor_1.Push(fetcher.DequeueImage())")
    print(processor_1.Push(fetcher.DequeueImage()))

    print("    processor_1.Process()")
    processor_1.Process()
