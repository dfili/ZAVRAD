import React, { Component } from "react";
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
  }
}
