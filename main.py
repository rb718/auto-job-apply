from PyQt5 import QtCore, QtGui, QtWidgets,uic
from PyQt5.QtWidgets import QApplication
import sys
import os
import yaml
import re
import logging
import datetime
import time
import json
import _thread

#--------------------  Directory Settings  --------------------#
dirname = os.getcwd()
os.chdir(dirname)
parameters ={}

#--------------------  Configuring Logging  --------------------#
epoch = str(int(time.time()))
TODAY = datetime.datetime.now()
TODAY = TODAY.strftime("%d-%m-%Y")
logFolder = os.path.join(dirname, 'logs')
if os.path.isdir(logFolder) is False:
    os.mkdir(logFolder)
logFile = os.path.join(logFolder,str(TODAY)+'-'+epoch+'.log')
# -------UNCOMMENT WHEN You want to redirect logs to logs file.
logging.basicConfig(filename=logFile,level=logging.INFO)
# -------UNCOMMENT WHEN if you dont want to redirect logs.
# logging.basicConfig(level=logging.INFO)

#--------------------  Enable Following For GUI Interface  --------------------#
GUI =True

if __name__ == '__main__':
    class startBot():
        logging.info("Application Started With GUI: {state}".format(state=GUI))
        def __init__(self):
            if GUI:
                app = QtWidgets.QApplication(sys.argv)
                self.call = uic.loadUi("LI.ui")
                self.call.setWindowTitle('EasyApply-LinkedIn')
                self.call.horizontalSlider.valueChanged.connect(self.number_changed)
                self.call.lineEdit_2.setEchoMode(self.call.lineEdit_2.Password)

                self.call.pushButton.clicked.connect(self.loginFunction) #Submit Button
                self.call.pauseButton.clicked.connect(self.enblPauseBtn) #Pause Button
                self.call.resumeButton.clicked.connect(self.enblResumeBtn) #Resume Button
                self.call.show()
                sys.exit(app.exec_())
            else:
                with open("config.yaml", 'r') as stream:
                    try:
                        parameters = yaml.safe_load(stream)
                    except yaml.YAMLError as exc:
                        raise exc
                
                assert len(parameters['positionList']) > 0
                assert len(parameters['locationList']) > 0
                assert parameters['username'] is not None
                assert parameters['password'] is not None
                
                output_filename = [f for f in parameters.get('output_filename', ['output.csv']) if f != None]
                output_filename = output_filename[0] if len(output_filename) > 0 else 'output.csv'
                parameters['oFile']= output_filename

                blacklist = parameters.get('blacklist', [])
                parameters['blacklist']= blacklist

                uploads = parameters.get('uploads', {})
                parameters['uploads']= uploads

                max_jobs_to_apply = 100
                parameters['max_jobs_to_apply']= max_jobs_to_apply

                if len(parameters['jobLinks'])== 1 and parameters['jobLinks'][0] is None:
                    parameters['jobLinks'] = []
                
                for key in uploads.keys():
                    assert uploads[key] != None

                bot = easyApplyBot(parameters)

        def easyApplyBot(self,params):

            username = params.get('username',None)
            password = params.get('password',None)
            uploads = params.get('uploads',{})
            filename = params.get('oFile',None)
            blacklist = params.get('blacklist',[])
            locationList = params.get('locationList',[])
            positionList = params.get('positionList',[])
            max_jobs_to_apply = params.get('max_jobs_to_apply',0)
            phone = params.get('phone',None)
            country = params.get('country',None)
            firstName = params.get('firstName','')
            lastName = params.get('lastName','')
            midName = params.get('midName','')
            jobLinks = params.get('jobLinks')

            jobIds =[]
            filterRichURL= False
            if len(jobLinks) > 0:
                positionList =[]
                locationList=[]
                try:
                    for jobLink in jobLinks:
                        regex_match_0 = re.search('(.*)/view/(.*)/(.*)',jobLink)
                        regex_match_1 = re.search('currentJobId=(\d+)(&.*)',jobLink)
                        regexMatch_2 = re.search('keywords=(.*)([&])location=(.*)',jobLink)
                        
                        if regex_match_0:
                            id = regex_match_0.group(2)
                            jobIds.append(id)
                        elif regex_match_1:
                            id = regex_match_1.group(1)
                            jobIds.append(id)
                        elif regexMatch_2:
                            filterRichURL = True
                        else:
                            logging.warning('Invalid Job Links.')
                    
                    if filterRichURL:
                        customUrls = jobLinks

                except Exception as jobLinkEncept:
                    logging.exception('Job Links not valid!!!',str(jobLinkEncept))
            if (midName) and (midName is not None):
                fullName = firstName +' '+ midName +' '+ lastName
            else:
                fullName = firstName +' '+ lastName

            obj = {'username':username,'uploads':uploads,'filename':filename,'blacklist':blacklist,
            'locationList-':locationList,'positionList-':positionList,'max_jobs_to_apply':max_jobs_to_apply,
            'jobIds':jobIds,'phone':phone,'country':country,'firstName':firstName,'lastName':lastName,'midName':midName,
            'fullName:':fullName}

            logging.info(json.dumps(obj))
            if username and password:
                from bots import li_apply_jobs
                aplyJob = li_apply_jobs.EasyApplyBot(fullName,username,password,max_jobs_to_apply,uploads,filename,blacklist)

                locations = [l for l in locationList if l != None]
                positions = [p for p in positionList if p != None]
                logging.info(json.dumps({'loc:':locations,'pos:':positions}))
                if len(jobIds) > 0:
                    logging.info('***********Specific Job Links are provided**************')
                    aplyJob.applications_loop(None, None,jobIds,None)
                elif filterRichURL:
                    apldJobs = []
                    logging.info('***********Custom FilterRich Job Links are provided**************')
                    for uri in customUrls:
                        apldJobs = aplyJob.applications_loop(None, None,jobIds,uri)
                    logging.info(f'~~~DONE~~~{apldJobs}')
                    self.enableSubmitBtn()
                    return True
                else:
                    logging.warning('************Automatic Job Application Process**********')
                    aplyJob.start_apply(positions, locations)
            else:
                logging.warning('Couldn"t start the process as no USERNAME PASSWORD IS SUPPLIED.')
                self.enableSubmitBtn()

        def loginFunction(self):
            self.disableSubmitBtn()

            parameters['username'] = self.call.lineEdit.text()
            parameters['password'] = self.call.lineEdit_2.text()
            parameters['positionList'] = (self.call.lineEdit_4.text()).split(',')
            parameters['locationList'] = (self.call.lineEdit_5.text()).split(',')
            parameters['max_jobs_to_apply'] = int(self.call.horizontalSlider.value()) -1

            parameters['firstName'] = self.call.lineEdit_6.text()
            parameters['lastName'] = self.call.lineEdit_8.text()
            parameters['midName'] = self.call.lineEdit_7.text()
            parameters['gender'] = self.call.lineEdit_12.text()
            parameters['phone'] = self.call.lineEdit_9.text()
            parameters['country'] = self.call.lineEdit_10.text()
            
            output_filename = 'output.csv'
            parameters['oFile'] = output_filename
            parameters['blacklist']= []
            parameters['uploads']= {}
            jobLinks = self.call.plainTextEdit.toPlainText()
            if jobLinks:
                parameters['jobLinks'] = (self.call.plainTextEdit.toPlainText()).split(',')
            else:
                parameters['jobLinks'] =[]
            
            _thread.start_new_thread( self.easyApplyBot, (parameters,) )
            # bot = self.easyApplyBot(parameters)

        def disableSubmitBtn(self):
            self.call.pushButton.setEnabled(False)
            self.call.pauseButton.setEnabled(True)
            self.call.resumeButton.setEnabled(False)
            self.updateJobRunConfig(True)
            self.call.logTextBox.append(f"User Pressed Submit Button.\n\
            Submit Button Disabled until Job is running.\
            Status of JobRunConfig: True\n\
            Pause Button State: Enabled\n\
            Resume Button State: Disabled\n")

        def enableSubmitBtn(self):
            self.call.pushButton.setEnabled(True)
            self.call.pauseButton.setEnabled(False)
            self.call.resumeButton.setEnabled(False)
            self.updateJobRunConfig(True)
            self.call.logTextBox.append(f"Job Finished. \n\
            Submit Button is Enabled.\n\
            Status of JobRunConfig: True\n\
            Pause Button State: Disabled\n\
            Resume Button State: Disabled\n")

        def enblPauseBtn(self):
            self.call.pauseButton.setEnabled(False)
            self.call.resumeButton.setEnabled(True)
            self.updateJobRunConfig(False)
            self.call.logTextBox.append(f"User Pressed Paused Button.\n\
            Pause Button is Disabled until *Resume* Button is not enabled.\
            Status of JobRunConfig: False\n")

        def enblResumeBtn(self):
            self.call.resumeButton.setEnabled(False)
            self.call.pauseButton.setEnabled(True)
            self.updateJobRunConfig(True)
            self.call.logTextBox.append(f"User Pressed Resume Button.\n\
            Pause Button is Enabled.\n\
            Resume Button is Disabled.\n\
            Status of JobRunConfig: True\n")

        def number_changed(self):
            new_value = self.call.horizontalSlider.value()
            self.call.progressBar.setValue(new_value)

        def updateJobRunConfig(self,u_status):
            # u_status False ----> Pause the bot
            # u_status True ----> Resume the bot
            jd={}
            logging.warning(f"Client Changed Bot State To:{u_status}")
            with open('threadConfig.json','w') as tcnf:
                if u_status:
                    jd['run'] = True
                    json.dump(jd,tcnf)
                    tcnf.close()
                else:
                    jd['run'] = False
                    json.dump(jd,tcnf)
                    tcnf.close()

    startBot()