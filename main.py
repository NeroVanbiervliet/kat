from PyQt4 import QtGui,QtCore
import sys 
import design 
import os  # For listing directory methods
from TelegramWorker import TelegramWorker
from inspect import signature

# TODO KatApp in aparte file steken? 
class KatApp(QtGui.QMainWindow, design.Ui_MainWindow):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.setupUi(self) # defined in design.py file
		self.center() # center window on screen

		# keeps track if the setup is complete
		self.setupComplete = False

		# keep track of layers
		self.ledger = {'base':[]}
		self.layers = ['base'] # necessary because a dictionary is not ordered

		# print path (only base layer for now)
		self.printPath()
		
		# list of commands
		self.commands = {'nl':self.newLayer, 'cl':self.closeLayer, 'help':self.displayHelp, 'phone':self.setPhone, 'verify':self.verify, 'partner':self.setPartner, 'quit':self.closeApp}
		
		# setup telegram worker
		self.workerThread = QtCore.QThread() 
		self.telegramWorker = TelegramWorker()

		# connect signals and slots
		self.telegramWorker.newMessage.connect(self.onMessage)
		self.telegramWorker.setReady.connect(self.onReady)
		self.telegramWorker.reqPartner.connect(self.onPartnerRequest)
		self.telegramWorker.reqVerify.connect(self.onVerifyRequest)
		self.telegramWorker.loadingFinished.connect(self.onLoadingFinished)

		# assign telegramWorker to seperate thread
		self.telegramWorker.moveToThread(self.workerThread)
		self.workerThread.start()

		# initialse telegram worker
		QtCore.QMetaObject.invokeMethod(self.telegramWorker, 'initialise')

		# assign event handler to input text changes
		self.lineEdit.textChanged.connect(self.onInputTextChange)

	# SIGNAL HANDLERS

	def onMessage(self,message):
		self.processMessage('in',message)

	def onPartnerRequest(self):
		self.consoleWrite('system','enter partner username with the partner function')

	def onVerifyRequest(self):
		self.consoleWrite('system','telegram account setup is necessary')	
		self.consoleWrite('system','enter your phone number using the phone function. e.g phone +32487244130')

	def onReady(self):
		self.setupComplete = True
		self.consoleWrite('system','ready to send')
		self.consoleWrite('system','type help for command index')

	def onLoadingFinished(self):
		self.loadingScreen.setVisible(False)

	# COMMAND FUNCTIONS

	def closeApp(self):
		self.workerThread.quit()
		self.close()

	def newLayer(self,name):
		if name in self.layers:
			self.consoleWrite('system','layer name ' + name + ' already exists')	
		else:
			# create new layer
			self.ledger[name] = []
			self.layers.append(name)
			self.switchLayer(name)

	def closeLayer(self):
		# remove lowest layer
		del self.ledger[self.layers[-1]] 
		del self.layers[-1]
		self.switchLayer(self.layers[-1])

	def displayHelp(self):
		self.consoleWrite('system','HELP')
		self.consoleWrite('system','quit or [ESC] quits the application')
		self.consoleWrite('system','nl (new layer) creates a new layer, args: name')
		self.consoleWrite('system','cl (close layer) closes the current layer, args: none')

	def setPhone(self,phone):
		QtCore.QMetaObject.invokeMethod(self.telegramWorker, 'setPhone', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, phone)) # NEED niet via signal emit() ?  Check ook waar dit nog gebruikt wordt!
		self.consoleWrite('system','check the code you received in the telegram app. Enter it with the verify function')

	def verify(self,code):
		QtCore.QMetaObject.invokeMethod(self.telegramWorker, 'verify', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, code)) 
		self.consoleWrite('system','telegram verification done')

	def setPartner(self,username):
		QtCore.QMetaObject.invokeMethod(self.telegramWorker, 'setPartner', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, username)) 
		self.consoleWrite('system','partner ' + username + ' registered')

	# AUXILIARY FUNCTIONS

	# centers the application on the screen
	def center(self):
		frameGm = self.frameGeometry()
		screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
		centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
		frameGm.moveCenter(centerPoint)
		self.move(frameGm.topLeft())

	# capture input text changed event
	def onInputTextChange(self):
		# check if current input text is a command
		# TODO een label boven het input vak laten verschijnen met tips voor gebruik van de functie
		inputText = self.lineEdit.text()
		possibleCommand = inputText.split(' ')[0]
		if possibleCommand in self.commands:
			# set bold
			font = self.lineEdit.font()
			font.setBold(True)
			self.lineEdit.setFont(font)
		else:
			# unset bold
			font = self.lineEdit.font()
			font.setBold(False)
			self.lineEdit.setFont(font)


	# capture key presses
	def keyPressEvent(self, e):
		# ESC = quit
		if e.key() == QtCore.Qt.Key_Escape:
			self.closeApp()

		# ENTER = send message | execute command
		if e.key() == 16777220 or e.key() == QtCore.Qt.Key_Enter: # two different enter keys on keyboard

			inputText = self.lineEdit.text()
			self.processMessage('out',inputText)
				
			if self.setupComplete:
				QtCore.QMetaObject.invokeMethod(self.telegramWorker, 'sendMessage', QtCore.Qt.QueuedConnection, QtCore.Q_ARG(str, inputText)) 
	
			# clear text
			self.lineEdit.setText('')

	def processMessage(self,mType,message):
		possibleCommand = message.split(' ')[0]
		args = message.split(' ')[1::]
		if possibleCommand in self.commands:
			numReqArgs = len(signature(self.commands[possibleCommand]).parameters)
			if len(args) != numReqArgs:
				self.consoleWrite('system',possibleCommand + ' requires ' + str(numReqArgs) + ' arguments')
			else:
				self.commands[possibleCommand](*args)
		else:
			self.consoleWrite(mType,message)

	# mType (message type) can be: out | in | system
	def consoleWrite(self,mType,message,logLedger=True):
		if logLedger:
			# add message to ledger
			self.ledger[self.layers[-1]].append({'type':mType, 'message':message}) 

		if mType == 'out':
			if int(self.textBrowser.alignment()) != QtCore.Qt.AlignRight:
				# current block not aligned right
				# create new block
				self.textBrowser.textCursor().insertBlock()
				# set alignment right
				self.textBrowser.setAlignment(QtCore.Qt.AlignRight)

			# add new message
			self.textBrowser.append(message)

		elif mType == 'in': 
			if int(self.textBrowser.alignment()) != QtCore.Qt.AlignLeft:
				self.textBrowser.textCursor().insertBlock()
				self.textBrowser.setAlignment(QtCore.Qt.AlignLeft)

			# add new message
			self.textBrowser.append(message)

		elif mType == 'system':
			if int(self.textBrowser.alignment()) != QtCore.Qt.AlignCenter:
				self.textBrowser.textCursor().insertBlock()
				self.textBrowser.setAlignment(QtCore.Qt.AlignCenter)

			# add new message
			self.textBrowser.append("<i>" + message + "</i>")

		# reset scrollbar to bottom TODO max scroll werkt niet helemaal bij inkomende berichten
		self.textBrowser.verticalScrollBar().setSliderPosition(self.textBrowser.verticalScrollBar().maximum())

	def switchLayer(self, destLayer):
		# clear console
		self.textBrowser.setText('')

		# write content from layer to console
		for item in self.ledger[destLayer]:
			self.consoleWrite(item['type'],item['message'], logLedger=False)

		self.consoleWrite('system','switched to layer ' + destLayer)
		self.printPath()

	def printPath(self):
		textToSet = self.layers[0]
		for layer in self.layers[1::]:
			textToSet += ' > ' + layer

		self.labelPath.setText(textToSet)


def main():
	app = QtGui.QApplication(sys.argv)
	win = KatApp()
	win.setWindowFlags(win.windowFlags() | QtCore.Qt.FramelessWindowHint)
	win.show()
	app.exec_()

if __name__ == '__main__':  # if we're running file directly and not importing it
	main()  # run the main function


