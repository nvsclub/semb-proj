import speech_recognition as sr
import queue
import threading
import RPi.GPIO as GPIO
import time
import vlc

###########################
#####   CONFIG PINS   #####
###########################

########    OUT PINS     ########
pin_outs = [8, 10, 12, 16]

###    MOTOR
choco_bar_motor = 8
coke_motor = 10
gum_motor = 12

###    LEDS
background_light_led = 16
light_button = 18

########    IN PINS PINS     ########
pin_ins = [18, 22, 24]

### CHANGE BUTTONS
small_change = 22
big_change = 24


##################################
#######    INITIAL SETUP   #######
##################################

### PIN INITIALIZATION

GPIO.cleanup()

# setup output pins
GPIO.setmode(GPIO.BOARD)
for pin in pin_outs:
    GPIO.setup(pin, GPIO.OUT)
for pin in pin_ins:
    GPIO.setup(pin, GPIO.IN)


########    CODE SETENCES

hello = ['hello', 'alo']
chocobar = ['chocobar', 'Google', 'bar', 'chocolate']
coke = ['Coca-Cola', 'coke', 'cocaine']
gum = ['gum']


##################################
######   SPEECH FUNCTIONS   ######
##################################


# listening thread
## gets all the recognized strings into a fifo queu
def listening(string_queue):
    r = sr.Recognizer()
    m = sr.Microphone()

    print("Calibrating, please remain silent.")
    # why use this || this is redundant?
    with m as source:
        r.adjust_for_ambient_noise(source)
    print("Set minimum energy threshold to {}".format(r.energy_threshold))
    print("Listening")
    while True:
        with m as source:
            audio = r.listen(source)
        try:
            value = r.recognize_google(audio)
            print(value)
            string_queue.put(value)
        except sr.UnknownValueError:
            print("Unrecognizable noise")

def string_processing(string_queue, speaker_flag):
    # start flag usage to manage resources
    choco_bar_motor_flag = threading.Event()
    choco_bar_motor_flag.set()
    coke_motor_flag = threading.Event()
    coke_motor_flag.set()
    gum_motor_flag = threading.Event()
    gum_motor_flag.set()

    hello_track = vlc.MediaPlayer("hello.mp3")

    while True:
        if not string_queue.empty():
            string = string_queue.get()
            word_list = string.split()
            print(word_list, hello)
            print(any(word_list == x for x in hello))
            # check for hello entry
            if any(w == x for x in hello for w in word_list):
                print('finkel')
                speaker_flag.clear()
                hello_track.play()
                time.sleep(3)
                hello_track.stop()
                speaker_flag.set()
            # check machine vending
            elif any(w == x for x in chocobar for w in word_list):
                th = threading.Thread(target=turn_on, args=(choco_bar_motor, 1, choco_bar_motor_flag))
                th.start()
            elif any(w == x for x in coke for w in word_list):
                th = threading.Thread(target=turn_on, args=(coke_motor, 1, coke_motor_flag))
                th.start()
            elif any(w == x for x in gum for w in word_list):
                th = threading.Thread(target=turn_on, args=(gum_motor, 1, gum_motor_flag))
                th.start()


##################################
######    MUSIC FUNCTIONS   ######
##################################


def background_music(speaker_flag):
    p = vlc.MediaPlayer("blackholesun.mp3")
    p.play()

    while True:
        if not speaker_flag.isSet():
            p.stop()
            speaker_flag.wait()
            p.play()

def background_light(light_flag):
  while True:
    input_value = GPIO.input(light_button)
    if not light_flag.isSet():
      while light_flag.isSet():
        GPIO.output(background_light_led,GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(background_light_led,GPIO.LOW)
        time.sleep(0.5)
    elif input_value == 1:
      GPIO.output(background_light_led,GPIO.HIGH)
      c = 0
      while c < 3:
        if not light_flag.isSet():
          break
        time.sleep(0.1)
        c += 1
      GPIO.output(background_light_led,GPIO.LOW)


##################################
####   OPERATIONS FUNCTIONS   ####
##################################


def turn_on(port_id, time_sec, resource_flag):
    resource_flag.wait()
    resource_flag.clear()

    GPIO.output(port_id, GPIO.HIGH)
    time.sleep(time_sec)
    GPIO.output(port_id, GPIO.LOW)

    resource_flag.set()


##################################
########   MAIN PROGRAM   ########
##################################


###THREAD INITIALIZATION

string_queue = queue.Queue()
listening_thread = threading.Thread(target=listening, args=(string_queue,))
listening_thread.start()

speaker_flag = threading.Event()
speaker_flag.set()
processing_thread = threading.Thread(target=string_processing, args=(string_queue, speaker_flag))
processing_thread.start()

back_music_thread = threading.Thread(target=background_music, args=(speaker_flag,))
back_music_thread.start()

light_flag = threading.Event()
background_light_thread = threading.Thread(target=background_light, args=(light_flag,))
background_light_thread.start()


'''a = 0
while 1:
  if a != string_queue.qsize():
    print(list(string_queue.queue))
    a = string_queue.qsize()'''