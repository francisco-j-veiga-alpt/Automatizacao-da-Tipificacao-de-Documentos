// src/types/feedbackTypes.ts

export interface ComplaintAnalysis {
    tema: string;
    descricao: string;
    percentagem: number;
    total: number
  }
  
  export interface FeedbackData {
    analise: ComplaintAnalysis[];
    sugestoes_de_melhoria_dos_clientes: string[];
    propostas_de_melhoria_AI: string[];
    data: string;
  }
  