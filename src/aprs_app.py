#!/Users/mlustig/anaconda/bin/python

# APRS application gui for EE123 Digital Signal Processing Class. 
#
# There are a few important places to look at:
#
#  OnToggleStart:   Is a function that is called when the start and quit buttons are pressed
#		    The function initializes everything and starts all the threads
#
#
#  OnPressEnter:    This function is called when the enter key is pressed after entering
#		    text in the message box. It creates a packet from the text
#		    and transmits it
#
#
#  beaconXmit:	    This function is called every 60seconds by the gui application. It 
#		    checks if the beacon button is pressed, if so it will transmit
#		    a beacon package with your location information. 
#
#
#   updateScreen    This function is called every 1/2 a second to check the text queue and
#		    if a message appears, it displays it on the screen. 
#
#
#
# Written by Michael Lustig, 2015 


import Tkinter
from Tkinter import RIGHT, Y, LEFT, N, S, RIDGE, SUNKEN, VERTICAL, NORMAL, DISABLED
from ttk import Frame, Button, Label, Style
import time
import threading
import Queue
import pyaudio
import sys
import glob
import serial
import ConfigParser
from aprs import *
import ax25
import bitarray
import string



def hex_escape(s):
    return ''.join(c if c in string.printable else "x" for c in s)	



