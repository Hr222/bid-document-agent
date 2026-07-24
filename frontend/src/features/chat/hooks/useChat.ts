import { useMutation } from "@tanstack/react-query";

import { sendChatMessage } from "../api/chatApi";

export function useChat() {
  return useMutation({ mutationFn: sendChatMessage });
}
