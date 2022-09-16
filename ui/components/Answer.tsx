import { useState } from "react";

import { Alert, Button, Input, Stack, Textarea, Code } from "@chakra-ui/react";
import { Components } from "../client";
import ReactMarkdown from "react-markdown";
import ChakraUIRenderer from "../lib/chakra_ui_renderer";
import useApi from "../hooks/useApi";

interface AnswerProps {
  sessionId: string;
  job: Components.Schemas.AnswerJob;
  onComplete: () => void;
}
const Answer = ({ sessionId, job, onComplete }: AnswerProps) => {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState(job.default);
  const getClient = useApi();

  const handleSubmit = async () => {
    if (!getClient) return;
    setSubmitting(true);
    setError(null);

    const client = await getClient;
    const response = await client.complete__session_id__job__job_id__put(
      { session_id: sessionId, job_id: String(job.id) },
      JSON.stringify(answer),
    );
    setSubmitting(false);
    onComplete();
  };

  return (
    <>
      <Stack spacing={2}>
        {error && <Alert status="error">{error}</Alert>}
        <ReactMarkdown components={ChakraUIRenderer()} skipHtml>
          {job.prompt}
        </ReactMarkdown>
        {job.multiline && (
          <Textarea
            placeholder="Your answer"
            value={answer}
            onChange={e => setAnswer(e.target.value)}
          />
        )}
        {!job.multiline && (
          <Input
            placeholder="Your answer"
            value={answer}
            onChange={e => setAnswer(e.target.value)}
          />
        )}
        <Button
          isLoading={submitting}
          loadingText="Submitting…"
          colorScheme="blue"
          onClick={handleSubmit}
        >
          Submit
        </Button>
      </Stack>
    </>
  );
};

export default Answer;
