import React, { Component} from "react";
import { gantt } from "dhtmlx-gantt";
import "dhtmlx-gantt/codebase/dhtmlxgantt.css";
import Dialog from "@material-ui/core/Dialog";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import Button from "@material-ui/core/Button";

export default class Export extends Component {
  constructor() {
    super();

   // this.configSetup();

    this.state = {
      open: false,
      options: [
        {
          value: "PNG",
          // onClick: function () {
          //   gantt.exportToPNG({ raw: true });,
          click: () => gantt.exportToPNG({ raw: true }),
        },
        {
          value: "PDF",
          click: () => gantt.exportToPDF({ raw: true })
          ,
        },
        {
          value: "Excel",
          click: () => gantt.exportToExcel({ raw: true })
          ,
        },
        {
          value: "iCal",
          click: () => gantt.exportToICal({ raw: true })
          ,
        },
        {
          value: "JSON",
          click: () => gantt.exportToJSON({ raw: true })
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
          <DialogContent>
          </DialogContent>
          <DialogActions>
            <div>{this.state.options.map(opt => <Button variant="contained" key={opt.value} onClick={() => opt.click}>{opt.value}</Button>)}</div>
            <Button onClick={this.handleClickToClose}>
              Close
            </Button>            
          </DialogActions>
      </Dialog>
      </div>
    );
  }
}
