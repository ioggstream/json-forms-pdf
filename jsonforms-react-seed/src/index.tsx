import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import registerServiceWorker from './registerServiceWorker';
import { combineReducers, createStore, Reducer, AnyAction } from 'redux';
// import schema from './schema.json';
// import uischema from './uischema.json';
import { Actions, jsonformsReducer, JsonFormsState } from '@jsonforms/core';
import {
  materialCells,
  materialRenderers
} from '@jsonforms/material-renderers';
import RatingControl from './RatingControl';
import ratingControlTester from './ratingControlTester';
import { devToolsEnhancer } from 'redux-devtools-extension';
import { safeLoad } from 'js-yaml';
const yaml = require("js-yaml");
const refParser = require("json-schema-ref-parser");

// Setup Redux store
const data = {
  name: 'Send email to Adrian',
  description: 'Confirm if you have passed the subject\nHereby ...',
  done: true,
  recurrence: 'Daily',
  rating: 3
};

const initState: JsonFormsState = {
  jsonforms: {
    cells: materialCells,
    renderers: materialRenderers
  }
};

const rootReducer: Reducer<JsonFormsState, AnyAction> = combineReducers({
  jsonforms: jsonformsReducer()
});
const store = createStore(rootReducer, initState, devToolsEnhancer({}));

fetch('form-1/schema.yaml')
  .then((response) => response.text())
  .then((text) => {
    const schema_ = yaml.safeLoad(text);
    refParser.dereference(schema_, (err: any, schema: any) => {
      if (err) {
        console.error(err);
        throw err;
      }
      console.log(schema);
      fetch('form-1/uischema.yaml')
        .then((response) => response.text())
        .then((text) => {
          const uischema = safeLoad(text);
          console.log(uischema);
          store.dispatch(Actions.init(data, schema, uischema));
        });
    });
  });


// Register custom renderer for the Redux tab
store.dispatch(Actions.registerRenderer(ratingControlTester, RatingControl));

ReactDOM.render(<App store={store} />, document.getElementById('root'));
registerServiceWorker();
