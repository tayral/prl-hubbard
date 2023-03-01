// Defines the d3 library
require.config({
    paths: {
        "svg-pan-zoom": "/custom/svg-pan-zoom",
        "d3": "/custom/d3.min"
    }
});

// Loads myQLM/QLM scripts
require(
    ["custom/display_library", "custom/FileSaver"],
    function() { }
);

// Loads the d3 library
require(["d3"], function(d3) {
    window.d3 = d3;
    console.log("d3 loaded");
});

// Do not open a new tab for each Jupyter Notebook by default
// If a new tab is wanted, use ctrl^click ; like that, the user
// is in control
$('a').attr('target', '_self');
require(["base/js/namespace"], function (Jupyter) {
  Jupyter._target = '_self';
});

// Loads the svg-pan-zoom library
// This library is used to be able to zoom
// quantum circuits displayed with the SVG
// engine
require(["svg-pan-zoom"], function(svgPanZoom) {
    window.svgPanZoom = svgPanZoom;
    console.log("svg-pan-zoom loaded");
});

$("body").on("click", "svg", function() {
    window.svgPanZoom(this, {
        controlIconsEnabled: true,
        maxZoom: 100,
        zoomScaleSensitivity: 0.5
    });
});
