#!/usr/bin/env python3
#!/opt/homebrew/bin/python3.11
# Author: Rafael Lee
# Email: rafael.lee2049@protonmail.com
# Date: 2024 April 20


# import cv2
import threading
import os
import sys
import time
import signal
from threading import Thread
from typing import overload
from typing import Optional
from typing import List
from typing import Set
from typing import NoReturn
import typing
from typing import TypeVar
from typing import Generic

# from typing import Type

# This code is a test for multi threading, thread pool and automic operations, so I ignored the computer vision part
# For a more modern approach, Python concurrent programming could be used.
# ImageFetcher is a base class, while ImageFetcherCamera, ImageFetcherDisk are 2 sub classes
# the critical parts in ImageFetcher are a queue which is a buffer of images, a mutex which controls the access of the queue and a thread to fetch images asynchronously
# ImageProcessor is a base class, it also has a queue, a mutex and several threads.
# ImageDistributor fetch images from ImageFetcher and push images to queue in ImageProcessor
# usage: python3 ./image_process.py

# optimization directions:
# 1, use some profiling tool like mypy to profiling, then optimize accordingly
# 2, use asyncio instead of thread pool
# 3, push multiple Images at one time
# 4, do not list dir everytime, use a queue for logging
# 5, use lock-less queue


#         +------------------------------------------------+                           +-------------------------------------------------+
#         |  ImageFetcher                                  |                           |   ImageProcessor                                |
#         |  variable Queue                                |                           |   variable   Queue                              |
#         |  variable Mutex                                |                           |   variable   Mutex                              |
#         |  variable 1 * Thread(while (1){FetchImage})    |                           |   variable   n * Thread(while (1){Process})     |
#         |  ...                                           |                           |   ...                                           |
#         |  method DequeueImage                           |                           |   method GetQueueLength                         |
#         |  method GetImageCount                          |                           |   method ThreadFunction                         |
#         |  method ThreadFunction                         |                           |   method Push                                   |
#         |  method ThreadStart                            | instantiate   instantiate |   method GetQueueSpace                          |
#         |  method ThreadJoin                             |<-------+      +---------->|   method ThreadsStart                           |
#         |  method FetchImage                             |        |      |           |   method ThreadsJoin                            |
#         |                                                |        |      |           |   method Process                                |
#         |                                                |        |      |           |                                                 |
#         +------------------------------------------------+        |      |           +-------------------------------------------------+
#                                         ^ ^                       |      |             ^  ^
#         +--------------------------+    | |       +--------------------------+         |  |   +----------------------------------------+
#         |  ImageFetcherCamera      |    | |       |  ImageDistributor        |         |  |   |  ImageProcessorCpu                     |
#         |                          |    | |       |  method FetcherStart     |         |  |   |                                        |
#         |                          |    | |       |  method ProcessorStart   |         |  |   |                                        |
#         |                          |    | |       |  method Loop             |         |  |   |                                        |
#         |                          |----+ |       |                          |         |  +---|                                        |
#         |                          |      |       |                          |         |      |                                        |
#         +--------------------------+      |       +--------------------------+         |      +----------------------------------------+
#                                           |                                            |
#         +--------------------------+      |                                            |      +----------------------------------------+
#         |  ImageFetcherDisk        |      |                                            |      |  ImageProcessorGpu                     |
#         |                          |      |inherit                              inherit|      |                                        |
#         |                          |      |                                            |      |                                        |
#         |                          |------+                                            +------|                                        |
#         |                          |                                                          |                                        |
#         |                          |                                                          |                                        |
#         +--------------------------+                                                          +----------------------------------------+


# for debugging
def tee(a, prefix="debug"):
    print(prefix, a)  # if debug, use this line, if not comment it out
    return a


# typing
T = TypeVar('T')


# global variables
thread_shall_stop = False
vacant_seconds_before_stop = 5
ImageFetcher_queue_length = 10
ImageProcessor_threads_counts = 2
ImageProcessor_queue_length = 5


# https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
def signal_handler(sig, frame):
    # print('You pressed Ctrl+C!')
    global thread_shall_stop
    thread_shall_stop = True
    # sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class Image:
    '''Image with name and content, use with care, class name is conflict with PIL Image class'''

    def __init__(self, name: Optional[str] = None, content: Optional[bytes] = None) -> None:
        if name:
            self.filename = name

    def SetContent(self, content: bytes) -> None:
        '''Set the file content of an Image object'''
        self.content = content

    def SetName(self, name: str) -> None:
        '''Set the file name of an Image object'''
        self.filename = name

    def Name(self) -> str:
        '''Get the file name of an Image object'''
        return self.filename


