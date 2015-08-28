#!/usr/bin/env python
# -*- coding: latin-1 -*-
#####
#
# A lean screencasting tool for Windows (Linux to come) using FFMPEG.
#
#   Dependence Windows :
#     - FFMPEG (Open Source), static Zeranoe build  http://ffmpeg.zeranoe.com/builds/
#     - "Screen Capture DirectShow source filter" (Freeware : http://www.umediaserver.net/components)
#     (looking to replace it with an OpenSoruce filter but not requiring Java for the end user)
#   
#    Author : https://sites.google.com/site/francoisschnell/
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#   
#####

__version__="1.0-alpha1"

import wx,os,subprocess,datetime,webbrowser

# Global variables
global pathData,audioinputName,videoFileOutput,recording

pathData=""
"Gives recording default folder path"
audioinputName=""
"Audio input name"
videoFileOutput=""
"Video file output path"
#recordingDuration=""
"Duration of the current recording"
recording=False
"recording status True or False"

def getAudioVideoInputFfmpeg(pathData=pathData):
        """A function to get Audio input from ffmpeg.exe (http://ffmpeg.zeranoe.com/builds/)
        Returns a list of two lists : [audioDevices,videoDevices]"""    
        os.system('ffmpeg -list_devices true -f dshow -i dummy > "%s"\devices.txt 2>&1' %pathData)
        audioDevices=[] 
        videoDevices=[]
        audioIndex=None 
        videoIndex=None 
        fileDevices =open(pathData+'\\devices.txt','r')
        devicesList=fileDevices.readlines()
        fileDevices.close()
        def fixCaracters(name):
            name=name.replace("Ã©","é")
            name=name.replace("Â®","®")
            name=name.replace("Ã¨","è")
            name=name.replace("Ãª","ê")
            return name
        # searching audio devices
        for index,device in enumerate(devicesList):
            if device.find("audio devices")>0:
                audioIndex= int(index) 
                print "Found 'audio devices' from Direcshow/ffmpeg, taking first device by default (0)"
            if (audioIndex!=None)and(index>audioIndex) and (device.find("exit")<0):
                aDevice=device.split('"')[1]
                print index-(audioIndex+1),":", aDevice
                audioDevices.append(fixCaracters(aDevice))
        # searching video devices
        for index,device in enumerate(devicesList):
            if device.find("video devices")>0:
                videoIndex= int(index) 
                print "Found 'video devices' from Direcshow/ffmpeg, taking first device by default (0)"
            if device.find("audio devices")>0:
                break
            if (videoIndex!=None) and (index>videoIndex):
                aDevice=device.split('"')[1]
                print index-(videoIndex+1),":", aDevice
                videoDevices.append(fixCaracters(aDevice))    
        print "audio device deduced from devices.txt", audioDevices
        print "video device deduced from devices.txt", videoDevices     
        return [audioDevices,videoDevices]
    
def engageRecording(pathData,audioinputName):
    """ Engage recording """
    global ffmpegHandle
    time = datetime.datetime.now()
    timeStr=str(time)
    videoFileOutput = pathData+"/"+timeStr[0:10]+'-'+ timeStr[11:13] +"h-"+timeStr[14:16] +"m-" +timeStr[17:19]+"s.mp4"
    cmd=('ffmpeg -f dshow -i video="UScreenCapture" -f dshow -i audio="%s" -q 5 "%s"')%(audioinputName, videoFileOutput)
    ffmpegHandle=subprocess.Popen(cmd,stdin=subprocess.PIPE,shell=True)
    
 
def stopRecording():
    """ Stop recording"""
    global ffmpegHandle
    try:
        ffmpegHandle.stdin.write("q") 
        ffmpegHandle.kill()
    except:
        print "WARNING: Can't stop properly FFMPEG subprocess, attempting forced taskkill, media may not be directly readable..."
        text=_("WARNING: Can't stop properly FFMPEG subprocess,\n attempting forced stop, media may not be readable.")
        dialog=wx.MessageDialog(None,message=text,caption="WARNING",style=wx.OK|wx.ICON_INFORMATION)
        dialog.ShowModal()
        #writeInLogs("- WARNING: Can't stop properly FFMPEG subprocess, attempting forced taskkill, media may lack header as a result and may not be directly readable... "+ str(datetime.datetime.now())+"\n")
        os.popen("taskkill /F /IM  ffmpeg.exe") 

def openFolder(pathData):
    """ Open Publish recording"""
    # Open publishing URL
    url="https://github.com/notfrancois/FFscreenrecorder"
    webbrowser.open(url, new=2, autoraise=True)
    # Open explorer folder
    subprocess.Popen('explorer "%s"'%(pathData))
        
def createRecordingsFolder():
    """ Create recordings folder """
    # Create a default folder for the recordings
    pathData=os.environ["USERPROFILE"]+"\\FFscreenrecorder"
    if os.path.isdir(os.environ["USERPROFILE"]+"\\FFscreenrecorder"):
        print "Default data folder OK"
    else: 
        print "Creating default data folder in USERPROFILE\\FFscreenrecorder"
        os.mkdir(pathData) 
    return pathData

