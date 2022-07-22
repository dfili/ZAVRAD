import React, { Component } from "react";
<<<<<<< HEAD

export default class Gantt extends Component {
  constructor(props) {
    super(props);

   // this.configSetup();

    this.state = {
      
    };
  }

  render() {
    return <div>

    </div>;
=======
import AcquiredResource from '../AcquiredResource/AcquiredResource.js';

export default class ResourceView extends Component {
  constructor(props) {
    super(props);

    // this.configSetup();

    this.state = {};
  }
  // resource, resource type, date acquired
  render() {
    return (
      <div>
        <AcquiredResource></AcquiredResource>
      </div>
    );
>>>>>>> c5d3b557 (dockerfileovi i yml redone)
  }
}