class ImageFetcher(Generic[T]):
    '''Fetch the image and put them to a local buffer'''

    def __init__(self, queue_length=ImageFetcher_queue_length) -> None:
        self.class_name = "ImageFetcher"
        self.local_cache: List[Image] = []
        self.queue_lock = threading.Lock()
        self.queue_length = queue_length
        self.thread = Thread(target=self.ThreadFunction, args=[])
        print("ImageFetcher")

    def DequeueImage(self) -> Optional[Image]:
        '''Lock queue, and pop 1 element if there are, return None if not exist'''
        image: Optional[Image] = None
        with self.queue_lock:
            if len(self.local_cache) > 0:
                image = self.local_cache.pop(0)
            else:
                image = None
        return image

    def GetImageCount(self) -> int:
        '''Lock queue, and return length of queue'''
        image: Optional[Image] = None
        length = None
        with self.queue_lock:
            length = len(self.local_cache)
        return length

    def ThreadFunction(self) -> None:
        '''The function to run in a thread'''
        global thread_shall_stop
        while not thread_shall_stop:
            items_in_queue = self.GetImageCount()  # atomic
            if items_in_queue < self.queue_length:
                self.FetchImage()
            time.sleep(0.1)

    def ThreadStart(self) -> None:
        '''Start threads'''
        print(f"ImageFetcher thread starts")
        self.thread.start()

    def ThreadJoin(self) -> None:
        '''Join threads'''
        print(f"ImageFetcher thread join")
        if self.thread:
            self.thread.join()
        else:
            raise ValueError('self.thread does not exist, please run self.ThreadStart first')

    def FetchImage(self) -> int:
        return 0


class ImageFetcherDisk(ImageFetcher[T]):
    '''Fetch images from local disk'''

    def __init__(self, disk_path: str) -> None:
        print("ImageFetcherDisk")
        self.__sent: Set[str] = set([])
        self.__path: str = disk_path
        super().__init__()

    def FetchImage(self) -> int:
        '''check image count and fill queue with Image elements
        fill the local cache as long as possible while less than self.queue_length'''
        def filter_filename(name: str) -> bool:
            if os.path.splitext(name)[-1] in ('.png', '.jpg', '.jpeg', '.svg'):
                return True
            else:
                return False

        # get the list of files of all images, pick all not sent
        files: List[str] = os.listdir(self.__path)
        list(filter(filter_filename, files))
        # get all file names of all images
        files_filtered: filter[str] = filter(filter_filename, files)
        not_sent = list(set(files_filtered) - self.__sent)  # set operation
        not_sent.sort()
        cnt = self.GetImageCount()  # atomic
        if cnt < self.queue_length:
            required = self.queue_length - cnt
            # the granularity of mutex can be smaller, only self.local_cache and self.__sent matter
            # file read can be exclude outside of mutex
            with self.queue_lock:
                for i in range(required):
                    # if the count of required image more than the number of not sent images
                    if i >= len(not_sent):
                        break
                    if not_sent[i]:  # not None
                        image = Image()
                        image.SetName(not_sent[i])
                        with open(os.path.join(self.__path, image.Name()), 'rb') as fr:
                            image.SetContent(fr.read())
                        self.local_cache.append(image)
                        # mark the image as sent
                        self.__sent.add(image.Name())
                    else:
                        return i + 1
                return i + 1
        else:
            return 0


class ImageFetcherCamera(ImageFetcher[T]):
    '''Fetch image from camera with OpenCV v4l2 camera driver'''

    def __init__(self) -> None:
        print("ImageFetcherCamera")
        super().__init__()


