import {
  Alert,
  Button,
  Stack,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Box,
  SliderMark,
} from "@chakra-ui/react";
import { useState } from "react";
import { Components } from "../client";
import useApi from "../hooks/useApi";

interface ScoreProps {
  sessionId: string;
  job: Components.Schemas.ScoreJob;
  onComplete: () => void;
}
const Score = ({ sessionId, job, onComplete }: ScoreProps) => {
  const [submitting, setSubmitting] = useState(false);
  const [sliderValue, setSliderValue] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const getClient = useApi();

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    const client = await getClient;
    if (!client) return;
    const response = await client.complete__session_id__job__job_id__put(
      { session_id: sessionId, job_id: String(job.id) },
      JSON.stringify(sliderValue),
    );
    setSubmitting(false);
    onComplete();
  };

  return (
    <Stack spacing={16}>
      {error && <Alert status="error">{error}</Alert>}
      <Box>{job.prompt}</Box>
      <Slider
        aria-label="score-slider"
        defaultValue={job.default ?? 0}
        min={0}
        max={1}
        step={0.01}
        onChange={setSliderValue}
      >
        <SliderMark value={sliderValue} textAlign="center" mt="-10" ml="-5" w="12">
          {sliderValue}
        </SliderMark>
        <SliderTrack>
          <SliderFilledTrack />
        </SliderTrack>
        <SliderThumb />
      </Slider>
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

export default Score;
