import React, { Component, useEffect, useState } from "react";

export default class ResourceView extends Component {

  constructor(props){
    super(props);
    this.onNewResources = this.props.onNewResources.bind(this)
    
}
  componentDidMount(){
    if (this.onNewResources){9
    this.onNewResources()}
  }

  shouldComponentUpdate(nextProps, nextState) {
    if (this.props.effects === nextProps.effects) {
      return false;
    }
  }

  componentDidUpdate(prevProps, prevState){
    if (prevProps.effects !== this.props.effects) {
      console.log('Effects state has changed.')
    }  
  }

  // resource, resource type, date acquired
  render() {
    console.log("Resources: ", this.props.effects);
    return (
      <div>
        {this.props.effects}
      </div>
    );
  }
}