class aprs_tk(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
       

	self.grid()

	self.fs = 48000
	self.Abuffer = 12000
	# set up text boxes for input and output text
	Sin = Tkinter.Scrollbar(self)
	Sin.grid(column=50, row=0, rowspan=20,sticky="N"+"S")
        Sout = Tkinter.Scrollbar(self)
	Sout.grid(column=50, row=20, rowspan=20,sticky="N"+"S")
	self.Tin = Tkinter.Text(self,relief=RIDGE, bg='gray')
	self.Tin.grid(column = 0, row=0, rowspan=20,columnspan=50,  sticky="N"+"S"+"E"+"W")
	self.Tout = Tkinter.Text(self,relief=SUNKEN)
	self.Tout.grid(column = 0, row=20,rowspan=20, columnspan=50,  sticky="N"+"S"+"E"+"W")
	Sin.config(command=self.Tin.yview)
	self.Tin.config(yscrollcommand=Sin.set)
	Sout.config(command=self.Tout.yview)
	self.Tout.config(yscrollcommand=Sout.set)
	

	# Make sure everything scales when resizing the window
	for n in range(0,40):
		self.grid_rowconfigure(n,weight=1)
        for n in range(0,53):
		self.grid_columnconfigure(n,weight=1)
 

	# Add the input text box entry -- set to disable by default. Will be enabled when Start button is pressed
	# Bind the event OnPressEnter when enter is pressed -- the transmitter will be enabled
        self.entryVariable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=1,row=40,columnspan=49 ,sticky="E"+"W")
        self.entry.bind("<Return>", self.OnPressEnter)
	self.entry.config(state=DISABLED)
	self.entryL = Tkinter.Label(self,text="MSG:")
	self.entryL.grid(column=0,row=40,sticky="E"+"W")

	#Add a start button
	self.toggleButton = Tkinter.Button(self,text=u"Start", command=self.OnToggleStart)
        self.toggleButton.grid(column=52,row=40, sticky="E"+"W")

	# Add configuration boxes and variables
	self.callSignVar = Tkinter.StringVar()
	self.digiVar = Tkinter.StringVar()
	self.destVar = Tkinter.StringVar()
	self.toCallSignVar = Tkinter.StringVar()
	self.serialBoxVar = Tkinter.StringVar()


	self.callSign = Tkinter.Entry(self,textvariable=self.callSignVar, width = 13)
	self.callSign.grid(column=52,row=0,columnspan=1, sticky=N)
	self.callSignL = Tkinter.Label(self,text="Your Callsign:")
	self.callSignL.grid(column=51,row=0,columnspan=1,sticky="N"+"W")

	self.digi = Tkinter.Entry(self,textvariable=self.digiVar, width = 13)
	self.digi.grid(column=52,row=1,columnspan=1, sticky=N)
	self.digiVar.set(b'WIDE1-1,WIDE2-1')
	self.digiL = Tkinter.Label(self,text="Digi Path:")
	self.digiL.grid(column=51,row=1,columnspan=1,sticky="N"+"W")

	self.dest = Tkinter.Entry(self,textvariable=self.destVar, width = 13)
	self.dest.grid(column=52,row=2,columnspan=1, sticky=N)
	self.destVar.set(b'APDSP')
	self.destL = Tkinter.Label(self,text="Dest:")
	self.destL.grid(column=51,row=2,columnspan=1,sticky="N"+"W")

	self.toCallSign = Tkinter.Entry(self,textvariable=self.toCallSignVar, width = 13)
	self.toCallSign.grid(column=52,row=3,columnspan=1, sticky=N)
	self.toCallSignVar.set(b'')
	self.toCallSignL = Tkinter.Label(self,text="To Callsign:")
	self.toCallSignL.grid(column=51,row=3,columnspan=1,sticky="N"+"W")

	self.audioInBox = Tkinter.Listbox(self,exportselection=0)
	self.audioInBoxS = Tkinter.Scrollbar(self, orient=VERTICAL)
	self.audioInBox.config(yscrollcommand=self.audioInBoxS.set)
	self.audioInBoxS.config(command=self.audioInBox.yview)
	self.audioInBox.grid(column=52,row=7,rowspan=5, sticky="W")
	self.audioInBoxS.grid(column=53,row=7,rowspan=5,sticky="W")
	self.audioInL = Tkinter.Label(self,text="USB In:")
	self.audioInL.grid(column=51,row=5,sticky="N"+"W")

	self.audioOutBox = Tkinter.Listbox(self,exportselection=0)
	self.audioOutBoxS = Tkinter.Scrollbar(self, orient=VERTICAL)
	self.audioOutBox.config(yscrollcommand=self.audioInBoxS.set)
	self.audioOutBoxS.config(command=self.audioInBox.yview)
	self.audioOutBox.grid(column=52,row=13,rowspan=5, sticky="W")
	self.audioOutBoxS.grid(column=53,row=13,rowspan=5,sticky="W")
	self.audioOutL = Tkinter.Label(self,text="USB Out:")
	self.audioOutL.grid(column=51,row=13,sticky="N"+"W")

	self.audioSpBox = Tkinter.Listbox(self,exportselection=0)
	self.audioSpBoxS = Tkinter.Scrollbar(self, orient=VERTICAL)
	self.audioSpBox.config(yscrollcommand=self.audioInBoxS.set)
	self.audioSpBoxS.config(command=self.audioInBox.yview)
	self.audioSpBox.grid(column=52,row=18,rowspan=5, sticky="W")
	self.audioSpBoxS.grid(column=53,row=18,rowspan=5,sticky="W")
	self.audioSpL = Tkinter.Label(self,text="Speaker:")
	self.audioSpL.grid(column=51,row=18,sticky="N"+"W")

	self.serialBox = Tkinter.Entry(self,textvariable=self.serialBoxVar, width = 15)
	self.serialBox.grid(column=52,row=25,columnspan=2, sticky=N)
	self.serialBoxVar.set(b'/dev/tty.SLAB_USBtoUART')
	self.serialBoxL = Tkinter.Label(self,text="PTT Serial Port:")
	self.serialBoxL.grid(column=51,row=25,columnspan=1,sticky="N"+"W")

