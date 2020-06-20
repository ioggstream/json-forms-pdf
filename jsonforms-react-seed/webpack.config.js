const path = require('path');

module: {
  rules: [{
    test: /\.yaml$/,
    use: 'js-yaml-loader',
  }]
}

