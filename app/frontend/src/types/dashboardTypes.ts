export interface Sentiment {
    sentiment: string;
    count: number;
    areas: Area[];
  }
  
  export interface Area {
    area: string;
    count: number;
    classificacoes: Classification[];
  }
  
  export interface Classification {
    classificacao: string;
    count: number;
    assuntos: Subject[];
  }
  
  export interface Subject {
    assunto: string;
    count: number;
  }
  
  export interface MonthData {
    sentiments: Sentiment[];
    yearMonth: string;
  }
  
  export interface DashboardData {
    results_total_by_mont: MonthData[];
  }
  