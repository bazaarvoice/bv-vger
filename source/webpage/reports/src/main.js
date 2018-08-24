import React from 'react';
import { Chart } from 'react-google-charts';

import { constants } from './reportConstants.js';

var i = 0;
var j = 0;
var k = 0;
var rawScatterChartData = [];
var rawThroughputData = [];

function openIssueInJIRA(Chart, point){
  var issueID = rawScatterChartData[point].name;
  var url = constants.JIRAURL + "browse/" + issueID;
  window.open(url, '_blank');
}

class Main extends React.Component {
  constructor() {
    super();
  
    this.chartEvents = [
      {
        eventName: 'select',
        callback(Chart) {
          // Returns Chart so you can access props and the ChartWrapper object from chart.wrapper
          var selected = Chart.chart.getSelection()[0]['row'];
          openIssueInJIRA(Chart, selected)
        },
      },
    ];
    
    //the most recent quarter to end based on QUARTERDATESORGANIZED
    this.mostRecentQuarterIndex = -1;
    this.numOfQuarters = 4;
    this.apiGatewayType = "";
    this.firstPageEntry = true;
    this.dates = [];
    this.noLeadTimeDataPresent = false;

    this.state = {
      //the data structure containing x (equal to maxAmountOfQuarters) amount of quarters with the correct year from the most recent quater end
      quarterEnddatesArray: [],

      //the max amount of quarters to store (greater than 8 in order to pass start of earliest quarter into API endpoint)
      maxAmountOfQuarters: 10,

      todaysDate: new Date(),
      
      //throughput data (initially fake data to ensure that containers are built due to render function being called before chart info grabbed)
      throughputRows:[
          ["initial data",  1000, null, 900, 700, 500],
      ],
      
      //leadtime data (initially fake data to ensure that containers are built due to render function being called before chart info grabbed)
      leadtimeRows:[
          [new Date("2001,01,09"),  32, "initial point"],
      ],
    };

    this.setQuarterEndDates = this.setQuarterEndDates.bind(this);
    this.getThroughputQuarterlyHistory = this.getThroughputQuarterlyHistory.bind(this);
    this.buildThroughputChartData = this.buildThroughputChartData.bind(this);
    this.getLeadTimeHistory = this.getLeadTimeHistory.bind(this);
    this.buildScatterChartData = this.buildScatterChartData.bind(this);
    this.chainFunctionCalls = this.chainFunctionCalls.bind(this);
    this.showChart = this.showChart.bind(this);
    this.toggleFullScreen = this.toggleFullScreen.bind(this);
    this.loading = this.loading.bind(this);
    this.noLeadTimeData = this.noLeadTimeData.bind(this);
  }

  //determine all the quarter year end dates
  setQuarterEndDates(){
    var reference = this;

    return new Promise(function(){
      //determine which quarter currently in
      //using only month and day offsets all dates to 2001 for checking closest quarter
      var todayDateToString = reference.state.todaysDate.getMonth()+1 + "/" + reference.state.todaysDate.getDate();
      var todaysDateToMS = new Date(todayDateToString).getTime();
      
      //differentiate between one of the 4 quarters and unassigned (unfound)
      var closestQuarterIndex = -1; 
      
      //find most recent quarter end
      for(i=0; i<constants.QUARTERDATESORGANIZED.length; i++){
        var quarterDateToMS = new Date(constants.QUARTERDATESORGANIZED[i]);
        quarterDateToMS = quarterDateToMS.getTime();

        var thisQuarterDifference = todaysDateToMS - quarterDateToMS;
        if(thisQuarterDifference < 0){
          closestQuarterIndex = i-1;
          break;
        }
      }
      reference.mostRecentQuarterIndex = closestQuarterIndex;

      //using most recent quarter, set first amount of quarters up to and including this quarter equal to current year
      var currYear = reference.state.todaysDate.getFullYear();
      for(var j = reference.mostRecentQuarterIndex; j > -1; j--){
        reference.state.quarterEnddatesArray.push(constants.QUARTERDATESORGANIZED[j]+"/"+currYear);  
      }
      
      //set remaining quarters while decrementing year
      var counter = reference.state.quarterEnddatesArray.length;
      var loopCounter = 3;
      currYear = currYear - 1;
      while(counter < reference.state.maxAmountOfQuarters){
        if(loopCounter === -1){
          currYear = currYear - 1;
          loopCounter = 3;
        }
        reference.state.quarterEnddatesArray.push(constants.QUARTERDATESORGANIZED[loopCounter]+"/"+currYear)  
        counter++;
        loopCounter--;
      }
    })
  };

