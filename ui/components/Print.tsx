import { Button, Stack, Text } from "@chakra-ui/react";
import { useCallback, useEffect } from "react";
import ReactMarkdown from "react-markdown";

import { Components } from "../client";
import useApi from "../hooks/useApi";
import ChakraUIRenderer from "../lib/chakra_ui_renderer";

interface PrintProps {
  sessionId: string;
  job: Components.Schemas.PrintJob;
  onComplete: () => void;
}
const Print = ({ sessionId, job, onComplete }: PrintProps) => {
  const getClient = useApi();

  const onConfirm = useCallback(async () => {
    if (!getClient) return;

    const client = await getClient;
    await client.complete__session_id__job__job_id__put(
      { session_id: sessionId, job_id: String(job.id) },
      JSON.stringify(""),
    );
    onComplete();
  }, [getClient, job.id, onComplete, sessionId]);

  useEffect(() => {
    if (!job.wait_for_confirmation) onConfirm().catch(console.error);
  }, [onConfirm, job]);

  return (
    <Stack spacing={2}>
      {job.format_markdown && (
        <ReactMarkdown components={ChakraUIRenderer()} skipHtml>
          {job.message}
        </ReactMarkdown>
      )}
      {!job.format_markdown && <Text>{job.message}</Text>}
      {job.wait_for_confirmation && <Button onClick={onConfirm}>OK</Button>}
    </Stack>
  );
};

export default Print;