class ImageProcessor(Generic[T]):
    '''Class for image processing with different backends. Designed in a thread pool fashion'''
    global ImageProcessor_threads_counts
    global ImageProcessor_queue_length

    def __init__(self, directory: str, thread_pool_number=ImageProcessor_threads_counts, queue_length=ImageProcessor_queue_length) -> None:
        self.lock = threading.Lock()
        self.queue: List[Image] = []
        self.path = directory
        self.thread_count = thread_pool_number
        self.queue_length = queue_length
        self.threads: List[Optional[Thread]] = [None] * self.thread_count
        for i in range(self.thread_count):
            print(f'Create Thread {i}')
            self.threads[i] = Thread(target=self.ThreadFunction, args=[])

    def GetQueueLength(self) -> int:
        '''Atomic operation, get the length of queue'''
        with self.lock:
            return len(self.queue)

    def ThreadFunction(self) -> None:
        '''The commands to run in the thread'''
        global thread_shall_stop
        while thread_shall_stop == False:
            self.Process()
            time.sleep(0.1)
        # TODO: find better way to distribute images in different threads
        # if there are 5 threads and 5 images in queue, they each thread will get less than 5 image
        print("Preparing exit")
        for i in range(tee(self.GetQueueLength(), "self.GetQueueLength() =")):
            print("Additional Process")
            self.Process()

    def Push(self, image: Optional[Image]) -> None:
        '''Push image to queue'''
        if image:
            with self.lock:
                self.queue.append(image)

    def GetQueueSpace(self) -> int:
        '''Calculate how many more item can be put in the queue'''
        with self.lock:
            return self.queue_length - len(self.queue)

    def ThreadsStart(self) -> None:
        '''Start all threads'''
        for i in range(self.thread_count):
            print(f"Threads[{i}] starts")
            thread_v = self.threads[i]
            if thread_v:
                thread_v.start()

    def ThreadsJoin(self) -> None:
        '''Join all threads'''
        for i in range(self.thread_count):
            print(f"Threads[{i}] join")
            thread_v = self.threads[i]
            if thread_v:
                thread_v.join()

    def Process(self) -> None:
        '''process no more than 1 image and write to file'''
        image: Optional[Image] = None
        with self.lock:
            if len(self.queue) > 0:
                image = self.queue.pop(0)
                if not image:
                    raise ValueError('Image in queue cannot be None')
        # make the lock time as short as possible
        if image:
            print(image.filename)
            with open(os.path.join(self.path, image.filename), 'wb') as fw:
                fw.write(image.content)


class ImageProcessorCpu(ImageProcessor[T]):
    '''Process image with CPU'''

    def __init__(self, directory: str) -> None:
        super().__init__(directory)


class ImageProcessorGpu(ImageProcessor[T]):
    '''Process image with GPU'''

    def __init__(self, directory) -> None:
        super().__init__(directory)


class ImageDistributor:
    '''Manage ImageFetcher and ImageProcessor and the communication between them, with polling'''

    def __init__(self, fetchers: List[ImageFetcher], processors: List[ImageProcessor]) -> None:
        self.fetchers = fetchers
        self.processors = processors
        return

    def FetcherStart(self) -> None:
        '''Start ImageFetcher image fetching thread'''
        for i in self.fetchers:
            i.ThreadStart()

    def ProcessorStart(self) -> None:
        '''Start ImageProcessor image processing thread queue'''
        for i in self.processors:
            i.ThreadsStart()

    def Loop(self) -> None:
        '''If there are space in ImageProcessor queue, push image
        Stop if there are several seconds without processing
        Join threads after stops'''
        last_push_time = time.time()
        global thread_shall_stop
        global vacant_seconds_before_stop
        print('ImageDistributor.Loop()')

        # TODO: measure the speed of different backend, and then distribute the items accordingly
        while thread_shall_stop == False:
            if time.time() - last_push_time > vacant_seconds_before_stop:
                thread_shall_stop = True
            for fetcher in self.fetchers:
                for processor in self.processors:
                    # processor_1.Push(fetcher_0.DequeueImage())
                    for i in range(processor.GetQueueSpace()):
                        if fetcher.GetImageCount() > 0:
                            img: Optional[Image] = fetcher.DequeueImage()  # atomic
                            # if img:
                            processor.Push(img)
                            last_push_time = time.time()
                            # else:
                            #     raise ValueError('queue empty')
            # check every 1 second
            time.sleep(0.1)
        for fetcher in self.fetchers:
            fetcher.ThreadJoin()
        print('join threads in fetchers')
        for processor in self.processors:
            processor.ThreadsJoin()
        print('join threads in processors')


def main() -> int:
    if len(sys.argv) >= 3:
        src_dir = sys.argv[1].split(',')
        dst_dir = sys.argv[2].split(',')
    else:
        print(f'usage: {sys.argv[0]} SRC_DIR1,SRC_DIR2,...  DST_DIR')
        print(f'example: {sys.argv[0]} /some/dir/A,/some/dir/B  /destination/dir')
        print(f'This program is a program use multi thread pool to process images')
        exit(0)

    # fetchers: List[typing.Type[ImageFetcher]] = []
    fetchers: List[ImageFetcher] = []
    for i in src_dir:
        fetchers.append(ImageFetcherDisk(i))

    processors: List[ImageProcessor] = [ImageProcessorGpu(dst_dir[0]), ImageProcessorCpu(dst_dir[0])]

    distributor = ImageDistributor(fetchers, processors)
    distributor.FetcherStart()
    distributor.ProcessorStart()
    distributor.Loop()  # join when thread stops
    return 0


if __name__ == '__main__':
    main()
