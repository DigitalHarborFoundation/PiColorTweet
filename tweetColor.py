#!/usr/bin/python
import sys
import ConfigParser
import datetime
from TwitterSearch import *
import requests
from twisted.internet import reactor
from twisted.internet import task
import smbus
import time
import re
from twisted.internet import pollreactor
from neopixel import *
from functools import partial

#Initial Setup
MY_HASH_TAG="#DHFColor"
MY_LED_COUNT      = 32      # Number of LED pixels.
MY_SEARCH_DELAY = 5
MY_CONSUMER_KEY = 'xxx'  #Created at https://apps.twitter.com/
MY_CONSUMER_SECRET = 'xxx'
MY_ACCESS_TOKEN = 'xxx'
MY_ACCESS_TOKEN_SECRET = 'xxx'


####### No need to modify anything below this line
LOG_FILE='log.ini'

config = ConfigParser.RawConfigParser()
config.read(LOG_FILE)
maxID=config.getint('Twitter', 'maxID')
tweetCount=config.getint('Twitter', 'tweetCount')
print("Using maxID: " + str(maxID))

##Twitter Search Setup
tso = TwitterSearchOrder() # create a TwitterSearchOrder object
tso.set_keywords([MY_HASH_TAG]) # let's define all words we would like to have a loook for
tso.set_include_entities(False) # and don't give us all those entity information
tso.set_result_type('recent')
ts = TwitterSearch(consumer_key=MY_CONSUMER_KEY,
                  consumer_secret=MY_CONSUMER_SECRET,
                  access_token=MY_ACCESS_TOKEN,
                  access_token_secret=MY_ACCESS_TOKEN_SECRET)


# LED strip configuration:
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# Create NeoPixel object with appropriate configuration.
global strip
strip = Adafruit_NeoPixel(MY_LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, strip_type=ws.WS2811_STRIP_GRB)

#######################
# If colors are not in right order, change strip_type value:
# WS2811_STRIP_BGR = 2064
# WS2811_STRIP_BRG = 4104
# WS2811_STRIP_GBR = 524304
# WS2811_STRIP_GRB = 528384
# WS2811_STRIP_RBG = 1048584
# WS2811_STRIP_RGB = 1050624
#######################


# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
	print "Color Wipe"
	"""Wipe color across display a pixel at a time."""
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
		strip.show()
		time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
	print "Theatre Mode"
	"""Movie theater light style chaser animation."""
	for j in range(iterations):
		for q in range(3):
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, color)
			strip.show()
			time.sleep(wait_ms/1000.0)
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, 0)
	colorWipe(strip,Color(0,0,0))

def wheel(pos):
	"""Generate rainbow colors across 0-255 positions."""
	if pos < 85:
		return Color(pos * 3, 255 - pos * 3, 0)
	elif pos < 170:
		pos -= 85
		return Color(255 - pos * 3, 0, pos * 3)
	else:
		pos -= 170
		return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
	print "Rainbow mode"
	"""Draw rainbow that fades across all pixels at once."""
	for j in range(256*iterations):
		for i in range(strip.numPixels()):
			strip.setPixelColor(i, wheel((i+j) & 255))
		strip.show()
		time.sleep(wait_ms/1000.0)
	colorWipe(strip,Color(0,0,0))

def rainbowCycle(strip, wait_ms=20, iterations=5):
	"""Draw rainbow that uniformly distributes itself across all pixels."""
	for j in range(256*iterations):
		for i in range(strip.numPixels()):
			strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
		strip.show()
		time.sleep(wait_ms/1000.0)
	colorWipe(strip,Color(0,0,0))

def theaterChaseRainbow(strip, wait_ms=50):
	"""Rainbow movie theater light style chaser animation."""
	for j in range(256):
		for q in range(3):
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, wheel((i+j) % 255))
			strip.show()
			time.sleep(wait_ms/1000.0)
			for i in range(0, strip.numPixels(), 3):
				strip.setPixelColor(i+q, 0)
	colorWipe(strip,Color(0,0,0))

def doTwitterSearch():
    global tso
    global ts
    global maxID
    global tweetCount
    global config
    global nextLetter
    global strip
    global MY_CODES
		
    if(maxID<>0):
        tso.set_since_id(maxID)

    print("Using maxID: " + str(maxID))

    try:
        searchResult=ts.search_tweets_iterable(tso)
        results=searchResult.get_tweets()

        #Process tweet search results
        for tweet in searchResult:
            #print "checking tweet: " + tweet['text']
            for code in MY_CODES.keys():
                #print "Checking for code: " + code.lower()
                if (code.lower() in tweet['text'].lower()):
                    print tweet['text']
                    MY_CODES[code]()
                    print "Breaking check"
                    break

        maxID=results['search_metadata']['max_id']
        tweetCount += len(results['statuses'])
        config.set('Twitter', 'maxID', maxID)
        config.set('Twitter', 'tweetCount', tweetCount)
        config.set('Twitter','lastUpdate',datetime.datetime.now())
        # Writing last tweet id and total number of tweets to config file
        with open(LOG_FILE, 'wb') as configfile:
            config.write(configfile)
    except:
        e = sys.exc_info()[0]
        print("<p>Error: %s</p>" % e)
        print "We had a problem but I'm going to continue anyway"
        pass

# Main program logic follows:
if __name__ == '__main__':

	# Intialize the library (must be called once before other functions).
	strip.begin()

	print ('Press Ctrl-C to quit.')
	
	#Look up new color codes here: http://www.rapidtables.com/web/color/RGB_Color.htm
	MY_CODES={
		"red":partial(colorWipe,strip, Color(255, 0, 0)),
		"blue":partial(colorWipe,strip, Color(0, 0, 255)),
		"green":partial(colorWipe,strip, Color(0, 255, 0)),
		"white":partial(colorWipe,strip, Color(255, 255, 255)),
		"yellow":partial(colorWipe,strip, Color(255, 255, 0)),
		"cyan":partial(colorWipe,strip, Color(0, 255, 255)),
		"aqua":partial(colorWipe,strip, Color(0, 255, 255)),
		"teal":partial(colorWipe,strip, Color(0, 255, 255)),
		"magenta":partial(colorWipe,strip, Color(255, 0, 255)),
		"fuscia":partial(colorWipe,strip, Color(255, 0, 255)),
		"pink":partial(colorWipe,strip, Color(255, 0, 255)),
		"theatre":partial(theaterChase,strip, Color(255, 0, 255), 50, 10),
		"rainbow":partial(rainbow,strip,20,3)
	}

	# Color wipe animations.
	colorWipe(strip, Color(255, 0, 0))  # Red wipe
	colorWipe(strip, Color(255, 255, 0))  # Blue wipe	
	colorWipe(strip, Color(0, 255, 0))  # Green wipe
	colorWipe(strip, Color(0, 0, 0))  # Off wipe
	
		
	twitterLoop=task.LoopingCall(doTwitterSearch)
	twitterLoop.start(MY_SEARCH_DELAY)
	reactor.run()

		
# Theater chase animations.
# 		theaterChase(strip, Color(127, 127, 127))  # White theater chase
# 		theaterChase(strip, Color(127,   0,   0))  # Red theater chase
# 		theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
# Rainbow animations.
# 		rainbow(strip)
# 		rainbowCycle(strip)
# 		theaterChaseRainbow(strip)
