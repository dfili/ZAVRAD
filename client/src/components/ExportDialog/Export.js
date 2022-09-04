import React, { Component} from "react";
import "dhtmlx-gantt/codebase/dhtmlxgantt.css";
import Dialog from "@material-ui/core/Dialog";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogActions from "@material-ui/core/DialogActions";
import Button from "@material-ui/core/Button"; 
import { gantt } from 'dhtmlx-gantt';

export default class Export extends Component {
  constructor() {
    super();
   // this.configSetup();
    const script = document.createElement("script");
    script.async = true;
    script.src = "http://export.dhtmlx.com/gantt/api.js";
    script.id = "ganttApi";
    document.body.appendChild(script);
    document.head.appendChild(script);
    // gantt.add_export_methods();
    this.state = {
      open: false,
      options: [
        {
          value: "PNG",
          // onClick: function () {
          //   gantt.exportToPNG({ raw: true });,
          click: () => gantt.exportToPNG({raw:true, start:gantt.getState().min_date}),
        },
        {
          value: "PDF",
          click: () => gantt.exportToPDF({raw:true, start:gantt.getState().min_date})
          ,
        },
        {
          value: "Excel",
          click: () => gantt.exportToExcel()
          ,
        },
        {
          value: "iCal",
          click: () => gantt.exportToICal()
          ,
        },
        {
          value: "JSON",
          click: () => gantt.exportToJSON()
          ,
        },
      ]
    };

  }

  handleClickToOpen = () => {
    this.setState({open: true});
  };

  handleClickToClose = () => {
    this.setState({open: false});
  };
  
  exportToJSON = async () => {
    var data;
    await fetch('http://localhost:8080/gantt').then(res => res.json()).then(output => {
      data = output;
      console.log(data);
    })
    const jsonString = `data:text/json;chatset=utf-8,${encodeURIComponent(
      JSON.stringify(data)
    )}`;
    const link = document.createElement("a");
    link.href = jsonString;
    link.download = "data.json";
    link.click();
  };

  render() {
    return (
      <div>
        <Button
          className="button-left"
          variant="contained"
          onClick={this.handleClickToOpen}
        >
          Export as
        </Button>
        <Dialog open={this.state.open}> 
          <DialogTitle>{"Export as:"}</DialogTitle>
          <DialogActions>
            <div>{this.state.options.map(opt => <Button variant="contained" key={opt.value} onClick={() => opt.click()}>{opt.value}</Button>)}</div>
            <Button onClick={this.handleClickToClose}>
              Close
            </Button>            
          </DialogActions>
      </Dialog>
      </div>
    );
  }
}