  getThroughputQuarterlyHistory() {
    //all parameters are passed in as props from index.js

    var projectID = this.props.data.projectId;
    var quarterEndDatesInSQLMS = [];

    for(i = 0; i < this.state.quarterEnddatesArray.length; i++)
      quarterEndDatesInSQLMS.push(Math.floor(new Date(this.state.quarterEnddatesArray[i]).getTime()/1000));

    var workTypeStr = this.props.data.selectedWorkTypes;
    var historyStr = 'quarterly/history'; 

    //find API gateway type (Prod, QA)
    if(this.props.data.baseURL.indexOf(constants.APIGATEWAYPRODURL) >= 0)
      this.apiGatewayType = constants.APIGATEWAYPROD;
    else if(this.props.data.baseURL.indexOf(constants.APIGATEWAYQAURL) >= 0)
      this.apiGatewayType = constants.APIGATEWAYQA;
    //USED FOR TESTING, if on localhost
    else if(this.props.data.baseURL.indexOf("localhost") >= 0 || this.props.data.baseURL.indexOf("127.0.0.1") >= 0)
      this.apiGatewayType = constants.APIGATEWAYQA;

    var historyAPIStr = this.apiGatewayType + 'project/' + projectID  + '/' + 'throughput/' + historyStr + '?';

    //need comma delimited string of worktypes
    if (workTypeStr !== '') historyAPIStr += '&workTypes=' + workTypeStr;

    // need to build string of quarter end dates to pass into script, attach first element so that remaining are comma separated
    // if 4 quarters, need to pass in 5 dates (from "q0 end" [aka last finished quarter before q1] to q1 end as Q1, from q1 end to q2 end as Q2, from q2 to q3 as Q3, from q3 to q4 as Q4)
    var quarterEndDatesString = "&dates=" + quarterEndDatesInSQLMS[0];
    
    for(var j = 1; j < this.numOfQuarters+1; j++)
      quarterEndDatesString += "," + quarterEndDatesInSQLMS[j];

    historyAPIStr += quarterEndDatesString;
    var fetchStr = historyAPIStr;
    return fetch(fetchStr, 
    {
      method: 'GET'
    })
      .catch((error) => {
        console.error(error);
      });
  };

