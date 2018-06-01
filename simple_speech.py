import speech_recognition as sr
import queue
import threading
import RPi.GPIO as GPIO
import time

# https://www.olivieraubert.net/vlc/python-ctypes/
import vlc


pin_outs = [15, 16]
choco_bar_motor = 15
coke_motor = 16

hello = ['hello', 'alo']
chocobar = ['chocobar', 'Google bar', 'chocolate']
coke = ['Coca-Cola', 'coke', 'cocaine']

# setup output pins
GPIO.setmode(GPIO.BOARD)
for pin in pin_outs:
  GPIO.setup(pin, GPIO.OUT)

# listening thread
## gets all the recognized strings into a fifo queue
def listening(string_queue):

  r = sr.Recognizer()
  m = sr.Microphone()

  print("Calibrating, please remain silent.")
  #why use this || this is redundant?
  with m as source: r.adjust_for_ambient_noise(source)
  print("Set minimum energy threshold to {}".format(r.energy_threshold))
  print("Listening")
  while True:
    with m as source: audio = r.listen(source)
    try:
      value = r.recognize_google(audio)
      print(value)
      string_queue.put(value)
    except sr.UnknownValueError:
      print("Unrecognizable noise")

def turn_on(port_id, time_sec, resource_flag):
  resource_flag.wait()
  resource_flag.clear()

  GPIO.output(port_id,GPIO.HIGH)
  time.sleep(time_sec)
  GPIO.output(port_id,GPIO.LOW)

  resource_flag.clear()


def string_processing(string_queue):
  # start flag usage to manage resources
  choco_bar_motor_flag = threading.Event()
  choco_bar_motor_flag.set()
  coke_motor_flag = threading.Event()
  coke_motor_flag.set()

  while True:
    if not string_queue.empty():
      string = string_queue.get()
      # check for hello entry
      if string in hello:
        # say hello back?
        pass
      # check for chocobar entry
      elif string in chocobar:
        th = threading.Thread(target=turn_on, args=(choco_bar_motor, 1, choco_bar_motor_flag))
        th.start()
      elif string in coke:
        th = threading.Thread(target=turn_on, args=(coke_motor, 1, coke_motor_flag))
        th.start()

def background_music(speaker_flag):
  p = vlc.MediaPlayer("file:///path/to/totowhilemyguitargentlywheeps.mp3")
  p.play()

  while True:
    if not speaker_flag.isSet():
      p.stop()
      speaker_flag.wait()
      p.play()



string_queue = queue.Queue()
listening_thread = threading.Thread(target=listening, args=(string_queue,))
listening_thread.start()

speaker_flag = threading.Event()
processing_thread = threading.Thread(target=string_processing, args=(string_queue, speaker_flag))
processing_thread.start()

back_music_thread = threading.Thread(target=background_music, args=(speaker_flag,))
back_music_thread.start()


a = 0
while 1:
  if a != string_queue.qsize():
    print(list(string_queue.queue))
    a = string_queue.qsize()
