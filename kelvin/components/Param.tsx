import { ActionParam } from "../types";

type Props = {
  param: ActionParam;
};

const Param = ({ param }: Props) => {
  return (
    <span className="bg-white px-2 py-1 rounded-md border border-gray-300">
      {`${param.name}: ${param.kind}`}
    </span>
  );
};

export default Param;
