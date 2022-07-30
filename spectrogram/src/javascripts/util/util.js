/********************************************************
Copyright 2016 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*********************************************************/

var Util = window.Util || {};

Util.loadTrackSrc = function(context, src, callback, opt_progressCallback) {
  var request = new XMLHttpRequest();
  request.open('GET', src, true);
  request.responseType = 'arraybuffer';

  // Decode asynchronously.
  request.onload = function() {
    context.decodeAudioData(request.response, function(buffer) {
      callback(buffer);
    }, function(e) {
      console.error(e);
    });
  };
  if (opt_progressCallback) {
    request.onprogress = function(e) {
      var percent = e.loaded / e.total;
      opt_progressCallback(percent);
    };
  }

  request.send();
};

// Log scale conversion functions. Cheat sheet:
// http://stackoverflow.com/questions/19472747/convert-linear-scale-to-logarithmic
Util.setLogScale = function(x1, y1, x2, y2) {
  this.b = Math.log(y1/y2) / (x1-x2);
  this.a = y1 / Math.exp( this.b * x1 );
};

Util.lin2log = function(x) {
  return this.a * Math.exp( this.b * x );
};

Util.log2lin = function(y) {
  return Math.log( y / this.a ) / this.b;
};


module.exports = Util;
