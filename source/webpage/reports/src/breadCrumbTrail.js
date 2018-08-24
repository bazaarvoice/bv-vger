import React from 'react';

export default ({ names }) => 
      <div>
        <ul className="nav navbar-nav text-padding" style={{paddingLeft: "0px"}}> 
        <div style={{display: "inline-block"}}> Quarterly Reports </div> 
        <div style={{display: "inline-block", fontSize: "10px", marginLeft: "5px", marginRight: "5px"}}> ▶ </div> 
        <div style={{display: "inline-block"}}> {decodeURIComponent(names.teamName)} </div>
        <div style={{display: "inline-block", fontSize: "10px", marginLeft: "5px", marginRight: "5px"}}> ▶ </div>   
        <div style={{display: "inline-block"}}> {decodeURIComponent(names.projectName)} </div>
        </ul>
        <ul className="nav navbar-nav"  style={{borderLeft: "1px solid #B0BEC5", marginLeft: "10px"}}>
        </ul>
      </div>