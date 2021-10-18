/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const queryDeviceInfoTables = /* GraphQL */ `
  query QueryDeviceInfoTables(
    $PartitionKey: String!
    $filter: TableDeviceInfoTableFilterInput
    $limit: Int
    $nextToken: String
  ) {
    queryDeviceInfoTables(
      PartitionKey: $PartitionKey
      filter: $filter
      limit: $limit
      nextToken: $nextToken
    ) {
      items {
        Alias
        IsConnected
        IsOccupied
        PartitionKey
        SensorID
        SortKey
      }
      nextToken
    }
  }
`;
