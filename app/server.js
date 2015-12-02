var express = require('express');
var app = express();

// Serve application file depending on environment
app.get('/index.js', function(req, res) {
  res.redirect('//localhost:9090/build/index.js');
});

app.get('/index.css', function(req, res) {
  res.redirect('//localhost:9090/build/style.css');
})

// Serve index page
app.get('*', function(req, res) {
  res.sendFile(__dirname + '/build/index.html');
});

if (!process.env.PRODUCTION) {
  var webpack = require('webpack');
  var WebpackDevServer = require('webpack-dev-server');
  var config = require('./webpack.local.config');

  new WebpackDevServer(webpack(config), {
    publicPath: config.output.publicPath,
    hot: true,
    noInfo: true,
    historyApiFallback: true
  }).listen(9090, 'localhost', function (err, result) {
    if (err) {
      console.log(err);
    }
  });
}§

var port = process.env.PORT || 8080;
var server = app.listen(port, function () {
  var host = server.address().address;
  var port = server.address().port;

  console.log('Server listening at http://%s:%s', host, port);
});
