import React, { Fragment, useState, useEffect, useCallback } from 'react';
import {
  JsonForms,
  JsonFormsDispatch,
  JsonFormsReduxContext
} from '@jsonforms/react';
import { Provider } from 'react-redux';
import Grid from '@material-ui/core/Grid';
import Typography from '@material-ui/core/Typography';
import withStyles, { WithStyles } from '@material-ui/core/styles/withStyles';
import createStyles from '@material-ui/core/styles/createStyles';
import { Tabs, Tab } from '@material-ui/core';
import logo from './logo.svg';
import './App.css';
import { safeLoad } from 'js-yaml';
//import schema from './schema.json';
//import uischema from './uischema.json';
import {
  materialCells,
  materialRenderers
} from '@jsonforms/material-renderers';
import { Store } from 'redux';
import { get } from 'lodash';
import RatingControl from './RatingControl';
import ratingControlTester from './ratingControlTester';
const jsPDF = require("jspdf");
const html2canvas = require("html2canvas");
const yaml = require("js-yaml");
const refParser = require("json-schema-ref-parser");


const styles = createStyles({
  container: {
    padding: '1em'
  },
  title: {
    textAlign: 'center',
    padding: '0.25em'
  },
  dataContent: {
    display: 'flex',
    justifyContent: 'center',
    borderRadius: '0.25em',
    backgroundColor: '#cecece'
  },
  demoform: {
    margin: 'auto',
    padding: '1rem'
  },
  textField: {
    marginLeft: '5em'
  }
});

export interface AppProps extends WithStyles<typeof styles> {
  store: Store;
}

const data = {
  name: 'Send email to Adrian',
  description: 'Confirm if you have passed the subject\nHereby ...',
  done: true,
  recurrence: 'Daily',
  rating: 3
};

const getDataAsStringFromStore = (store: Store) =>
  store
    ? JSON.stringify(
      get(store.getState(), ['jsonforms', 'core', 'data']),
      null,
      2
    )
    : '';

const loadFiles = async () => {
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
            console.log("processed uischema", uischema);
            return { "schema": schema, "uischema": uischema };
          });
      });
    });
};

function downloadCurrentDocument() {
  var base64doc = btoa(unescape(encodeURIComponent(document.documentElement.innerHTML))),
    a = document.createElement('a'),
    e = new MouseEvent('click');

  a.download = 'doc.html';
  a.href = 'data:text/html;base64,' + base64doc;
  a.dispatchEvent(e);
}

/**
 * Convert an html element in PDF.
 * 
 * @param document 
 */
function getPDF(pdf_element: any) {
  console.log("document", pdf_element);
  var HTML_Width = pdf_element.offsetWidth;
  var HTML_Height = pdf_element.offsetHeight;
  var top_left_margin = 15;
  var PDF_Width = HTML_Width + (top_left_margin * 2);
  var PDF_Height = (PDF_Width * 1.5) + (top_left_margin * 2);
  var canvas_image_width = HTML_Width;
  var canvas_image_height = HTML_Height;

  var totalPDFPages = Math.ceil(HTML_Height / PDF_Height) - 1;


  html2canvas(pdf_element, { allowTaint: true }).then(function (canvas: any) {
    canvas.getContext('2d');

    console.log(canvas.height + "  " + canvas.width);


    var imgData = canvas.toDataURL("image/jpeg", 1.0);
    var pdf = new jsPDF('p', 'pt', [PDF_Width, PDF_Height]);
    pdf.addImage(imgData, 'JPG', top_left_margin, top_left_margin, canvas_image_width, canvas_image_height);


    for (var i = 1; i <= totalPDFPages; i++) {
      pdf.addPage(PDF_Width, PDF_Height);
      pdf.addImage(imgData, 'JPG', top_left_margin, -(PDF_Height * i) + (top_left_margin * 4), canvas_image_width, canvas_image_height);
    }

    pdf.save("HTML-Document.pdf");
  });
};


const App = ({ store, classes }: AppProps) => {
  const [tabIdx, setTabIdx] = useState(0);
  const [displayDataAsString, setDisplayDataAsString] = useState('');
  const [standaloneData, setStandaloneData] = useState(data);
  const handleTabChange = useCallback(
    (event: any, newValue: number) => {
      setTabIdx(newValue);
      setDisplayDataAsString(
        newValue === 0
          ? getDataAsStringFromStore(store)
          : JSON.stringify(standaloneData, null, 2)
      );
    },
    [store, standaloneData]
  );
  const [butIdx, setButIdx] = useState(0);
  const handleButChange = downloadCurrentDocument;
  const getMyPDF = () => { getPDF(document.body) };
  useEffect(() => {
    const updateStringData = () => {
      const stringData = getDataAsStringFromStore(store);
      setDisplayDataAsString(stringData);
    };
    store.subscribe(updateStringData);
    updateStringData();
  }, [store]);

  useEffect(() => {
    setDisplayDataAsString(JSON.stringify(standaloneData, null, 2));
  }, [standaloneData]);

  const state = { "schema": {}, "uischema": { "type": "foo" } }

  loadFiles().then((ret: any) => {
    console.log("ret: ", ret);
    if (ret) {
      state.schema = ret.schema;
      state.uischema = ret.uischema;
    }
  });
  const schema = state.schema;
  const uischema = state.uischema;
  console.log("uischema", uischema);
  return (
    <Fragment>
      <div className='App'>
        <header className='App-header'>
          <img src={logo} className='App-logo' alt='logo' />
          <h1 className='App-title'>Welcome to JSON Forms with React</h1>
          <p className='App-intro'>More Forms. Less Code.</p>
        </header>
      </div>
      <input type="button" value="Download HTML." onClick={getMyPDF} />
      <form action="" method="POST">
        <Grid
          container
          justify={'center'}
          spacing={1}
          className={classes.container}
        >
          <Grid item sm={6}>
            <Typography variant={'h3'} className={classes.title}>
              Rendered form
          </Typography>
            <Tabs value={tabIdx} onChange={handleTabChange}>
              <Tab label='via Redux' />
              <Tab label='Standalone' />
            </Tabs>
            {tabIdx === 0 && (
              <div className={classes.demoform} id='form'>
                {store ? (
                  <Provider store={store}>
                    <JsonFormsReduxContext>
                      <JsonFormsDispatch />
                    </JsonFormsReduxContext>
                  </Provider>
                ) : null}
              </div>
            )}
            {tabIdx === 1 && (
              <div className={classes.demoform}>
                <JsonForms
                  schema={schema}
                  uischema={uischema}
                  data={standaloneData}
                  renderers={[
                    ...materialRenderers,
                    //register custom renderer
                    { tester: ratingControlTester, renderer: RatingControl }
                  ]}
                  cells={materialCells}
                  onChange={({ errors, data }) => setStandaloneData(data)}
                />
              </div>
            )}
          </Grid>
        </Grid>
      </form>
    </Fragment>
  );

}; //App
/*
        <Grid item sm={6}>
          <Typography variant={'h3'} className={classes.title}>
            Bound data
          </Typography>
          <div className={classes.dataContent}>
            <pre id='boundData'>{displayDataAsString}</pre>
          </div>
        </Grid>

*/



export default withStyles(styles)(App);
