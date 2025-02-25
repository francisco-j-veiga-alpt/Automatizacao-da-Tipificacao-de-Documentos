// src/types.ts
export interface SentimentData {
  count: number;
  sentiment: string;
}

export interface SentimentByMonth {
  sentiments: SentimentData[];
  yearMonth: string;
}

export interface NegativeFeedAreaCount {
  count: number;
  area_de_feedback: string;
}

export interface TopEntries {
  area_de_feedback: string;
  count: number;
  classificacao?: string;
  assunto?: string;
}

export interface TopNegativeFeedAreaByMonth {
  yearMonth: string;
  top_entries: TopEntries[];
}

export interface NegativeFeedAreaClassCount {
  count: number;
  area_de_feedback: string;
  classificacao: string;
}

export interface NegativeFeedAreaClassTopicCount {
  count: number;
  area_de_feedback: string;
  classificacao: string;
  assunto: string;
}

export interface TopNegativeFeedAreaClassTopicByMonth {
  yearMonth: string;
  top_entries: {
    area_de_feedback: string;
    classificacao: string;
    assunto: string;
    count: number;
  }[];
}


export interface FeedbackData {
  total_sentiment: SentimentData[];
  sentiment_by_month: SentimentByMonth[];
  total_negative_feed_count: number;
  total_negative_feed_by_month: { count: number; yearMonth: string }[];
  total_negative_feed_area_count: NegativeFeedAreaCount[];
  top10_negative_feed_area_by_month: TopNegativeFeedAreaByMonth[];
  total_negative_feed_area_class_count: NegativeFeedAreaClassCount[];
  top10_negative_feed_area_class_by_month: TopNegativeFeedAreaByMonth[];
  total_negative_feed_area_class_topic_count: NegativeFeedAreaClassTopicCount[];
  top10_negative_feed_area_class_topic_by_month: TopNegativeFeedAreaClassTopicByMonth[];
}
