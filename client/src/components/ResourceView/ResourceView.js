import React, { Component} from "react";
import "./ResourceView.css"

export default class ResourceView extends Component {

  constructor(props){
    super(props);
    this.handleResourceUpdated = this.props.handleResourceUpdated.bind(this);
  }

  shouldComponentUpdate(nextProps, nextState) {
    if (nextProps.resourceShouldUpdate === true) {
      // TODO treba li mi handler i za ovo?
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
        {this.props.effects.map(eff => <div className="resource_container" key={eff.effect_id}>
          <div className="resource_container_name" >{eff.effect}</div>
          <div className="resource_container_time" >Date acquired: {eff.date_acquired}</div>
          <div className="resource_container_parent" >Acquired from: {eff.task_name}</div>
          </div>)}
      </div>
    );
  }
}
