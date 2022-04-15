import React, { Component } from "react";
import { gantt } from 'dhtmlx-gantt';
import "dhtmlx-gantt/codebase/dhtmlxgantt.css";

export default class Export extends Component {
  render() {
    console.log("Export dialog rendered");
    return (
      <div
        className="modal fade"
        id="my-export-form"
        tabIndex="-1"
        role="dialog"
        aria-labelledby="exampleModalLabel"
        aria-hidden="true"
      >
        <div className="modal-dialog modal-dialog-centered" role="document">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="exampleModalLabel">
                Export as:
              </h5>
            </div>
            <div className="modal-body">
                <button className="button-right" onClick={() => gantt.exportToPNG({raw:true})}>PNG</button>
                <button className="button-right" onClick={() => gantt.exportToPDF({raw:true})}>PDF</button>
                <button className="button-right" onClick={() => gantt.exportToExcel({raw:true})}>Excel</button>
                <button className="button-right" onClick={() => gantt.exportToICal({raw:true})}>iCal</button>
                <button className="button-right" onClick={() => gantt.exportToJSON({raw:true})}>JSON</button>   
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                name="close"
                value="Close"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
