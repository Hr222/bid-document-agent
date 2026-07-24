export type ChatApiResponse = {
  answer: string;
  model: string;
  prompt_version: string;
  usage: {
    input_tokens: number | null;
    output_tokens: number | null;
    total_tokens: number | null;
  };
};

export type ChatResult = {
  answer: string;
  model: string;
  promptVersion: string;
  durationMs: number;
  totalTokens: number | null;
};
