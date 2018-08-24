import React from "react";
import { render } from "react-dom";
import BreadCrumbTrail from "./breadCrumbTrail";
import Menus from "./menus"; 
import Main from "./main";

import { constants } from './reportConstants.js';

// ------------------------- PRE ------------------------------ //

//for counters
var i = 0;

function efficientSort(array) {
  var len = array.length;
  if(len < 2) { 
    return array;
  }
  var pivot = Math.ceil(len/2);
  return merge(efficientSort(array.slice(0,pivot)), efficientSort(array.slice(pivot)));
};

function merge(left, right) {
  var result = [];
  while((left.length > 0) && (right.length > 0)) {
    if(left[0].workingDays > right[0].workingDays) {
      result.push(left.shift());
    }
    else {
      result.push(right.shift());
    }
  }

  result = result.concat(left, right);
  return result;
};

// ------------------------- PRE ------------------------------ //

class Root extends React.Component {
  constructor(props) {
    super(props);
    this.obj = {};
    this.obj["newData"] = {};
    this.obj["dataRendered"] = false;
    this.throughputData = [];
    this.leadTimeData = [];
    this.currentChart = [];
    this.menuOpened = false;

    this.state = {
      renderIsReady: false
    }

    this.loadScripts = this.loadScripts.bind(this);
    this.gatherInitialInformation = this.gatherInitialInformation.bind(this);
    this.slideToggle = this.slideToggle.bind(this);
    this.reloadData = this.reloadData.bind(this);
    this.downloadData = this.downloadData.bind(this);
    this.downloadableData = this.downloadableData.bind(this);
    this.updateChartView = this.updateChartView.bind(this);
  }

  loadScripts(){
    var reference = this;
    var url = "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.12.4/js/bootstrap-select.min.js";
    window.$.getScript(url).done(function( script, textStatus ) {
      let promise = new Promise(function(resolve, reject){
          reference.gatherInitialInformation();
          resolve(true);      
      })
      promise.then(function(response){
        console.log(textStatus)
        if(textStatus == "success")
          reference.setState({renderIsReady: true});
      })      
    })
  }

  slideToggle(){
    window.$('.mainNavDropDown').slideToggle(500);
    var body = window.$("body");
    if(this.menuOpened == false){
      body.addClass("hamburgerOpened")
      this.menuOpened = true;
    }
    else{
      body.removeClass("hamburgerOpened");
      this.menuOpened = false
    }
  }

  gatherInitialInformation(){
    //get paramaters of project from sessionStorage and update URL
    var currURL = window.location.href;
    var objURL = currURL;

    try{
      objURL = objURL.split("?");
      this.obj['baseURL'] = objURL[0];
      //if session storage is empty and current URL does not contain any parameters, give error
      if(objURL.length === 1){
        window.alert("This session contains no information that can be used to draw reports. Please close this tab and open quarterly reports from a VGer project page or click 'OK' to be redirected to VGer's team page", "");
        window.location.replace(this.obj['baseURL'].split("reports")+"#!/team");
      }
      else{
        var queryStr = objURL[1].split("&");
        var tempIndex = "";
        for(i=0; i<queryStr.length;i++){
          tempIndex = queryStr[i].split("=");
          this.obj[tempIndex[0]] = tempIndex[1];
        }
        this.obj.dataRendered = true;
      }
    } 
    catch(error) {
      console.log('ignore next error');
      console.log(error)}
  }

  reloadData(data){
    this.obj["newData"] = data;
    this.child.chainFunctionCalls();
  }

