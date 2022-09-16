import { Components } from "../client";
import { Job } from "../pages/workspace";
import Answer from "./Answer";
import Checkboxes from "./Checkboxes";
import Print from "./Print";
import Score from "./Score";
import Select from "./Select";

const isPrint = (job: Job): job is Components.Schemas.PrintJob => {
  return job.type === "print";
};

const isCheckboxes = (job: Job): job is Components.Schemas.CheckboxesJob => {
  return job.type === "checkboxes";
};

const isAnswer = (job: Job): job is Components.Schemas.AnswerJob => {
  return job.type === "answer";
};

const isSelect = (job: Job): job is Components.Schemas.SelectJob => {
  return job.type === "select";
};

const isScore = (job: Job): job is Components.Schemas.ScoreJob => {
  return job.type === "score";
};

const PendingJob = ({
  sessionId,
  job,
  onComplete,
}: {
  sessionId: string;
  job: Job;
  onComplete: () => void;
}) => {
  return (
    <>
      {isPrint(job) && <Print sessionId={sessionId} job={job} onComplete={onComplete} />}
      {isCheckboxes(job) && <Checkboxes sessionId={sessionId} job={job} onComplete={onComplete} />}
      {isAnswer(job) && <Answer sessionId={sessionId} job={job} onComplete={onComplete} />}
      {isSelect(job) && <Select sessionId={sessionId} job={job} onComplete={onComplete} />}
      {isScore(job) && <Score sessionId={sessionId} job={job} onComplete={onComplete} />}
    </>
  );
};

export default PendingJob;
