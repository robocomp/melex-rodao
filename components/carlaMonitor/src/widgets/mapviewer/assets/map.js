var map;
var marker;

function initialize(){
    map = L.map('map').setView([55.61121, 12.99351], 16);

    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>',
        maxZoom: 25
    }).addTo(map);

    marker = L.marker(map.getCenter()).addTo(map);
    // marker.bindPopup("Hello World!").openPopup();
    new QWebChannel(qt.webChannelTransport, function (channel) {
        window.MapViewer = channel.objects.MapViewer;
        if(typeof MapViewer != 'undefined') {
            var onMapMove = function() { MapViewer.onMapMove(map.getCenter().lat, map.getCenter().lng) };
            map.on('move', onMapMove);
            onMapMove();
        }
    });
}