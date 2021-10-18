import { API, graphqlOperation } from 'aws-amplify';
import * as queries from '../graphql/queries';
import { onLambdaDeviceInfoTable } from '../graphql/subscriptions';
import Select from 'aws-northstar/components/Select';
import Container from 'aws-northstar/layouts/Container';
import { useEffect, useContext } from 'react';
import { MainContext, PosContext } from './Context';
import { redIcon, blackIcon, sensor, floor } from '../data';
import 'leaflet/dist/leaflet.css';
import { MapContainer, useMapEvents, Marker, Popup, useMap } from 'react-leaflet';
import Text from 'aws-northstar/components/Text';
import Inline from 'aws-northstar/layouts/Inline';
import RoomIcon from '@material-ui/icons/Room';
import Leaflet, { CRS } from 'leaflet';
Leaflet.Icon.Default.imagePath = '//cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/';

function CheckLatLng() {
  useMapEvents({
    click: (e) => {
      //console.log(e.latlng.lat + "," + e.latlng.lng);
    },
  });
  return [<div key="CheckLatLng" />];
}

function SetMarker() {
  var Markers = [];
  const context = useContext(MainContext)[0];
  const [position, setPosition] = useContext(PosContext);
  const partition = context.office + '_' + context.floor;

  useEffect(() => {
    (async () => {
      try {
        const DeviceData = await API.graphql({
          query: queries.queryDeviceInfoTables,
          variables: {
            PartitionKey: partition,
            limit: 100,
          },
        });
        const DeviceSrc = DeviceData.data.queryDeviceInfoTables.items;

        const records = DeviceSrc.map(function (v) {
          if (v['SortKey'] in sensor) {
            v['pos'] = sensor[v['SortKey']];
            return v;
          } else {
            return null;
          }
        }).filter((v) => v !== null);
        setPosition(records);
      } catch (err) {
        console.log('error');
      }
    })();
  }, [setPosition, context, partition]);

  for (var pos of position) {
    if (typeof pos['PartitionKey'] === 'undefined') {
      continue;
    }
    if (!pos['IsConnected']) {
      Markers.push(
        <div key={pos['SortKey']}>
          <Marker position={pos['pos']} icon={redIcon}>
            <Popup>Disconnected</Popup>
          </Marker>
        </div>
      );
    } else if (pos['IsOccupied']) {
      Markers.push(
        <div key={pos['SortKey']}>
          <Marker position={pos['pos']} icon={blackIcon} />
        </div>
      );
    }
  }
  return Markers;
}

function Subscription() {
  const setPosition = useContext(PosContext)[1];
  const context = useContext(MainContext)[0];
  const partition = context.office + '_' + context.floor;

  useEffect(() => {
    const subscribe = API.graphql(graphqlOperation(onLambdaDeviceInfoTable)).subscribe({
      next: (eventData) => {
        var newitem = eventData.value.data.onLambdaDeviceInfoTable;
        if (newitem['PartitionKey'] === partition) {
          newitem['pos'] = sensor[newitem['SortKey']];
          setPosition((prevPosition) =>
            prevPosition.map((obj) => (obj.SortKey === newitem['SortKey'] ? newitem : obj))
          );
        }
      },
    });
    return () => subscribe.unsubscribe();
  }, [setPosition, context, partition]);

  return null;
}

function SetBounds() {
  const context = useContext(MainContext)[0];
  const url = './floormap/' + context.office + '_' + context.floor + '.png';
  const map = useMap();
  var bounds;

  const img = new Image();
  var ratio;
  img.onload = function () {
    ratio = img.naturalWidth / img.naturalHeight ;
    if (ratio > 1) {
      bounds = [
        [-128 / ratio, -128],
        [128 / ratio, 128],
      ];
    } else {
      bounds = [
        [-128 / ratio, -128],
        [128 / ratio, 128],
      ];
    }
    map.addLayer(Leaflet.imageOverlay(url, bounds));
  };
  img.src = url;

  return null;
}

const Floormap = () => {
  const [context, setContext] = useContext(MainContext);
  const onChange = (event) => {
    setContext((prevctx) => ({ ...prevctx, floor: event.target.value }));
  };

  return (
    <Container
      title={context.office + '_' + context.floor}
      subtitle={
        <Inline spacing="xs">
          <RoomIcon fontSize="small" style={{ color: 'black' }} />
          <Text variant="small">Occupied</Text>
          <RoomIcon fontSize="small" style={{ color: 'red' }} />
          <Text variant="small">Disconnected</Text>
        </Inline>
      }
      actionGroup={
        <Inline spacing="xs">
          <Select options={floor[context.office]} selectedOption={{ value: context.floor }} onChange={onChange} />
        </Inline>
      }
    >
      <div id="wrapper">
        <MapContainer zoom={1} center={[0, 0]} scrollWheelZoom={true} crs={CRS.Simple} maxZoom={3}>
          <SetBounds />
          <Subscription />
          <SetMarker />
          <CheckLatLng />
        </MapContainer>
      </div>
    </Container>
  );
};

export default Floormap;
