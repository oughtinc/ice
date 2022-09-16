import { Alert, Button, Checkbox, Heading, Stack, useCheckboxGroup } from "@chakra-ui/react";
import { useState } from "react";
import { Components } from "../client";
import useApi from "../hooks/useApi";

interface CheckboxesProps {
  sessionId: string;
  job: Components.Schemas.CheckboxesJob;
  onComplete: () => void;
}
const Checkboxes = ({ sessionId, job, onComplete }: CheckboxesProps) => {
  const [submitting, setSubmitting] = useState(false);
  const { value, getCheckboxProps } = useCheckboxGroup({ defaultValue: [] });
  const [error, setError] = useState<string | null>(null);
  const getClient = useApi();

  const handleSubmit = async () => {
    if (value.length === 0) {
      setError("You must select at least one checkbox.");
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
          <Checkbox key={choice} {...getCheckboxProps({ value: choice })}>
            {choice}
          </Checkbox>
        ))}
      </Stack>
      <Button
        isLoading={submitting}
        loadingText="Submitting…"
        colorScheme="blue"
        onClick={handleSubmit}
      >
        Select
      </Button>
    </Stack>
  );
};

export default Checkboxes;
