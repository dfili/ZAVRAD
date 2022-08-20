import React, { Component } from "react";
import AcquiredResource from '../AcquiredResource/AcquiredResource.js';

export default class ResourceView extends Component {
  constructor(props) {
    super(props);

    // this.configSetup();

    this.state = {};
  }
  // shouldComponentUpdate(nextProps, nextState) {
  //   console.log("NextProps: ", nextProps);
  //   var effectsUpdated = this.props.effects.length !== nextProps.effects.length;
  //   return effectsUpdated;
  // }

  getEffects = async () => {
    var data = []
    await fetch('http://localhost:8080/effects').then(res => res.json()).then(output => {
      data = output;
      console.log(data);
    })
  }
  // resource, resource type, date acquired
  render() {
    return (
      <div>
        
      </div>
    );
  }
}
