import React, { Component } from "react";
import { post } from "axios";
import Button from "@material-ui/core/Button";
import Export from "../ExportDialog/Export";

export default class Toolbar extends Component {
  handleZoomChange = (e) => {
    if (this.props.onZoomChange) {
      this.props.onZoomChange(e.target.value);
    }
  };

  // za dohvacanje svih dostupnih akcija
  importExistingGanttActions() {
    debugger;
    if (this.props.onGetActions) {
      this.props.onGetActions(); // prop u app.js za hvatanje svih dostupnih akcija
    }
  }

  calculatePlan() {
    console.log("Will trigger props method for plan calculation.");
    if (this.props.onCalculatePlan) {
      this.props.onCalculatePlan();
    }
  }

  clearPlan() {
    console.log("Will clear current plan.");
    if (this.props.onClearPlan) {
      this.props.onClearPlan();
    }
  }

  // za importanje akcija
  handleFileChange = async (e) => {
    console.log("Handling file change");
    var fileChanged = await this.onChangeFile(e);
    console.log("Promise returned: ", fileChanged);
    if (fileChanged) {
      console.log("File changed!");
      this.importExistingGanttActions();
    }
  };
  // za importanje projekta
  handleProjectFileChange = async (e) => {
    console.log("Importing existing project.");
    var projectImported = await this.onProjectImport(e).catch(err => console.log(err));
    console.log("Promise returned: ", projectImported);
    if (projectImported) {
      if (this.props.onProjectImport) {
        this.props.onProjectImport();
      }
    }
  };
  // za import akcija 
  async onChangeFile(event) {
    return new Promise((resolve, reject) => {
      var file = event.target.files[0];
      console.log(file);
      if (file === "undefined") {
        resolve(false);
      }
      var reader = new FileReader();

      reader.onload = (e) => {
        var loaded_data = JSON.parse(e.target.result);
        console.log("Loaded data, should import actions now.");
        console.log(loaded_data);
        // send loaded data to server to save in database
        const url = "http://localhost:8080/actions/import";
        const formData = { data: loaded_data };
        var postResult = post(url, formData).then(response => {resolve(true)});
        console.log(postResult.data);
      };
      reader.readAsText(file);
    });
  }

  async onProjectImport(event) {
    return new Promise((resolve, reject) => {
      var file = event.target.files[0];
      if (file === "undefined") {
        resolve(false);
      }
      var reader = new FileReader();

      // 4 mirko računala vdx
      // 4 24gu...
      // laptop za bazu cva
      reader.onload = (e) => {
        var loaded_data = JSON.parse(e.target.result);
        console.log(loaded_data);
        console.log("Loaded data, should import project now.");
        // send loaded data to server to save in database
        const config = {
          headers:{
            "Content-type": "application/json"
          }
        }
        const url = "http://localhost:8080/gantt/import";
        const formData = { "data": loaded_data };
        console.log("formdata is " + formData);
        var postResult = post(url, formData, config).then((response) => resolve(true));
        console.log(postResult.data);
      };
      reader.readAsText(file);
    });
  }
  // async onClearPlan(event) {}
  render() {
    const zoomRadios = ["Hours", "Days", "Months"].map((value) => {
      const isActive = this.props.zoom === value;
      return (
        <label
          key={value}
          className={`radio-label ${isActive ? "radio-label-active" : ""}`}
        >
          <input
            type="radio"
            checked={isActive}
            onChange={this.handleZoomChange}
            value={value}
          />
          {value}
        </label>
      );
    });

    return (
      <div>
        <div>
          <b>Zooming: </b>
          {zoomRadios}
        </div>
        <div>
          <Button
            className="button-left"
            variant="contained"
            onClick={() => this.calculatePlan()}
          >
            Calculate plan
          </Button>
          <Button
            className="button-left"
            variant="contained"
            onClick={() => this.clearPlan()}
          >
            Close
          </Button>
          <input
            id="myInput"
            type="file"
            ref={(ref) => (this.uploadActions = ref)}
            style={{ display: "none" }}
            onChange={this.handleFileChange.bind(this)} // tf je onChange
          />
          <Button
            className="button-left"
            variant="contained"
            onClick={() => {
              this.uploadActions.click();
            }}
          >
            Import actions
          </Button>
          <input
            id="myInputPlan"
            type="file"
            ref={(ref) => (this.uploadProject = ref)}
            style={{ display: "none" }}
            onChange={this.handleProjectFileChange.bind(this)}
          />
          <Button
            className="button-left"
            variant="contained"
            onClick={() => {
              this.uploadProject.click();
            }}
          >
            Import project
          </Button>

          <Export />
        </div>
      </div>
    );
  }
}
