import React from 'react';

var i = 0;

class Menus extends React.Component {
  constructor() {
    super();
    this.dataset = [];
    this.selectedData = [];
    this.workTypeItems = [];
    this.pageRendered = false;

    this.submitData = this.submitData.bind(this);
    this.createWorkTypeSelectedItems = this.createWorkTypeSelectedItems.bind(this);
  }

  submitData() {
    var workTypes = window.$('#worktypesSelect').val();
    var numOfQuarters = window.$('#quartersSelect').val();
    var data = {'workTypes': workTypes, 'quarters': numOfQuarters};
    this.props.onSubmit(data);
  }

  // helper function for menus that should only be called once, so it is called in root and the component info is passed as props
  createWorkTypeSelectedItems() {
    if((this.props.data.dataRendered == true || Object.keys(this.props.data.newData).length != 0) && !this.pageRendered){
      this.pageRendered = true;
      console.log(this.props.data)
      //create option strings for each work type separated by comma
      this.dataset = this.props.data.workTypes.split(",");
      this.props.data.selectedWorkTypes = this.props.data.selectedWorkTypes.split(",");

      var selected = [];
      for(i=0; i<this.props.data.selectedWorkTypes.length;i++)
        selected[i] = decodeURIComponent(this.props.data.selectedWorkTypes[i]);

      let items = [];
      for(i=0; i<this.dataset.length;i++){
        this.dataset[i] = decodeURIComponent(this.dataset[i]);
        items.push(<option key={this.dataset[i]} value={this.dataset[i]}>{this.dataset[i]}</option>);   
      }
      this.workTypeItems = items;
      this.selectedData = selected;
      this.forceUpdate()
    }
  }

  render() {
    this.createWorkTypeSelectedItems();

    //force selectpicker to refresh since new information is populated in it
    try{
      window.$('#worktypesSelect').selectpicker('render');
      window.$('#worktypesSelect').selectpicker('refresh');
      window.$('#quartersSelect').selectpicker('refresh');
    }
    catch(error){
      console.log("selectpicker error / ignore")
    }      

    return (
        <div className="menuStyles">
              <select    
                className="selectpicker bs-select inlineMenu"
                id="quartersSelect"
                data-width="fit"
              >
                <option value="4">Last 4 Quarters</option>
                <option value="6">Last 6 Quarters</option>
                <option value="8">Last 8 Quarters</option>
              </select> 

             <div className="inlineMenu-next">Work Types: </div> 
             <select
                className="selectpicker bs-select inlineMenu"
                id="worktypesSelect"
                data-actions-box="true"
                defaultValue = {this.selectedData}
                data-select-all-text = "All"
                data-deselect-all-text = "None"
                multiple data-selected-text-format="count"
                data-width="fit"
              >
              {this.workTypeItems}
              </select>
              
              <button className="button" onClick={this.submitData}> Submit </button>
              <div className="downloadButton">
                <button className="button2" onClick={this.props.onDownload}><span>Download </span></button>
              </div>
        </div>
      )
    }    
  };

export default Menus;