######### Position Beacon iface ############################

	# check button for APRS position Beacon
	self.beaconVar = Tkinter.IntVar()
	self.beaconVar.set(0)
	self.beaconButt = Tkinter.Checkbutton(self,text="Beacon",variable=self.beaconVar)
	self.beaconButt.grid(column=52,row=27,sticky="N"+"E")
	
	self.beaconLatBoxVar = Tkinter.StringVar()
	self.beaconLatBox = Tkinter.Entry(self,textvariable=self.beaconLatBoxVar, width = 8)
	self.beaconLatBox.grid(column=52,row=28,columnspan=1, sticky="N"+"W")
	self.beaconLatBoxVar.set(b'3752.50N')
	self.beaconLatBoxL = Tkinter.Label(self,text="Lat/Lon")
	self.beaconLatBoxL.grid(column=51,row=28,columnspan=1,sticky="N"+"W")

	self.beaconLonBoxVar = Tkinter.StringVar()
	self.beaconLonBox = Tkinter.Entry(self,textvariable=self.beaconLonBoxVar, width = 8)
	self.beaconLonBox.grid(column=52,row=28,columnspan=1, sticky="N"+"E")
	self.beaconLonBoxVar.set(b'12215.43W')

	self.beaconIcnBoxVar = Tkinter.StringVar()
	self.beaconIcnBox = Tkinter.Entry(self,textvariable=self.beaconIcnBoxVar, width = 1)
	self.beaconIcnBox.grid(column=52,row=30,columnspan=2, sticky="N"+"W")
	self.beaconIcnBoxVar.set(b'K')
	self.beaconIcnBoxL = Tkinter.Label(self,text="Symb/Comnt")
	self.beaconIcnBoxL.grid(column=51,row=30,columnspan=1,sticky="N"+"W")

	self.beaconCmntBoxVar = Tkinter.StringVar()
	self.beaconCmntBox = Tkinter.Entry(self,textvariable=self.beaconCmntBoxVar, width = 15)
	self.beaconCmntBox.grid(column=52,row=30,columnspan=2, sticky="N"+"E")
	self.beaconCmntBoxVar.set(b'EE123 Rocks!')


	# pyaudio and serial variable to be used later
	self.p = ''
	self.serial = ''
	self.run = False

	# to populate the devices for the configuration boxes open pyaudio and get a list of devices
	p = pyaudio.PyAudio()
	for n in range(0,p.get_device_count()):
		self.audioInBox.insert(Tkinter.END,p.get_device_info_by_index(n).get('name'))
		self.audioOutBox.insert(Tkinter.END,p.get_device_info_by_index(n).get('name'))
		self.audioSpBox.insert(Tkinter.END,p.get_device_info_by_index(n).get('name'))

	p.terminate()	
	
	# attempt to load an aprs.ini -- ini is generated/updated when start button or quit button are presseds	
	try:
		Config = ConfigParser.ConfigParser()
		Config.read('aprs.ini')
		self.audioSpBox.select_set(int(Config.get('Settings','SP_OUT')))
		self.audioInBox.select_set(int(Config.get('Settings','USB_IN')))
		self.audioOutBox.select_set(int(Config.get('Settings','USB_OUT')))
		self.callSignVar.set(Config.get('Settings','CallSign'))
		self.destVar.set(Config.get('Settings','Dest'))
		self.digiVar.set(Config.get('Settings','Digi'))
		self.toCallSignVar.set(Config.get('Settings','ToCallSign'))
		self.serialBoxVar.set(Config.get('Settings','SERIAL'))
		self.beaconVar.set(int(Config.get('Beacon','On')))
		self.beaconLatBoxVar.set(Config.get('Beacon','Lat'))
		self.beaconLonBoxVar.set(Config.get('Beacon','Lon'))
		self.beaconIcnBoxVar.set(Config.get('Beacon','Icn'))
		self.beaconCmntBoxVar.set(Config.get('Beacon','Cmnt'))


	except:
		print("Initializing... no ini file... will write later")

        # create Queues for audio and text
	self.textQ = Queue.Queue()
	self.ainQ = Queue.Queue()
	self.aoutQ = Queue.Queue()
	self.spQ = Queue.Queue()
	
	self.ctrlQ1 = Queue.Queue()
	self.ctrlQ2 = Queue.Queue()

	# create modem

	self.modem = TNCaprs(fs = self.fs,Abuffer = self.Abuffer,Nchunks = self.fs//self.Abuffer+1 )

	# variables for threading
	self.t_rrec = ''
	self.t_rplay = ''
	self.t_splay = ''
	self.t_aprs_rcv = ''

	# message counter
	self.msgnum = 1

	self.update()
        self.geometry(self.geometry())       
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    # function for start button. 	
    def OnToggleStart(self):

######## QUIT IS PRESSED ####################################################
# if already started, then button shows quit. This will quit the program as gently as possible
# pyaudio is killed, then an ini file is updated with the current configuration
	if self.run:
		self.p.terminate()
		Config = ConfigParser.ConfigParser()
		
		try:
			usb_in = self.audioInBox.curselection()[0]
			usb_out = self.audioOutBox.curselection()[0]
			sp_out = self.audioSpBox.curselection()[0]
			cfgfile=open("aprs.ini",'w')
			Config.add_section('Settings')
			Config.add_section('Beacon')
			Config.set('Settings','CallSign',self.callSignVar.get())
			Config.set('Settings','Dest',self.destVar.get())
			Config.set('Settings','Digi',self.digiVar.get())
			Config.set('Settings','ToCallSign',self.toCallSignVar.get())
			Config.set('Settings','USB_IN',usb_in)
			Config.set('Settings','USB_OUT',usb_out)
			Config.set('Settings','SP_OUT',sp_out)
			Config.set('Settings','SERIAL',self.serialBoxVar.get())
			Config.set('Beacon','On',str(self.beaconVar.get()))
			Config.set('Beacon','Lon',self.beaconLonBoxVar.get())
			Config.set('Beacon','Lat',self.beaconLatBoxVar.get())
			Config.set('Beacon','Icn',self.beaconIcnBoxVar.get())
			Config.set('Beacon','Cmnt',self.beaconCmntBoxVar.get())
			Config.write(cfgfile)
			cfgfile.close()
		except:
			print("Can't save to config file")


		self.quit()
		
######## START IS PRESSED ####################################################
	# When start is pressed, everything with regard to APRS is initialized
	# 1) Audio configuration lists are disabled
	# 2) Button label  is changed to Quit
	# 3) Entry box is enabled
	# 4) Serial port is opened
	# 5) usb and audio device numbers are read from the listboxes
	# 6) Audio threads are started in daemon mode, so they are killed with the application
	# 7) APRS listener is started
	# 8) aprs.ini file is written with current configuration
	# 9) Start beacon

	else: 
		self.toggleButton["text"]=u"Quit"
		self.run = not self.run
	# Diasable Listboxes
		self.audioInBox.configure(state=DISABLED)
		self.audioOutBox.configure(state=DISABLED)
		self.audioSpBox.configure(state=DISABLED)
	# Enable Entry box 
		self.entry.configure(state=NORMAL)
	# Initialize pyaudio and get device numbers
		self.p = pyaudio.PyAudio()
		usb_in = self.audioInBox.curselection()[0]
		usb_out = self.audioOutBox.curselection()[0]
		sp_out = self.audioSpBox.curselection()[0]
	# attempt to open a serial port for PTT control
		try:
			self.serial = serial.Serial(port=self.serialBoxVar.get())
			self.serial.setDTR(0)
		except:
			print("Can't open Serial Port!")
	# Create thread for radio-> computer via usb audio 
		self.t_rrec =  threading.Thread(target = record_audio,   args = (self.ainQ, self.ctrlQ1,   self.p, self.fs, usb_in, self.Abuffer  ))
		self.t_rrec.setDaemon(True)
	# Create thread for computer -> radio via usb audio
		self.t_rplay =  threading.Thread(target = play_audio,   args = (self.aoutQ, self.ctrlQ2,   self.p, self.fs, usb_out,self.serial  ))
		self.t_rplay.setDaemon(True)
	# Create thread for playing on computer speaker. Audio is received from the radio and played on the computer for debugging
		self.t_splay =  threading.Thread(target = play_audio,   args = (self.spQ, self.ctrlQ2,  self.p, self.fs, sp_out  ))
		self.t_splay.setDaemon(True)
	# Creat thread for the aprs receiver application. It receives audio from radio, plays the audio on the speaker, decodes packet and sends decoded text back through textQ to be displayes
		self.t_aprs_rcv =  threading.Thread(target = APRS_rcv, args= (self.ainQ, self.spQ,self.textQ, self.modem))
		self.t_aprs_rcv.setDaemon(True)

	# start threads
		self.t_rrec.start()
		self.t_rplay.start()
		self.t_splay.start()
		self.t_aprs_rcv.start()

	# save configureation file
		Config = ConfigParser.ConfigParser()
		try:
			cfgfile=open("aprs.ini",'w')
			Config.add_section('Settings')
			Config.add_section('Beacon')
			Config.set('Settings','CallSign',self.callSignVar.get())
			Config.set('Settings','Dest',self.destVar.get())
			Config.set('Settings','Digi',self.digiVar.get())
			Config.set('Settings','ToCallSign',self.toCallSignVar.get())
			Config.set('Settings','USB_IN',usb_in)
			Config.set('Settings','USB_OUT',usb_out)
			Config.set('Settings','SP_OUT',sp_out)			
			Config.set('Settings','SERIAL',self.serialBoxVar.get())
			Config.set('Beacon','On',str(self.beaconVar.get()))
			Config.set('Beacon','Lon',self.beaconLonBoxVar.get())
			Config.set('Beacon','Lat',self.beaconLatBoxVar.get())
			Config.set('Beacon','Icn',self.beaconIcnBoxVar.get())
			Config.set('Beacon','Cmnt',self.beaconCmntBoxVar.get())
			Config.write(cfgfile)
			cfgfile.close()
		except:
			print("Can't save to config file")
		
		self.beaconXmit()
			
		
					 	
    # When Enter is pressed on the MSG box, a packet will be contructed and transmitted to the radio
    #
    def OnPressEnter(self,event):
        
	# insert the text to the input text window
	self.Tout.insert(Tkinter.INSERT,  self.entryVariable.get()+"\n" )
	
	# get information on callsign, digi, dest and tocallsign to construct a message
	Digi =  self.digiVar.get()
	callsign = self.callSignVar.get()
	dest = self.destVar.get()
	tmp = self.toCallSignVar.get()
	if len(tmp)>=9:
		tocallsign = tmp[:9]
	else:
		tocallsign='{:<9}'.format(tmp)
        
	# Construct the info message that can be interpreted -- concatenate message number to be compatible with 
	# existing radios
	if self.entryVariable.get()[:3]=="ack":
		info = ":"+tocallsign+":"+ self.entryVariable.get() 
	else:
		info = ":"+tocallsign+":"+ self.entryVariable.get() + "{"+ "{0:02d}".format(self.msgnum)
	self.msgnum = (self.msgnum + 1)%100


	# create afsk1200 signal
	msg = self.modem.modulatPacket(callsign[:7], Digi, dest[:6], info,  preflags=100, postflags=100  )
	
	# send keyon, message and keyoff to the radio -- and clear box
	self.aoutQ.put("KEYON")
	self.aoutQ.put(msg*0.2)
	self.aoutQ.put("KEYOFF")
	self.entryVariable.set(u"")
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

    # intermitenly check the text Queue -- if there's something there, display it. 
    def updateScreen(self):
     #try:
	while not(self.textQ.empty()) :
		ax = self.textQ.get()
		callsign = self.callSignVar.get()
		if callsign in ax.info:
			self.Tin.tag_config("a", foreground="blue")
			self.Tin.insert('1.0', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M") ,str(ax)),"a" )
			print("Callsign:"+callsign+"  was detected\n")
		else:			
			self.Tin.insert('1.0', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M") ,str(ax)) )
		self.Tin.insert('1.0', "\n")
	self.after(500,self.updateScreen)
     #except:
#	print('exception')
        # intermitenly check for beacon status and xmit position beacon
    def beaconXmit(self):
	if (self.beaconVar.get()) :
		Digi =  self.digiVar.get()
		callsign = self.callSignVar.get()
		dest = self.destVar.get()
		tmp = self.toCallSignVar.get()
		if len(tmp)>=9:
			tocallsign = tmp[:9]
		else:
			tocallsign='{:<9}'.format(tmp)
		# construct the beacon message from the input boxes
		info = "="+self.beaconLatBoxVar.get()+"/"+self.beaconLonBoxVar.get()+self.beaconIcnBoxVar.get()+self.beaconCmntBoxVar.get()
		# use the AX25 package to construct the bits
		

		msg = self.modem.modulatPacket(callsign[:7], Digi, dest[:6], info, preflags = 100, postflags = 100 )
		# send keyon, message and keyoff to the radio -- and clear box
		self.aoutQ.put("KEYON")
		self.aoutQ.put(msg*0.2)
		self.aoutQ.put("KEYOFF")

	 	
	self.after(60000,self.beaconXmit)



if __name__ == "__main__":
    app = aprs_tk(None)
#    counter= threading.Thread(target=count)
#    counter.start()
    app.after(500,app.updateScreen)
    app.title('APRS123')
    app.mainloop()
