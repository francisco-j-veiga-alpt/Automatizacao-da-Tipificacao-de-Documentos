// src/components/DetailedDataTable.tsx
import React from 'react';
import { Table } from 'react-bootstrap';
import { TopNegativeFeedAreaClassTopicByMonth } from '../types'; // Updated type

interface DetailedDataTableProps {
  data: TopNegativeFeedAreaClassTopicByMonth[]; // Updated type
}

const DetailedDataTable: React.FC<DetailedDataTableProps> = ({ data }) => {
  return (
    <Table striped bordered hover responsive>
      <thead>
        <tr>
          <th>Month</th>
          <th>Area</th>
          <th>Classification</th>
          <th>Topic</th>
          <th>Count</th>
        </tr>
      </thead>
      <tbody>
        {data.map(monthData => (
          monthData.top_entries.map((entry, index) => (
            <tr key={`${monthData.yearMonth}-${index}`}>
              <td>{monthData.yearMonth}</td>
              <td>{entry.area_de_feedback}</td>
              <td>{entry.classificacao}</td>
              <td>{entry.assunto}</td>
              <td>{entry.count}</td>
            </tr>
          ))
        ))}
      </tbody>
    </Table>
  );
};

export default DetailedDataTable;
