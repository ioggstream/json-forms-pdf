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
import {
  materialCells,
  materialRenderers
} from '@jsonforms/material-renderers';
import { Store } from 'redux';
import { get } from 'lodash';
import RatingControl from './RatingControl';
import ratingControlTester from './ratingControlTester';
// qrcode
const QRCode = require('qrcode')

// pdf
const jsPDF = require("jspdf");
const html2canvas = require("html2canvas");
// yaml
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
  "richiedente": {
    "given_name": "Roberto",
    "family_name": "Polli"
  }
};

const getDataAsStringFromStore = (store: Store) =>
  store
    ? JSON.stringify(
      get(store.getState(), ['jsonforms', 'core', 'data']),
      null,
      2
    )
    : '';


function renderQrcode(store: Store) {
  QRCode.toCanvas(document.getElementById('qrcode'),
    getDataAsStringFromStore(store)
  );

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


    var imgData = canvas.toDataURL("image/png", 1.0);
    var pdf = new jsPDF('p', 'pt', [PDF_Width, PDF_Height]);
    pdf.addImage(imgData, 'png', top_left_margin, top_left_margin, canvas_image_width, canvas_image_height);


    for (var i = 1; i <= totalPDFPages; i++) {
      pdf.addPage(PDF_Width, PDF_Height);
      pdf.addImage(imgData, 'png', top_left_margin, -(PDF_Height * i) + (top_left_margin * 4), canvas_image_width, canvas_image_height);
    }

    pdf.save("tmp-jsonforms.pdf");
  });
};


const App = ({ store, classes }: AppProps) => {
  const processed = 0;
  const [displayDataAsString, setDisplayDataAsString] = useState('');
  const [standaloneData, setStandaloneData] = useState(data);
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

  useEffect(() => {
    renderQrcode(store);
  });

  return (
    <Fragment>
      <div className='App'>
        <header className='App-header'>
          <h1 className='App-title'>Welcome to JSON Forms with React</h1>
          <p className='App-intro'>Reference an URI with schema.yaml and uischema.yaml to rock.</p>
          <input type="button" value="Download PDF." onClick={getMyPDF} />
        </header>
      </div>
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
            <div className={classes.demoform} id='form'>
              {store ? (
                <Provider store={store}>
                  <JsonFormsReduxContext>
                    <JsonFormsDispatch />
                  </JsonFormsReduxContext>
                </Provider>
              ) : null}
            </div>
          </Grid>
          <canvas id="qrcode"></canvas>
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