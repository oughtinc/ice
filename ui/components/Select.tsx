import { Alert, Button, Heading, Radio, Stack, useRadioGroup } from "@chakra-ui/react";
import { useState } from "react";
import { Components } from "../client";
import useApi from "../hooks/useApi";

interface SelectProps {
  sessionId: string;
  job: Components.Schemas.SelectJob;
  onComplete: () => void;
}
const Select = ({ sessionId, job, onComplete }: SelectProps) => {
  const [submitting, setSubmitting] = useState(false);
  const { value, getRadioProps } = useRadioGroup({ defaultValue: undefined });
  const [error, setError] = useState<string | null>(null);
  const getClient = useApi();

  const handleSubmit = async () => {
    if (value === null) {
      setError("You must select a response.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const client = await getClient;
    if (!client) return;
    const response = await client.complete__session_id__job__job_id__put(
      { session_id: sessionId, job_id: String(job.id) },
      JSON.stringify(value),
    );
    setSubmitting(false);
    onComplete();
  };

  return (
    <Stack spacing={5}>
      {error && <Alert status="error">{error}</Alert>}
      <Heading as={"h2"}>{job.prompt}</Heading>
      <Stack spacing={2}>
        {job.choices.map(choice => (
          <Radio key={choice} {...getRadioProps({ value: choice })}>
            {choice}
          </Radio>
        ))}
      </Stack>
      <Button
        isLoading={submitting}
        loadingText="Submitting…"
        colorScheme="blue"
        onClick={handleSubmit}
      >
        Submit
      </Button>
    </Stack>
  );
};

export default Select;
