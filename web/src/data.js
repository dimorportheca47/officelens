import Leaflet from 'leaflet';

Leaflet.Icon.Default.imagePath = '//cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/';

const LeafIcon = Leaflet.Icon.extend({
  options: {},
});

export const blueIcon = new LeafIcon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export const redIcon = new LeafIcon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export const greenIcon = new LeafIcon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export const blackIcon = new LeafIcon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-black.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export const sensor = {
  '10.X1': [0, -73.5],
  '10.X2': [22, -68],
  '10.X3': [35, -51],
  '10.X4': [36.5, -31.5],
  '10.X5': [36.5, -16.5],
  '10.X6': [36.5, -1.5],
  '10.X7': [36.5, 13.5],
  '10.X8': [36.5, 28.5],
  '10.X9': [35, 47.5],
  '10.X10': [22, 62.5],
  '10.X11': [0, 70],
  '10.X12': [-18, 64],
  '10.X13': [-33.5, 47],
  '10.X14': [-33.5, 28],
  '10.X15': [-33.5, 13],
  '10.X16': [-33.5, -2],
  '10.X17': [-33.5, 18],
  '10.X18': [-33.5, -31],
  '10.X19': [-32, -51],
  '10.X20': [-19, -68],
};

export const floor = {
  DEMO: [{ label: ' 10th', value: '10F' }],
};