  downloadData(){
    var csvContent = "data:text/csv;charset=utf-8,";
    //since first set of data is throughput, have title this
    if(this.currentChart == "throughput"){
      csvContent += "Quarterly throughput Raw Data, , Likeliness \r\n";
      csvContent += "Date, Actual, ,50%, 80%, 90%  \r\n";
      for(i = 0; i < this.throughputData.length; i++){
        var date = String(this.throughputData[i][0]).split("00:00:00")[0];
        var info = this.throughputData[i].splice(1,this.throughputData.length+1);
        info = info.join(",");
        csvContent += date + "," + info + "\r\n";
      }; 
    }
    else if(this.currentChart == "leadtime"){
      csvContent += "Leadtime Raw Data \r\n";
      csvContent += "Closed Date, Name, Number of Working Days  \r\n";
      //sort leadtime by number of working days first
      var newArr = efficientSort(this.leadTimeData);
      this.leadTimeData = newArr;

      for(i = 0; i < this.leadTimeData.length; i++){
        var date = String(new Date(this.leadTimeData[i].endTime * 1000)).substring(0,15);
        var row = "";
        var reference = this;
        Object.keys(this.leadTimeData[i]).map(function(key){
          if(key === "endTime"){}
          else if(key === "workingDays"){
            //without doing this formatting, a number like 1.345 would round to 1.34 instead of 1.35
            row += Number(Math.round(reference.leadTimeData[i][key]+'e2')+'e-2').toFixed(2) + "," ;          
          }
          else{
            row += reference.leadTimeData[i][key] + "," ;
          }
        })
        csvContent += date + "," + row + "\r\n";     
      }
    }
    var encodedUri = encodeURI(csvContent);
  
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", decodeURIComponent(this.obj.projectName)+".csv");
    link.innerHTML= "Click Here to Download";
    document.body.appendChild(link); // Required for FF

    link.click(); // This will download the data file
    //after download completes (use set interval timer), remove child
    setTimeout(function(){ document.body.removeChild(link); }, 5000);
  }

  downloadableData(type, data){
    if(type === "throughput")
      this.throughputData = data;

    else if(type === "leadtime")
      this.leadTimeData = data;
  }

  updateChartView(type){
    if(type === "throughput")
      this.currentChart = "throughput";
    else if(type === "leadtime")
      this.currentChart = "leadtime";
  }

  componentDidMount(){
    this.loadScripts();
  }

  render() {
    if(this.state.renderIsReady){
      return (
        <div>
         <div className="hamburgerOpenedModal" onClick={this.slideToggle}>
         </div>
          <nav className="navbar navbar-inverse navigation" style={{marginBottom: "0px", border: "none", background: "#62757f", fontWeight: "400"}}>
            <div className="container-fluid">
                <div collapse="navCollapsed" className="collapse navbar-collapse" aria-expanded="true">
                  <BreadCrumbTrail names={this.obj} />

                    <ul className="nav navbar-right" style={{paddingTop: "4px"}}>
                       <div className = "mainNav clearfix list-inline" style={{marginLeft: "185px"}}> 
                          <p className = "navicon noSelect" onClick={this.slideToggle}>☰</p>
                       </div>
                       <ul className = "mainNavDropDown clearfix overlay" onClick={this.slideToggle}>
                         <li><a id="VGer-Link" target="_blank" rel="noopener noreferrer" href={this.obj['baseURL'].split("reports")+"#!/team"}>VGer</a></li>
                         <li><a id="JIRA-Link" target="_blank" rel="noopener noreferrer" href={constants.JIRA_BOARD_URL+this.obj["boardID"]}>View Board in JIRA </a></li>
                       </ul>
                    </ul>
                  </div>
              </div>
          </nav>

          <nav className="navbar navbar-inverse" style={{marginBottom: "0px", border: "none", background: "#bfd4df"}}>
              <div className="container-fluid text-padding">
                  <div collapse="navCollapsed" className="collapse navbar-collapse" aria-expanded="true" style={{paddingRight: "0px !important", marginTop: "3px"}}>
                    <Menus data={this.obj} onSubmit={this.reloadData} onDownload={this.downloadData}/>
                  </div>
              </div>
          </nav>

          <Main data={this.obj} newDataPush={this.downloadableData} currentChartView={this.updateChartView} ref={instance => { this.child = instance; }} style={{width: '100%', height: '100%'}}/>   
            <div className="loadingModal">
              <span className="loadingText">Loading....</span>
            </div>
        </div>
      );
    }
    else{
      var isLoaded = false;
      return (
        <div>
          <Menus data={this.obj}/>
          <Main data={isLoaded} style={{width: '100%', height: '100%'}}/>   
        </div>
      )
    }

  }

}

render(<Root />, document.getElementById("root"));