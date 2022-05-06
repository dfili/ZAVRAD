import React, { Component } from "react";
import { gantt } from "dhtmlx-gantt";
import "dhtmlx-gantt/codebase/dhtmlxgantt.css";
import Dialog from "@material-ui/core/Dialog";
import DialogContentText from "@material-ui/core/DialogContentText";
import DialogTitle from "@material-ui/core/DialogTitle";
import DialogActions from "@material-ui/core/DialogActions";
import DialogContent from "@material-ui/core/DialogContent";
import Button from "@material-ui/core/Button";

export default class Export extends Component {
  render() {

    const handleClickToOpen = () => {
      this.setOpen(true);
    };

    const handleToClose = () => {
      this.setOpen(false);
    };
    var options = [
      {
        value: "PNG",
        label: "PNG",
        type: "button",
        // onClick: function () {
        //   gantt.exportToPNG({ raw: true });,
        onClick: () => gantt.exportToPNG({ raw: true }),
      },
      {
        value: "PDF",
        label: "PDF",
        type: "button",
        onClick: function () {
          gantt.exportToPDF({ raw: true });
        },
      },
      {
        value: "Excel",
        label: "Excel",
        type: "button",
        onClick: function () {
          gantt.exportToExcel({ raw: true });
        },
      },
      {
        value: "iCal",
        label: "iCal",
        type: "button",
        onClick: function () {
          gantt.exportToICal({ raw: true });
        },
      },
      {
        value: "JSON",
        label: "JSON",
        type: "button",
        onClick: function () {
          gantt.exportToJSON({ raw: true });
        },
      },
    ];
    return (
      <div>
        <Button
            className="button-left"
            variant="contained"
            onClick={handleClickToOpen}
          >
            Export as
          </Button>
        <Dialog open={this.open} onClose={handleToClose}>
          <DialogTitle>{"How are you?"}</DialogTitle>
          <DialogContent>
            <DialogContentText>
              I am Good, Hope the same for you!
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleToClose} color="primary" autoFocus>
              Close
            </Button>
          </DialogActions>
        </Dialog>
      </div>
    );
  }
}