  buildThroughputChartData(data) {
    //the index of the data points (the 0th index is the type of point)
    var indexOfDataPoints = 1;
    var chartData = [];
    for(i=0; i<this.numOfQuarters; i++){
      chartData.push([]);
      rawThroughputData.push([]);
    }

    if(data != null){
      var numOfActiveQuarters = data[0][indexOfDataPoints].length;
      for(i=0; i<data.length; i++){
        if(data[i][0] === "eightiethStraight" || data[i][0] === "ninetiethStraight")
          continue;

        //assign quarter end date to 0th index of chart data in first loop but not anytime else (since it doesnt change for other data point assignments)
        if(i === 0){
          // organize constant into arrangable amount of quarters
          var Q1Date, Q2Date, Q3Date, Q4Date = "";
          //since there is 4 quarters in a fiscal year
          for(j=0;j<4;j++){
            if(constants.DATETOQUARTER[j].quarter == "Q1"){
              Q1Date = constants.DATETOQUARTER[j].date
              continue;
            }
            else if(constants.DATETOQUARTER[j].quarter == "Q2"){
              Q2Date = constants.DATETOQUARTER[j].date
              continue;
            }
            else if(constants.DATETOQUARTER[j].quarter == "Q3"){
              Q3Date = constants.DATETOQUARTER[j].date
              continue;
            }
            else if(constants.DATETOQUARTER[j].quarter == "Q4"){
              Q4Date = constants.DATETOQUARTER[j].date
              continue;
            }
          }

          //clear previous date ticks to add new ones to graph
          //add 1 more date so that haxis ticks shows 4 active regions instead of 3 (when choosing last 4 quarters)       
          this.dates = [];
          for(j=0; j<numOfActiveQuarters+1; j++){
            //build full string to use for date ex. 7/31/2017 \n FY18 Q1
            //[{v:32, f:'thirty two'}, {v:64, f:'sixty four'}]
            var date = this.state.quarterEnddatesArray[j];
            var dateString = "" 
            if(date.indexOf(Q1Date)>=0)
              dateString = date + "\n FY" + String(parseInt(date.slice(-2), 10)+1) + " Q1"  
            else if(date.indexOf(Q2Date)>=0)
              dateString = date + "\n FY" + String(parseInt(date.slice(-2), 10)+1) + " Q2"  
            else if(date.indexOf(Q3Date)>=0)
              dateString = date + "\n FY" + date.slice(-2) + " Q3"  
            else if(date.indexOf(Q4Date)>=0)
              dateString = date + "\n FY" + date.slice(-2) + " Q4"  

            var customTickObj = {v:new Date(date), f:dateString};
            this.dates.push(customTickObj);

            //do not add last tick to data since it is just a tick  
            if( j!=numOfActiveQuarters ){
              rawThroughputData[j][0] = date            
              chartData[j][0] = dateString;
            }
          }
          //flip chart data since dates are stored reverse chronologically (latest date is smallest index)   
          chartData.reverse();
          rawThroughputData.reverse();
        }

        if(data[i][0] === "actualData"){
          //data is recieved chronologically (largest index point is most recent date)
          //chartData is displayed chronologically (largest index point is most recent date)
          for(j=0; j<numOfActiveQuarters; j++){
            chartData[j][1] = data[i][indexOfDataPoints][j];
            rawThroughputData[j][1] = data[i][indexOfDataPoints][j];
          }        
        }

        if(data[i][0] === "fiftiethStraight"){
          for(j=0; j<numOfActiveQuarters; j++){
            chartData[j][5] = data[i][indexOfDataPoints][j];
            rawThroughputData[j][5] = data[i][indexOfDataPoints][j];
          }   
        }

        if(data[i][0] === "twentiethStraight"){
          for(j=0; j<numOfActiveQuarters; j++){
            chartData[j][4] = data[i][indexOfDataPoints][j];
            rawThroughputData[j][4] = data[i][indexOfDataPoints][j];
          }   
        }
        
        if(data[i][0] === "tenthStraight"){
          for(j=0; j<numOfActiveQuarters; j++){
            chartData[j][3] = data[i][indexOfDataPoints][j];
            rawThroughputData[j][3] = data[i][indexOfDataPoints][j];
          }   
        }
      }
      return chartData;
    }
    else{
      //this case should never happen according to throughput script, but good to know why page isn't loading with this
      console.error("null throughput data set")
    }
  }

  getLeadTimeHistory() {
    //all parameters are passed in as props from index.js
    var projectID = this.props.data.projectId;

    var quarterEndDatesInSQLMS = [];

    for(i=0; i<(this.numOfQuarters+1); i++)
      quarterEndDatesInSQLMS.push(Math.floor(new Date(this.state.quarterEnddatesArray[i]).getTime()/1000));

    var workTypeStr = this.props.data.selectedWorkTypes;
    var historyStr = 'leadtime/quarterly'; 

    var historyAPIStr = this.apiGatewayType + 'project/' + projectID  + '/' + historyStr + '?';

    //need comma delimited string of worktypes
    if (workTypeStr !== '') historyAPIStr += '&workTypes=' + workTypeStr;

    // need to build string of quarter end dates to pass into script, attach first element so that remaining are comma separated
    // if 4 quarters, need to pass in 5 dates (from "q0 end" [aka last finished quarter before q1] to q1 end as Q1, from q1 end to q2 end as Q2, from q2 to q3 as Q3, from q3 to q4 as Q4)
    var quarterEndDatesString = "&dates=" + quarterEndDatesInSQLMS[0];
        
    for(var j = 1; j < this.numOfQuarters+1; j++)
      quarterEndDatesString += "," + quarterEndDatesInSQLMS[j];
    historyAPIStr += quarterEndDatesString;

    var fetchStr = historyAPIStr;  
    return fetch(fetchStr, 
    {
      method: 'GET'
    })
      .catch((error) => {
        console.error(error);
      });
  }

  buildScatterChartData(newData){
    //if there is no leadtime data
    if(newData.length == 0){
      this.noLeadTimeData(true);
      return newData;
    }
    else{
      var arr = newData.map(obj =>{ 
          var tooltip = "<div style='white-space: nowrap; padding: 5px'><b>"+obj.name+"</b> <br /> <span>"+ String(new Date(obj.endTime*1000)).substring(4,15) + "</span><br /> <span>" + Math.round(obj.workingDays * 100) / 100 + "  days </span></div>";
          var tempArr = [new Date(obj.endTime*1000), obj.workingDays, tooltip];
          return tempArr;
      });
      rawScatterChartData = newData;
      return arr;
    }
  }

