import { Box, Center, Container, Spinner, VStack } from "@chakra-ui/react";
import type { NextPage } from "next";
import { useEffect, useState } from "react";
import { Components } from "../client";
import Header from "../components/Header";
import PendingJob from "../components/PendingJob";
import useApi from "../hooks/useApi";

export type Job =
  | Components.Schemas.PrintJob
  | Components.Schemas.CheckboxesJob
  | Components.Schemas.AnswerJob
  | Components.Schemas.ScoreJob
  | Components.Schemas.SelectJob;

const Workspace: NextPage = () => {
  const [sessionId, setSessionId] = useState("");
  const [pendingJob, setPendingJob] = useState<Job | null>(null);
  const getClient = useApi();

  useEffect(() => {
    const createSession = async () => {
      if (!getClient) return;
      const client = await getClient;
      const response = await client.create_session_session_post();
      setSessionId(response.data.session_id);
    };

    createSession().catch(console.error);
  }, [getClient]);

  useEffect(() => {
    if (!sessionId) return;
    if (pendingJob) return;
    let cancelled = false;

    const poll = async () => {
      if (!getClient) return;
      const client = await getClient;

      while (!cancelled) {
        if (pendingJob) continue;
        const response = await client.next_job__session_id__job_get({
          session_id: sessionId,
        });

        if (response.status === 204) continue; // no pending jobs
        const job = response.data;
        setPendingJob(job as Job);
      }
    };

    poll().catch(console.error);
    return () => {
      cancelled = true;
    };
  }, [sessionId, pendingJob, getClient]);

  return (
    <>
      <Header />
      <Container>
        <Box my={16}>
          {!pendingJob && (
            <Center>
              <VStack spacing={5}>
                <Spinner />
                <Box>Loading workspace...</Box>
              </VStack>
            </Center>
          )}
          {pendingJob && (
            <PendingJob
              sessionId={sessionId}
              job={pendingJob}
              onComplete={() => setPendingJob(null)}
            />
          )}
        </Box>
      </Container>
    </>
  );
};

export default Workspace;
