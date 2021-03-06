import random,ctypes,math,time,copy,Queue
import threading,signal ,traceback
import numpy

from GlobalData import *

# spectrum = numpy.array(hackrf_settings.fft_size,dtype=numpy.complex64)
spectrum = []
spectrum_lock = threading.Lock()

time1= time.time()
all_cnt = 0
dataQueue = Queue.Queue([2]);

def rx_callback_fun(hackrf_transfer):
    global have_recv,all_cnt,time1 
    length = hackrf_transfer.contents.valid_length
    array_type = (ctypes.c_byte*length)
    values = ctypes.cast(hackrf_transfer.contents.buffer, ctypes.POINTER(array_type)).contents
    all_cnt += length
    if time.time() - time1 > 1:
        time1 = time.time()
        print all_cnt
        all_cnt = 0
    buf = copy.deepcopy(values)
    dataQueue.put_nowait(buf)
    return 0

def get_spectrum():
    global spectrum
    arr = list()
    spectrum_lock.acquire() 
    step = len(spectrum) / 512
    for i in range(len(spectrum)):
        if i % step == 0:
        # if i != None:
            # get = 0.0
            # for j in range(step):
            #         get += abs(spectrum[i + j])
            # arr.append(numpy.log10(get / step)*20)             
            arr.append(numpy.log10( abs(spectrum[i]) ) * 20)  #calculate power in dBFS               
            # arr.append(numpy.log10(abs(spectrum[i])  + 1e-20) * 10)  #calculate power in dBFS               
            # arr.append(abs(spectrum[i]) )  # -1 ~1
        # arr.append(-10)
    spectrum_lock.release()
    return arr


class RxThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.fft_time =time.time()
    def run(self):
        global spectrum
        #note: we don't set self.running to False anywhere...
        while self.running:
                # iq = hackrf.packed_bytes_to_iq(transfer_lbuf)
                buf = dataQueue.get()
                iq = hackrf.packed_bytes_to_iq_withsize(buf, hackrf_settings.fft_size)
                time_get = time.time()
                if time_get - self.fft_time > 1.0 / hackrf_settings.fft_rate:
                    spectrum_lock.acquire() 
                    # iq = iq - numpy.mean(iq) #dc offset
                    spectrum1 = numpy.fft.fft(iq)  * 2 / iq.size
                    spectrum = numpy.fft.fftshift(spectrum1)
                    spectrum_lock.release()  
                    self.fft_time = time_get


# import pylab as p
# class test(threading.Thread):
#     def run(self):
#         while True:
#             pl.figure()
#             spectrum_lock.acquire() 
#             pl.plot(abs(spectrum))
#             pl.plot(spectrum)
#             spectrum_lock.release()  
#             pl.show()

# aaa = test()
# aaa.start()