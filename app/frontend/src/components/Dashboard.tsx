// Inside Dashboard.tsx
import React, { useState, useMemo } from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar, ResponsiveContainer } from 'recharts';
import { TagCloud, TagCloudTag } from 'react-tagcloud';
import { FeedbackData } from '../types';
import 'bootstrap/dist/css/bootstrap.min.css';
import DetailedDataTable from './DetailedDataTable';

interface DashboardProps {
  data: FeedbackData;
}

const Dashboard: React.FC<DashboardProps> = ({ data }) => {

  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  // KPI Calculation
  const totalFeedbackCount = data.total_sentiment.reduce((sum, item) => sum + item.count, 0);
  const positiveSentiment = data.total_sentiment.find(item => item.sentiment === 'Positivo')?.count || 0;
  const negativeSentiment = data.total_sentiment.find(item => item.sentiment === 'Negativo')?.count || 0;
  const neutralSentiment = data.total_sentiment.find(item => item.sentiment === 'Neutro')?.count || 0;
  const positivePercentage = ((positiveSentiment / totalFeedbackCount) * 100).toFixed(1);
  const negativePercentage = ((negativeSentiment / totalFeedbackCount) * 100).toFixed(1);
  const neutralPercentage = ((neutralSentiment / totalFeedbackCount) * 100).toFixed(1);

  // Data for charts
  const sentimentDonutData = data.total_sentiment.map(item => ({ name: item.sentiment, value: item.count }));
  const sentimentColors = ['#28a745', '#dc3545', '#ffc107'];
  const sentimentTrendData = data.sentiment_by_month.map(item => ({ yearMonth: item.yearMonth, Negativo: item.sentiments.find(s => s.sentiment === 'Negativo')?.count || 0, Neutro: item.sentiments.find(s => s.sentiment === 'Neutro')?.count || 0, Positivo: item.sentiments.find(s => s.sentiment === 'Positivo')?.count || 0 }));
  const topNegativeAreasData = data.total_negative_feed_area_count.slice(0, 5).map(item => ({ area: item.area_de_feedback, count: item.count }));
  const negativeFeedbackTrendData = data.total_negative_feed_by_month.map(item => ({ yearMonth: item.yearMonth, count: item.count }));

  const wordCloudData = data.total_negative_feed_area_class_topic_count
    .slice(0, 50)
    .map(item => ({ value: item.assunto, count: item.count }));

  const tagCloudOptions = {
    callbacks: {
      onTagClicked: (tag: TagCloudTag) => setSelectedTopic(tag.value),
      getWordColor: (tag: TagCloudTag) => tag.count > 50 ? '#dc3545' : '#6c757d',
      getWordTooltip: (tag: TagCloudTag) => `"${tag.value}" appears ${tag.count} times`,
    },
    minSize: 12,
    maxSize: 35,
    shuffle: true
  };

  const filteredFeedback = useMemo(() => {
    if (!selectedTopic) return data.top10_negative_feed_area_class_topic_by_month;
    return data.top10_negative_feed_area_class_topic_by_month.map(monthData => ({
      ...monthData,
      top_entries: monthData.top_entries.filter(entry => entry.assunto === selectedTopic)
    }));
  }, [selectedTopic, data.top10_negative_feed_area_class_topic_by_month]);

  const topIssuesByArea = useMemo(() => {
    const areaMap: { [area: string]: { assunto: string; count: number }[] } = {};

    data.total_negative_feed_area_class_topic_count.forEach(item => {
      if (!areaMap[item.area_de_feedback]) {
        areaMap[item.area_de_feedback] = [];
      }
      areaMap[item.area_de_feedback].push({ assunto: item.assunto, count: item.count });
    });

    for (const area in areaMap) {
      areaMap[area].sort((a, b) => b.count - a.count); // Sort by count
      areaMap[area] = areaMap[area].slice(0, 3); // Take top 3
    }

    return areaMap;
  }, [data.total_negative_feed_area_class_topic_count]);

  return (
    <Container fluid>
      {/* KPIs */}
      <Row className="mb-3">
        <Col>
          <Card className="text-center">
            <Card.Body>
              <Card.Title>Total Feedback</Card.Title>
              <Card.Text>{totalFeedbackCount}</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col>
          <Card className="text-center text-success">
            <Card.Body>
              <Card.Title>Positive Sentiment</Card.Title>
              <Card.Text>{positivePercentage}%</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col>
          <Card className="text-center text-danger">
            <Card.Body>
              <Card.Title>Negative Sentiment</Card.Title>
              <Card.Text>{negativePercentage}%</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col>
          <Card className="text-center text-muted">
            <Card.Body>
              <Card.Title>Neutral Sentiment</Card.Title>
              <Card.Text>{neutralPercentage}%</Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Sentiment Overview */}
      <Row className="mb-3">
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Sentiment Overview</Card.Title>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={sentimentDonutData} cx="50%" cy="50%" labelLine={false} outerRadius={80} dataKey="value" label>
                      {sentimentDonutData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={sentimentColors[index % sentimentColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>

        {/* Sentiment Trend */}
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Sentiment Trend</Card.Title>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={sentimentTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="yearMonth" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="Negativo" stroke="#dc3545" />
                    <Line type="monotone" dataKey="Neutro" stroke="#ffc107" />
                    <Line type="monotone" dataKey="Positivo" stroke="#28a745" />
                  </LineChart>
                </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Top Negative Feedback Areas */}
      <Row className="mb-3">
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Top Negative Feedback Areas</Card.Title>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={topNegativeAreasData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="area" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#6c757d" />
                  </BarChart>
                </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>

        {/* Negative Feedback Trend */}
        <Col md={6}>
          <Card>
            <Card.Body>
              <Card.Title>Negative Feedback Trend</Card.Title>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={negativeFeedbackTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="yearMonth" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#dc3545" />
              </LineChart>
                </ResponsiveContainer>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Word Cloud */}
      <Row className="mb-3">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Top Negative Feedback Topics</Card.Title>
              <div style={{ width: '100%', height: '400px' }}>
                <TagCloud
                  tags={wordCloudData}
                  minSize={tagCloudOptions.minSize}
                  maxSize={tagCloudOptions.maxSize}
                  shuffle={tagCloudOptions.shuffle}
                  callbacks={tagCloudOptions.callbacks}
                />
              </div>
              {selectedTopic && <p>Selected Topic: {selectedTopic}</p>}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Top Issues by Area */}
      <Row className="mb-3">
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Top Issues by Area</Card.Title>
              {Object.entries(topIssuesByArea).map(([area, issues]) => (
                <div key={area}>
                  <h5>{area}</h5>
                  <ul>
                    {issues.map(issue => (
                      <li key={issue.assunto}>
                        {issue.assunto} ({issue.count})
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Detailed Data Table */}
      <Row>
        <Col>
          <Card>
            <Card.Body>
              <Card.Title>Detailed Feedback</Card.Title>
              <DetailedDataTable data={filteredFeedback} />
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Dashboard;
