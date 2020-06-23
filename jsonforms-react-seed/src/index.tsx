import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import registerServiceWorker from './registerServiceWorker';
import { combineReducers, createStore, Reducer, AnyAction } from 'redux';
import { Actions, jsonformsReducer, JsonFormsState } from '@jsonforms/core';
import {
  materialCells,
  materialRenderers
} from '@jsonforms/material-renderers';
import RatingControl from './RatingControl';
import ratingControlTester from './ratingControlTester';
import MarkdownControl from './MarkdownControl';
import markdownControlTester from './markdownControlTester';

import { devToolsEnhancer } from 'redux-devtools-extension';
import { safeLoad } from 'js-yaml';
const yaml = require("js-yaml");
const refParser = require("json-schema-ref-parser");


// Setup Redux store
const data = {
  richiedente: {
    given_name: "Roberto",
    family_name: "Polli"
  }
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

const p = new URLSearchParams(window.location.search).get("q") || "form-1";
const schema_url = p + '/schema.yaml'
const uischema_url = p + '/uischema.yaml'

const fetchYaml = async (url: string) => {
  const text = await (await fetch(url)).text();
  const y = yaml.safeLoad(text);
  console.debug(url, y);
  return y;
}

fetchYaml(schema_url)
  .then((schema_yaml) => {
    refParser.dereference(schema_yaml, (err: any, schema: any) => {
      if (err) {
        console.error(err);
        throw err;
      }
      console.log(schema);
      fetchYaml(uischema_url)
        .then((uischema) => {
          store.dispatch(Actions.init(data, schema, uischema));
        });
    });
  });


// Register custom renderer for the Redux tab
store.dispatch(Actions.registerRenderer(ratingControlTester, RatingControl));
store.dispatch(Actions.registerRenderer(markdownControlTester, MarkdownControl));

ReactDOM.render(<App store={store} />, document.getElementById('root'));
registerServiceWorker();
