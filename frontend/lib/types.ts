export interface MedicamentoDetalhe {
  entrada_original: string;
  nome_normalizado: string;
  encontrado: boolean;
  pim_beers: boolean;
  afinidade_ac: string;
  afinidade_sedativa: string;
  peso_afinidade: number;
  contribuicao: number;
  duplicata: boolean;
  observacao: string;
}

export interface FPRSResponse {
  paciente_id: string | null;
  idade: number | null;
  data_avaliacao: string | null;
  observacao: string | null;
  medicamentos: MedicamentoDetalhe[];
  total_medicamentos: number;
  label_polifarmacia: string;
  pontos_polifarmacia: number;
  carga_afinidade: number;
  pim_adicional: number;
  fprs: number;
  categoria: string;
  alerta: string;
}