  chainFunctionCalls(){
    //page has not fully loaded
    if(this.props.data == false){
      this.loading(true)
    }
    else{
      console.log(this.props.data.newData)
      var updatesNeeded = false;

      var newWorkTypes = this.props.data.newData.workTypes;
      if( newWorkTypes == null || newWorkTypes == undefined )
        newWorkTypes = []; 
      this.props.data.newData.quarters = parseInt(this.props.data.newData.quarters, 10) 

      //re-assign worktypes and number of quarters if either has changed and submit was clicked
      //first turn worktypes into comma separated URI encoded string
      for(i=0; i<newWorkTypes.length; i++)
        newWorkTypes[i] = encodeURIComponent(newWorkTypes[i])
      newWorkTypes = newWorkTypes.join(",")
      
      if ( newWorkTypes !== this.props.data.selectedWorkTypes && newWorkTypes !== "" && !this.firstPageEntry ){
        this.props.data.selectedWorkTypes = newWorkTypes;
        updatesNeeded = true;
      }

      if ( this.props.data.newData.quarters !== this.numOfQuarters  && this.props.data.newData.quarters !== null && !this.firstPageEntry ){
        this.numOfQuarters = this.props.data.newData.quarters;
        updatesNeeded = true;
      }

      if( updatesNeeded || this.firstPageEntry ){
        //loading modal
        this.loading(true)
        //default chart view
        this.showChart();
        var throughputQuarterlyData;
        var reference = this;
        this.setQuarterEndDates()
        .then(throughputQuarterlyData = this.getThroughputQuarterlyHistory())    
          throughputQuarterlyData.then(function(throughputResponse) {
            //asynchronously get leadtime history as throughput history is drawn
            reference.getLeadTimeHistory()
            .then(function(leadtimeResponse) {
              leadtimeResponse.json()
              .then( function(leadtimeResponseJson) {
                var newChartData = reference.buildScatterChartData(leadtimeResponseJson);
                if(newChartData.length !== 0){
                  //check if chart is hidden and unhide
                  var graph = document.getElementById("leadTimeGraphDiv");
                  if(graph.style.display == 'none')
                    graph.style.display = "";  
                  let promise = new Promise(function(resolve, reject) {
                    //set up ticks
                    constants.LEADTIMEOPTIONS.hAxis.ticks = reference.dates;
                    resolve(true);
                    reference.setState({leadtimeRows: newChartData});
                    reference.loading(false);                
                  });

                  promise.then( function(response){
                    reference.props.newDataPush("leadtime", rawScatterChartData);
                    reference.firstPageEntry = false;
                  });
                }
                else{
                  //hide scatter chart since there is no data for it
                  var graph = document.getElementById("leadTimeGraphDiv");
                  graph.style.display = 'none';
                  reference.loading(false);                  
                }
              });       
            });

            //finish building throughput at same time as starting leadtime history (now that some data has been gathered for leadtime history)
            throughputResponse.json()
            .then( function(throughputResponseJson) {
              var newChartData = reference.buildThroughputChartData(throughputResponseJson);
              
              let promise = new Promise(function(resolve, reject) {
                reference.throughputRows = newChartData;
                reference.setState({throughputRows: newChartData})
              });

              promise.then(reference.props.newDataPush("throughput", rawThroughputData));
            });
          });
      }
    }
  }

  //put full screen loading modal if screen is loading
  loading(isLoading){
    var body = window.$("body");
    if(isLoading)
      body.addClass("loading")
    else
      body.removeClass("loading");
  }

  noLeadTimeData(dataIsEmpty){
    var body = window.$("body");
    if(dataIsEmpty){
      body.addClass("noLeadTimeData");
      this.noLeadTimeDataPresent = true;
    }
    else{
      if(this.noLeadTimeDataPresent == true){
        this.noLeadTimeDataPresent = false
        body.removeClass("noLeadTimeData");
      }   
    }
  }