class MainFrame(wx.Frame):
    """ 
    Main app's frame.
    """
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=(400, 170))
        
        panel=wx.Panel(self)
        panel.SetBackgroundColour("white") 
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        
        favicon = wx.Icon('images/statusIdle.ico', wx.BITMAP_TYPE_ICO, 16, 16)
        wx.Frame.SetIcon(self, favicon)
    
        self.statusBar=self.CreateStatusBar()
        self.statusBar.SetStatusText("FFscreenrecorder version "+__version__)
        
        menubar=wx.MenuBar()
        menuInformation=wx.Menu()
        menubar.Append(menuInformation,"Menu")
        helpMenu=menuInformation.Append(wx.NewId(),"FFscreenrecorder Github page")
        self.Bind(wx.EVT_MENU,self.helpInfos,helpMenu)
        conf=menuInformation.Append(wx.NewId(),"Configuration")
        self.Bind(wx.EVT_MENU,self.configuration,conf)
        version=menuInformation.Append(wx.NewId(),"Version")
        self.Bind(wx.EVT_MENU,self.about,version)
        self.SetMenuBar(menubar)
                    
        self.timeLabel= wx.StaticText(panel, -1,"Duration (hh.mm.ss) : Start a recording. ",size=(300,30),style=wx.ALIGN_CENTER)
        
        btnRecord = wx.Button(parent=panel, id=-1, label="Record!",size=(100,30))
        self.Bind(wx.EVT_BUTTON, self.orderRecording, btnRecord)
        btnStop = wx.Button(parent=panel, id=-1, label="Stop",size=(50,30))
        self.Bind(wx.EVT_BUTTON, self.orderStopRecording, btnStop)
        btnOpen = wx.Button(parent=panel, id=-1, label="Open",size=(100,30))
        self.Bind(wx.EVT_BUTTON, self.orderOpen,btnOpen)
        
        sizerV = wx.BoxSizer(wx.VERTICAL)
        sizerH=wx.BoxSizer()
        sizerV.Add(sizerH, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        sizerH.Add(btnRecord, 0, wx.ALIGN_CENTER|wx.ALL, 0)
        sizerH.Add(btnStop, 0, wx.ALIGN_CENTER|wx.ALL, 0)
        sizerH.Add(btnOpen, 0, wx.ALIGN_CENTER|wx.ALL, 0)
        sizerV.Add(self.timeLabel, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        panel.SetSizer(sizerV)
        panel.Layout() 

    def update(self, evt):
        self.timeLabel.SetLabel("Duration (hh.mm.ss) : "+str(datetime.datetime.now()-self.recordingStart)[0:7])
        
    def orderRecording(self,evt):
        """Order recording from GUI button"""
        global recording
        if recording==False:
            recording=True
            self.Iconize( True )
            tbicon.SetIcon(icon2, "FFscreenrecorder, recording ongoing...")
            self.recordingStart=datetime.datetime.now()
            self.timer.Start(1000)
            engageRecording(pathData,audioinputName)
        if recording==True:
            self.statusBar.SetStatusText("Screen recording already ongoing...")
        
    def orderStopRecording(self,evt):
        """Order stop recording from GUI button"""
        global recording
        if recording ==True:
            recording=False
            self.timer.Stop()
            tbicon.SetIcon(icon1, "FFscreenrecorder idle")
            stopRecording()
        if recording==False:
            self.statusBar.SetStatusText("Idle")
            
    def orderOpen(self,evt):
        """ Order Open/Publish from the GUI button"""
        openFolder(pathData)
        
    def helpInfos(self,evt):
        """ A function to provide help on how to use the software"""
        webbrowser.open(url="https://github.com/notfrancois/FFscreenrecorder", new=2, autoraise=True)
        
    def configuration(self,evt):
        """ A function to search for a configuration file"""
        print "Configuration file to come..."
        
    def about(self,evt):
        """ A function to show an about popup"""
        print "In about"

if __name__=="__main__":
        
    app=wx.App(redirect=False)
    frame = MainFrame(None, "FFscreenrecorder") 
    frame.Show(True)
    
    # Create and set a taskbar icon giving app state
    icon1 = wx.Icon('images/statusIdle.ico', wx.BITMAP_TYPE_ICO)
    icon2 = wx.Icon('images/statusRecording.ico', wx.BITMAP_TYPE_ICO)
    tbicon = wx.TaskBarIcon()
    tbicon.SetIcon(icon1, "FFSR Idle")
    
    # Create a data folder if not present in ALLUSERSDATA
    pathData=createRecordingsFolder()
    
    # Use audio source
    audioinputName=getAudioVideoInputFfmpeg(pathData)[0][0]
    
    app.MainLoop()