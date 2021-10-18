import { useState, useEffect, useContext } from 'react';
import Container from 'aws-northstar/layouts/Container';
import { API } from 'aws-amplify';
import { MainContext } from './Context';
import KeyValuePair from 'aws-northstar/components/KeyValuePair';
import ColumnLayout, { Column } from 'aws-northstar/layouts/ColumnLayout';
import Stack from 'aws-northstar/layouts/Stack';

import Grid from 'aws-northstar/layouts/Grid';
import Table from 'aws-northstar/components/Table';
import StatusIndicator from 'aws-northstar/components/StatusIndicator';
import * as queries from '../graphql/queries';

import { CircularProgressbar } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const columnDefinitions = [
  {
    id: 'PartitionKey',
    width: 150,
    Header: 'PartitionKey',
    accessor: 'PartitionKey',
  },
  {
    id: 'SortKey',
    width: 150,
    Header: 'SortKey',
    accessor: 'SortKey',
  },
  {
    id: 'Alias',
    width: 150,
    Header: 'Alias',
    accessor: 'Alias',
  },
  {
    id: 'IsConnected',
    width: 150,
    Header: 'IsConnected',
    accessor: 'IsConnected',
    Cell: ({ row }) => {
      if (row && row.original) {
        const status = row.original.IsConnected;
        switch (status) {
          case true:
            return <StatusIndicator statusType="positive">True</StatusIndicator>;
          case false:
            return <StatusIndicator statusType="negative">False</StatusIndicator>;
          default:
            return null;
        }
      }
      return row.id;
    },
  },
  {
    id: 'IsOccupied',
    width: 150,
    Header: 'IsOccupied',
    accessor: 'IsOccupied',
    Cell: ({ row }) => {
      if (row && row.original) {
        const status = row.original.IsOccupied;
        switch (status) {
          case true:
            return <StatusIndicator statusType="positive">True</StatusIndicator>;
          case false:
            return <StatusIndicator statusType="negative">False</StatusIndicator>;
          default:
            return null;
        }
      }
      return row.id;
    },
  },
  {
    id: 'SensorID',
    width: 200,
    Header: 'SensorID',
    accessor: 'SensorID',
  },
];

function CalCongestion({ data }) {
  var SeatsNum = data.length;
  var IsOccupied = data.filter(function (x) {
    return x.IsOccupied;
  }).length;
  var NotConnected = data.filter(function (x) {
    return !x.IsConnected;
  }).length;

  var congestion = ((IsOccupied / SeatsNum) * 100) | 0;

  return (
    <Grid container spacing={1}>
      <Grid item xs={4}>
        <Container headingVariant="h4" title="OFFICE UTILIZATION">
          <CircularProgressbar value={congestion} text={`${congestion}%`} strokeWidth={5} />
        </Container>
      </Grid>
      <Grid item xs={4}>
        <Container headingVariant="h4" title="FLOOR UTILIZATION">
          <CircularProgressbar value={congestion} text={`${congestion}%`} strokeWidth={5} />
        </Container>
      </Grid>
      <Grid item xs={4}>
        <Container headingVariant="h4" title="INVENTORY">
          <ColumnLayout>
            <Column key="column1">
              <Stack>
                <KeyValuePair label="BUILDING CAPACITY" value={ SeatsNum }></KeyValuePair>
                <KeyValuePair label="NUMBER OF FLOORS" value={ NotConnected }></KeyValuePair>
                <KeyValuePair label="NUMBER OF Disconnected Devices" value={ NotConnected }></KeyValuePair>
              </Stack>
            </Column>
          </ColumnLayout>
        </Container>
      </Grid>
    </Grid>
  );
}

const Portofolio = () => {
  const [data, setData] = useState([]);
  const context = useContext(MainContext)[0];
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
        setData(DeviceSrc);
      } catch (err) {
        console.log('error');
      }
    })();
  }, [setData, context, partition]);

  return (
    <div>
      <CalCongestion data={data} />
      <Table
        onSelectionChange={() => {}}
        tableTitle="Device Infomation"
        columnDefinitions={columnDefinitions}
        items={data}
      ></Table>
    </div>
  );
};

export default Portofolio;