  //depending on chartSelect value or if first page render, display correct chart in single chart view
  showChart(){
    var selection = window.$('#chartSelect').val();
    var newSelect;

    if(selection !== null && selection !== 'default')
      newSelect = selection;
    else if(this.firstEntry === true){
      //default chart view
      newSelect = 'throughput';
    }
    else
      newSelect = 'throughput';
    
    var topElement, bottomElement;
    if(newSelect === "throughput"){
      topElement = document.getElementById("throughputGraphContainer");
      bottomElement = document.getElementById("leadTimeGraphContainer");
      //use try catch since errors are thrown from bootstrap even though bootstrap-select works
      try{
        window.$('#chartSelect').selectpicker('val', 'throughput');
      }
      catch(error){
      }
    }
    else if(newSelect === "leadtime"){
      topElement = document.getElementById("leadTimeGraphContainer");
      bottomElement = document.getElementById("throughputGraphContainer");
      //use try catch since errors are thrown from bootstrap even though bootstrap-select works
      try{   
        window.$('#chartSelect').selectpicker('val', 'leadtime');
      }
      catch(error){
      }    
    }
    topElement.style.zIndex = 100;
    bottomElement.style.zIndex = -1;
    //pass data of current view into index.js for downloading that charts data exclusively
    this.props.currentChartView(newSelect);
  }

  //toggle to a fullscreen view without the menus
  toggleFullScreen() {
    var charts = [];
    charts.push(document.getElementById("throughputGraphContainer"));
    charts.push(document.getElementById("leadTimeGraphContainer"));

    for(i=0;i<charts.length;i++){
      var currSize = charts[i].style.top;
      //if not fullscreen
      if(currSize !== "0px"){
        let promise = new Promise(function(resolve, reject) {
          charts[i].style.top = 0;
          resolve(true)
        })
        promise.then(function(response){
          setTimeout(function(){ 
            var select = document.getElementById("select");          
            select.style.position = "fixed";
            select.style.top = 0;
            select.style.left = "40%";
          }, 1);
        })
      }
      else{
        let promise = new Promise(function(resolve, reject) {
          charts[i].style.top = "";
          resolve(true)
        })
        promise.then(function(response){
          setTimeout(function(){ 
            var select = document.getElementById("select");          
            select.style.position = "";
            select.style.top = "";
            select.style.left = "";
          }, 1);
        })  
      }
    }
  }

  componentDidMount(){
    //start info gathering for charts
    this.chainFunctionCalls();
  }

  render() {
      return (
        <div className="charts">
          <div id="select" style={{position: '',top: '',left: '', zIndex: '200'}}>
          <select id="chartSelect" className="selectpicker chartTitles" data-width="auto" onChange={() => this.showChart()}>
            <option value="default" disabled className="text-padding" style={{fontSize: "16px", fontWeight: "700"}}> Please select</option>
            <option value="throughput" className="text-padding dropDownSelection">🎬 Quarterly Throughput</option>
            <option value="leadtime" className="text-padding dropDownSelection"> ⏱ Quarterly Lead Times </option>
          </select>
          </div>
          <div id="chartOverLay" style={{backgroundColor: "#FFF", zIndex:"10",position: "fixed", height:"100%", width:"100%"}}></div>
          <div id="throughputGraphContainer" style={{position: "fixed", height:"100%", width:"100%", zIndex:"5"}}>
             <div style={{position: "fixed", height:"90%", width:"100%", justifyContent: 'center'}}>
              <Chart
                chartType="LineChart"
                columns={constants.THROUGHPUTCOLUMNS}  
                rows={this.state.throughputRows}
                options={constants.THROUGHPUTOPTIONS}
                width="100%"
                height="90%"
                legend_toggle
              />
              </div>
          </div>
          <div id="leadTimeGraphContainer" style={{position: "fixed", height:"90%", width:"100%", zIndex:"4"}}>
            <div className="noLeadTimeDataModal">
              <span id="noLeadTimeDataSpan" className="noLeadTimeDataText">There are no tickets with leadtimes greater than 0 Days</span>
            </div>
            <div id="leadTimeGraphDiv" style={{position: "fixed", height:"100%", width:"100%", justifyContent: 'center'}}>
              <Chart
                chartType="ScatterChart"
                columns={constants.LEADTIMECOLUMNS}  
                rows={this.state.leadtimeRows}
                options={constants.LEADTIMEOPTIONS}
                width="100%"
                height="80%"
                chartEvents={this.chartEvents}
                legend_toggle
              />
            </div>
          </div>
        <a className="fullScreenBottom" title="Toggle FullScreen..." onClick={this.toggleFullScreen}> 👁️‍🗨️ </a>
        </div>
    );
  };
}

export default Main;