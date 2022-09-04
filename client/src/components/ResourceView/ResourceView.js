import React, { Component} from "react";

export default class ResourceView extends Component {

  constructor(props){
    super(props);
    this.handleResourceUpdated = this.props.handleResourceUpdated.bind(this);
  }

  shouldComponentUpdate(nextProps, nextState) {
    if (this.props.ResourceShouldUpdate === true) {
      if (this.handleResourceUpdated){
      this.handleResourceUpdated();}
      return true;
    }
    return false;
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
        <div>{this.props.effects.map(eff => <div name={eff.name} >{eff.name}</div>)}</div>
      </div>
    );
  }
}
