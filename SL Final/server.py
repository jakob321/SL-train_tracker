from flask import Flask, request, render_template, redirect, url_for
import requests
import json
import bs4
from bs4 import BeautifulSoup
import copy

class sl:
    #urlinfo = "http://api.sl.se/api2/realtimedeparturesV4.<FORMAT>?key=<DIN API NYCKEL>&siteid=<SITEID>&timewindow=<TIMEWINDOW>"
    #urlplatts = "https://api.sl.se/api2/typeahead.<FORMAT>?key=<DIN NYCKEL>&searchstring=<SÖKORD>&stationsonly=<ENDAST STATIONER>&maxresults=<MAX ANTAL SVAR>"

    def __init__(self, term): 
        self.term = term
        self.keyRealtidsinformation = "b3c5d43e054f4fa4a94453bacaaddd74"
        self.keyPlattsuppslag = "d518048fb82b4ada9e08acf2be482285"
        self.timeframe = 60

        self.getData()

    def siteID(self, key, term):
        #Getting siteId
        urlPlattsuppslag = "https://api.sl.se/api2/typeahead.json?key="+key+"&searchstring="+term+"&stationsonly=true"
        plattsuppslag = (requests.get(urlPlattsuppslag)).json()
        return plattsuppslag["ResponseData"][0]["SiteId"]


    def Realtidsinformation(self, siteid):
        #Getting the data
        urlRealtidsinformation = "http://api.sl.se/api2/realtimedeparturesV4.json?key="+self.keyRealtidsinformation+"&siteid="+str(siteid)+"&timewindow=:60"+str(self.timeframe)+"METRO=false"
        return (requests.get(urlRealtidsinformation)).json()

    def getData(self):
        return self.Realtidsinformation(self.siteID(self.keyPlattsuppslag, self.term))

class responsePage:
    
    def __init__(self, inputList):
        self.inputList = inputList
        self.outputList = []
        self.stationName = ''
        self.lineImgList = {'tunnelbanans gröna linje':"""{{ url_for('static', filename='images/greenLine.png')}}""", 
        'tunnelbanans röda linje':"""{{ url_for('static', filename='images/redLine.png')}}""", 
        'tunnelbanans blå linje':"""{{ url_for('static', filename='images/blueLine.png')}}"""}

        # Getting the important part of the recived info into a list
        self.filterInfo()
        # Bulding a new HTML page with the information
        self.addRows()

    def filterInfo(self):
        for trains in self.inputList["ResponseData"]["Metros"]:

            # Remowing the date from the time
            tabledTime = str(trains['TimeTabledDateTime']).split('T')[1]
            expectedTime = str(trains['ExpectedDateTime']).split('T')[1]
  
            # Mayby should set it to key-value pairs for ease of reading...
            self.outputList.append([trains['Destination'], trains['GroupOfLine'], tabledTime, expectedTime, trains["JourneyDirection"]])

    def addRows(self):
        # load the template main file
        with open("templates/response.html") as inf:
            txt = inf.read()
            response = bs4.BeautifulSoup(txt)

        # Loads the template for the displayed train
        with open("templates/responseTemplate.html") as inf:
            txt = inf.read()
            responseTemplate = bs4.BeautifulSoup(txt)


        # Sends all the data for all directions and lets the client change visability to therefore limit server calls
        already_assigned_directions = {}
        allContentStr = ""
        for i in range(0, len(self.outputList)):
            # creates a copy of the template so the template is not edited
            template = copy.copy(responseTemplate)
        
            found_direction = False
            # Assigns every direction on every line a number for later easy sorting
            # Checks if that directions and line already have an assinged number, else assign a new number for that route
            for direction in already_assigned_directions:
                if self.outputList[i][1] + str(self.outputList[i][4]) == direction:
                    template.find('div')['id'] = 'direction'+str(already_assigned_directions[direction])
                    found_direction = True
            if found_direction == False:
                line = self.outputList[i][1] + str(self.outputList[i][4])
                listLength = str(len(already_assigned_directions))
                already_assigned_directions[line] = listLength
                template.find('div')['id'] = 'direction'+listLength

            

            template.find('img', class_='lineImg')['src'] = self.lineImgList[self.outputList[i][1]]
            template.find('h2', class_='time').append(self.outputList[i][2])
            template.find('h2', class_='destination').append(self.outputList[i][0])


            # edeting out the html and body tags
            newContent = template.find('div', class_='contentContainer')

            # Converts the bs objects to string to combine them
            allContentStr = allContentStr + str(newContent)

            # cenverts them back to bs object
            allContent = BeautifulSoup(allContentStr)


        # This station header text
        self.stationName = self.inputList["ResponseData"]["Metros"][0]["StopAreaName"]
        response.find("h1", class_='thisStation').append(self.stationName)
        # Adds the content to the "responce" page
        response.find('div', class_='content').append(allContent)

        # saves the edited responce page ready to be sent to the client.
        pageName = 'output.html'
        address = 'templates/' + pageName
        outputPage = open(address, 'w', encoding='utf-8')
        responseString = str(response)
        outputPage.write(responseString)
        outputPage.close()

    def returnStationName(self):
        return self.stationName




app = Flask(__name__)


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        # The user input in string format ex. Tallkrogen
        content = str(request.form['content'])

        # Contacts the SL API with the term and outputs the recieved data
        slData = sl(content).getData()

        # With the recieved data a new HTML page is built. The station name is returned to use in the address to the new page
        stationName = responsePage(slData).returnStationName()
        
        # redirect to the new page (few lines down)
        return redirect("/trips/"+stationName)     
         
    else:
        # First time the page is loaded
        return render_template("index.html")

@app.route("/trips/<station>")
def trips(station):
    return render_template('output.html')


if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='192.168.1.140', port=9000, debug=True)